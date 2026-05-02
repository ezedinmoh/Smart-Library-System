"""
Background Tasks for Borrow Management
Handles automated email reminders and status updates
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from apps.borrow.models import BorrowRecord
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.borrow.tasks.update_overdue_books')
def update_overdue_books():
    """
    Update overdue status for all borrowed books
    Runs daily at midnight
    """
    try:
        today = timezone.now().date()
        
        # Find all borrowed books that are past due date
        overdue_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date__lt=today
        )
        
        count = overdue_records.count()
        
        # Update status to overdue
        overdue_records.update(status='overdue')
        
        logger.info(f"Updated {count} books to overdue status")
        return f"Updated {count} books to overdue status"
        
    except Exception as e:
        logger.error(f"Error updating overdue books: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.send_due_reminders')
def send_due_reminders():
    """
    Send email reminders for books due in 3 days
    Runs daily at 9 AM
    """
    try:
        today = timezone.now().date()
        due_soon_date = today + timedelta(days=3)
        
        # Find books due in 3 days
        due_soon_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date=due_soon_date
        ).select_related('user', 'book')
        
        sent_count = 0
        
        for record in due_soon_records:
            try:
                subject = f'Reminder: "{record.book.title}" is due in 3 days'
                message = f"""
Dear {record.user.get_full_name() or record.user.username},

This is a friendly reminder that the following book is due in 3 days:

Book: {record.book.title}
Author: {record.book.author}
Due Date: {record.due_date.strftime('%B %d, %Y')}

Please return the book on or before the due date to avoid late fees.

Thank you,
Smart Library Management System
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [record.user.email],
                    fail_silently=False
                )
                
                sent_count += 1
                logger.info(f"Sent due reminder to {record.user.email} for book {record.book.title}")
                
            except Exception as e:
                logger.error(f"Failed to send due reminder to {record.user.email}: {str(e)}")
        
        logger.info(f"Sent {sent_count} due soon reminders")
        return f"Sent {sent_count} due soon reminders"
        
    except Exception as e:
        logger.error(f"Error sending due reminders: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.send_overdue_reminders')
def send_overdue_reminders():
    """
    Send email reminders for overdue books
    Runs daily at 10 AM
    """
    try:
        # Find all overdue books
        overdue_records = BorrowRecord.objects.filter(
            status='overdue'
        ).select_related('user', 'book')
        
        sent_count = 0
        
        for record in overdue_records:
            try:
                days_overdue = (timezone.now().date() - record.due_date).days
                
                subject = f'OVERDUE: "{record.book.title}" - {days_overdue} days late'
                message = f"""
Dear {record.user.get_full_name() or record.user.username},

The following book is OVERDUE:

Book: {record.book.title}
Author: {record.book.author}
Due Date: {record.due_date.strftime('%B %d, %Y')}
Days Overdue: {days_overdue}
Fine Amount: ETB {record.fine_amount}

Please return the book as soon as possible and pay the fine.

Thank you,
Smart Library Management System
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [record.user.email],
                    fail_silently=False
                )
                
                sent_count += 1
                logger.info(f"Sent overdue reminder to {record.user.email} for book {record.book.title}")
                
            except Exception as e:
                logger.error(f"Failed to send overdue reminder to {record.user.email}: {str(e)}")
        
        logger.info(f"Sent {sent_count} overdue reminders")
        return f"Sent {sent_count} overdue reminders"
        
    except Exception as e:
        logger.error(f"Error sending overdue reminders: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.check_waitlist_notifications')
def check_waitlist_notifications():
    """
    Check for available books and notify waitlist users
    Uses BookRequest model as waitlist system
    Runs every hour
    
    NOTE: This task is automatically handled by BorrowRecord.return_book()
    which calls _notify_waitlist() when a book is returned.
    This hourly task is a backup to catch any missed notifications.
    """
    try:
        from apps.books.models import Book
        from apps.borrow.models import BookRequest
        
        # Find books with available copies that have pending requests (waitlist)
        books_with_waitlist = Book.objects.filter(
            available_copies__gt=0
        ).distinct()
        
        notified_count = 0
        
        for book in books_with_waitlist:
            # Get pending requests for this book (waitlist entries)
            # Get first 3 users in waitlist (oldest requests first)
            pending_requests = BookRequest.objects.filter(
                book=book,
                status='pending',
                notified=False  # Only notify once
            ).select_related('user').order_by('request_date')[:3]
            
            for index, book_request in enumerate(pending_requests):
                try:
                    # Calculate position in queue
                    position = index + 1
                    total_in_queue = BookRequest.objects.filter(
                        book=book,
                        status='pending'
                    ).count()
                    
                    subject = f'Book Available: "{book.title}"'
                    message = f"""
Dear {book_request.user.get_full_name() or book_request.user.username},

Good news! The book you requested is now available:

Book: {book.title}
Author: {book.author}
Available Copies: {book.available_copies}

Your Position in Queue: #{position} of {total_in_queue}

You can now request this book from the library. Please visit the library or log in to your account to complete the borrowing process.

Book Details: {settings.SITE_URL}/books/{book.id}/

Thank you,
Smart Library Management System
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [book_request.user.email],
                        fail_silently=False
                    )
                    
                    # Mark as notified
                    book_request.notified = True
                    book_request.save()
                    
                    notified_count += 1
                    logger.info(f"Notified {book_request.user.email} about available book {book.title} (position #{position})")
                    
                except Exception as e:
                    logger.error(f"Failed to notify {book_request.user.email}: {str(e)}")
        
        logger.info(f"Sent {notified_count} waitlist notifications")
        return f"Sent {notified_count} waitlist notifications"
        
    except Exception as e:
        logger.error(f"Error checking waitlist: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.calculate_fines')
def calculate_fines():
    """
    Calculate and update fines for overdue books
    Runs daily at 11 PM
    """
    try:
        from apps.dashboard.models import SystemSettings
        from decimal import Decimal
        
        settings_obj = SystemSettings.get_settings()
        fine_per_day = settings_obj.fine_per_day
        
        # Find all overdue books
        overdue_records = BorrowRecord.objects.filter(status='overdue')
        
        updated_count = 0
        
        for record in overdue_records:
            days_overdue = record.get_days_overdue()
            new_fine = Decimal(str(days_overdue)) * fine_per_day
            
            if record.fine_amount != new_fine:
                BorrowRecord.objects.filter(id=record.id).update(fine_amount=new_fine)
                updated_count += 1
        
        logger.info(f"Updated fines for {updated_count} overdue books")
        return f"Updated fines for {updated_count} overdue books"
        
    except Exception as e:
        logger.error(f"Error calculating fines: {str(e)}")
        return f"Error: {str(e)}"
