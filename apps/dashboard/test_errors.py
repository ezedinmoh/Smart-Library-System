"""
Test views for error pages - FOR DEVELOPMENT ONLY
Remove or comment out these views in production
"""
from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden


def test_404(request):
    """Test 404 error page"""
    return render(request, '404.html', status=404)


def test_500(request):
    """Test 500 error page"""
    return render(request, '500.html', status=500)


def test_403(request):
    """Test 403 error page"""
    return render(request, '403.html', status=403)
