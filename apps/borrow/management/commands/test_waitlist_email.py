"""
Test command to send waitlist notification email
"""
from django.core.management.base import BaseCommand
from apps.borrow.models import BookRequest
from apps.users.notifications import notify_book_available_waitlist


class Command(BaseCommand):
    help = 'Test waitlist email notification for pending book requests'
    
    def handle(self, *args, **options):
        # Get first pending request
        request = BookRequest.objects.filter(status='pending').first()
        
        if not request:
            self.stdout.write(self.style.ERROR('No pending book requests found. Please create a book request first.'))
            return
        
        # Send notification (position 1 of 1 for testing)
        notify_book_available_waitlist(request, position_in_queue=1, total_in_queue=1)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Test waitlist email sent to: {request.user.username} for book "{request.book.title}"'
            )
        )
