"""
Celery Configuration for Positivity Push
Handles background tasks for daily messaging, weekly reports, and email notifications.
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Celery app
celery_app = Celery(
    "positivity_push_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[
        "worker.tasks.daily_messages",
        "worker.tasks.weekly_reports",
        "worker.tasks.email_notifications",
        "worker.tasks.onboarding_tasks"
    ]
)

# Force task discovery and registration
try:
    from worker.tasks import daily_messages, weekly_reports, email_notifications, onboarding_tasks
    print(f"📦 Successfully imported task modules")
except ImportError as e:
    print(f"❌ Task import error: {e}")

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
    broker_connection_retry_on_startup=True,
    # Task time limits to prevent stalled WhatsApp/API calls
    task_soft_time_limit=30,  # Warning after 30 seconds
    task_time_limit=60,       # Hard kill after 60 seconds
)

# Dynamic user-specific scheduling - replaces hardcoded timezone broadcasts
celery_app.conf.beat_schedule = {
    # Driver task: sweeps DB for users whose next_notification_utc <= now() and enqueues personalized messages
    'process-personalized-messages': {
        'task': 'worker.tasks.daily_messages.process_personalized_messages',
        'schedule': crontab(minute='*/5'),  # Check every 5 minutes for due messages (responsive delivery)
    },
    
    # Weekly progress reports (Sunday 6 PM)
    'send-weekly-progress-reports': {
        'task': 'worker.tasks.weekly_reports.send_weekly_progress_reports',
        'schedule': crontab(day_of_week=0, hour=18, minute=0),  # Sunday 6 PM UTC
    },
    
    # Activation reminders (check every 4 hours for users who haven't activated)
    'send-activation-reminders': {
        'task': 'worker.tasks.email_notifications.send_activation_reminders',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
    
    # Clean up old scheduled messages (daily at 2 AM)
    'cleanup-old-scheduled-messages': {
        'task': 'worker.tasks.daily_messages.cleanup_old_scheduled_messages',
        'schedule': crontab(hour=2, minute=0),
    },
}

# Simplified queue configuration - use default queue for all tasks
# This ensures Beat and Workers use the same queue
celery_app.conf.task_routes = {}  # Remove custom routing
celery_app.conf.task_default_queue = 'celery'  # Use standard celery queue

# Run configuration test on import (for Railway deployment)
def run_diagnostics():
    """Run diagnostics when module is imported"""
    print("=== CELERY CONFIGURATION TEST ===")
    
    # Check task registration
    all_tasks = list(celery_app.tasks.keys())
    print(f"Total registered tasks: {len(all_tasks)}")

    daily_tasks = [name for name in all_tasks if 'daily_messages' in name]
    print(f"Daily message tasks found: {len(daily_tasks)}")
    for task in daily_tasks:
        print(f"  ✅ {task}")

    # Check beat schedule
    schedule = celery_app.conf.beat_schedule
    print(f"Beat schedule entries: {len(schedule)}")

    for name, config in schedule.items():
        if 'personalized' in name or 'weekly' in name or 'cleanup' in name:
            print(f"  📅 {name}: {config['task']}")
    
    # Check specific tasks
    target_tasks = [
        'worker.tasks.daily_messages.process_personalized_messages'
    ]

    print(f"Driver task registration:")
    for task_name in target_tasks:
        if task_name in all_tasks:
            print(f"✅ {task_name} - REGISTERED")
        else:
            print(f"❌ {task_name} - NOT REGISTERED")
    print("=== END CELERY TEST ===")

# Run diagnostics when imported
try:
    run_diagnostics()
except Exception as e:
    print(f"Diagnostic failed: {e}")

def test_celery_config():
    """Test Celery configuration for debugging"""
    print("=== CELERY CONFIGURATION TEST ===")
    
    # Check task registration
    all_tasks = list(celery_app.tasks.keys())
    print(f"Total registered tasks: {len(all_tasks)}")

    daily_tasks = [name for name in all_tasks if 'daily_messages' in name]
    print(f"\nDaily message tasks found: {len(daily_tasks)}")
    for task in daily_tasks:
        print(f"  ✅ {task}")

    # Check beat schedule
    schedule = celery_app.conf.beat_schedule
    print(f"\nBeat schedule entries: {len(schedule)}")

    for name, config in schedule.items():
        if 'personalized' in name or 'weekly' in name or 'cleanup' in name:
            print(f"  📅 {name}: {config['task']}")
    
    # Check driver task
    target_tasks = [
        'worker.tasks.daily_messages.process_personalized_messages'
    ]

    print(f"\nDriver task registration:")
    for task_name in target_tasks:
        if task_name in all_tasks:
            print(f"✅ {task_name} - REGISTERED")
        else:
            print(f"❌ {task_name} - NOT REGISTERED")

def test_manual_task_trigger():
    """Test manual task triggering to verify worker communication"""
    print("\n🧪 MANUAL TASK TRIGGER TEST")
    print("=" * 40)
    
    try:
        from worker.tasks.daily_messages import process_personalized_messages
        print("✅ Task import successful")
        
        # Trigger driver task manually
        print("📤 Triggering personalized messages driver task...")
        result = process_personalized_messages.delay()
        print(f"✅ Task triggered! ID: {result.id}")
        
        # Try to get result
        print("⏳ Waiting for task completion (30s timeout)...")
        task_result = result.get(timeout=30)
        print(f"🎉 Task completed! Result: {task_result}")
        
    except Exception as e:
        print(f"❌ Manual trigger failed: {e}")
    
    print("=" * 40)

# Debug functions available for manual testing
# Call test_manual_task_trigger() manually when debugging
# Call test_celery_config() manually to verify configuration

if __name__ == '__main__':
    # Run configuration test
    test_celery_config()
    # Then start celery
    celery_app.start()