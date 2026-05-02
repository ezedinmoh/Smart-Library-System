"""
Management command to automatically update overdue books and calculate fines.
Run this daily via cron job or task scheduler.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.borrow.models import BorrowRecord
from apps.users.notifications import notify_book_overdue


class Command(BaseCommand):
    help = 'Update overdue books and calculate fines'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--send-emails',
            action='store_true',
            help='Send email notifications to users with overdue books',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_emails = options['send_emails']
        today = timezone.now().date()
        
        # Find books that are overdue
        overdue_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date__lt=today
        )
        
        updated_count = 0
        total_fines = 0
        emails_sent = 0
        
        for record in overdue_records:
            days_overdue = (today - record.due_date).days
            fine_amount = days_overdue * settings.FINE_PER_DAY  # ETB 2 per day
            
            if not dry_run:
                record.status = 'overdue'
                record.fine_amount = fine_amount
                record.save()
                
                # Update user profile total fines
                profile = record.user.profile
                profile.total_fines += fine_amount
                profile.save()
                
                # Send email notification if requested
                if send_emails:
                    notify_book_overdue(record)
                    emails_sent += 1
            
            updated_count += 1
            total_fines += fine_amount
            
            self.stdout.write(
                f"{'[DRY RUN] ' if dry_run else ''}Updated: {record.user.username} - "
                f"{record.book.title} (ETB {fine_amount} fine)"
            )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'[DRY RUN] ' if dry_run else ''}Successfully updated {updated_count} "
                    f"overdue records. Total fines: ETB {total_fines}"
                )
            )
            if send_emails and not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"Sent {emails_sent} email notification(s)")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("No overdue books found.")
            )