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
        payload = await request.json()
        logger.info(f"Received WhatsApp webhook: {json.dumps(payload, indent=2)}")
        
        # Initialize services
        supabase_service = SupabaseService(db)
        whatsapp_service = WhatsAppService()
        ai_coach = AICoachService()
        
        # Process webhook payload
        if payload.get("object") == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        await process_message(
                            change["value"], 
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

async def process_message(
    message_data: Dict[str, Any],
    supabase_service: SupabaseService,
    whatsapp_service: WhatsAppService,
    ai_coach: AICoachService
):
    """Process individual WhatsApp message"""
    
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
        
        # Send welcome message and start onboarding
        welcome_message = await ai_coach.generate_welcome_message(subscription)
        await whatsapp_service.send_message(wa_id, welcome_message)
        
        logger.info(f"Successfully activated subscription for {wa_id}")
        
    except Exception as e:
        logger.error(f"Error in activation: {e}")
        await whatsapp_service.send_message(
            wa_id,
            "❌ Something went wrong during activation. Please contact support."
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
    Handle regular coaching conversation messages
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