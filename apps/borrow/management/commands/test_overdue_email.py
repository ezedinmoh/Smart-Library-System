"""
Test command to send overdue email for any borrowed book
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.borrow.models import BorrowRecord
from apps.users.notifications import notify_book_overdue


class Command(BaseCommand):
    help = 'Test overdue email notification by temporarily making a book overdue'
    
    def handle(self, *args, **options):
        # Get first borrowed book
        record = BorrowRecord.objects.filter(status='borrowed').first()
        
        if not record:
            self.stdout.write(self.style.ERROR('No borrowed books found. Please borrow a book first.'))
            return
        
        # Temporarily set as overdue for testing
        original_due_date = record.due_date
        original_status = record.status
        
        record.due_date = timezone.now().date() - timezone.timedelta(days=5)
        record.status = 'overdue'
        record.fine_amount = 10.00  # 5 days * ETB 2
        record.save()
        
        # Send notification
        notify_book_overdue(record)
        
        # Restore original values
        record.due_date = original_due_date
        record.status = original_status
        record.fine_amount = 0
        record.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test overdue email sent to: {record.user.username} for book "{record.book.title}"'
            )
        )
        self.stdout.write(self.style.WARNING('Note: Book status was temporarily changed and restored.'))
