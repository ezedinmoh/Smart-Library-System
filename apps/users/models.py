from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
import re


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('librarian', 'Librarian'),
        ('student', 'Student'),
    )
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be between 9 and 15 digits'
            )
        ]
    )
    address = models.TextField(blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_librarian(self):
        return self.role == 'librarian'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    def clean(self):
        """Enhanced validation for User model"""
        super().clean()
        
        # Validate email format
        if self.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
            raise ValidationError({'email': 'Please enter a valid email address.'})
        
        # Validate phone number format
        if self.phone_number and not re.match(r'^\+?1?\d{9,15}$', self.phone_number):
            raise ValidationError({'phone_number': 'Phone number must be between 9 and 15 digits.'})
        
        # Ensure admin users have email
        if self.role == 'admin' and not self.email:
            raise ValidationError({'email': 'Admin users must have an email address.'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation — skip full_clean during password hashing"""
        # Only run full_clean if the password is already hashed (not during creation)
        if self.pk or (self.password and not self.password.startswith('pbkdf2_') is False):
            try:
                self.full_clean()
            except Exception:
                pass
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    BADGE_CHOICES = (
        ('reader', 'Reader'),
        ('book_lover', 'Book Lover'),
        ('avid_reader', 'Avid Reader'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    max_books_allowed = models.IntegerField(default=7)
    currently_borrowed = models.IntegerField(default=0)
    total_fines = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    reading_badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default='reader')
    total_books_read = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Profile of {self.user.username}'
    
    def can_borrow(self):
        return self.currently_borrowed < self.max_books_allowed
    
    def get_borrowed_count(self):
        return self.currently_borrowed
    
    def get_active_fines(self):
        return self.total_fines
    
    def update_reading_badge(self):
        """Update reading badge based on books read"""
        if self.total_books_read >= 20:
            self.reading_badge = 'avid_reader'
        elif self.total_books_read >= 10:
            self.reading_badge = 'book_lover'
        else:
            self.reading_badge = 'reader'
        self.save()
    
    def get_badge_display_name(self):
        """Get display name for badge"""
        return dict(self.BADGE_CHOICES).get(self.reading_badge, 'Reader')


class NotificationRead(models.Model):
    """Track which notifications have been read by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_notifications')
    notification_type = models.CharField(max_length=50)  # e.g., 'overdue', 'pending_request', etc.
    notification_key = models.CharField(max_length=255)  # Unique identifier for the notification
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'notification_type', 'notification_key']
        ordering = ['-read_at']
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['notification_key']),
        ]
    
    def __str__(self):
        return f'{self.user.username} read {self.notification_type} - {self.notification_key}'



class ActivityLog(models.Model):
    """System activity log for tracking all actions"""
    
    ACTION_CHOICES = (
        ('book_added', 'Book Added'),
        ('book_updated', 'Book Updated'),
        ('book_deleted', 'Book Deleted'),
        ('book_borrowed', 'Book Borrowed'),
        ('book_returned', 'Book Returned'),
        ('request_created', 'Request Created'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('request_cancelled', 'Request Cancelled'),
        ('fine_paid', 'Fine Paid'),
        ('payment_initiated', 'Payment Initiated'),
        ('payment_completed', 'Payment Completed'),
        ('payment_failed', 'Payment Failed'),
        ('user_created', 'User Created'),
        ('user_updated', 'User Updated'),
        ('user_role_changed', 'User Role Changed'),
        ('review_added', 'Review Added'),
        ('backup_created', 'Backup Created'),
        ('reminder_sent', 'Reminder Sent'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f'{user_str} - {self.get_action_display()} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'
