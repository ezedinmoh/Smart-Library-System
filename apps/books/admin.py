from django.contrib import admin
from .models import Book, Category, BookReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category Admin"""
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Book Admin"""
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'times_borrowed', 'created_at')
    list_filter = ('category', 'language', 'created_at')
    search_fields = ('title', 'author', 'isbn')
    readonly_fields = ('times_borrowed', 'created_at', 'updated_at')
    fieldsets = (
        ('Book Information', {
            'fields': ('isbn', 'title', 'author', 'description', 'category')
        }),
        ('Availability', {
            'fields': ('total_copies', 'available_copies', 'times_borrowed')
        }),
        ('Details', {
            'fields': ('publisher', 'publication_date', 'pages', 'language', 'rating')
        }),
        ('Files', {
            'fields': ('cover_image', 'pdf_file')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    """Book Review Admin"""
    list_display = ('user', 'book', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
