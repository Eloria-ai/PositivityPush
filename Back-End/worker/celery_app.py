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
        "worker.tasks.email_notifications"
    ]
)

# Force task discovery and registration
try:
    from worker.tasks import daily_messages, weekly_reports, email_notifications
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
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # Morning affirmations (8 AM in various timezones)
    'send-morning-affirmations-utc': {
        'task': 'worker.tasks.daily_messages.send_morning_affirmations',
        'schedule': crontab(hour=8, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-morning-affirmations-est': {
        'task': 'worker.tasks.daily_messages.send_morning_affirmations',
        'schedule': crontab(hour=13, minute=0),  # 8 AM EST = 13:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-morning-affirmations-pst': {
        'task': 'worker.tasks.daily_messages.send_morning_affirmations',
        'schedule': crontab(hour=16, minute=0),  # 8 AM PST = 16:00 UTC
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-morning-affirmations-cet': {
        'task': 'worker.tasks.daily_messages.send_morning_affirmations',
        'schedule': crontab(hour=7, minute=0),  # 8 AM CET = 7:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Evening gratitude prompts (8 PM in various timezones)
    'send-evening-gratitude-utc': {
        'task': 'worker.tasks.daily_messages.send_evening_gratitude',
        'schedule': crontab(hour=20, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-evening-gratitude-est': {
        'task': 'worker.tasks.daily_messages.send_evening_gratitude',
        'schedule': crontab(hour=1, minute=0),  # 8 PM EST = 01:00 UTC next day
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-evening-gratitude-pst': {
        'task': 'worker.tasks.daily_messages.send_evening_gratitude',
        'schedule': crontab(hour=4, minute=0),  # 8 PM PST = 04:00 UTC next day
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-evening-gratitude-cet': {
        'task': 'worker.tasks.daily_messages.send_evening_gratitude',
        'schedule': crontab(hour=19, minute=0),  # 8 PM CET = 19:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Day planning (9 AM in various timezones)
    'send-day-planning-utc': {
        'task': 'worker.tasks.daily_messages.send_day_planning',
        'schedule': crontab(hour=9, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-day-planning-est': {
        'task': 'worker.tasks.daily_messages.send_day_planning',
        'schedule': crontab(hour=14, minute=0),  # 9 AM EST = 14:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-day-planning-pst': {
        'task': 'worker.tasks.daily_messages.send_day_planning',
        'schedule': crontab(hour=17, minute=0),  # 9 AM PST = 17:00 UTC
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-day-planning-cet': {
        'task': 'worker.tasks.daily_messages.send_day_planning',
        'schedule': crontab(hour=8, minute=0),  # 9 AM CET = 8:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Mid-day affirmations (12 PM in various timezones)
    'send-midday-affirmation-utc': {
        'task': 'worker.tasks.daily_messages.send_midday_affirmation',
        'schedule': crontab(hour=12, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-midday-affirmation-est': {
        'task': 'worker.tasks.daily_messages.send_midday_affirmation',
        'schedule': crontab(hour=17, minute=0),  # 12 PM EST = 17:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-midday-affirmation-pst': {
        'task': 'worker.tasks.daily_messages.send_midday_affirmation',
        'schedule': crontab(hour=20, minute=0),  # 12 PM PST = 20:00 UTC
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-midday-affirmation-cet': {
        'task': 'worker.tasks.daily_messages.send_midday_affirmation',
        'schedule': crontab(hour=11, minute=0),  # 12 PM CET = 11:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Evening affirmations (6 PM in various timezones)
    'send-evening-affirmation-utc': {
        'task': 'worker.tasks.daily_messages.send_evening_affirmation',
        'schedule': crontab(hour=18, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-evening-affirmation-est': {
        'task': 'worker.tasks.daily_messages.send_evening_affirmation',
        'schedule': crontab(hour=23, minute=0),  # 6 PM EST = 23:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-evening-affirmation-pst': {
        'task': 'worker.tasks.daily_messages.send_evening_affirmation',
        'schedule': crontab(hour=2, minute=0),  # 6 PM PST = 02:00 UTC next day
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-evening-affirmation-cet': {
        'task': 'worker.tasks.daily_messages.send_evening_affirmation',
        'schedule': crontab(hour=17, minute=0),  # 6 PM CET = 17:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Daily accountability check-ins (7 PM in various timezones - after evening affirmation, before evening gratitude)
    'send-daily-accountability-utc': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=19, minute=0),  # 7 PM UTC
        'kwargs': {'timezone': 'UTC'}
    },
    'send-daily-accountability-est': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=0, minute=0),  # 7 PM EST = 00:00 UTC next day
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-daily-accountability-pst': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=3, minute=0),  # 7 PM PST = 03:00 UTC next day
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-daily-accountability-cet': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=18, minute=0),  # 7 PM CET = 18:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
    },
    
    # Weekly reflection and planning (Sunday 10 AM in various timezones)
    'send-weekly-reflection-utc': {
        'task': 'worker.tasks.daily_messages.send_weekly_reflection',
        'schedule': crontab(day_of_week=0, hour=10, minute=0),  # Sunday 10 AM UTC
        'kwargs': {'timezone': 'UTC'}
    },
    'send-weekly-reflection-est': {
        'task': 'worker.tasks.daily_messages.send_weekly_reflection',
        'schedule': crontab(day_of_week=0, hour=15, minute=0),  # Sunday 10 AM EST = 15:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-weekly-reflection-pst': {
        'task': 'worker.tasks.daily_messages.send_weekly_reflection',
        'schedule': crontab(day_of_week=0, hour=18, minute=0),  # Sunday 10 AM PST = 18:00 UTC
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-weekly-reflection-cet': {
        'task': 'worker.tasks.daily_messages.send_weekly_reflection',
        'schedule': crontab(day_of_week=0, hour=9, minute=0),  # Sunday 10 AM CET = 9:00 UTC
        'kwargs': {'timezone': 'Europe/Paris'}
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
        if 'daily' in name or 'morning' in name or 'accountability' in name or 'evening' in name:
            print(f"  📅 {name}: {config['task']}")
    
    # Check specific tasks
    target_tasks = [
        'worker.tasks.daily_messages.send_morning_affirmations',
        'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'worker.tasks.daily_messages.send_evening_gratitude'
    ]

    print(f"Specific task registration:")
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
        if 'daily' in name or 'morning' in name or 'accountability' in name or 'evening' in name:
            print(f"  📅 {name}: {config['task']}")
    
    # Check specific tasks
    target_tasks = [
        'worker.tasks.daily_messages.send_morning_affirmations',
        'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'worker.tasks.daily_messages.send_evening_gratitude'
    ]

    print(f"\nSpecific task registration:")
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
        from worker.tasks.daily_messages import send_morning_affirmations
        print("✅ Task import successful")
        
        # Trigger task manually
        print("📤 Triggering morning affirmations task...")
        result = send_morning_affirmations.delay('UTC')
        print(f"✅ Task triggered! ID: {result.id}")
        
        # Try to get result
        print("⏳ Waiting for task completion (30s timeout)...")
        task_result = result.get(timeout=30)
        print(f"🎉 Task completed! Result: {task_result}")
        
    except Exception as e:
        print(f"❌ Manual trigger failed: {e}")
    
    print("=" * 40)

# Test manual task trigger on worker startup (ALWAYS RUN FOR DEBUGGING)
try:
    print("🚀 RUNNING WORKER STARTUP TEST...")
    test_manual_task_trigger()
except Exception as e:
    print(f"Worker test failed: {e}")

# Debug queue configuration
print("📋 CELERY QUEUE CONFIGURATION:")
print(f"Task routes: {celery_app.conf.task_routes}")
print(f"Default queue: {celery_app.conf.task_default_queue}")
print("🔧 Using simplified queue setup - all tasks go to 'celery' queue")

if __name__ == '__main__':
    # Run configuration test
    test_celery_config()
    # Then start celery
    celery_app.start()