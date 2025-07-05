"""
Daily Messaging Tasks for Positivity Push
Sends personalized affirmations, gratitude prompts, and check-ins.
"""

from celery import shared_task
from datetime import datetime, timedelta
import logging
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from services.ai_coach import AICoachService
from services.whatsapp_service import WhatsAppService
from services.supabase_client import SupabaseService
from deps import get_supabase_client
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_daily_accountability_checkin(self, timezone='UTC'):
    """
    Send personalized daily accountability check-ins to users
    Ask about their goals: gym, habits, work progress, etc.
    """
    logger.info(f"Starting daily accountability check-ins for timezone: {timezone}")
    
    try:
        return asyncio.run(_send_daily_accountability_async(timezone))
    except Exception as e:
        logger.error(f"Error in daily accountability task: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

async def _send_daily_accountability_async(timezone):
    """Async implementation of daily accountability check-ins"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    ai_coach = AICoachService()
    whatsapp_service = WhatsAppService()
    
    # Get active subscribers for accountability check-ins
    active_users = supabase_service.get_active_subscribers_for_timezone(timezone)
    
    successful_sends = 0
    failed_sends = 0
    
    for user in active_users:
        try:
            # Generate personalized accountability check-in
            user_context = {
                "email": user.get("email"),
                "plan_type": user.get("plan_type"),
                "goals": user.get("personal_goals"),
                "challenges": user.get("active_challenges")
            }
            
            # AI generates personalized accountability message
            accountability_message = await ai_coach.generate_accountability_checkin(
                user["id"], 
                user_context
            )
            
            # Send via WhatsApp
            if user.get("wa_id"):
                await whatsapp_service.send_message(
                    to=user["wa_id"],
                    message=accountability_message
                )
                successful_sends += 1
                logger.info(f"Accountability check-in sent to user {user['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send accountability check-in to user {user['id']}: {e}")
            failed_sends += 1
    
    logger.info(f"Accountability check-ins completed. Success: {successful_sends}, Failed: {failed_sends}")
    return {"successful": successful_sends, "failed": failed_sends}

@shared_task(bind=True, max_retries=3)
def send_morning_affirmations(self, timezone='UTC'):
    """
    Send personalized morning affirmations to active users
    """
    logger.info(f"Starting morning affirmations for timezone: {timezone}")
    
    try:
        # Run async function in sync context
        return asyncio.run(_send_morning_affirmations_async(timezone))
    except Exception as e:
        logger.error(f"Error in morning affirmations task: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

async def _send_morning_affirmations_async(timezone):
    """Async implementation of morning affirmations"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    ai_coach = AICoachService()
    whatsapp_service = WhatsAppService()
    
    # Get active subscribers for this timezone
    subscribers = await supabase_service.get_subscribers_for_daily_message(timezone)
    
    sent_count = 0
    error_count = 0
    
    for subscriber in subscribers:
        try:
            # Skip if user has already received affirmation today
            if await _already_received_message_today(subscriber['id'], 'daily_affirmation', supabase_service):
                continue
            
            # Generate personalized affirmation
            affirmation = await ai_coach.generate_daily_affirmation(
                user_id=subscriber['id'],
                user_context=subscriber
            )
            
            # Send via WhatsApp
            if subscriber.get('wa_id'):
                success = await whatsapp_service.send_message(
                    to=subscriber['wa_id'],
                    message=affirmation
                )
                
                if success:
                    # Log the sent message
                    await supabase_service.log_conversation(
                        subscriber_id=subscriber['id'],
                        content=affirmation,
                        message_type='assistant'
                    )
                    sent_count += 1
                    logger.info(f"Affirmation sent to user {subscriber['id']}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send affirmation to user {subscriber['id']}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing user {subscriber.get('id', 'unknown')}: {e}")
    
    logger.info(f"Morning affirmations complete. Sent: {sent_count}, Errors: {error_count}")
    return {"sent": sent_count, "errors": error_count, "timezone": timezone}

@shared_task(bind=True, max_retries=3)
def send_evening_gratitude(self, timezone='UTC'):
    """
    Send personalized evening gratitude prompts to active users
    """
    logger.info(f"Starting evening gratitude prompts for timezone: {timezone}")
    
    try:
        return asyncio.run(_send_evening_gratitude_async(timezone))
    except Exception as e:
        logger.error(f"Error in evening gratitude task: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

async def _send_evening_gratitude_async(timezone):
    """Async implementation of evening gratitude prompts"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    ai_coach = AICoachService()
    whatsapp_service = WhatsAppService()
    
    # Get active subscribers for this timezone
    subscribers = await supabase_service.get_subscribers_for_daily_message(timezone)
    
    sent_count = 0
    error_count = 0
    
    for subscriber in subscribers:
        try:
            # Skip if user has already received gratitude prompt today
            if await _already_received_message_today(subscriber['id'], 'gratitude_prompt', supabase_service):
                continue
            
            # Generate personalized gratitude prompt
            gratitude_prompt = await ai_coach.generate_gratitude_prompt(
                user_id=subscriber['id'],
                user_context=subscriber
            )
            
            # Send via WhatsApp
            if subscriber.get('wa_id'):
                success = await whatsapp_service.send_message(
                    to=subscriber['wa_id'],
                    message=gratitude_prompt
                )
                
                if success:
                    # Log the sent message
                    await supabase_service.log_conversation(
                        subscriber_id=subscriber['id'],
                        content=gratitude_prompt,
                        message_type='assistant'
                    )
                    sent_count += 1
                    logger.info(f"Gratitude prompt sent to user {subscriber['id']}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send gratitude prompt to user {subscriber['id']}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing user {subscriber.get('id', 'unknown')}: {e}")
    
    logger.info(f"Evening gratitude prompts complete. Sent: {sent_count}, Errors: {error_count}")
    return {"sent": sent_count, "errors": error_count, "timezone": timezone}

@shared_task(bind=True, max_retries=3)
def send_weekly_check_ins(self, timezone='UTC'):
    """
    Send weekly check-in messages to users
    """
    logger.info(f"Starting weekly check-ins for timezone: {timezone}")
    
    try:
        return asyncio.run(_send_weekly_check_ins_async(timezone))
    except Exception as e:
        logger.error(f"Error in weekly check-ins task: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

async def _send_weekly_check_ins_async(timezone):
    """Async implementation of weekly check-ins"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    whatsapp_service = WhatsAppService()
    
    # Get active subscribers
    subscribers = await supabase_service.get_active_subscribers()
    
    sent_count = 0
    error_count = 0
    
    check_in_messages = [
        "How has your week been? What's one thing you're proud of? 🌟",
        "What's been the highlight of your week so far? I'd love to celebrate with you! 🎉",
        "How are you feeling about your goals this week? Any wins to share? 💪",
        "What's one thing you've learned about yourself this week? 💭",
        "How's your energy been? What's been fueling you or draining you? ⚡",
    ]
    
    for subscriber in subscribers:
        try:
            # Skip if user received check-in this week
            if await _already_received_message_this_week(subscriber['id'], 'weekly_check_in', supabase_service):
                continue
            
            # Choose check-in message based on user ID (for variety)
            message_index = hash(subscriber['id']) % len(check_in_messages)
            check_in_message = check_in_messages[message_index]
            
            # Send via WhatsApp
            if subscriber.get('wa_id'):
                success = await whatsapp_service.send_message(
                    to=subscriber['wa_id'],
                    message=check_in_message
                )
                
                if success:
                    # Log the sent message
                    await supabase_service.log_conversation(
                        subscriber_id=subscriber['id'],
                        content=check_in_message,
                        message_type='assistant'
                    )
                    sent_count += 1
                    logger.info(f"Check-in sent to user {subscriber['id']}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send check-in to user {subscriber['id']}")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing user {subscriber.get('id', 'unknown')}: {e}")
    
    logger.info(f"Weekly check-ins complete. Sent: {sent_count}, Errors: {error_count}")
    return {"sent": sent_count, "errors": error_count, "timezone": timezone}

@shared_task
def cleanup_old_scheduled_messages():
    """
    Clean up old scheduled messages (older than 7 days)
    """
    logger.info("Starting cleanup of old scheduled messages")
    
    try:
        return asyncio.run(_cleanup_old_scheduled_messages_async())
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        return {"error": str(e)}

async def _cleanup_old_scheduled_messages_async():
    """Async implementation of message cleanup"""
    
    db = get_supabase_client()
    
    # Delete messages older than 7 days
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    try:
        result = db.table("scheduled_messages").delete().lt("created_at", cutoff_date.isoformat()).execute()
        deleted_count = len(result.data) if result.data else 0
        
        logger.info(f"Cleaned up {deleted_count} old scheduled messages")
        return {"deleted": deleted_count}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"error": str(e)}

# Helper functions
async def _already_received_message_today(subscriber_id: str, message_type: str, supabase_service: SupabaseService) -> bool:
    """Check if user already received a specific message type today"""
    try:
        today = datetime.utcnow().date()
        
        # Check conversations table for today's messages
        conversations = await supabase_service.get_conversation_history(subscriber_id, limit=50)
        
        for conv in conversations:
            conv_date = datetime.fromisoformat(conv['timestamp']).date()
            if (conv_date == today and 
                conv['message_type'] == 'assistant' and
                any(keyword in conv['content'].lower() for keyword in _get_message_keywords(message_type))):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking message history: {e}")
        return False

async def _already_received_message_this_week(subscriber_id: str, message_type: str, supabase_service: SupabaseService) -> bool:
    """Check if user already received a specific message type this week"""
    try:
        week_start = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        
        conversations = await supabase_service.get_conversation_history(subscriber_id, limit=100)
        
        for conv in conversations:
            conv_date = datetime.fromisoformat(conv['timestamp']).date()
            if (conv_date >= week_start and 
                conv['message_type'] == 'assistant' and
                any(keyword in conv['content'].lower() for keyword in _get_message_keywords(message_type))):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking weekly message history: {e}")
        return False

def _get_message_keywords(message_type: str) -> list:
    """Get keywords to identify message types"""
    keywords = {
        'daily_affirmation': ['today', 'this morning', 'affirmation', 'you are', 'you can'],
        'gratitude_prompt': ['grateful', 'gratitude', 'appreciate', 'thankful', 'reflect'],
        'weekly_check_in': ['week', 'how has', 'how are you', 'check in', 'proud of']
    }
    return keywords.get(message_type, [])