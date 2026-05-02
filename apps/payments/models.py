from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from apps.borrow.models import BorrowRecord
import uuid


class Payment(models.Model):
    """Base payment model for all payment transactions"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('stripe', 'Stripe'),
        ('chapa', 'Chapa'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    borrow_record = models.ForeignKey(BorrowRecord, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)  # USD, ETB
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_gateway_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['payment_method', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} - {self.status}"
    
    def mark_as_completed(self):
        """Mark payment as completed and update borrow record"""
        self.status = 'completed'
        self.save()
        
        # Mark fine as paid in borrow record
        self.borrow_record.fine_paid = True
        self.borrow_record.save()
    
    def mark_as_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()


class StripePayment(models.Model):
    """Stripe-specific payment details"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='stripe_details')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Stripe: {self.stripe_payment_intent_id}"


class ChapaPayment(models.Model):
    """Chapa-specific payment details"""
    
    CHAPA_METHOD_CHOICES = (
        ('telebirr', 'Telebirr'),
        ('cbebirr', 'CBE Birr'),
        ('ebirr', 'eBirr'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='chapa_details')
    chapa_tx_ref = models.CharField(max_length=255, unique=True)
    chapa_checkout_url = models.URLField(blank=True)
    payment_method_type = models.CharField(max_length=20, choices=CHAPA_METHOD_CHOICES, default='telebirr')
    
    def __str__(self):
        return f"Chapa: {self.chapa_tx_ref}"
