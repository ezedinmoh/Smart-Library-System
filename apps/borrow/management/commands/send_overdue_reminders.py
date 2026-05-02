"""
Management command to send overdue book reminders.
Run daily via Render cron job at 10 AM UTC.
"""
from django.core.management.base import BaseCommand
from apps.borrow.tasks import send_overdue_reminders


class Command(BaseCommand):
    help = 'Send email reminders for overdue books'

    def handle(self, *args, **options):
        result = send_overdue_reminders()
        self.stdout.write(self.style.SUCCESS(result))
