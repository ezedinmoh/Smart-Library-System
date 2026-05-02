from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class SystemSettings(models.Model):
    """System-wide settings for the library"""
    
    # Singleton pattern - only one instance should exist
    default_borrow_limit = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Default maximum books a user can borrow (1-20)"
    )
    
    fine_per_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        validators=[MinValueValidator(0)],
        help_text="Fine amount per day for overdue books (ETB)"
    )
    
    etb_to_usd_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0.0180,
        validators=[MinValueValidator(0)],
        help_text="Exchange rate: 1 ETB = X USD (e.g., 0.0180)"
    )
    
    max_borrow_days = models.IntegerField(
        default=14,
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Maximum days a book can be borrowed (1-90)"
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_settings_updates'
    )
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return f"System Settings (Borrow Limit: {self.default_borrow_limit})"
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of settings"""
        pass
