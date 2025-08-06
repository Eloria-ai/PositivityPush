"""
WhatsApp Webhook Handler for Positivity Push
Handles incoming WhatsApp messages and AI coaching conversations.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.deps import get_supabase_client
from app.services.whatsapp_service import WhatsAppService
from app.services.supabase_client import SupabaseService
from app.services.onboarding_service import OnboardingService
from app.services.timezone_service import TimezoneService
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("app.webhooks.whatsapp")

router = APIRouter()

def extract_client_ip(request: Request) -> str:
    """Extract real client IP from request headers"""
    return (
        request.headers.get("cf-connecting-ip") or
        request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
        request.headers.get("x-real-ip") or
        getattr(request.client, 'host', None) or
        "unknown"
    )

@router.get("/webhook")
async def whatsapp_webhook_verify(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Verify WhatsApp webhook endpoint
    Meta requires this for webhook setup
    """
    if mode == "subscribe" and token == settings.WA_WEBHOOK_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(challenge)
    else:
        logger.error("WhatsApp webhook verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed"
        )

@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    db = Depends(get_supabase_client)
):
    """
    Handle incoming WhatsApp messages
    Process activation messages and AI coaching conversations
    """
    
    try:
        # Extract client IP and correlation ID for timezone detection and tracing
        client_ip = extract_client_ip(request)
        correlation_id = getattr(request.state, 'correlation_id', None)
        logger.info(f"Twilio WhatsApp webhook received from IP: {client_ip}")
        
        # Initialize services
        supabase_service = SupabaseService(db)
        whatsapp_service = WhatsAppService()
        
        # Parse Twilio form data
        form_data = await request.form()
        logger.info(f"Received Twilio WhatsApp webhook: {dict(form_data)}")
        
        # Extract message data from Twilio format
        message_body = form_data.get("Body", "")
        from_number_raw = form_data.get("From", "")
        to_number = form_data.get("To", "")
        message_sid = form_data.get("MessageSid", "")  # Twilio's unique message ID
        
        # Store both formats - raw for message sending, clean for database lookup
        from_number_full = from_number_raw  # Keep whatsapp:+31657779475 for sending
        from_number = from_number_raw.replace("whatsapp:", "") if from_number_raw else ""  # +31657779475 for DB lookup
        
        logger.info(f"Phone number formats - Raw: {from_number_raw}, DB lookup: {from_number}, Sending: {from_number_full}")
        
        logger.info(f"Message from {from_number}: {message_body}")
        
        if message_body and from_number:
            # Look up subscription once here
            subscription = await supabase_service.get_subscription_by_wa_id(from_number)
            logger.info(f"SUBSCRIPTION LOOKUP for '{from_number}': {subscription is not None}")
            if subscription:
                logger.info(f"Found subscription ID: {subscription.get('id')}, Status: {subscription.get('status')}")
            else:
                logger.info(f"No subscription found for {from_number} - will send test response")
            
            await process_twilio_message(
                message_body,
                from_number,  # Clean format for DB operations
                from_number_full,  # Full format for message sending
                to_number,
                message_sid,  # Twilio message ID for deduplication
                subscription,
                supabase_service,
                whatsapp_service,
                client_ip=client_ip,
                correlation_id=correlation_id
            )
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

async def process_twilio_message(
    message_body: str,
    from_number: str,  # Clean format for DB operations (+31657779475)
    from_number_full: str,  # Full format for message sending (whatsapp:+31657779475)
    to_number: str,
    message_sid: str,  # Twilio message ID for deduplication
    subscription: dict,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    client_ip: str = None,
    correlation_id: str = None
):
    """Process message from Twilio WhatsApp webhook"""
    
    logger.info(f"Processing Twilio message from {from_number}: {message_body}")
    
    # Check if this is an activation message
    if message_body.startswith("POSITIVITY-PUSH START"):
        await handle_activation_message(
            from_number, message_body, supabase_service, whatsapp_service, correlation_id
        )
    else:
        # Handle regular coaching conversation - use full format for message sending
        await handle_coaching_message_with_subscription(
            from_number_full, message_body, message_sid, subscription, supabase_service, whatsapp_service, client_ip=client_ip, message_metadata=None, correlation_id=correlation_id
        )

async def handle_activation_message(
    wa_id: str,
    message_text: str,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    correlation_id: str = None
):
    """
    Handle POSITIVITY-PUSH START activation messages
    Links WhatsApp ID to subscription and starts coaching
    """
    
    try:
        # Extract session ID from message
        parts = message_text.split()
        if len(parts) < 3:
            await whatsapp_service.send_message(
                wa_id, 
                "❌ Invalid activation message. Please use the link from your payment confirmation."
            )
            return
        
        session_id = parts[2]
        logger.info(f"Activating subscription for session: {session_id}")
        
        # Find subscription by session ID
        subscription = await supabase_service.get_subscription_by_session(session_id)
        
        if not subscription:
            await whatsapp_service.send_message(
                wa_id,
                "❌ Invalid session ID. Please check your payment confirmation or contact support."
            )
            return
        
        if subscription.get("status") == "active":
            await whatsapp_service.send_message(
                wa_id,
                "✅ Your AI coach is already activated! How can I help you today?"
            )
            return
        
        # Activate subscription - store wa_id in clean format for consistency with existing data
        await supabase_service.update_subscription(
            subscription["id"],
            {
                "wa_id": wa_id,
                "status": "active",
                "activated_at": "now()"
            }
        )
        
        # Start onboarding process via Celery task with client IP for timezone detection
        # Try to get stored client IP from the subscription activation
        stored_client_ip = subscription.get("client_ip")
        client_ip = stored_client_ip if stored_client_ip else None
        
        # correlation_id is now passed as parameter
        
        if client_ip:
            logger.info("activation_using_stored_ip", 
                       wa_id=wa_id,
                       client_ip=client_ip,
                       correlation_id=correlation_id)
        else:
            logger.info("activation_no_ip_fallback", 
                       wa_id=wa_id,
                       correlation_id=correlation_id)
        
        from worker.tasks.onboarding_tasks import send_onboarding_welcome_flow
        send_onboarding_welcome_flow.delay(
            subscription["id"], 
            wa_id, 
            client_ip,
            correlation_id=correlation_id
        )
        
        logger.info("subscription_activated_onboarding_started", 
                   wa_id=wa_id,
                   user_id=subscription["id"],
                   correlation_id=correlation_id)
        
    except Exception as e:
        logger.error("activation_error", 
                    wa_id=wa_id,
                    error=str(e),
                    correlation_id=correlation_id,
                    exc_info=True)
        await whatsapp_service.send_message(
            wa_id,
            "❌ Something went wrong during activation. Please contact support."
        )

async def handle_coaching_message_with_subscription(
    wa_id: str,
    message_text: str,
    message_id: str,
    subscription: dict,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    client_ip: str = None,
    message_metadata: dict = None,
    correlation_id: str = None
):
    """
    Handle regular coaching conversation messages with pre-fetched subscription
    Generate AI responses based on user context
    """
    
    try:
        # Check if subscription exists and is active
        if not subscription or subscription.get("status") != "active":
            await whatsapp_service.send_message(
                wa_id,
                "❌ No active subscription found. Please complete your payment first at https://positivity-push.vercel.app"
            )
            return
        
        # Deduplication: Check if we've already processed this message
        if message_id:
            # Check if we've already processed this Twilio MessageSid
            existing_conversation = await supabase_service.get_conversation_by_message_id(message_id)
            if existing_conversation:
                logger.info(f"Duplicate message detected - already processed MessageSid: {message_id}")
                return  # Skip processing duplicate message
        
        # Note: Automatic timezone detection removed - users now update timezone manually
        # via natural language (e.g., "I'm in London now") or during onboarding
        
        # Check for natural language timezone updates (e.g., "I'm in London now", "Africa/Casablanca")
        timezone_service = TimezoneService()
        detected_timezone = timezone_service.extract_timezone(message_text)
        if detected_timezone:
            await supabase_service.update_subscription(
                subscription["id"], 
                {
                    'current_timezone': detected_timezone,
                    'timezone_updated_at': datetime.utcnow().isoformat()
                }
            )
            # Check if user is in onboarding to show appropriate message
            preferences = await supabase_service.get_user_preferences(subscription["id"])
            is_onboarding = not preferences.get("onboarding_completed", True)
            
            if is_onboarding:
                # During onboarding - timezone is being set for first time
                await whatsapp_service.send_message(
                    wa_id,
                    f"🌍 Perfect! I've set your timezone to {detected_timezone}. Your personalized messages will be perfectly timed for you!"
                )
                
                # Check if onboarding is now complete after timezone update
                onboarding_service = OnboardingService(supabase_service)
                
                # Get updated preferences (including the new timezone)
                updated_preferences = await supabase_service.get_user_preferences(subscription["id"])
                completion_status = await onboarding_service.check_completion_status(updated_preferences)
                
                if completion_status["is_complete"]:
                    # Onboarding is complete! Send completion message and create scheduled messages
                    await supabase_service.mark_onboarding_completed(subscription["id"])
                    await supabase_service.set_preference_value(subscription["id"], "onboarding_step", None)
                    
                    completion_message = onboarding_service.get_completion_message()
                    await whatsapp_service.send_message(wa_id, completion_message)
                    
                    logger.info(f"✅ Onboarding completed after timezone detection for user {subscription['id']}")
            else:
                # After onboarding - timezone is being changed/updated
                await whatsapp_service.send_message(
                    wa_id,
                    f"🌍 Got it! I've switched you to {detected_timezone}. Your schedule is now in sync with your current location!"
                )
            return
        
        # Check for timezone update command - privacy-first approach
        if message_text.lower().strip() in ["update timezone", "timezone", "change timezone", "fix timezone"]:
            await whatsapp_service.send_message(
                wa_id,
                "🌍 I'd love to update your timezone! Please tell me your location like 'I'm in Amsterdam' or 'Europe/London'."
            )
            return
        
        # Check if user is in onboarding process
        logger.info(f"Checking onboarding status for user {subscription['id']}")
        try:
            onboarding_service = OnboardingService(supabase_service)
            onboarding_result = await onboarding_service.process_webhook_message(
                subscription["id"], wa_id, message_text
            )
            logger.info(f"Onboarding result: {onboarding_result}")
        except Exception as onboarding_error:
            logger.error(f"CRITICAL: Onboarding service failed for user {subscription['id']}: {onboarding_error}")
            # Send error message to user and continue
            await whatsapp_service.send_message(
                wa_id,
                "I'm having a technical issue right now. Let me try to help you anyway!"
            )
            # Set a default result to prevent webhook from failing
            onboarding_result = {"is_onboarding": False, "completed": False}
        
        # If in onboarding, enqueue response message and return
        if onboarding_result.get("is_onboarding"):
            response_message = onboarding_result.get("message")
            # correlation_id is now passed as parameter
            
            if response_message:
                logger.info(f"DISPATCHING CELERY TASK: message='{response_message}' to wa_id={wa_id}")
                from worker.tasks.onboarding_tasks import send_onboarding_response
                task = send_onboarding_response.delay(
                    subscription["id"], 
                    wa_id, 
                    response_message,
                    correlation_id=correlation_id
                )
                logger.info(f"CELERY TASK DISPATCHED: task_id={task.id}")
            else:
                logger.error(f"NO RESPONSE MESSAGE TO SEND: onboarding_result={onboarding_result}")
            
            # Onboarding completion is now handled internally by OnboardingService
            # No need for external completion logic - service manages its own state
            if onboarding_result.get("completed"):
                logger.info("onboarding_completed", 
                           user_id=subscription['id'],
                           wa_id=wa_id,
                           correlation_id=correlation_id)
            
            return
        
        # Log user conversation immediately
        await supabase_service.log_conversation(
            subscription["id"],
            message_text,
            "user",
            message_id
        )
        
        # Dispatch AI response generation to background task (prevents webhook timeout)
        from worker.tasks.ai_coach_async import send_ai_coach_response_async
        task = send_ai_coach_response_async.delay(
            subscription["id"],  # user_id
            wa_id,              # wa_id (format: whatsapp:+1234567890)
            message_text,       # user_message
            subscription,       # user_context
            message_id,         # message_sid
            correlation_id      # correlation_id
        )
        
        logger.info(f"AI coach response queued for background processing", 
                   task_id=task.id, wa_id=wa_id, correlation_id=correlation_id)
        
    except Exception as e:
        logger.error(f"Error in coaching conversation: {e}")
        await whatsapp_service.send_message(
            wa_id,
            "❌ Something went wrong. Please try again or contact support."
        )

@router.post("/store-client-ip")
async def store_client_ip(
    request: Request,
    db = Depends(get_supabase_client)
):
    """
    Store client IP address for timezone detection
    Called by frontend before user activates WhatsApp
    """
    try:
        # Get request data
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id is required"
            )
        
        # Get real client IP from headers
        client_ip = extract_client_ip(request)
        
        logger.info(f"Storing client IP {client_ip} for session {session_id}")
        
        # Initialize database service
        supabase_service = SupabaseService(db)
        
        # Update subscription with client IP
        subscription = await supabase_service.get_subscription_by_session(session_id)
        if subscription:
            await supabase_service.update_subscription(
                subscription["id"], 
                {"client_ip": client_ip}
            )
            logger.info(f"Successfully stored client IP for session {session_id}")
            return {"status": "success", "client_ip": client_ip}
        else:
            logger.warning(f"No subscription found for session {session_id}")
            return {"status": "error", "message": "Session not found"}
        
    except Exception as e:
        logger.error(f"Error storing client IP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store client IP"
        )

@router.get("/health")
async def whatsapp_health():
    """Health check for WhatsApp integration"""
    return {"status": "healthy", "service": "whatsapp-webhook"}
