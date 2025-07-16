"""
Celery tasks for onboarding message sending
Handles WhatsApp message delivery with retry logic and exponential backoff
"""

import logging
from celery import current_app
from celery.exceptions import Retry
from typing import Dict, Any, Optional

from app.services.whatsapp_service import WhatsAppService
from app.services.supabase_client import SupabaseService
from app.deps import get_supabase_client

logger = logging.getLogger(__name__)

@current_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_onboarding_message(self, wa_id: str, message: str, message_type: str = "onboarding"):
    """
    Send onboarding message via WhatsApp with retry logic
    
    Args:
        wa_id: WhatsApp ID to send message to
        message: Message content to send
        message_type: Type of message for logging
    """
    try:
        logger.info(f"Sending {message_type} message to {wa_id}")
        
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Send message (using asyncio.run for async call)
        import asyncio
        success = asyncio.run(whatsapp_service.send_message(wa_id, message))
        
        if success:
            logger.info(f"Successfully sent {message_type} message to {wa_id}")
            return {"status": "success", "wa_id": wa_id, "message_type": message_type}
        else:
            logger.error(f"Failed to send {message_type} message to {wa_id}")
            raise Exception(f"WhatsApp message sending failed for {wa_id}")
            
    except Exception as exc:
        logger.error(f"Error sending {message_type} message to {wa_id}: {exc}")
        
        # Exponential backoff retry
        retry_delay = 60 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_onboarding_welcome_flow(self, user_id: str, wa_id: str):
    """
    Send welcome message + first question for onboarding
    
    Args:
        user_id: User ID from database
        wa_id: WhatsApp ID to send messages to
    """
    try:
        logger.info(f"Starting onboarding welcome flow for user {user_id}")
        
        # Initialize services
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        whatsapp_service = WhatsAppService()
        
        # Get onboarding messages
        from app.services.onboarding_service import OnboardingService
        onboarding_service = OnboardingService(supabase_service)
        
        # Use sync version of start_onboarding (we need to create this)
        from app.services.onboarding_service import OnboardingStep
        messages = {
            "welcome_message": onboarding_service.get_welcome_message(),
            "first_question": onboarding_service.questions.get(OnboardingStep.START)
        }
        
        # Set initial onboarding state in database
        import asyncio
        asyncio.run(supabase_service.set_preference_value(user_id, "onboarding_step", "morning_affirmation"))
        
        if not messages:
            logger.error(f"No onboarding messages generated for user {user_id}")
            return {"status": "error", "message": "No messages generated"}
        
        # Send welcome message
        welcome_msg = messages.get("welcome_message")
        if welcome_msg:
            import asyncio
            success = asyncio.run(whatsapp_service.send_message(wa_id, welcome_msg))
            if not success:
                raise Exception("Failed to send welcome message")
        
        # Send first question
        first_question = messages.get("first_question")
        if first_question:
            import asyncio
            success = asyncio.run(whatsapp_service.send_message(wa_id, first_question))
            if not success:
                raise Exception("Failed to send first question")
        
        logger.info(f"Successfully sent onboarding welcome flow to {user_id}")
        return {"status": "success", "user_id": user_id, "wa_id": wa_id}
        
    except Exception as exc:
        logger.error(f"Error in onboarding welcome flow for {user_id}: {exc}")
        
        # Exponential backoff retry
        retry_delay = 60 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_onboarding_response(self, user_id: str, wa_id: str, response_message: str):
    """
    Send onboarding response message (next question or completion)
    
    Args:
        user_id: User ID from database
        wa_id: WhatsApp ID to send message to
        response_message: Message to send
    """
    try:
        logger.info(f"Sending onboarding response to user {user_id}")
        
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Send response message
        import asyncio
        success = asyncio.run(whatsapp_service.send_message(wa_id, response_message))
        
        if success:
            logger.info(f"Successfully sent onboarding response to {user_id}")
            return {"status": "success", "user_id": user_id, "wa_id": wa_id}
        else:
            logger.error(f"Failed to send onboarding response to {user_id}")
            raise Exception(f"WhatsApp message sending failed for {user_id}")
            
    except Exception as exc:
        logger.error(f"Error sending onboarding response to {user_id}: {exc}")
        
        # Exponential backoff retry
        retry_delay = 30 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=2, default_retry_delay=120)
def log_onboarding_progress(self, user_id: str, step: str, response: str, success: bool):
    """
    Log onboarding progress to database
    
    Args:
        user_id: User ID from database
        step: Current onboarding step
        response: User's response
        success: Whether the step was completed successfully
    """
    try:
        logger.info(f"Logging onboarding progress for user {user_id}, step {step}")
        
        # Initialize database service
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        
        # Log the conversation
        message_type = f"onboarding_{step}"
        
        # Log conversation using asyncio.run for database operations
        import asyncio
        result = asyncio.run(supabase_service.log_conversation(
            user_id, 
            response, 
            message_type
        ))
        
        logger.info(f"Successfully logged onboarding progress for user {user_id}")
        return {"status": "success", "user_id": user_id, "step": step}
        
    except Exception as exc:
        logger.error(f"Error logging onboarding progress for {user_id}: {exc}")
        
        # Retry with longer delay for database operations
        retry_delay = 120 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=2
        )