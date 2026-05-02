"""
Test command to send due soon email for any borrowed book
"""
from django.core.management.base import BaseCommand
from apps.borrow.models import BorrowRecord
from apps.users.notifications import notify_book_due_soon


class Command(BaseCommand):
    help = 'Test due soon email notification by sending to first borrowed book'
    
    def handle(self, *args, **options):
        # Get first borrowed book
        record = BorrowRecord.objects.filter(status='borrowed').first()
        
        if not record:
            self.stdout.write(self.style.ERROR('No borrowed books found. Please borrow a book first.'))
            return
        
        # Send notification
        notify_book_due_soon(record)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test email sent to: {record.user.username} for book "{record.book.title}"'
            )
        )
