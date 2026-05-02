"""
Role-based permission system for the library management system.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.permissions import BasePermission


# Function-based view decorators
def admin_required(view_func):
    """Decorator for views that require admin access"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def librarian_or_admin_required(view_func):
    """Decorator for views that require librarian or admin access"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_librarian or request.user.is_admin):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """Decorator for views that require student access"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_student:
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Class-based view mixins
class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for views that require admin access"""
    
    def test_func(self):
        return self.request.user.is_admin
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard:home')


class LibrarianOrAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for views that require librarian or admin access"""
    
    def test_func(self):
        return self.request.user.is_librarian or self.request.user.is_admin
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard:home')


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin for views that require student access"""
    
    def test_func(self):
        return self.request.user.is_student
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access this page.")
        return redirect('dashboard:home')


# DRF Permission Classes
class IsAdmin(BasePermission):
    """Permission class for admin users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsLibrarianOrAdmin(BasePermission):
    """Permission class for librarian or admin users"""
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                (request.user.is_librarian or request.user.is_admin))


class IsStudent(BasePermission):
    """Permission class for student users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_student


class IsOwnerOrLibrarianOrAdmin(BasePermission):
    """Permission class for owner, librarian, or admin users"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the owner, librarian, or admin
        if hasattr(obj, 'user'):
            return (obj.user == request.user or 
                   request.user.is_librarian or 
                   request.user.is_admin)
        return request.user.is_librarian or request.user.is_admin


# Utility functions
def check_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_admin


def check_librarian_or_admin(user):
    """Check if user is librarian or admin"""
    return user.is_authenticated and (user.is_librarian or user.is_admin)


def check_student(user):
    """Check if user is student"""
    return user.is_authenticated and user.is_student