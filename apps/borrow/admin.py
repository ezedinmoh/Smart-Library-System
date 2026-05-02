from django.contrib import admin
from .models import BorrowRecord


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    """Borrow Record Admin"""
    list_display = ('user', 'book', 'borrow_date', 'due_date', 'return_date', 'status', 'fine_amount')
    list_filter = ('status', 'borrow_date', 'due_date')
    search_fields = ('user__username', 'book__title', 'book__isbn')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'borrow_date'
    
    fieldsets = (
        ('Borrow Information', {
            'fields': ('user', 'book', 'borrow_date')
        }),
        ('Dates', {
            'fields': ('due_date', 'return_date')
        }),
        ('Status & Fine', {
            'fields': ('status', 'fine_amount', 'fine_paid')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
