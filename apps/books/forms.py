from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Book, Category, BookReview
import re


class BookForm(forms.ModelForm):
    """Form for creating and editing books"""
    
    class Meta:
        model = Book
        fields = ['isbn', 'title', 'author', 'description', 'category', 'total_copies', 'available_copies',
                  'publisher', 'publication_date', 'pages', 'language', 'cover_image', 'pdf_file']
        widgets = {
            'isbn': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'ISBN (10 or 13 digits)',
                'pattern': '[0-9X-]{10,17}',
                'title': 'Enter ISBN-10 or ISBN-13 (with or without hyphens)'
            }),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Book Title', 'required': True}),
            'author': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Author Name', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Book Description'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'required': True}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'required': True}),
            'publisher': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Publisher'}),
            'publication_date': forms.DateInput(attrs={
                'class': 'form-input', 
                'type': 'date',
                'max': timezone.now().date().isoformat()
            }),
            'pages': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Number of pages'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'cover_image': forms.FileInput(attrs={'class': 'file-input', 'accept': 'image/*'}),
            'pdf_file': forms.FileInput(attrs={'class': 'file-input', 'accept': 'application/pdf'}),
        }
    
    def clean_isbn(self):
        """Validate ISBN format and check for duplicates"""
        isbn = self.cleaned_data.get('isbn')
        
        if isbn:
            # Remove hyphens and spaces for validation
            isbn_clean = isbn.replace('-', '').replace(' ', '').upper()
            
            # Validate format
            if len(isbn_clean) == 10:
                if not re.match(r'^\d{9}[\dX]$', isbn_clean):
                    raise ValidationError('Invalid ISBN-10 format. Must be 10 digits (last digit can be X).')
            elif len(isbn_clean) == 13:
                if not re.match(r'^\d{13}$', isbn_clean):
                    raise ValidationError('Invalid ISBN-13 format. Must be 13 digits.')
            else:
                raise ValidationError('ISBN must be either 10 or 13 characters long (excluding hyphens).')
            
            # Check for duplicates
            if self.instance.pk:
                # Updating existing book
                duplicate = Book.objects.filter(isbn=isbn).exclude(pk=self.instance.pk).exists()
            else:
                # Creating new book
                duplicate = Book.objects.filter(isbn=isbn).exists()
            
            if duplicate:
                raise ValidationError(f'A book with ISBN "{isbn}" already exists in the system.')
        
        return isbn
    
    def clean_title(self):
        """Validate book title"""
        title = self.cleaned_data.get('title')
        
        if title:
            # Remove extra whitespace
            title = ' '.join(title.split())
            
            # Check minimum length
            if len(title) < 2:
                raise ValidationError('Book title must be at least 2 characters long.')
            
            # Allow letters, numbers, spaces, and common punctuation (.,!?:;'-&)
            if not re.match(r'^[a-zA-Z0-9\s.,!?:;\'\-&()]+$', title):
                raise ValidationError('Book title contains invalid characters. Only letters, numbers, spaces, and common punctuation are allowed.')
        
        return title
    
    def clean_author(self):
        """Validate author name"""
        author = self.cleaned_data.get('author')
        
        if author:
            # Remove extra whitespace
            author = ' '.join(author.split())
            
            # Check minimum length
            if len(author) < 2:
                raise ValidationError('Author name must be at least 2 characters long.')
            
            # Allow letters, spaces, dots, hyphens, and apostrophes
            if not re.match(r'^[a-zA-Z\s.\'\-]+$', author):
                raise ValidationError('Author name can only contain letters, spaces, dots, hyphens, and apostrophes.')
        
        return author
    
    def clean_publisher(self):
        """Validate publisher name"""
        publisher = self.cleaned_data.get('publisher')
        
        if publisher:
            # Remove extra whitespace
            publisher = ' '.join(publisher.split())
            
            # Allow letters, numbers, spaces, and common punctuation
            if not re.match(r'^[a-zA-Z0-9\s.,&\'\-()]+$', publisher):
                raise ValidationError('Publisher name contains invalid characters.')
        
        return publisher
        
    def clean_publication_date(self):
        """Validate publication date is not in the future"""
        pub_date = self.cleaned_data.get('publication_date')
        
        if pub_date and pub_date > timezone.now().date():
            raise ValidationError('Publication date cannot be in the future.')
        
        return pub_date
    
    def clean(self):
        """Validate that available copies don't exceed total copies"""
        cleaned_data = super().clean()
        total_copies = cleaned_data.get('total_copies')
        available_copies = cleaned_data.get('available_copies')
        
        if total_copies and available_copies:
            if available_copies > total_copies:
                raise ValidationError({
                    'available_copies': 'Available copies cannot exceed total copies.'
                })
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Category Description'}),
        }
    
    def clean_name(self):
        """Validate category name"""
        name = self.cleaned_data.get('name')
        
        if name:
            # Remove extra whitespace
            name = ' '.join(name.split())
            
            # Check minimum length
            if len(name) < 2:
                raise ValidationError('Category name must be at least 2 characters long.')
            
            # Allow letters, numbers, spaces, and basic punctuation
            if not re.match(r'^[a-zA-Z0-9\s&\'\-]+$', name):
                raise ValidationError('Category name can only contain letters, numbers, spaces, ampersands, hyphens, and apostrophes.')
        
        return name


class BookSearchForm(forms.Form):
    """Form for searching and filtering books"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, author, or ISBN...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    language = forms.ChoiceField(
        choices=[('', 'All Languages')] + list(Book.LANGUAGE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    availability = forms.ChoiceField(
        choices=[
            ('', 'All Books'),
            ('available', 'Available Only'),
            ('unavailable', 'Unavailable Only'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BookReviewForm(forms.ModelForm):
    """Form for writing book reviews"""
    
    class Meta:
        model = BookReview
        fields = ['rating', 'review_text']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'review_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write your review...'}),
        }
