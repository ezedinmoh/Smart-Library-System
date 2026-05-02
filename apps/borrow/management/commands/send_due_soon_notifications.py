"""
Management command to send email notifications for books due soon (3 days before due date).
Run this daily via cron job or task scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.borrow.models import BorrowRecord
from apps.users.notifications import notify_book_due_soon


class Command(BaseCommand):
    help = 'Send email notifications for books due in 3 days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what notifications would be sent without actually sending them',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Number of days before due date to send notification (default: 3)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_before = options['days']
        
        # Calculate the target due date (e.g., 3 days from now)
        target_date = timezone.now().date() + timedelta(days=days_before)
        
        # Find books due on the target date that are still borrowed
        due_soon_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date=target_date
        ).select_related('user', 'book')
        
        sent_count = 0
        
        for record in due_soon_records:
            if not dry_run:
                # Send email notification
                notify_book_due_soon(record)
            
            sent_count += 1
            
            self.stdout.write(
                f"{'[DRY RUN] ' if dry_run else ''}Notification sent to: {record.user.username} - "
                f"{record.book.title} (due on {record.due_date})"
            )
        
        if sent_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'[DRY RUN] ' if dry_run else ''}Successfully sent {sent_count} "
                    f"due soon notification(s) for books due on {target_date}"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"No books due on {target_date}.")
            )
