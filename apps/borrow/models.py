from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


class BookRequest(models.Model):
    """Book request/reservation model for students to request books"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('ready', 'Approved - Ready to Read'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='book_requests')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='book_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    notified = models.BooleanField(default=False)  # Track if user was notified
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} requested {self.book.title} - {self.get_status_display()}"
    
    def can_cancel(self):
        """Check if request can be cancelled by user"""
        return self.status in ['pending', 'ready']
    
    def approve(self, approved_by):
        """Approve the book request - mark as ready for pickup"""
        self.status = 'ready'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
    
    def reject(self, rejected_by, reason=""):
        """Reject the book request"""
        self.status = 'rejected'
        self.approved_by = rejected_by
        self.approved_date = timezone.now()
        self.rejection_reason = reason
        self.save()
    
    def cancel(self, reason=""):
        """Cancel the request (by user)"""
        if self.can_cancel():
            self.status = 'cancelled'
            self.cancellation_reason = reason
            self.save()
            return True
        return False
    
    def fulfill(self):
        """Mark request as fulfilled (when borrow record is created)"""
        self.status = 'fulfilled'
        self.save()
    
    def clean(self):
        """Validate book request before creation"""
        super().clean()
        
        # Check total limit: borrowed + pending/ready requests (excluding this one if updating)
        if self.user and not self.pk:  # Only validate on creation
            from django.conf import settings
            
            current_borrows = BorrowRecord.objects.filter(
                user=self.user,
                status__in=['borrowed', 'overdue']
            ).count()
            
            pending_requests = BookRequest.objects.filter(
                user=self.user,
                status__in=['pending', 'ready']
            ).count()
            
            total_books = current_borrows + pending_requests
            
            max_limit = self.user.profile.max_books_allowed
            if total_books >= max_limit:
                raise ValidationError({
                    'user': f'Maximum limit of {max_limit} books reached (borrowed: {current_borrows}, pending/ready requests: {pending_requests}). Cannot create more requests.'
                })
        
        # Check for duplicate pending/ready request
        if self.user and self.book and not self.pk:
            existing_request = BookRequest.objects.filter(
                user=self.user,
                book=self.book,
                status__in=['pending', 'ready']
            ).exists()
            
            if existing_request:
                raise ValidationError({
                    'book': f'You already have a pending or ready request for "{self.book.title}".'
                })
        
        # Check for duplicate active borrow
        if self.user and self.book and not self.pk:
            existing_borrow = BorrowRecord.objects.filter(
                user=self.user,
                book=self.book,
                status__in=['borrowed', 'overdue']
            ).exists()
            
            if existing_borrow:
                raise ValidationError({
                    'book': f'You have already borrowed "{self.book.title}".'
                })


class BorrowRecord(models.Model):
    """Borrow record tracking for books"""
    
    STATUS_CHOICES = (
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    )
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='borrow_records')
    book = models.ForeignKey('books.Book', on_delete=models.CASCADE, related_name='borrow_records')
    book_request = models.ForeignKey(BookRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='borrow_record')
    borrow_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fine_paid = models.BooleanField(default=False)
    issued_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_books')
    returned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='returned_books')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-borrow_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['book']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate due date and check for overdue status"""
        # Validation before saving
        self.full_clean()
        
        if not self.due_date and not self.return_date:
            # Set default due date to 14 days from borrow date
            self.due_date = (timezone.now() + timedelta(days=14)).date()
        
        # Check if overdue
        if self.status == 'borrowed' and self.due_date < timezone.now().date():
            self.status = 'overdue'
            self._calculate_fine()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Enhanced validation for BorrowRecord"""
        super().clean()
        
        # Prevent borrowing unavailable books
        if self.book and not self.book.is_available() and not self.pk:
            raise ValidationError({
                'book': f'"{self.book.title}" is currently not available for borrowing.'
            })
        
        # Prevent duplicate active borrows
        if self.user and self.book and not self.pk:
            existing_borrow = BorrowRecord.objects.filter(
                user=self.user,
                book=self.book,
                status__in=['borrowed', 'overdue']
            ).exists()
            
            if existing_borrow:
                raise ValidationError({
                    'book': f'You have already borrowed "{self.book.title}".'
                })
        
        # Check total limit: borrowed + pending/ready requests
        if self.user and not self.pk:
            from django.conf import settings
            current_borrows = BorrowRecord.objects.filter(
                user=self.user,
                status__in=['borrowed', 'overdue']
            ).count()
            
            # Count pending and ready requests
            # If this borrow is from a book request, exclude that request from the count
            pending_requests_query = BookRequest.objects.filter(
                user=self.user,
                status__in=['pending', 'ready']
            )
            
            # Exclude the current book request if this borrow is being created from one
            if hasattr(self, 'book_request') and self.book_request:
                pending_requests_query = pending_requests_query.exclude(pk=self.book_request.pk)
            
            pending_requests = pending_requests_query.count()
            
            total_books = current_borrows + pending_requests
            
            max_limit = self.user.profile.max_books_allowed
            if total_books >= max_limit:
                raise ValidationError({
                    'user': f'Maximum limit of {max_limit} books reached (borrowed: {current_borrows}, pending/ready requests: {pending_requests}). Cannot issue more books.'
                })
        
        # Validate return date is not before borrow date
        if self.return_date and self.borrow_date:
            if self.return_date < self.borrow_date.date():
                raise ValidationError({
                    'return_date': 'Return date cannot be before borrow date.'
                })
        
        # Validate due date is not before borrow date
        if self.due_date and self.borrow_date:
            if self.due_date < self.borrow_date.date():
                raise ValidationError({
                    'due_date': 'Due date cannot be before borrow date.'
                })
    
    def _calculate_fine(self):
        """Calculate fine for overdue books using system settings"""
        if self.status == 'overdue' and not self.fine_paid:
            from apps.dashboard.models import SystemSettings
            settings = SystemSettings.get_settings()
            
            days_overdue = (timezone.now().date() - self.due_date).days
            if days_overdue > 0:
                self.fine_amount = days_overdue * settings.fine_per_day
    
    def return_book(self):
        """Process book return and notify waitlist"""
        from apps.dashboard.models import SystemSettings
        settings = SystemSettings.get_settings()
        
        return_date = timezone.now().date()
        
        # Calculate fine if overdue
        fine_amount = self.fine_amount
        if self.due_date < return_date:
            days_late = (return_date - self.due_date).days
            fine_amount = days_late * settings.fine_per_day
        
        # Update using queryset to bypass validation
        BorrowRecord.objects.filter(pk=self.pk).update(
            return_date=return_date,
            status='returned',
            fine_amount=fine_amount
        )
        
        # Refresh from database
        self.refresh_from_db()
        
        # Update book availability
        self.book.return_book()
        
        # Update user profile
        if self.user.profile.currently_borrowed > 0:
            self.user.profile.currently_borrowed -= 1
            self.user.profile.total_books_read += 1
            self.user.profile.update_reading_badge()
            self.user.profile.save()
        
        # Notify users in waitlist if book is now available
        self._notify_waitlist()
    
    def get_days_borrowed(self):
        """Get number of days book has been borrowed"""
        if self.return_date:
            return (self.return_date - self.borrow_date.date()).days
        return (timezone.now().date() - self.borrow_date.date()).days
    
    def get_days_remaining(self):
        """Get days remaining until due date"""
        days = (self.due_date - timezone.now().date()).days
        return max(0, days)
    
    def get_days_overdue(self):
        """Get days overdue"""
        if self.status != 'overdue':
            return 0
        return (timezone.now().date() - self.due_date).days
    
    def _notify_waitlist(self):
        """Notify users in waitlist when book becomes available"""
        # Check if book is now available
        if not self.book.is_available():
            return
        
        # Get pending requests for this book (oldest first)
        pending_requests = BookRequest.objects.filter(
            book=self.book,
            status='pending'
        ).select_related('user').order_by('request_date')[:3]  # Notify first 3 in queue
        
        # Get total count for queue position
        total_in_queue = pending_requests.count()
        
        # Send email notifications using the new notification system
        from apps.users.notifications import notify_book_available_waitlist
        
        for index, request in enumerate(pending_requests):
            if request.user.email:
                try:
                    position = index + 1
                    notify_book_available_waitlist(request, position, total_in_queue)
                except Exception as e:
                    # Log error but don't fail the return process
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send waitlist notification to {request.user.email}: {str(e)}")
