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

    # Get error details
    exc_type, exc_value, exc_tb = sys.exc_info()
    error_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    error_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
    error_type = exc_type.__name__ if exc_type else 'Unknown Error'
    error_message = str(exc_value) if exc_value else 'No details available'
    request_url = request.build_absolute_uri()
    request_method = request.method
    user_info = f'{request.user.username} ({request.user.email})' if request.user.is_authenticated else 'Anonymous'

    subject = f'🚨 [Smart Library] 500 Error - {error_type}'

    text_content = f"""
SMART LIBRARY - SERVER ERROR ALERT
====================================
Time:    {error_time}
URL:     {request_url}
Method:  {request_method}
User:    {user_info}
Error:   {error_type}: {error_message}

TRACEBACK:
{error_traceback}
====================================
Smart Library System
"""

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333;">
    <div style="background:#dc2626;padding:20px;border-radius:10px 10px 0 0;text-align:center;">
        <h1 style="color:white;margin:0;font-size:22px;">🚨 Server Error Alert</h1>
        <p style="color:#fecaca;margin:5px 0 0 0;">Smart Library Management System</p>
    </div>
    <div style="background:#fef2f2;border:1px solid #fecaca;padding:25px;border-radius:0 0 10px 10px;">
        <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
            <tr style="background:#fee2e2;">
                <td style="padding:10px;font-weight:bold;width:120px;border:1px solid #fecaca;">Time</td>
                <td style="padding:10px;border:1px solid #fecaca;">{error_time}</td>
            </tr>
            <tr>
                <td style="padding:10px;font-weight:bold;border:1px solid #fecaca;">URL</td>
                <td style="padding:10px;border:1px solid #fecaca;word-break:break-all;">{request_url}</td>
            </tr>
            <tr style="background:#fee2e2;">
                <td style="padding:10px;font-weight:bold;border:1px solid #fecaca;">Method</td>
                <td style="padding:10px;border:1px solid #fecaca;">{request_method}</td>
            </tr>
            <tr>
                <td style="padding:10px;font-weight:bold;border:1px solid #fecaca;">User</td>
                <td style="padding:10px;border:1px solid #fecaca;">{user_info}</td>
            </tr>
            <tr style="background:#fee2e2;">
                <td style="padding:10px;font-weight:bold;border:1px solid #fecaca;">Error Type</td>
                <td style="padding:10px;border:1px solid #fecaca;color:#dc2626;font-weight:bold;">{error_type}</td>
            </tr>
            <tr>
                <td style="padding:10px;font-weight:bold;border:1px solid #fecaca;">Message</td>
                <td style="padding:10px;border:1px solid #fecaca;">{error_message}</td>
            </tr>
        </table>

        <div style="background:#1f2937;border-radius:8px;padding:15px;margin-top:15px;">
            <p style="color:#9ca3af;font-size:12px;margin:0 0 8px 0;font-weight:bold;">TRACEBACK:</p>
            <pre style="color:#f9fafb;font-size:11px;margin:0;white-space:pre-wrap;word-break:break-all;">{error_traceback}</pre>
        </div>

        <p style="color:#6b7280;font-size:12px;margin-top:20px;text-align:center;">
            This is an automated alert from Smart Library Management System.<br>
            Please investigate and fix the issue as soon as possible.
        </p>
    </div>
</body>
</html>"""

    # Send to all admins
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
        pass  # Don't let email failure break the error page

    return render(request, '500.html', status=500)


def custom_403(request, exception):
    """Custom 403 error handler."""
    return render(request, '403.html', status=403)
