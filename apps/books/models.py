from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import re
import logging
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

logger = logging.getLogger(__name__)


class Category(models.Model):
    """Book Category Model"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'
        indexes = [models.Index(fields=['name'])]
    
    def __str__(self):
        return self.name


class Book(models.Model):
    """Book Model with comprehensive details"""
    
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('other', 'Other'),
    )
    
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    total_copies = models.IntegerField(validators=[MinValueValidator(1)])
    available_copies = models.IntegerField(validators=[MinValueValidator(0)])
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_date = models.DateField(blank=True, null=True)
    pages = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    times_borrowed = models.IntegerField(default=0)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['available_copies']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def clean(self):
        """Enhanced validation for Book model"""
        super().clean()
        
        # Validate ISBN format (ISBN-10 or ISBN-13)
        if self.isbn:
            # Remove hyphens and spaces for validation
            isbn_clean = self.isbn.replace('-', '').replace(' ', '').upper()
            
            # Check if ISBN-10 (10 digits, last can be X)
            if len(isbn_clean) == 10:
                if not re.match(r'^\d{9}[\dX]$', isbn_clean):
                    raise ValidationError({
                        'isbn': 'Invalid ISBN-10 format. Must be 10 digits (last digit can be X).'
                    })
            # Check if ISBN-13 (13 digits)
            elif len(isbn_clean) == 13:
                if not re.match(r'^\d{13}$', isbn_clean):
                    raise ValidationError({
                        'isbn': 'Invalid ISBN-13 format. Must be 13 digits.'
                    })
            else:
                raise ValidationError({
                    'isbn': 'ISBN must be either 10 or 13 characters long (excluding hyphens).'
                })
            
            # Check for duplicate ISBN (excluding current instance)
            if self.pk:
                # Updating existing book
                duplicate = Book.objects.filter(isbn=self.isbn).exclude(pk=self.pk).exists()
            else:
                # Creating new book
                duplicate = Book.objects.filter(isbn=self.isbn).exists()
            
            if duplicate:
                raise ValidationError({
                    'isbn': f'A book with ISBN "{self.isbn}" already exists in the system.'
                })
        
        # Ensure available copies don't exceed total copies
        if self.available_copies > self.total_copies:
            raise ValidationError({
                'available_copies': 'Available copies cannot exceed total copies.'
            })
        
        # Validate publication date (not in future)
        if self.publication_date and self.publication_date > timezone.now().date():
            raise ValidationError({
                'publication_date': 'Publication date cannot be in the future.'
            })
        
        # Validate pages count
        if self.pages and self.pages <= 0:
            raise ValidationError({'pages': 'Number of pages must be positive.'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation and generate QR code"""
        self.full_clean()

        qr_generated = False
        if not self.qr_code:
            try:
                self.generate_qr_code()
                qr_generated = True
            except Exception:
                logger.exception('Failed to generate QR code for book %s', self.pk)

        # Persist qr_code when save() is called with update_fields (e.g. rating sync)
        if qr_generated:
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = list(set(update_fields) | {'qr_code'})

        super().save(*args, **kwargs)

    def generate_qr_code(self):
        """Generate QR code for the book"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr_data = f"ISBN: {self.isbn}\nTitle: {self.title}\nAuthor: {self.author}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        safe_isbn = re.sub(r'[^\w\-]', '_', self.isbn)
        filename = f'qr_{safe_isbn}.png'
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()
    
    def is_available(self):
        """Check if book is available for borrowing"""
        return self.available_copies > 0
    
    def borrow_book(self):
        """Decrease available copies when borrowed"""
        if self.available_copies > 0:
            self.available_copies -= 1
            self.times_borrowed += 1
            self.save()
            return True
        return False
    
    def return_book(self):
        """Increase available copies when returned"""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save()
            return True
        return False


class BookReview(models.Model):
    """Book reviews for recommendations"""
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='book_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['book', 'user']
        ordering = ['-created_at']
        indexes = [models.Index(fields=['book', 'user'])]
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.book.title}"
    
    def clean(self):
        """Validate that user has borrowed the book before reviewing (students only)"""
        super().clean()
        
        # Import here to avoid circular import
        from apps.borrow.models import BorrowRecord
        
        # Skip validation if user or book is not properly set
        try:
            user = self.user
            book = self.book
        except (AttributeError, ObjectDoesNotExist):
            # User or book not set yet, skip validation
            return
        
        # Only students can review
        if not (hasattr(user, 'is_student') and user.is_student):
            raise ValidationError({
                'user': 'Only students can write reviews.'
            })
        
        # Students must have borrowed and returned the book
        has_borrowed = BorrowRecord.objects.filter(
            user=user,
            book=book,
            status='returned'
        ).exists()
        
        if not has_borrowed:
            raise ValidationError({
                'book': 'You can only review books you have borrowed and returned.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
