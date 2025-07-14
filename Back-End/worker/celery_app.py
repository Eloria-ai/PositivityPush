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
    
    # Daily accountability check-ins (2 PM in various timezones)
    'send-daily-accountability-utc': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=14, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    'send-daily-accountability-est': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=19, minute=0),  # 2 PM EST = 19:00 UTC
        'kwargs': {'timezone': 'America/New_York'}
    },
    'send-daily-accountability-pst': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=22, minute=0),  # 2 PM PST = 22:00 UTC
        'kwargs': {'timezone': 'America/Los_Angeles'}
    },
    'send-daily-accountability-cet': {
        'task': 'worker.tasks.daily_messages.send_daily_accountability_checkin',
        'schedule': crontab(hour=13, minute=0),  # 2 PM CET = 13:00 UTC
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

# Task routing
celery_app.conf.task_routes = {
    'worker.tasks.daily_messages.*': {'queue': 'daily_messages'},
    'worker.tasks.weekly_reports.*': {'queue': 'weekly_reports'},
    'worker.tasks.email_notifications.*': {'queue': 'email_notifications'},
}

# Default queue
celery_app.conf.task_default_queue = 'default'

if __name__ == '__main__':
    celery_app.start()