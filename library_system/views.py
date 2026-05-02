"""
Custom error handlers for the library system.
"""
from django.shortcuts import render


def custom_404(request, exception):
    """Custom 404 error handler."""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 error handler."""
    return render(request, '500.html', status=500)


def custom_403(request, exception):
    """Custom 403 error handler."""
    return render(request, '403.html', status=403)
