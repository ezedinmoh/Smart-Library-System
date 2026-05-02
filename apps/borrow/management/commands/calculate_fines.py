"""
Management command to calculate and update fines for overdue books.
Run daily via Render cron job at 11 PM UTC.
"""
from django.core.management.base import BaseCommand
from apps.borrow.tasks import calculate_fines


class Command(BaseCommand):
    help = 'Calculate and update fines for overdue books'

    def handle(self, *args, **options):
        result = calculate_fines()
        self.stdout.write(self.style.SUCCESS(result))
