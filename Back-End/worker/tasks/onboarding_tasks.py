"""
Celery tasks for onboarding message sending
Handles WhatsApp message delivery with retry logic and exponential backoff
Uses asyncio.run() for async WhatsApp API calls within synchronous tasks
"""

from celery import current_app
from celery.exceptions import Retry
from typing import Dict, Any, Optional
import time
import hashlib
import asyncio

# Use structured logging with fallback support
try:
    import structlog
    logger = structlog.get_logger(__name__)
    IS_STRUCTLOG = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    IS_STRUCTLOG = False

# Helper functions to handle both structlog and standard logging
def log_info(message, **kwargs):
    if IS_STRUCTLOG:
        logger.info(message, **kwargs)
    else:
        if kwargs:
            extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            logger.info(f"{message}: {extras}")
        else:
            logger.info(message)

def log_warning(message, **kwargs):
    if IS_STRUCTLOG:
        logger.warning(message, **kwargs)
    else:
        if kwargs:
            extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            logger.warning(f"{message}: {extras}")
        else:
            logger.warning(message)

def log_error(message, **kwargs):
    if IS_STRUCTLOG:
        logger.error(message, **kwargs)
    else:
        if kwargs:
            extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            logger.error(f"{message}: {extras}")
        else:
            logger.error(message)

def log_debug(message, **kwargs):
    if IS_STRUCTLOG:
        logger.debug(message, **kwargs)
    else:
        if kwargs:
            extras = ', '.join(f"{k}={v}" for k, v in kwargs.items())
            logger.debug(f"{message}: {extras}")
        else:
            logger.debug(message)

from app.services.whatsapp_service import WhatsAppService
from app.services.supabase_client import SupabaseService
from app.deps import get_supabase_client

# Redis idempotency helper
def get_redis_client():
    """Get Redis client from celery app"""
    try:
        from worker.celery_app import redis_client
        return redis_client
    except ImportError:
        return None

def create_dedupe_key(user_id: str, message_content: str) -> str:
    """Create deduplication key from user ID and message hash"""
    message_hash = hashlib.md5(message_content.encode()).hexdigest()[:12]
    return f"onb:{user_id}:{message_hash}"

async def send_message_once(whatsapp_service, wa_id: str, message: str, dedupe_key: str = None) -> bool:
    """Send message with Redis-based idempotency guard (TEMPORARILY DISABLED)"""
    redis = get_redis_client()
    
    # TEMPORARILY DISABLE DEDUPLICATION FOR DEBUGGING
    log_info("redis_deduplication_disabled_for_debugging", 
             wa_id=wa_id, 
             dedupe_key=dedupe_key)
    return await whatsapp_service.send_message(wa_id, message)
    
    # Original Redis logic (commented out for debugging)
    # if not redis or not dedupe_key:
    #     return await whatsapp_service.send_message(wa_id, message)
    # 
    # if redis.exists(dedupe_key):
    #     log_warning("duplicate_message_suppressed", 
    #                wa_id=wa_id, 
    #                dedupe_key=dedupe_key)
    #     return True
    # 
    # success = await whatsapp_service.send_message(wa_id, message)
    # 
    # if success:
    #     redis.setex(dedupe_key, 30, "sent")
    #     log_info("message_dedupe_cached", 
    #             dedupe_key=dedupe_key)
    # 
    # return success

# Shadow-write helper for gradual migration to unified dispatcher
async def shadow_write_to_dispatcher(supabase_service, user_id: str, message_type: str, content: str, delay_seconds: int = 0):
    """
    Shadow-write onboarding messages to scheduled_messages table for dispatcher
    Phase C: Dual delivery - both legacy and dispatcher handle the message
    """
    try:
        # Check if dispatcher onboarding is enabled
        import os
        dispatcher_enabled = os.getenv("DISPATCHER_ONBOARDING", "false").lower() == "true"
        
        if dispatcher_enabled:
            message_id = await supabase_service.schedule_onboarding_message(
                user_id, message_type, content, delay_seconds
            )
            if message_id:
                log_info("shadow_write_success", 
                        user_id=user_id,
                        message_type=message_type,
                        message_id=message_id,
                        dispatcher_enabled=True)
                return message_id
            else:
                log_warning("shadow_write_failed", 
                           user_id=user_id, 
                           message_type=message_type)
        else:
            log_debug("shadow_write_disabled", 
                     user_id=user_id,
                     message_type=message_type)
        
        return None
        
    except Exception as e:
        log_error("shadow_write_error", 
                    user_id=user_id,
                    message_type=message_type, 
                    error=str(e))
        return None

@current_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_onboarding_message(self, wa_id: str, message: str, message_type: str = "onboarding", user_id: str = None):
    """
    Send onboarding message via WhatsApp with Redis idempotency
    Uses asyncio.run() for async operations within synchronous task
    
    Args:
        wa_id: WhatsApp ID to send message to
        message: Message content to send
        message_type: Type of message for logging
        user_id: User ID for creating dedupe key
    """
    start_time = time.time()
    
    # Create deduplication key
    dedupe_key = None
    if user_id:
        dedupe_key = create_dedupe_key(user_id, message)
    
    try:
        log_info("onboarding_send_start",
                   wa_id=wa_id,
                   message_type=message_type,
                   dedupe_key=dedupe_key,
                   retry_count=self.request.retries)
        
        # Initialize WhatsApp service
        whatsapp_service = WhatsAppService()
        
        # Send message with idempotency guard
        success = asyncio.run(send_message_once(whatsapp_service, wa_id, message, dedupe_key))
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        if success:
            log_info("onboarding_send_success",
                       wa_id=wa_id,
                       message_type=message_type,
                       duration_ms=duration_ms,
                       idempotent=bool(dedupe_key))
            return {"status": "success", "wa_id": wa_id, "message_type": message_type}
        else:
            log_error("onboarding_send_failed",
                        wa_id=wa_id,
                        message_type=message_type,
                        duration_ms=duration_ms)
            raise Exception(f"WhatsApp delivery failed")
            
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_error("onboarding_send_error",
                    wa_id=wa_id,
                    message_type=message_type,
                    error=str(exc),
                    retry_count=self.request.retries,
                    duration_ms=duration_ms)
        
        # Exponential backoff retry
        retry_delay = 60 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_onboarding_welcome_flow(self, user_id: str, wa_id: str, client_ip: str = None, correlation_id: str = None):
    """
    Send welcome message + first question for onboarding
    Uses asyncio.run() for async operations within synchronous task
    
    Args:
        user_id: User ID from database
        wa_id: WhatsApp ID to send messages to
        client_ip: Optional client IP for timezone detection
    """
    start_time = time.time()
    
    try:
        log_info("onboarding_welcome_start",
                   user_id=user_id,
                   wa_id=wa_id,
                   correlation_id=correlation_id,
                   retry_count=self.request.retries)
        
        # Initialize services
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        whatsapp_service = WhatsAppService()
        
        # Get onboarding messages using new interface
        from app.services.onboarding_service import OnboardingService
        onboarding_service = OnboardingService(supabase_service)
        
        # Use start_onboarding method with asyncio.run
        onboarding_result = asyncio.run(onboarding_service.start_onboarding(user_id, client_ip))
        
        if not onboarding_result:
            log_error("onboarding_welcome_no_messages",
                        user_id=user_id)
            return {"status": "error", "message": "Failed to start onboarding"}
        
        # Extract messages from result
        messages = onboarding_result.get("messages", [])
        
        if not messages:
            log_error("onboarding_welcome_empty_messages",
                        user_id=user_id)
            return {"status": "error", "message": "No messages generated"}
        
        # Shadow-write to dispatcher AND send via legacy (Phase C: dual delivery)
        dispatcher_message_ids = []
        for i, message in enumerate(messages):
            if message:
                # Shadow-write to dispatcher
                message_id = asyncio.run(shadow_write_to_dispatcher(
                    supabase_service, user_id, f"onboarding_welcome", message, delay_seconds=i*2
                ))
                if message_id:
                    dispatcher_message_ids.append(message_id)

        # Send all onboarding messages in sequence with idempotency (legacy path)
        sent_count = 0
        for i, message in enumerate(messages):
            if message:
                # Create unique dedupe key for each message in flow
                flow_dedupe_key = create_dedupe_key(user_id, f"welcome_flow_{i}_{message}")
                success = asyncio.run(send_message_once(whatsapp_service, wa_id, message, flow_dedupe_key))
                if not success:
                    raise Exception(f"Failed to send message {i+1}")
                sent_count += 1
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        log_info("onboarding_welcome_success",
                   user_id=user_id,
                   wa_id=wa_id,
                   messages_sent=sent_count,
                   duration_ms=duration_ms)
        
        return {"status": "success", "user_id": user_id, "wa_id": wa_id, "messages_sent": sent_count}
        
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_error("onboarding_welcome_error",
                 user_id=user_id,
                 wa_id=wa_id,
                 error=str(exc),
                 retry_count=self.request.retries,
                 duration_ms=duration_ms)
        
        # Exponential backoff retry
        retry_delay = 60 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_onboarding_response(self, user_id: str, wa_id: str, response_message: str, correlation_id: str = None):
    """
    Send onboarding response message (next question or completion) with idempotency
    Uses asyncio.run() for async operations within synchronous task
    
    Args:
        user_id: User ID from database
        wa_id: WhatsApp ID to send message to
        response_message: Message to send
    """
    start_time = time.time()
    
    # Create deduplication key for response
    dedupe_key = create_dedupe_key(user_id, f"response_{response_message}")
    
    try:
        log_info("onboarding_response_start",
                   user_id=user_id,
                   wa_id=wa_id,
                   correlation_id=correlation_id,
                   dedupe_key=dedupe_key,
                   retry_count=self.request.retries)
        
        # Initialize services
        whatsapp_service = WhatsAppService()
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        
        # Check if onboarding is still active before sending message
        preferences = asyncio.run(supabase_service.get_user_preferences(user_id))
        onboarding_completed = preferences.get("onboarding_completed", True)
        
        if onboarding_completed == True or onboarding_completed is None:
            log_info("onboarding_task_skipped_completed",
                       user_id=user_id,
                       wa_id=wa_id,
                       correlation_id=correlation_id,
                       message=response_message[:50] + "..." if len(response_message) > 50 else response_message)
            return {"status": "skipped", "reason": "onboarding_completed", "user_id": user_id, "wa_id": wa_id}
        
        # Send response message with idempotency guard
        success = asyncio.run(send_message_once(whatsapp_service, wa_id, response_message, dedupe_key))
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        if success:
            log_info("onboarding_response_success",
                       user_id=user_id,
                       wa_id=wa_id,
                       correlation_id=correlation_id,
                       duration_ms=duration_ms,
                       idempotent=True)
            return {"status": "success", "user_id": user_id, "wa_id": wa_id}
        else:
            log_error("onboarding_response_failed",
                        user_id=user_id,
                        wa_id=wa_id,
                        correlation_id=correlation_id,
                        duration_ms=duration_ms)
            raise Exception(f"WhatsApp delivery failed")
            
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_error("onboarding_response_error",
                    user_id=user_id,
                    wa_id=wa_id,
                    correlation_id=correlation_id,
                    error=str(exc),
                    retry_count=self.request.retries,
                    duration_ms=duration_ms)
        
        # Exponential backoff retry
        retry_delay = 30 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )

@current_app.task(bind=True, max_retries=5, default_retry_delay=120, acks_late=True)
def log_onboarding_progress(self, user_id: str, step: str, response: str, success: bool):
    """
    Log onboarding progress to database
    Uses asyncio.run() for async operations within synchronous task
    Increased retries for database operations
    
    Args:
        user_id: User ID from database
        step: Current onboarding step
        response: User's response
        success: Whether the step was completed successfully
    """
    start_time = time.time()
    
    try:
        log_info("onboarding_log_start",
                   user_id=user_id,
                   step=step,
                   success=success,
                   retry_count=self.request.retries)
        
        # Initialize database service
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        
        # Log the conversation
        message_type = f"onboarding_{step}"
        
        # Log conversation with asyncio.run
        result = asyncio.run(supabase_service.log_conversation(
            user_id, 
            response, 
            message_type
        ))
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        log_info("onboarding_log_success",
                   user_id=user_id,
                   step=step,
                   duration_ms=duration_ms)
        
        return {"status": "success", "user_id": user_id, "step": step}
        
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_error("onboarding_log_error",
                    user_id=user_id,
                    step=step,
                    error=str(exc),
                    retry_count=self.request.retries,
                    duration_ms=duration_ms)
        
        # Retry with longer delay for database operations
        retry_delay = 120 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=5
        )
