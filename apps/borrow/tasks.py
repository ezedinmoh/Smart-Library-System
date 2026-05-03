"""
Background Tasks for Borrow Management
Handles automated email reminders and status updates
"""

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from apps.borrow.models import BorrowRecord
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.borrow.tasks.update_overdue_books')
def update_overdue_books():
    """Update overdue status for all borrowed books. Runs daily at midnight."""
    try:
        today = timezone.now().date()
        overdue_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date__lt=today
        )
        count = overdue_records.count()
        overdue_records.update(status='overdue')
        logger.info(f"Updated {count} books to overdue status")
        return f"Updated {count} books to overdue status"
    except Exception as e:
        logger.error(f"Error updating overdue books: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.send_due_reminders')
def send_due_reminders():
    """Send HTML email reminders for books due in 3 days. Runs daily at 9 AM."""
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string

        today = timezone.now().date()
        due_soon_date = today + timedelta(days=3)

        due_soon_records = BorrowRecord.objects.filter(
            status='borrowed',
            due_date=due_soon_date
        ).select_related('user', 'book')

        sent_count = 0

        for record in due_soon_records:
            if not record.user.email:
                continue
            try:
                days_remaining = (record.due_date - today).days
                ctx = {
                    'user':           record.user,
                    'book':           record.book,
                    'due_date':       record.due_date,
                    'days_remaining': days_remaining,
                    'site_name':      settings.SITE_NAME,
                    'site_url':       settings.SITE_URL,
                }
                subject      = f'Reminder: "{record.book.title}" is due in {days_remaining} day(s)'
                text_content = render_to_string('emails/book_due_soon.txt', ctx)
                html_content = render_to_string('emails/book_due_soon.html', ctx)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[record.user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                sent_count += 1
                logger.info(f"Sent due reminder to {record.user.email} for '{record.book.title}'")

            except Exception as e:
                logger.error(f"Failed to send due reminder to {record.user.email}: {str(e)}")

        logger.info(f"Sent {sent_count} due soon reminders")
        return f"Sent {sent_count} due soon reminders"

    except Exception as e:
        logger.error(f"Error sending due reminders: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.send_overdue_reminders')
def send_overdue_reminders():
    """Send HTML email reminders for overdue books. Runs daily at 10 AM."""
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string

        overdue_records = BorrowRecord.objects.filter(
            status='overdue'
        ).select_related('user', 'book')

        sent_count = 0

        for record in overdue_records:
            if not record.user.email:
                continue
            try:
                days_overdue = (timezone.now().date() - record.due_date).days
                ctx = {
                    'user':         record.user,
                    'book':         record.book,
                    'due_date':     record.due_date,
                    'days_overdue': days_overdue,
                    'fine_amount':  record.fine_amount,
                    'site_name':    settings.SITE_NAME,
                    'site_url':     settings.SITE_URL,
                }
                subject      = f'OVERDUE: "{record.book.title}" — {days_overdue} day(s) late, Fine: ETB {record.fine_amount}'
                text_content = render_to_string('emails/book_overdue.txt', ctx)
                html_content = render_to_string('emails/book_overdue.html', ctx)

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[record.user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send(fail_silently=False)

                sent_count += 1
                logger.info(f"Sent overdue reminder to {record.user.email} for '{record.book.title}'")

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
    Notify waitlist users when a book becomes available.
    Runs every hour as a backup — primary notification happens in BorrowRecord.return_book().
    """
    try:
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from apps.books.models import Book
        from apps.borrow.models import BookRequest

        books_with_waitlist = Book.objects.filter(available_copies__gt=0)
        notified_count = 0

        for book in books_with_waitlist:
            pending_requests = BookRequest.objects.filter(
                book=book,
                status='pending',
                notified=False
            ).select_related('user').order_by('request_date')[:3]

            total_in_queue = BookRequest.objects.filter(
                book=book, status='pending'
            ).count()

            for index, book_request in enumerate(pending_requests):
                if not book_request.user.email:
                    continue
                try:
                    position = index + 1
                    ctx = {
                        'user':              book_request.user,
                        'book':              book_request.book,
                        'position_in_queue': position,
                        'total_in_queue':    total_in_queue,
                        'site_name':         settings.SITE_NAME,
                        'site_url':          settings.SITE_URL,
                    }
                    subject      = f'Book Available: "{book.title}"'
                    text_content = render_to_string('emails/book_available_waitlist.txt', ctx)
                    html_content = render_to_string('emails/book_available_waitlist.html', ctx)

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[book_request.user.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send(fail_silently=False)

                    book_request.notified = True
                    book_request.save()

                    notified_count += 1
                    logger.info(f"Notified {book_request.user.email} — '{book.title}' position #{position}")

                except Exception as e:
                    logger.error(f"Failed to notify {book_request.user.email}: {str(e)}")

        logger.info(f"Sent {notified_count} waitlist notifications")
        return f"Sent {notified_count} waitlist notifications"

    except Exception as e:
        logger.error(f"Error checking waitlist: {str(e)}")
        return f"Error: {str(e)}"


@shared_task(name='apps.borrow.tasks.calculate_fines')
def calculate_fines():
    """Calculate and update fines for overdue books. Runs daily at 11 PM."""
    try:
        from apps.dashboard.models import SystemSettings
        from decimal import Decimal

        settings_obj = SystemSettings.get_settings()
        fine_per_day = settings_obj.fine_per_day

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
