"""
Celery tasks for async AI coach response processing
Protects AICoachService from webhook timeouts and provides reliable delivery
Uses exact patterns from onboarding_tasks.py for proven reliability
"""

from celery import current_app
from celery.exceptions import Retry
from typing import Dict, Any, Optional
import time
import hashlib
import asyncio

# Use structured logging with fallback support (same as onboarding)
try:
    import structlog
    logger = structlog.get_logger(__name__)
    IS_STRUCTLOG = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    IS_STRUCTLOG = False

# Helper functions to handle both structlog and standard logging (exact copy from onboarding)
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

# Safe service imports (following established patterns)
from app.services.whatsapp_service import WhatsAppService
from app.services.supabase_client import SupabaseService
from app.services.ai_coach import AICoachService
from app.deps import get_supabase_client

# Redis idempotency helper (reuse from onboarding pattern)
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
    return f"ai_coach:{user_id}:{message_hash}"

async def send_message_once(whatsapp_service, wa_id: str, message: str, dedupe_key: str = None) -> bool:
    """Send message with Redis-based idempotency guard"""
    import os
    
    # Check if deduplication is enabled via environment variable
    deduplication_enabled = os.getenv("DEDUPLICATION_ENABLED", "false").lower() == "true"
    ttl_seconds = int(os.getenv("DEDUP_TTL_SECONDS", "60"))
    
    redis = get_redis_client()
    
    # Skip deduplication if disabled, no Redis, or no dedupe key
    if not deduplication_enabled or not redis or not dedupe_key:
        if not deduplication_enabled:
            log_info("redis_deduplication_disabled_by_config", wa_id=wa_id, dedupe_key=dedupe_key)
        elif not redis:
            log_info("redis_deduplication_unavailable", wa_id=wa_id, dedupe_key=dedupe_key)
        return await whatsapp_service.send_message(wa_id, message)
    
    # Check for existing message in Redis cache
    try:
        if redis.exists(dedupe_key):
            log_warning("duplicate_message_suppressed", 
                       wa_id=wa_id, 
                       dedupe_key=dedupe_key,
                       ttl_seconds=ttl_seconds)
            return True
    except Exception as redis_error:
        log_warning("redis_dedup_check_failed", 
                   error=str(redis_error),
                   wa_id=wa_id,
                   dedupe_key=dedupe_key)
        # Continue with sending if Redis check fails
    
    # Send the message
    success = await whatsapp_service.send_message(wa_id, message)
    
    # Cache successful send in Redis
    if success:
        try:
            redis.setex(dedupe_key, ttl_seconds, "sent")
            log_info("message_dedupe_cached", 
                    dedupe_key=dedupe_key,
                    ttl_seconds=ttl_seconds)
        except Exception as redis_error:
            log_warning("redis_dedup_cache_failed",
                       error=str(redis_error),
                       dedupe_key=dedupe_key)
            # Don't fail the overall operation if caching fails
    
    return success

@current_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_ai_coach_response_async(self, user_id: str, wa_id: str, user_message: str, user_context: Dict[str, Any], message_sid: str, correlation_id: str = None):
    """
    Protective angel for AICoachService - handles 24/7 conversational AI responses in background
    Prevents webhook timeouts while providing reliable AI coach delivery
    
    This is NOT for scheduled coaching messages (that's daily_messages.py)
    This is for real-time chat responses when users message the AI coach directly
    
    Args:
        user_id: User ID from database
        wa_id: WhatsApp ID to send message to (format: whatsapp:+1234567890)
        user_message: User's message content
        user_context: User subscription context
        message_sid: Twilio MessageSid for deduplication
        correlation_id: Request correlation ID for tracing
    """
    start_time = time.time()
    
    # Create deduplication key for conversational AI response
    dedupe_key = create_dedupe_key(user_id, f"conversation_{user_message}")
    
    try:
        log_info("ai_coach_async_start",
                   user_id=user_id,
                   wa_id=wa_id,
                   correlation_id=correlation_id,
                   dedupe_key=dedupe_key,
                   retry_count=self.request.retries)
        
        # Initialize services (same pattern as onboarding and daily_messages)
        whatsapp_service = WhatsAppService()
        db = get_supabase_client()
        supabase_service = SupabaseService(db)
        ai_coach = AICoachService(supabase_service)
        
        # Generate AI response with timeout protection (this is the heavy operation)
        try:
            ai_response = asyncio.run(
                asyncio.wait_for(
                    ai_coach.generate_response(
                        user_id=user_id,
                        message=user_message,
                        user_context=user_context
                    ),
                    timeout=25.0  # 25 second timeout to prevent webhook issues
                )
            )
            log_info("ai_response_generated",
                       user_id=user_id,
                       correlation_id=correlation_id,
                       response_length=len(ai_response))
        except asyncio.TimeoutError:
            log_error("ai_response_timeout",
                        user_id=user_id,
                        wa_id=wa_id,
                        correlation_id=correlation_id,
                        timeout_seconds=25)
            # Use AICoachService fallback mechanism
            ai_response = ai_coach._get_fallback_response(user_message)
        except Exception as ai_error:
            log_error("ai_response_error",
                        user_id=user_id,
                        correlation_id=correlation_id,
                        error=str(ai_error))
            # Use AICoachService fallback mechanism
            ai_response = ai_coach._get_fallback_response(user_message)
        
        # Send AI response with idempotency guard (reuse existing pattern)
        success = asyncio.run(send_message_once(whatsapp_service, wa_id, ai_response, dedupe_key))
        
        if success:
            # Log AI response to database (same pattern as webhook)
            asyncio.run(supabase_service.log_conversation(
                user_id,
                ai_response,
                "assistant",
                None  # No message_id for outbound messages
            ))
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        if success:
            log_info("ai_coach_async_success",
                       user_id=user_id,
                       wa_id=wa_id,
                       correlation_id=correlation_id,
                       duration_ms=duration_ms,
                       idempotent=True)
            return {"status": "success", "user_id": user_id, "wa_id": wa_id}
        else:
            log_error("ai_coach_async_failed",
                        user_id=user_id,
                        wa_id=wa_id,
                        correlation_id=correlation_id,
                        duration_ms=duration_ms)
            raise Exception(f"WhatsApp delivery failed")
            
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        log_error("ai_coach_async_error",
                    user_id=user_id,
                    wa_id=wa_id,
                    correlation_id=correlation_id,
                    error=str(exc),
                    retry_count=self.request.retries,
                    duration_ms=duration_ms)
        
        # Exponential backoff retry (same pattern as onboarding)
        retry_delay = 30 * (2 ** self.request.retries)
        
        raise self.retry(
            exc=exc,
            countdown=retry_delay,
            max_retries=3
        )