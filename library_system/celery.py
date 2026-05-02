"""
Celery Configuration for Library Management System
Handles background tasks and periodic scheduling
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')

# Create Celery app
app = Celery('library_system')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Periodic Task Schedule
app.conf.beat_schedule = {
    # Update overdue books every day at midnight
    'update-overdue-books-daily': {
        'task': 'apps.borrow.tasks.update_overdue_books',
        'schedule': crontab(hour=0, minute=0),  # 00:00 (midnight)
    },
    
    # Send due soon reminders every day at 9 AM
    'send-due-reminders-daily': {
        'task': 'apps.borrow.tasks.send_due_reminders',
        'schedule': crontab(hour=9, minute=0),  # 09:00 AM
    },
    
    # Send overdue reminders every day at 10 AM
    'send-overdue-reminders-daily': {
        'task': 'apps.borrow.tasks.send_overdue_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10:00 AM
    },
    
    # Check waitlist and notify users every hour
    'check-waitlist-hourly': {
        'task': 'apps.borrow.tasks.check_waitlist_notifications',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Calculate fines daily at 11 PM
    'calculate-fines-daily': {
        'task': 'apps.borrow.tasks.calculate_fines',
        'schedule': crontab(hour=23, minute=0),  # 23:00 (11 PM)
    },
}

# Celery Beat Configuration
app.conf.timezone = 'UTC'  # Or your timezone: 'Africa/Addis_Ababa'


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')
