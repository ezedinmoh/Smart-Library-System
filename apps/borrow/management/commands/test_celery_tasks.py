"""
Management command to test Celery tasks manually
"""

from django.core.management.base import BaseCommand
from apps.borrow.tasks import (
    update_overdue_books,
    send_due_reminders,
    send_overdue_reminders,
    check_waitlist_notifications,
    calculate_fines
)


class Command(BaseCommand):
    help = 'Test Celery background tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            help='Specific task to run (overdue, due, reminders, waitlist, fines, all)',
            default='all'
        )

    def handle(self, *args, **options):
        task = options['task']
        
        self.stdout.write(self.style.WARNING('Testing Celery Tasks...'))
        self.stdout.write('')
        
        if task in ['overdue', 'all']:
            self.stdout.write('Running: update_overdue_books...')
            result = update_overdue_books()
            self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            self.stdout.write('')
        
        if task in ['due', 'all']:
            self.stdout.write('Running: send_due_reminders...')
            result = send_due_reminders()
            self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            self.stdout.write('')
        
        if task in ['reminders', 'all']:
            self.stdout.write('Running: send_overdue_reminders...')
            result = send_overdue_reminders()
            self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            self.stdout.write('')
        
        if task in ['waitlist', 'all']:
            self.stdout.write('Running: check_waitlist_notifications...')
            result = check_waitlist_notifications()
            self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            self.stdout.write('')
        
        if task in ['fines', 'all']:
            self.stdout.write('Running: calculate_fines...')
            result = calculate_fines()
            self.stdout.write(self.style.SUCCESS(f'✓ {result}'))
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('All tasks completed successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
