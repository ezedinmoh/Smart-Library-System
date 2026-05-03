"""
Enhanced notification system for the library management system.
Supports Student, Librarian, and Admin notifications.
"""
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta


def notify_book_issued(request, borrow_record):
    """Notify user when book is issued"""
    messages.success(
        request, 
        f'Book "{borrow_record.book.title}" has been issued successfully. '
        f'Due date: {borrow_record.due_date.strftime("%B %d, %Y")}'
    )


def notify_book_returned(request, borrow_record):
    """Notify when book is returned"""
    if borrow_record.fine_amount > 0:
        messages.warning(
            request,
            f'Book "{borrow_record.book.title}" returned. Fine: ₹{borrow_record.fine_amount}'
        )
    else:
        messages.success(
            request,
            f'Book "{borrow_record.book.title}" returned successfully.'
        )


def _send_email_async(subject, text_content, html_content, from_email, to_email):
    """
    Send email in a background thread.
    Templates are pre-rendered before the thread starts (safe for gunicorn).
    The thread only handles the SMTP connection.
    Skips obviously fake/invalid email addresses to protect Gmail quota.
    """
    import threading
    import re
    from django.core.mail import EmailMultiAlternatives

    # Guard: skip invalid or known-fake emails before even starting a thread
    _fake_domains = {
        'test.com', 'example.com', 'example.org', 'example.net',
        'fake.com', 'dummy.com', 'noreply.com', 'invalid.com',
        'mailinator.com', 'guerrillamail.com', 'tempmail.com',
        'localhost', 'test.local', 'demo.com',
    }
    _valid_email = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

    if not to_email or not _valid_email.match(to_email.strip().lower()):
        return  # skip silently — invalid format
    domain = to_email.strip().lower().split('@')[-1]
    if domain in _fake_domains:
        return  # skip silently — known fake domain

    # Capture values as local variables for the thread closure
    _subject = subject
    _text = text_content
    _html = html_content
    _from = from_email
    _to = to_email

    def _send():
        try:
            # Close inherited DB connections — threads must not reuse them
            from django.db import connections
            for conn in connections.all():
                conn.close()

            msg = EmailMultiAlternatives(
                subject=_subject,
                body=_text,
                from_email=_from,
                to=[_to]
            )
            msg.attach_alternative(_html, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Async email failed to {_to}: {str(e)}"
            )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


def notify_request_approved(request, book_request):
    """Notify when book request is approved - sends email in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from apps.borrow.models import BorrowRecord

        borrow_record = BorrowRecord.objects.filter(
            book_request=book_request,
            user=book_request.user
        ).first()

        if borrow_record and book_request.user.email:
            context = {
                'user': book_request.user,
                'book': book_request.book,
                'due_date': borrow_record.due_date,
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
            }
            subject = f'Book Request Approved - {book_request.book.title}'
            text_content = render_to_string('emails/book_request_approved.txt', context)
            html_content = render_to_string('emails/book_request_approved.html', context)
            _send_email_async(subject, text_content, html_content,
                              settings.DEFAULT_FROM_EMAIL, book_request.user.email)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue approved email: {str(e)}")


def notify_request_rejected(request, book_request, reason=""):
    """Notify when book request is rejected - sends email in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string

        if not book_request.user.email:
            return

        context = {
            'user': book_request.user,
            'book': book_request.book,
            'reason': reason,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        subject = f'Book Request Rejected - {book_request.book.title}'
        text_content = render_to_string('emails/book_request_rejected.txt', context)
        html_content = render_to_string('emails/book_request_rejected.html', context)
        _send_email_async(subject, text_content, html_content,
                          settings.DEFAULT_FROM_EMAIL, book_request.user.email)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue rejected email: {str(e)}")


def notify_book_due_soon(borrow_record):
    """Notify user when book is due soon - sends in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not borrow_record.user.email:
            return
        days_remaining = (borrow_record.due_date - timezone.now().date()).days
        ctx = {'user': borrow_record.user, 'book': borrow_record.book,
               'due_date': borrow_record.due_date, 'days_remaining': days_remaining,
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Book Due Soon - {borrow_record.book.title}'
        _send_email_async(subject,
                          render_to_string('emails/book_due_soon.txt', ctx),
                          render_to_string('emails/book_due_soon.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, borrow_record.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue due-soon email: {e}")


def notify_book_overdue(borrow_record):
    """Notify user when book becomes overdue - sends in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not borrow_record.user.email:
            return
        days_overdue = (timezone.now().date() - borrow_record.due_date).days
        ctx = {'user': borrow_record.user, 'book': borrow_record.book,
               'due_date': borrow_record.due_date, 'days_overdue': days_overdue,
               'fine_amount': borrow_record.fine_amount,
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Overdue Book - {borrow_record.book.title}'
        _send_email_async(subject,
                          render_to_string('emails/book_overdue.txt', ctx),
                          render_to_string('emails/book_overdue.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, borrow_record.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue overdue email: {e}")


def notify_fine_applied(borrow_record):
    """Notify user when fine is applied - sends in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not borrow_record.user.email:
            return
        days_overdue = (timezone.now().date() - borrow_record.due_date).days
        ctx = {'user': borrow_record.user, 'book': borrow_record.book,
               'due_date': borrow_record.due_date, 'days_overdue': days_overdue,
               'fine_amount': borrow_record.fine_amount, 'fine_paid': borrow_record.fine_paid,
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Fine Applied - {borrow_record.book.title}'
        _send_email_async(subject,
                          render_to_string('emails/fine_applied.txt', ctx),
                          render_to_string('emails/fine_applied.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, borrow_record.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue fine email: {e}")


def notify_book_available_waitlist(book_request, position_in_queue, total_in_queue):
    """Notify waitlist user when book becomes available - sends in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not book_request.user.email:
            return
        ctx = {'user': book_request.user, 'book': book_request.book,
               'position_in_queue': position_in_queue, 'total_in_queue': total_in_queue,
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Book Available - {book_request.book.title}'
        _send_email_async(subject,
                          render_to_string('emails/book_available_waitlist.txt', ctx),
                          render_to_string('emails/book_available_waitlist.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, book_request.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue waitlist email: {e}")


def send_welcome_email(user):
    """Send welcome email to newly verified users - sends in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not user.email:
            return
        ctx = {'user': user, 'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Welcome to {settings.SITE_NAME}!'
        _send_email_async(subject,
                          render_to_string('emails/welcome.txt', ctx),
                          render_to_string('emails/welcome.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue welcome email: {e}")


def get_user_notifications(user, include_deleted=False):
    """Get pending notifications for a user based on their role
    
    Args:
        user: The user to get notifications for
        include_deleted: If True, show all notifications. If False, hide deleted ones.
    """
    from apps.borrow.models import BorrowRecord, BookRequest
    from apps.users.models import NotificationRead
    from django.utils import timezone
    
    notifications = []
    
    if user.is_student:
        # Student notifications
        notifications.extend(_get_student_notifications(user))
    
    if user.is_librarian or user.is_admin:
        # Librarian/Admin notifications
        notifications.extend(_get_librarian_notifications(user))
    
    # Get deleted notification keys (marked as read = deleted from view)
    deleted_keys = set(NotificationRead.objects.filter(
        user=user
    ).values_list('notification_key', flat=True))
    
    # Filter notifications based on deleted status
    filtered_notifications = []
    for notification in notifications:
        notification_key = notification.get('key')
        is_deleted = notification_key in deleted_keys
        
        # For pending requests: never filter them out (they disappear when approved/rejected)
        if notification['type'] == 'pending_request':
            notification['is_read'] = False
            filtered_notifications.append(notification)
        else:
            # For other notifications: only show if not deleted (unless include_deleted=True)
            if include_deleted or not is_deleted:
                notification['is_read'] = is_deleted
                filtered_notifications.append(notification)
    
    # Sort by date (most recent first)
    # Ensure all dates are datetime objects for proper comparison
    def get_sort_date(notification):
        date_val = notification.get('date', timezone.now())
        # If it's a date object (not datetime), convert to datetime
        if hasattr(date_val, 'date') and not hasattr(date_val, 'hour'):
            from datetime import datetime
            date_val = datetime.combine(date_val, datetime.min.time())
            date_val = timezone.make_aware(date_val) if timezone.is_naive(date_val) else date_val
        return date_val
    
    filtered_notifications.sort(key=get_sort_date, reverse=True)
    
    return filtered_notifications


def _get_student_notifications(user):
    """Get notifications specific to students"""
    from apps.borrow.models import BorrowRecord, BookRequest
    from datetime import datetime
    
    notifications = []
    
    # Overdue books
    overdue_books = BorrowRecord.objects.filter(
        user=user, 
        status='overdue'
    ).select_related('book')
    
    for record in overdue_books:
        days_overdue = (timezone.now().date() - record.due_date).days
        # Convert date to datetime for sorting
        due_datetime = datetime.combine(record.due_date, datetime.min.time())
        due_datetime = timezone.make_aware(due_datetime) if timezone.is_naive(due_datetime) else due_datetime
        
        notifications.append({
            'type': 'overdue',
            'level': 'danger',
            'icon': 'exclamation-triangle',
            'title': 'Overdue Book',
            'message': f'"{record.book.title}" is {days_overdue} day(s) overdue',
            'fine': record.fine_amount,
            'link': f'/borrow/my-books/',
            'date': due_datetime,
            'key': f'overdue_{record.pk}'
        })
    
    # Books due soon (within 3 days)
    due_soon = BorrowRecord.objects.filter(
        user=user,
        status='borrowed',
        due_date__lte=timezone.now().date() + timedelta(days=3),
        due_date__gte=timezone.now().date()
    ).select_related('book')
    
    for record in due_soon:
        days_remaining = (record.due_date - timezone.now().date()).days
        # Convert date to datetime for sorting
        due_datetime = datetime.combine(record.due_date, datetime.min.time())
        due_datetime = timezone.make_aware(due_datetime) if timezone.is_naive(due_datetime) else due_datetime
        
        notifications.append({
            'type': 'due_soon',
            'level': 'warning',
            'icon': 'clock',
            'title': 'Due Soon',
            'message': f'"{record.book.title}" is due in {days_remaining} day(s)',
            'link': f'/borrow/my-books/',
            'date': due_datetime,
            'key': f'due_soon_{record.pk}'
        })
    
    # Approved requests (both ready and recently fulfilled)
    # Show ready requests (if any exist in the brief moment)
    approved_requests = BookRequest.objects.filter(
        user=user,
        status='ready'
    ).select_related('book').order_by('-approved_date')
    
    for request in approved_requests:
        notifications.append({
            'type': 'approved',
            'level': 'success',
            'icon': 'check-circle',
            'title': 'Book Approved',
            'message': f'"{request.book.title}" is ready! You can now read it online or get the physical copy from the library',
            'link': f'/borrow/my-books/',
            'date': request.approved_date if request.approved_date else request.updated_at,
            'key': f'approved_{request.pk}'
        })
    
    # Recently fulfilled requests (approved and borrowed within last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    fulfilled_requests = BookRequest.objects.filter(
        user=user,
        status='fulfilled',
        approved_date__isnull=False,
        approved_date__gte=week_ago
    ).select_related('book').order_by('-approved_date')
    
    for request in fulfilled_requests:
        notifications.append({
            'type': 'approved',
            'level': 'success',
            'icon': 'check-circle',
            'title': 'Book Approved',
            'message': f'"{request.book.title}" has been approved! You can now read it online or get the physical copy from the library',
            'link': f'/borrow/my-books/',
            'date': request.approved_date,
            'key': f'approved_{request.pk}'
        })
    
    # Rejected requests (recent - last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    rejected_requests = BookRequest.objects.filter(
        user=user,
        status='rejected',
        updated_at__gte=week_ago
    ).select_related('book')
    
    for request in rejected_requests:
        reason_snippet = f' — {request.rejection_reason[:60]}{"..." if len(request.rejection_reason) > 60 else ""}' if request.rejection_reason else ''
        notifications.append({
            'type': 'rejected',
            'level': 'danger',
            'icon': 'x-circle',
            'title': 'Request Rejected',
            'message': f'Your request for "{request.book.title}" was rejected{reason_snippet}',
            'link': f'/borrow/my-books/',
            'date': request.updated_at,
            'key': f'rejected_{request.pk}'
        })
    
    return notifications


def _get_librarian_notifications(user):
    """Get notifications specific to librarians and admins"""
    from apps.borrow.models import BorrowRecord, BookRequest
    from apps.books.models import Book
    from datetime import datetime
    
    notifications = []
    
    # Pending book requests
    pending_requests = BookRequest.objects.filter(
        status='pending'
    ).select_related('user', 'book').order_by('-request_date')
    
    for request in pending_requests:
        notifications.append({
            'type': 'pending_request',
            'level': 'warning',
            'icon': 'hourglass-split',
            'title': 'New Book Request',
            'message': f'{request.user.get_full_name() or request.user.username} requested "{request.book.title}"',
            'link': f'/borrow/pending-requests/',
            'date': request.request_date,
            'key': f'pending_request_{request.pk}'
        })
    
    # Overdue books (all users)
    overdue_books = BorrowRecord.objects.filter(
        status='overdue'
    ).select_related('user', 'book').order_by('due_date')
    
    for record in overdue_books:
        days_overdue = (timezone.now().date() - record.due_date).days
        # Convert date to datetime for sorting
        due_datetime = datetime.combine(record.due_date, datetime.min.time())
        due_datetime = timezone.make_aware(due_datetime) if timezone.is_naive(due_datetime) else due_datetime
        
        notifications.append({
            'type': 'overdue_book',
            'level': 'danger',
            'icon': 'exclamation-triangle',
            'title': 'Overdue Book',
            'message': f'{record.user.get_full_name() or record.user.username} - "{record.book.title}" ({days_overdue} days overdue)',
            'fine': record.fine_amount,
            'link': f'/borrow/overdue/',
            'date': due_datetime,
            'key': f'overdue_book_{record.pk}'
        })
    
    # Low stock books (2 or fewer copies available)
    low_stock_books = Book.objects.filter(
        available_copies__lte=2,
        available_copies__gt=0
    ).order_by('available_copies')
    
    for book in low_stock_books:
        # Use book's updated_at if available, otherwise use current time
        book_date = book.updated_at if hasattr(book, 'updated_at') and book.updated_at else timezone.now()
        notifications.append({
            'type': 'low_stock',
            'level': 'warning',
            'icon': 'exclamation-circle',
            'title': 'Low Stock Alert',
            'message': f'"{book.title}" - Only {book.available_copies} cop{"y" if book.available_copies == 1 else "ies"} left',
            'link': f'/books/{book.pk}/',
            'date': book_date,
            'key': f'low_stock_{book.pk}'
        })
    
    # Books due today
    due_today = BorrowRecord.objects.filter(
        status='borrowed',
        due_date=timezone.now().date()
    ).select_related('user', 'book')
    
    for record in due_today:
        # Convert date to datetime for sorting
        due_datetime = datetime.combine(record.due_date, datetime.min.time())
        due_datetime = timezone.make_aware(due_datetime) if timezone.is_naive(due_datetime) else due_datetime
        
        notifications.append({
            'type': 'due_today',
            'level': 'info',
            'icon': 'calendar-check',
            'title': 'Due Today',
            'message': f'{record.user.get_full_name() or record.user.username} - "{record.book.title}" is due today',
            'link': f'/borrow/issue-return/',
            'date': due_datetime,
            'key': f'due_today_{record.pk}'
        })
    
    return notifications


def get_notification_count(user):
    """Get count of important unread notifications"""
    from apps.borrow.models import BorrowRecord, BookRequest
    from apps.users.models import NotificationRead
    
    # Get all read notification keys for this user
    read_keys = set(NotificationRead.objects.filter(
        user=user
    ).values_list('notification_key', flat=True))
    
    count = 0
    
    if user.is_student:
        # Count overdue books (unread)
        overdue = BorrowRecord.objects.filter(user=user, status='overdue')
        for record in overdue:
            if f'overdue_{record.pk}' not in read_keys:
                count += 1
        
        # Count approved requests (ready for pickup) (unread)
        approved = BookRequest.objects.filter(user=user, status='ready')
        for request in approved:
            if f'approved_{request.pk}' not in read_keys:
                count += 1
        
        # Count rejected requests (recent - last 7 days) (unread)
        week_ago = timezone.now() - timedelta(days=7)
        rejected = BookRequest.objects.filter(
            user=user,
            status='rejected',
            updated_at__gte=week_ago
        )
        for request in rejected:
            if f'rejected_{request.pk}' not in read_keys:
                count += 1
        
        # Count books due within 2 days (unread)
        due_soon = BorrowRecord.objects.filter(
            user=user,
            status='borrowed',
            due_date__lte=timezone.now().date() + timedelta(days=2),
            due_date__gte=timezone.now().date()
        )
        for record in due_soon:
            if f'due_soon_{record.pk}' not in read_keys:
                count += 1
    
    if user.is_librarian or user.is_admin:
        # Count ALL pending requests (ALWAYS show, don't check read status)
        # These should only disappear when approved/rejected
        count += BookRequest.objects.filter(status='pending').count()
        
        # Count overdue books (unread)
        overdue = BorrowRecord.objects.filter(status='overdue')
        for record in overdue:
            if f'overdue_book_{record.pk}' not in read_keys:
                count += 1
        
        # Count books due today (unread)
        due_today = BorrowRecord.objects.filter(
            status='borrowed',
            due_date=timezone.now().date()
        )
        for record in due_today:
            if f'due_today_{record.pk}' not in read_keys:
                count += 1
    
    return count


def mark_notification_read(user, notification_key, notification_type):
    """Mark a notification as read"""
    from apps.users.models import NotificationRead
    
    NotificationRead.objects.get_or_create(
        user=user,
        notification_key=notification_key,
        notification_type=notification_type
    )


def mark_all_notifications_read(user):
    """Mark all current notifications as read (except pending requests)"""
    from apps.users.models import NotificationRead
    
    notifications = get_user_notifications(user)
    
    for notification in notifications:
        # Never mark pending requests as read via "mark all" - they clear only on approve/reject
        if notification['type'] == 'pending_request':
            continue
        NotificationRead.objects.get_or_create(
            user=user,
            notification_key=notification['key'],
            notification_type=notification['type']
        )


def delete_notification(user, notification_key, notification_type):
    """Delete a single notification by marking it as read and adding a deleted flag"""
    from apps.users.models import NotificationRead
    
    # Mark as read (deleted)
    NotificationRead.objects.get_or_create(
        user=user,
        notification_key=notification_key,
        notification_type=notification_type
    )
    return True


def clear_all_notifications(user):
    """Clear all notifications for the user by marking them as deleted"""
    from apps.users.models import NotificationRead
    
    # Get all currently visible (non-deleted) notifications
    notifications = get_user_notifications(user, include_deleted=False)
    count = 0
    
    # Mark ALL visible notifications as deleted (by creating NotificationRead entries)
    for notification in notifications:
        # Skip pending requests - they should only disappear when approved/rejected
        if notification['type'] == 'pending_request':
            continue
            
        NotificationRead.objects.get_or_create(
            user=user,
            notification_key=notification['key'],
            notification_type=notification['type']
        )
        count += 1
    
    return count



def notify_payment_success(payment):
    """Send payment success email in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not payment.user.email:
            return
        ctx = {'user': payment.user, 'payment': payment,
               'book': payment.borrow_record.book, 'amount': payment.amount,
               'currency': payment.currency,
               'payment_method': payment.get_payment_method_display(),
               'transaction_id': payment.transaction_id,
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Payment Successful - {settings.SITE_NAME}'
        _send_email_async(subject,
                          render_to_string('emails/payment_success.txt', ctx),
                          render_to_string('emails/payment_success.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, payment.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue payment success email: {e}")


def notify_payment_failure(payment):
    """Send payment failure email in background thread"""
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        if not payment.user.email:
            return
        ctx = {'user': payment.user, 'payment': payment,
               'book': payment.borrow_record.book, 'amount': payment.amount,
               'currency': payment.currency,
               'payment_method': payment.get_payment_method_display(),
               'site_name': settings.SITE_NAME, 'site_url': settings.SITE_URL}
        subject = f'Payment Failed - {settings.SITE_NAME}'
        _send_email_async(subject,
                          render_to_string('emails/payment_failure.txt', ctx),
                          render_to_string('emails/payment_failure.html', ctx),
                          settings.DEFAULT_FROM_EMAIL, payment.user.email)
    except Exception as e:
        import logging; logging.getLogger(__name__).error(f"Failed to queue payment failure email: {e}")


def notify_admins_new_request(book_request):
    """
    Notify all librarians and admins when a student submits a new book request.
    Sends email in background thread — non-blocking.
    """
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from apps.users.models import User

        # Get all active librarians and admins
        staff = User.objects.filter(
            role__in=['librarian', 'admin'],
            is_active=True
        ).exclude(email='')

        if not staff.exists():
            return

        ctx = {
            'book_request': book_request,
            'student': book_request.user,
            'book': book_request.book,
            'request_date': book_request.request_date,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        subject = f'New Book Request — {book_request.book.title}'
        text_content = render_to_string('emails/admin_new_request.txt', ctx)
        html_content = render_to_string('emails/admin_new_request.html', ctx)

        for staff_member in staff:
            _send_email_async(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=staff_member.email
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue admin new-request email: {e}")


def notify_admins_fine_paid(payment):
    """
    Notify all librarians and admins when a student pays a fine.
    Sends email in background thread — non-blocking.
    """
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from apps.users.models import User

        # Get all active librarians and admins
        staff = User.objects.filter(
            role__in=['librarian', 'admin'],
            is_active=True
        ).exclude(email='')

        if not staff.exists():
            return

        ctx = {
            'payment': payment,
            'student': payment.user,
            'book': payment.borrow_record.book,
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.get_payment_method_display(),
            'transaction_id': payment.transaction_id,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        subject = f'Fine Paid — {payment.user.get_full_name() or payment.user.username} — {payment.borrow_record.book.title}'
        text_content = render_to_string('emails/admin_fine_paid.txt', ctx)
        html_content = render_to_string('emails/admin_fine_paid.html', ctx)

        for staff_member in staff:
            _send_email_async(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=staff_member.email
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue admin fine-paid email: {e}")


def notify_admins_new_request(book_request):
    """
    Notify all librarians and admins when a student submits a new book request.
    Sends email in background thread — non-blocking.
    """
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from apps.users.models import User

        staff = User.objects.filter(
            role__in=['librarian', 'admin'],
            is_active=True
        ).exclude(email='')

        if not staff.exists():
            return

        ctx = {
            'book_request': book_request,
            'student': book_request.user,
            'book': book_request.book,
            'request_date': book_request.request_date,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        subject = f'New Book Request — {book_request.book.title}'
        text_content = render_to_string('emails/admin_new_request.txt', ctx)
        html_content = render_to_string('emails/admin_new_request.html', ctx)

        for staff_member in staff:
            _send_email_async(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=staff_member.email
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue admin new-request email: {e}")


def notify_admins_fine_paid(payment):
    """
    Notify all librarians and admins when a student pays a fine.
    Sends email in background thread — non-blocking.
    """
    try:
        from django.conf import settings
        from django.template.loader import render_to_string
        from apps.users.models import User

        staff = User.objects.filter(
            role__in=['librarian', 'admin'],
            is_active=True
        ).exclude(email='')

        if not staff.exists():
            return

        ctx = {
            'payment': payment,
            'student': payment.user,
            'book': payment.borrow_record.book,
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.get_payment_method_display(),
            'transaction_id': payment.transaction_id,
            'site_name': settings.SITE_NAME,
            'site_url': settings.SITE_URL,
        }
        subject = f'Fine Paid — {payment.user.get_full_name() or payment.user.username} — {payment.borrow_record.book.title}'
        text_content = render_to_string('emails/admin_fine_paid.txt', ctx)
        html_content = render_to_string('emails/admin_fine_paid.html', ctx)

        for staff_member in staff:
            _send_email_async(
                subject=subject,
                text_content=text_content,
                html_content=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_email=staff_member.email
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to queue admin fine-paid email: {e}")
