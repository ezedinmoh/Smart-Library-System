from django import template
from apps.users.notifications import get_notification_count as get_count, get_user_notifications as get_notifications

register = template.Library()

@register.simple_tag
def get_notification_count(user):
    """Get notification count for a user"""
    if user.is_authenticated:
        return get_count(user)
    return 0

@register.simple_tag
def get_user_notifications(user):
    """Get all notifications for a user"""
    if user.is_authenticated:
        return get_notifications(user)
    return []

@register.simple_tag
def get_pending_requests_count():
    """Get count of pending book requests (for librarian/admin badge)"""
    from apps.borrow.models import BookRequest
    return BookRequest.objects.filter(status='pending').count()
