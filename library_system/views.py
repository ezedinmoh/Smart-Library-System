"""
Custom error handlers for the library system.
"""
from django.shortcuts import render


def custom_404(request, exception):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error handler - sends organized email to all admins."""
    import sys
    import traceback
    from django.utils import timezone
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string

    # Get error details
    exc_type, exc_value, exc_tb = sys.exc_info()
    error_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    error_time     = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
    error_type     = exc_type.__name__ if exc_type else 'Unknown Error'
    error_message  = str(exc_value) if exc_value else 'No details available'
    request_url    = request.build_absolute_uri()
    request_method = request.method
    user_info      = f'{request.user.username} ({request.user.email})' if request.user.is_authenticated else 'Anonymous'

    ctx = {
        'error_time':      error_time,
        'request_url':     request_url,
        'request_method':  request_method,
        'user_info':       user_info,
        'error_type':      error_type,
        'error_message':   error_message,
        'error_traceback': error_traceback,
    }

    subject      = f'🚨 [Smart Library] 500 Error - {error_type}'
    text_content = render_to_string('emails/server_error_alert.txt', ctx)
    html_content = render_to_string('emails/server_error_alert.html', ctx)

    try:
        admin_emails = [email for name, email in settings.ADMINS]
        if admin_emails:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=True)
    except Exception:
        pass

    return render(request, '500.html', status=500)


def custom_403(request, exception):
    """Custom 403 error handler."""
    return render(request, '403.html', status=403)
