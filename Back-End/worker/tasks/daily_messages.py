"""
Daily Messaging Tasks for Positivity Push - REFACTORED ARCHITECTURE
Implements driver + dispatcher pattern to respect user preferences from onboarding.
Replaces old timezone-broadcast approach with user-specific scheduling.
"""

from celery import shared_task
from datetime import datetime, timedelta
import time
import asyncio
import sys
import os
from typing import Optional, Dict, List, Tuple

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from services.ai_coach import AICoachService
from services.whatsapp_service import WhatsAppService
from services.supabase_client import SupabaseService
from deps import get_supabase_client
from config import settings

# Configure structured logging for production-ready observability
try:
    import structlog
    import logging
    import sys
    
    # Configure structlog with JSON output for log collectors
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def get_services() -> Tuple[SupabaseService, AICoachService, WhatsAppService]:
    """Utility to avoid duplicating service initialization across tasks"""
    db = get_supabase_client()
    return (
        SupabaseService(db),
        AICoachService(),
        WhatsAppService()
    )

# ===== NEW ARCHITECTURE: DRIVER + DISPATCHER =====

@shared_task(bind=True)
def process_personalized_messages(self, batch_size: int = 500) -> Dict:
    """
    DRIVER TASK: Sweeps scheduled_messages table for due messages and dispatches individual jobs.
    
    Replaces old timezone-broadcast approach with user-specific scheduling.
    Uses existing DB index: idx_scheduled_messages_pending(status, scheduled_for)
    """
    start_time = time.time()
    
    try:
        supabase_service, _, _ = get_services()
        
        # Sweep query using existing index with SKIP LOCKED
        due_messages = asyncio.run(supabase_service.get_due_scheduled_messages(
            batch_size=batch_size,
            use_skip_locked=True
        ))
        
        dispatched_count = 0
        
        for message in due_messages:
            # Enqueue individual dispatcher job for each message
            dispatch_message.delay(message['id'])
            dispatched_count += 1
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            "personalized_messages_sweep",
            messages_claimed=dispatched_count,
            duration_ms=duration_ms,
            batch_size=batch_size
        )
        
        return {
            "dispatched": dispatched_count,
            "duration_ms": duration_ms,
            "status": "success"
        }
        
    except Exception as e:
        logger.error("personalized_messages_sweep_failed", error=str(e))
        raise e

@shared_task(bind=True, max_retries=3)
def dispatch_message(self, message_id: int) -> Dict:
    """
    DISPATCHER TASK: Handles individual message delivery.
    
    Unified dispatcher replaces all the old per-template tasks.
    Each scheduled_messages row becomes exactly one lightweight job.
    """
    try:
        supabase_service, ai_coach, whatsapp_service = get_services()
        
        # Fetch message details and user context
        message_data = asyncio.run(supabase_service.get_message_with_user_context(message_id))
        
        if not message_data:
            logger.warning("message_not_found", message_id=message_id)
            return {"status": "not_found", "message_id": message_id}
        
        subscriber = message_data['subscriber']
        message_type = message_data['message_type']
        
        # Generate content using appropriate AI template or use pre-generated content
        content = asyncio.run(_generate_content_by_type(
            ai_coach, message_type, subscriber['id'], subscriber
        ))
        
        # For onboarding messages, use pre-generated content from the message record
        if not content and message_type in ['onboarding_welcome', 'onboarding_response', 'onboarding_question']:
            # Get pre-generated content from the scheduled message
            full_message = asyncio.run(supabase_service.get_scheduled_message_content(message_id))
            content = full_message.get('content') if full_message else None
            
            if content:
                logger.info("using_pregenerated_content", 
                           message_id=message_id,
                           message_type=message_type)
        
        if not content:
            logger.error("content_generation_failed", 
                        message_id=message_id, 
                        message_type=message_type)
            raise Exception(f"Failed to generate {message_type} content")
        
        # Send and log using common pattern
        success = asyncio.run(_send_and_log(subscriber, content, message_type, supabase_service, whatsapp_service))
        
        if success:
            # Mark message as sent
            asyncio.run(supabase_service.mark_message_sent(message_id))
            
            logger.info("message_sent_successfully",
                       message_id=message_id,
                       message_type=message_type,
                       user_email=subscriber.get('email'))
            
            return {
                "status": "sent",
                "message_id": message_id,
                "message_type": message_type
            }
        else:
            raise Exception("Message delivery failed")
            
    except Exception as e:
        logger.error("message_dispatch_failed", 
                    message_id=message_id, 
                    error=str(e),
                    retry_count=self.request.retries)
        
        # If this is the final retry, mark as failed to prevent infinite requeues
        if self.request.retries >= self.max_retries:
            try:
                supabase_service, _, _ = get_services()
                asyncio.run(supabase_service.mark_message_failed(message_id, str(e)))
                logger.error("message_marked_failed", 
                            message_id=message_id, 
                            final_error=str(e))
                return {"status": "failed", "message_id": message_id, "error": str(e)}
            except Exception as mark_error:
                logger.error("failed_to_mark_failed", 
                            message_id=message_id, 
                            mark_error=str(mark_error))
                return {"status": "failed", "message_id": message_id, "error": f"Final retry failed: {str(e)}"}
        
        # Exponential backoff retry
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=countdown)

async def _generate_content_by_type(
    ai_coach: AICoachService, 
    message_type: str, 
    user_id: str, 
    user_context: Dict
) -> Optional[str]:
    """Generate content using appropriate AI template based on message type"""
    
    try:
        # Regular coaching messages
        if message_type == 'daily_affirmation':
            return await ai_coach.generate_daily_affirmation(user_id, user_context)
        elif message_type == 'gratitude_prompt':
            return await ai_coach.generate_gratitude_prompt(user_id, user_context)
        elif message_type == 'accountability_checkin':
            return await ai_coach.generate_accountability_checkin(user_id, user_context)
        elif message_type == 'day_planning':
            return await ai_coach.generate_day_planning_prompt(user_id, user_context)
        elif message_type == 'weekly_reflection':
            return await ai_coach.generate_weekly_reflection(user_id, user_context)
        elif message_type == 'midday_boost':
            return await ai_coach.generate_midday_boost(user_id, user_context)
        elif message_type == 'evening_wind_down':
            return await ai_coach.generate_evening_wind_down(user_id, user_context)
        # Onboarding messages (pre-generated content stored in scheduled_messages)
        elif message_type in ['onboarding_welcome', 'onboarding_response', 'onboarding_question']:
            # For onboarding, content is pre-generated and stored in the message record
            # Return None to trigger fallback to stored content
            return None
        else:
            logger.error("unknown_message_type", message_type=message_type)
            return None
            
    except Exception as e:
        logger.error("content_generation_error", 
                    message_type=message_type, 
                    user_id=user_id,
                    error=str(e))
        return None

async def _send_and_log(subscriber: Dict, content: str, message_type: str, 
                       supabase_service: SupabaseService, whatsapp_service: WhatsAppService) -> bool:
    """Common send-and-log pattern to eliminate duplication"""
    if not subscriber.get('wa_id'):
        logger.warning("no_whatsapp_id", user_email=subscriber.get('email'))
        return False
    
    success = await whatsapp_service.send_message(
        to=subscriber['wa_id'],
        message=content
    )
    
    if success:
        await supabase_service.log_conversation(
            subscriber_id=subscriber['id'],
            content=content,
            message_type='assistant'
        )
        return True
    else:
        logger.error("whatsapp_delivery_failed", 
                    user_email=subscriber.get('email'),
                    wa_id=subscriber['wa_id'])
        return False

# ===== LEGACY TASKS (for backward compatibility during transition) =====

@shared_task(bind=True, max_retries=3)
def send_daily_accountability_checkin(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", 
                   task="send_daily_accountability_checkin", 
                   timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_morning_affirmations(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_morning_affirmations", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_evening_gratitude(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_evening_gratitude", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_weekly_reflection(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_weekly_reflection", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_day_planning(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_day_planning", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_midday_affirmation(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_midday_affirmation", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_evening_affirmation(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_evening_affirmation", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task(bind=True, max_retries=3)
def send_weekly_check_ins(self, timezone='UTC'):
    """DEPRECATED: Use process_personalized_messages driver instead"""
    logger.warning("deprecated_task_called", task="send_weekly_check_ins", timezone=timezone)
    return {"status": "deprecated", "message": "Use process_personalized_messages driver instead"}

@shared_task
def cleanup_old_scheduled_messages():
    """Clean up old completed/failed messages"""
    try:
        supabase_service, _, _ = get_services()
        cleaned_count = asyncio.run(supabase_service.cleanup_old_messages(days_old=7))
        
        logger.info("cleanup_completed", messages_cleaned=cleaned_count)
        return {"cleaned": cleaned_count, "status": "success"}
        
    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        raise e

# OLD IMPLEMENTATIONS REMOVED - functionality consolidated into dispatch_message

# END OF FILE - All old implementations removed and replaced with new driver+dispatcher architecture
