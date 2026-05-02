"""
User Management Views - Delete, Deactivate, Activate, and Batch Operations
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import User
from apps.dashboard.utils import log_activity
from apps.borrow.models import BorrowRecord, BookRequest


def check_admin(user):
    """Check if user is an admin"""
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(check_admin)
def user_deactivate(request, pk):
    """
    Soft Delete - Deactivate user account (preserve all data)
    """
    user = get_object_or_404(User, pk=pk)
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('users:detail', pk=pk)
    
    # Prevent deactivating the last admin
    if user.role == 'admin':
        active_admins = User.objects.filter(role='admin', is_active=True).count()
        if active_admins <= 1:
            messages.error(request, "Cannot deactivate the last active admin account.")
            return redirect('users:detail', pk=pk)
    
    if request.method == 'POST':
        # Check if user has active borrows
        active_borrows = BorrowRecord.objects.filter(
            user=user, 
            return_date__isnull=True
        ).count()
        
        if active_borrows > 0:
            messages.warning(
                request, 
                f"Warning: User has {active_borrows} active borrow(s). "
                f"They will not be able to return books while deactivated."
            )
        
        # Deactivate user
        user.is_active = False
        user.save()
        
        # Log activity
        log_activity(
            request.user,
            'user_updated',
            f'Deactivated user: {user.username} ({user.get_role_display()})',
            request
        )
        
        messages.success(
            request, 
            f'User "{user.username}" has been deactivated. All data is preserved and can be reactivated later.'
        )
        return redirect('users:list')
    
    # GET request - show confirmation page
    context = {
        'user_to_deactivate': user,
        'active_borrows': BorrowRecord.objects.filter(user=user, return_date__isnull=True).count(),
        'total_borrows': BorrowRecord.objects.filter(user=user).count(),
        'total_payments': user.payments.count() if hasattr(user, 'payments') else 0,
        'total_reviews': user.book_reviews.count() if hasattr(user, 'book_reviews') else 0,
    }
    return render(request, 'users/user_deactivate_confirm.html', context)


@login_required
@user_passes_test(check_admin)
def user_activate(request, pk):
    """
    Reactivate a deactivated user account
    """
    user = get_object_or_404(User, pk=pk)
    
    if user.is_active:
        messages.info(request, f'User "{user.username}" is already active.')
        return redirect('users:detail', pk=pk)
    
    if request.method == 'POST':
        user.is_active = True
        user.save()
        
        # Log activity
        log_activity(
            request.user,
            'user_updated',
            f'Reactivated user: {user.username} ({user.get_role_display()})',
            request
        )
        
        messages.success(request, f'User "{user.username}" has been reactivated successfully.')
        return redirect('users:detail', pk=pk)
    
    # GET request - show confirmation
    context = {'user_to_activate': user}
    return render(request, 'users/user_activate_confirm.html', context)


@login_required
@user_passes_test(check_admin)
def user_delete(request, pk):
    """
    Hard Delete - Permanently delete user and ALL related data
    WARNING: This action cannot be undone!
    """
    user = get_object_or_404(User, pk=pk)
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('users:detail', pk=pk)
    
    # Prevent deleting the last admin
    if user.role == 'admin':
        active_admins = User.objects.filter(role='admin', is_active=True).count()
        if active_admins <= 1:
            messages.error(request, "Cannot delete the last admin account.")
            return redirect('users:detail', pk=pk)
    
    if request.method == 'POST':
        # Verify confirmation
        confirmation = request.POST.get('confirmation', '').strip()
        if confirmation != user.username:
            messages.error(request, 'Username confirmation does not match. Deletion cancelled.')
            return redirect('users:delete', pk=pk)
        
        # Collect statistics before deletion
        username = user.username
        email = user.email
        role = user.get_role_display()
        
        borrow_count = BorrowRecord.objects.filter(user=user).count()
        request_count = BookRequest.objects.filter(user=user).count()
        payment_count = user.payments.count() if hasattr(user, 'payments') else 0
        review_count = user.book_reviews.count() if hasattr(user, 'book_reviews') else 0
        
        # Delete user (CASCADE will delete all related data)
        with transaction.atomic():
            user.delete()
            
            # Log activity
            log_activity(
                request.user,
                'user_deleted',
                f'PERMANENTLY DELETED user: {username} ({role}) - '
                f'Email: {email}, Borrows: {borrow_count}, Requests: {request_count}, '
                f'Payments: {payment_count}, Reviews: {review_count}',
                request
            )
        
        messages.success(
            request,
            f'User "{username}" and all related data have been permanently deleted. '
            f'Deleted: {borrow_count} borrow records, {request_count} requests, '
            f'{payment_count} payments, {review_count} reviews.'
        )
        return redirect('users:list')
    
    # GET request - show confirmation page with data summary
    context = {
        'user_to_delete': user,
        'borrow_records': BorrowRecord.objects.filter(user=user).count(),
        'active_borrows': BorrowRecord.objects.filter(user=user, return_date__isnull=True).count(),
        'book_requests': BookRequest.objects.filter(user=user).count(),
        'payments': user.payments.count() if hasattr(user, 'payments') else 0,
        'reviews': user.book_reviews.count() if hasattr(user, 'book_reviews') else 0,
        'issued_books': BorrowRecord.objects.filter(issued_by=user).count(),
        'returned_books': BorrowRecord.objects.filter(returned_to=user).count(),
        'approved_requests': BookRequest.objects.filter(approved_by=user).count(),
    }
    return render(request, 'users/user_delete_confirm.html', context)


@login_required
@user_passes_test(check_admin)
@require_POST
def batch_deactivate_users(request):
    """
    Batch deactivate multiple users
    """
    user_ids = request.POST.getlist('user_ids[]')
    
    if not user_ids:
        return JsonResponse({'success': False, 'message': 'No users selected'})
    
    try:
        users = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        
        # Prevent deactivating all admins
        admin_ids = users.filter(role='admin').values_list('id', flat=True)
        if admin_ids:
            remaining_admins = User.objects.filter(
                role='admin', 
                is_active=True
            ).exclude(id__in=admin_ids).count()
            
            if remaining_admins < 1:
                return JsonResponse({
                    'success': False, 
                    'message': 'Cannot deactivate all admin accounts. At least one admin must remain active.'
                })
        
        # Deactivate users
        deactivated_count = users.update(is_active=False)
        
        # Log activity
        usernames = ', '.join(users.values_list('username', flat=True))
        log_activity(
            request.user,
            'user_updated',
            f'Batch deactivated {deactivated_count} users: {usernames}',
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deactivated {deactivated_count} user(s)',
            'count': deactivated_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(check_admin)
@require_POST
def batch_activate_users(request):
    """
    Batch activate multiple users
    """
    user_ids = request.POST.getlist('user_ids[]')
    
    if not user_ids:
        return JsonResponse({'success': False, 'message': 'No users selected'})
    
    try:
        users = User.objects.filter(id__in=user_ids, is_active=False)
        activated_count = users.update(is_active=True)
        
        # Log activity
        usernames = ', '.join(users.values_list('username', flat=True))
        log_activity(
            request.user,
            'user_updated',
            f'Batch activated {activated_count} users: {usernames}',
            request
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully activated {activated_count} user(s)',
            'count': activated_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@user_passes_test(check_admin)
@require_POST
def batch_delete_users(request):
    """
    Batch delete multiple users permanently
    WARNING: This cannot be undone!
    """
    user_ids = request.POST.getlist('user_ids[]')
    confirmation = request.POST.get('confirmation', '').strip()
    
    if not user_ids:
        return JsonResponse({'success': False, 'message': 'No users selected'})
    
    # Require confirmation
    if confirmation != 'DELETE':
        return JsonResponse({
            'success': False, 
            'message': 'Confirmation failed. Type DELETE to confirm.'
        })
    
    try:
        users = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        
        # Prevent deleting all admins
        admin_ids = users.filter(role='admin').values_list('id', flat=True)
        if admin_ids:
            remaining_admins = User.objects.filter(
                role='admin', 
                is_active=True
            ).exclude(id__in=admin_ids).count()
            
            if remaining_admins < 1:
                return JsonResponse({
                    'success': False, 
                    'message': 'Cannot delete all admin accounts. At least one admin must remain.'
                })
        
        # Collect statistics
        usernames = list(users.values_list('username', flat=True))
        user_count = users.count()
        
        # Delete users
        with transaction.atomic():
            users.delete()
            
            # Log activity
            log_activity(
                request.user,
                'user_deleted',
                f'BATCH DELETED {user_count} users: {", ".join(usernames)}',
                request
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {user_count} user(s) and all their related data',
            'count': user_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
