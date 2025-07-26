"""
Email Notification Tasks for Positivity Push
Handles welcome emails, activation reminders, and other email communications.
"""

from celery import shared_task
from datetime import datetime, timedelta
import asyncio

# Use proper package imports instead of sys.path manipulation
from app.services.email_service import EmailService
from app.services.supabase_client import SupabaseService
from app.deps import get_supabase_client
from app.config import settings
from app.logging_config import get_logger

# Configure structured logging
logger = get_logger("worker.tasks.email_notifications")

@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, subscription_data):
    """
    Send welcome email immediately after payment completion
    """
    logger.info(f"Sending welcome email to {subscription_data.get('email')}")
    
    try:
        return asyncio.run(_send_welcome_email_async(subscription_data))
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

async def _send_welcome_email_async(subscription_data):
    """Async implementation of welcome email"""
    
    email_service = EmailService()
    
    try:
        success = await email_service.send_welcome_email(
            to_email=subscription_data['email'],
            subscription_data=subscription_data
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to {subscription_data['email']}")
            return {"status": "sent", "email": subscription_data['email']}
        else:
            logger.error(f"Failed to send welcome email to {subscription_data['email']}")
            return {"status": "failed", "email": subscription_data['email']}
            
    except Exception as e:
        logger.error(f"Error in welcome email service: {e}")
        raise

@shared_task(bind=True, max_retries=3)
def send_activation_reminders(self):
    """
    Send activation reminders to users who haven't activated WhatsApp after 24 hours
    """
    logger.info("Starting activation reminder check")
    
    try:
        return asyncio.run(_send_activation_reminders_async())
    except Exception as e:
        logger.error(f"Error in activation reminders task: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

async def _send_activation_reminders_async():
    """Async implementation of activation reminders"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    email_service = EmailService()
    
    # Get users who paid but haven't activated WhatsApp
    # (created 24-72 hours ago, status still 'paid_pending_optin')
    cutoff_start = datetime.utcnow() - timedelta(hours=72)  # Don't send after 72 hours
    cutoff_end = datetime.utcnow() - timedelta(hours=24)    # Wait 24 hours before first reminder
    
    try:
        # Query Supabase for users needing reminders
        result = (
            db.table("subscribers")
            .select("*")
            .eq("status", "paid_pending_optin")
            .gte("created_at", cutoff_start.isoformat())
            .lte("created_at", cutoff_end.isoformat())
            .execute()
        )
        
        pending_users = result.data if result.data else []
        
        sent_count = 0
        error_count = 0
        
        for user in pending_users:
            try:
                # Check if we already sent a reminder
                if await _already_sent_activation_reminder(user['id'], supabase_service):
                    continue
                
                # Generate WhatsApp activation link
                whatsapp_link = _generate_whatsapp_activation_link(user['stripe_session_id'])
                
                # Send activation reminder email
                success = await email_service.send_activation_reminder(
                    to_email=user['email'],
                    whatsapp_activation_link=whatsapp_link
                )
                
                if success:
                    # Log that we sent the reminder
                    await _log_activation_reminder_sent(user['id'], supabase_service)
                    sent_count += 1
                    logger.info(f"Activation reminder sent to {user['email']}")
                else:
                    error_count += 1
                    logger.error(f"Failed to send activation reminder to {user['email']}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing user {user.get('id', 'unknown')}: {e}")
        
        logger.info(f"Activation reminders complete. Sent: {sent_count}, Errors: {error_count}")
        return {"sent": sent_count, "errors": error_count, "checked_users": len(pending_users)}
        
    except Exception as e:
        logger.error(f"Error querying pending users: {e}")
        return {"error": str(e)}

@shared_task(bind=True, max_retries=3) 
def send_payment_failed_notification(self, customer_data):
    """
    Send notification when a recurring payment fails
    """
    logger.info(f"Sending payment failed notification to {customer_data.get('email')}")
    
    try:
        return asyncio.run(_send_payment_failed_notification_async(customer_data))
    except Exception as e:
        logger.error(f"Error sending payment failed notification: {e}")
        raise self.retry(exc=e, countdown=300)

async def _send_payment_failed_notification_async(customer_data):
    """Async implementation of payment failed notification"""
    
    email_service = EmailService()
    
    try:
        success = await email_service.send_payment_failed_email(
            to_email=customer_data['email'],
            customer_data=customer_data
        )
        
        if success:
            logger.info(f"Payment failed notification sent to {customer_data['email']}")
            return {"status": "sent", "email": customer_data['email']}
        else:
            logger.error(f"Failed to send payment failed notification to {customer_data['email']}")
            return {"status": "failed", "email": customer_data['email']}
            
    except Exception as e:
        logger.error(f"Error in payment failed notification service: {e}")
        raise

@shared_task(bind=True, max_retries=3)
def send_subscription_cancelled_notification(self, customer_data):
    """
    Send notification when a subscription is cancelled
    """
    logger.info(f"Sending cancellation notification to {customer_data.get('email')}")
    
    try:
        return asyncio.run(_send_subscription_cancelled_notification_async(customer_data))
    except Exception as e:
        logger.error(f"Error sending cancellation notification: {e}")
        raise self.retry(exc=e, countdown=300)

async def _send_subscription_cancelled_notification_async(customer_data):
    """Async implementation of cancellation notification"""
    
    email_service = EmailService()
    
    try:
        success = await email_service.send_cancellation_email(
            to_email=customer_data['email'],
            customer_data=customer_data
        )
        
        if success:
            logger.info(f"Cancellation notification sent to {customer_data['email']}")
            return {"status": "sent", "email": customer_data['email']}
        else:
            logger.error(f"Failed to send cancellation notification to {customer_data['email']}")
            return {"status": "failed", "email": customer_data['email']}
            
    except Exception as e:
        logger.error(f"Error in cancellation notification service: {e}")
        raise


# Helper functions
async def _already_sent_activation_reminder(subscriber_id: str, supabase_service: SupabaseService) -> bool:
    """Check if we already sent an activation reminder to this user"""
    
    try:
        # Check conversations for activation reminder
        conversations = await supabase_service.get_conversation_history(subscriber_id, limit=20)
        
        # Look for system message about activation reminder
        for conv in conversations:
            if (conv.get('message_type') == 'system' and 
                'activation reminder' in conv.get('content', '').lower()):
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking activation reminder history: {e}")
        return False

async def _log_activation_reminder_sent(subscriber_id: str, supabase_service: SupabaseService):
    """Log that we sent an activation reminder"""
    
    try:
        await supabase_service.log_conversation(
            subscriber_id=subscriber_id,
            content="Activation reminder email sent",
            message_type="system"
        )
        
    except Exception as e:
        logger.error(f"Error logging activation reminder: {e}")

def _generate_whatsapp_activation_link(session_id: str) -> str:
    """Generate WhatsApp activation link for the success page"""
    
    # Use the frontend URL from settings
    frontend_url = settings.FRONTEND_URL
    
    return f"{frontend_url}/success?session_id={session_id}"

@shared_task
def cleanup_failed_email_logs():
    """
    Clean up old failed email logs (keep for 30 days)
    Note: Email logs are handled by SendGrid - no cleanup needed
    """
    logger.info("Email log cleanup - no action needed (SendGrid handles email logs)")
    return {"status": "completed", "message": "SendGrid handles email logs"}
