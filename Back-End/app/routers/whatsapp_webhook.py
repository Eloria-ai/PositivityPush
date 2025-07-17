"""
WhatsApp Webhook Handler for Positivity Push
Handles incoming WhatsApp messages and AI coaching conversations.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
import json
import logging
from typing import Dict, Any, Optional

from app.config import settings
from app.deps import get_supabase_client
from app.services.whatsapp_service import WhatsAppService
from app.services.ai_coach import AICoachService
from app.services.supabase_client import SupabaseService
from app.services.onboarding_service import OnboardingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

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
        # Initialize services
        supabase_service = SupabaseService(db)
        whatsapp_service = WhatsAppService()
        ai_coach = AICoachService()
        
        # Try to get JSON data first (WhatsApp Business API)
        try:
            json_data = await request.json()
            logger.info(f"Received WhatsApp Business API webhook: {json_data}")
            
            # Handle WhatsApp Business API format
            if json_data.get("object") == "whatsapp_business_account":
                await process_whatsapp_business_message(
                    json_data,
                    supabase_service,
                    whatsapp_service,
                    ai_coach
                )
                return JSONResponse(content={"status": "success"})
        
        except Exception:
            # Fall back to Twilio format (form data)
            form_data = await request.form()
            logger.info(f"Received Twilio WhatsApp webhook: {dict(form_data)}")
            
            # Extract message data from Twilio format
            message_body = form_data.get("Body", "")
            from_number = form_data.get("From", "")
            to_number = form_data.get("To", "")
            
            # Clean phone numbers (remove "whatsapp:" prefix)
            from_number = from_number.replace("whatsapp:", "") if from_number else ""
            to_number = to_number.replace("whatsapp:", "") if to_number else ""
            
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
                    from_number,
                    to_number,
                    subscription,
                    supabase_service,
                    whatsapp_service,
                    ai_coach
                )
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

async def process_whatsapp_business_message(
    webhook_data: Dict[str, Any],
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
):
    """Process WhatsApp Business API webhook data"""
    
    entries = webhook_data.get("entry", [])
    
    for entry in entries:
        changes = entry.get("changes", [])
        
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            for message in messages:
                # Skip status messages
                if message.get("type") == "status":
                    continue
                    
                wa_id = message["from"]
                message_text = message.get("text", {}).get("body", "")
                message_id = message["id"]
                
                logger.info(f"Processing WhatsApp Business message from {wa_id}: {message_text}")
                
                # Look up subscription
                subscription = await supabase_service.get_subscription_by_wa_id(wa_id)
                logger.info(f"SUBSCRIPTION LOOKUP for '{wa_id}': {subscription is not None}")
                
                # Check if this is an activation message
                if message_text.startswith("POSITIVITY-PUSH START"):
                    await handle_activation_message(
                        wa_id, message_text, supabase_service, whatsapp_service, ai_coach
                    )
                else:
                    # Handle regular coaching conversation
                    await handle_coaching_message_with_subscription(
                        wa_id, message_text, message_id, subscription, supabase_service, whatsapp_service, ai_coach
                    )

async def process_message(
    message_data: Dict[str, Any],
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
):
    """Process individual WhatsApp message (legacy)"""
    
    messages = message_data.get("messages", [])
    
    for message in messages:
        # Skip status messages
        if message.get("type") == "status":
            continue
            
        wa_id = message["from"]
        message_text = message.get("text", {}).get("body", "")
        message_id = message["id"]
        
        logger.info(f"Processing message from {wa_id}: {message_text}")
        
        # Check if this is an activation message
        if message_text.startswith("POSITIVITY-PUSH START"):
            await handle_activation_message(
                wa_id, message_text, supabase_service, whatsapp_service, ai_coach
            )
        else:
            # Handle regular coaching conversation
            await handle_coaching_message(
                wa_id, message_text, message_id, supabase_service, whatsapp_service, ai_coach
            )

async def process_twilio_message(
    message_body: str,
    from_number: str,
    to_number: str,
    subscription: dict,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
):
    """Process message from Twilio WhatsApp webhook"""
    
    logger.info(f"Processing Twilio message from {from_number}: {message_body}")
    
    # Check if this is an activation message
    if message_body.startswith("POSITIVITY-PUSH START"):
        await handle_activation_message(
            from_number, message_body, supabase_service, whatsapp_service, ai_coach
        )
    else:
        # Handle regular coaching conversation - pass the subscription we already found
        await handle_coaching_message_with_subscription(
            from_number, message_body, None, subscription, supabase_service, whatsapp_service, ai_coach
        )

async def handle_activation_message(
    wa_id: str,
    message_text: str,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
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
        
        # Activate subscription
        await supabase_service.update_subscription(
            subscription["id"],
            {
                "wa_id": wa_id,
                "status": "active",
                "activated_at": "now()"
            }
        )
        
        # Start onboarding process via Celery task with client IP for timezone detection
        # Note: For WhatsApp webhook, we don't have direct access to user's IP
        # The IP we get is from Twilio/Meta servers, not user's actual IP
        client_ip = None  # Will fallback to UTC timezone detection
        logger.info(f"Starting onboarding with timezone detection")
        
        from worker.tasks.onboarding_tasks import send_onboarding_welcome_flow
        send_onboarding_welcome_flow.delay(subscription["id"], wa_id, client_ip)
        
        logger.info(f"Successfully activated subscription and started onboarding for {wa_id}")
        
    except Exception as e:
        logger.error(f"Error in activation: {e}")
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
    ai_coach: AICoachService
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
        
        # Check if user is in onboarding process
        logger.error(f"🚨 WEBHOOK DEBUG - About to check onboarding for user {subscription['id']}")
        onboarding_service = OnboardingService(supabase_service)
        onboarding_result = await onboarding_service.process_webhook_message(
            subscription["id"], wa_id, message_text
        )
        logger.error(f"🚨 WEBHOOK DEBUG - Onboarding result: {onboarding_result}")
        
        # If in onboarding, enqueue response message and return
        if onboarding_result.get("is_onboarding"):
            response_message = onboarding_result.get("message")
            if response_message:
                from worker.tasks.onboarding_tasks import send_onboarding_response
                send_onboarding_response.delay(subscription["id"], wa_id, response_message)
            
            # Check if onboarding was completed in this interaction
            if onboarding_result.get("completed"):
                logger.info(f"🎉 Onboarding completed for user {subscription['id']}")
                # Mark onboarding as completed in database
                await supabase_service.mark_onboarding_completed(subscription["id"])
                # Clear onboarding step
                await supabase_service.set_preference_value(subscription["id"], "onboarding_step", None)
                logger.info(f"✅ Database updated: onboarding_completed = True for user {subscription['id']}")
            
            return
        
        # Log conversation
        await supabase_service.log_conversation(
            subscription["id"],
            message_text,
            "user",
            message_id
        )
        
        # Generate AI response
        ai_response = await ai_coach.generate_response(
            user_id=subscription["id"],
            message=message_text,
            user_context=subscription
        )
        
        # Send AI response
        await whatsapp_service.send_message(wa_id, ai_response)
        
        # Log AI response
        await supabase_service.log_conversation(
            subscription["id"],
            ai_response,
            "assistant",
            None
        )
        
        logger.info(f"Successfully handled coaching message for {wa_id}")
        
    except Exception as e:
        logger.error(f"Error in coaching conversation: {e}")
        await whatsapp_service.send_message(
            wa_id,
            "❌ Something went wrong. Please try again or contact support."
        )

async def handle_coaching_message(
    wa_id: str,
    message_text: str,
    message_id: str,
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
):
    """
    Handle regular coaching conversation messages (legacy function)
    Generate AI responses based on user context
    """
    
    try:
        # Check if user has active subscription
        subscription = await supabase_service.get_subscription_by_wa_id(wa_id)
        
        if not subscription or subscription.get("status") != "active":
            await whatsapp_service.send_message(
                wa_id,
                "❌ No active subscription found. Please complete your payment first at https://positivity-push.vercel.app"
            )
            return
        
        # Log conversation
        await supabase_service.log_conversation(
            subscription["id"],
            message_text,
            "user",
            message_id
        )
        
        # Generate AI response
        ai_response = await ai_coach.generate_response(
            user_id=subscription["id"],
            message=message_text,
            user_context=subscription
        )
        
        # Send AI response
        await whatsapp_service.send_message(wa_id, ai_response)
        
        # Log AI response
        await supabase_service.log_conversation(
            subscription["id"],
            ai_response,
            "assistant",
            None
        )
        
        logger.info(f"Successfully handled coaching message for {wa_id}")
        
    except Exception as e:
        logger.error(f"Error in coaching message: {e}")
        await whatsapp_service.send_message(
            wa_id,
            "❌ I'm having trouble right now. Please try again in a moment."
        )

@router.get("/health")
async def whatsapp_health():
    """Health check for WhatsApp integration"""
    return {"status": "healthy", "service": "whatsapp-webhook"}