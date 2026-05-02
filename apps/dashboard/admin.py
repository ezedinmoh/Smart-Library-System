from django.contrib import admin
from apps.dashboard.models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin interface for system settings"""
    
    fieldsets = (
        ('Borrowing Settings', {
            'fields': ('default_borrow_limit', 'max_borrow_days'),
            'description': 'Configure default borrowing limits and duration'
        }),
        ('Fine Settings', {
            'fields': ('fine_per_day',),
            'description': 'Configure fine amount for overdue books'
        }),
        ('Payment Settings', {
            'fields': ('etb_to_usd_rate',),
            'description': 'Configure currency exchange rate for international payments'
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('updated_at', 'updated_by')
    
    def has_add_permission(self, request):
        """Prevent adding more than one settings instance"""
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Track who updated the settings"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

