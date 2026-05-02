from django import forms
from .models import BorrowRecord
from datetime import timedelta
from django.utils import timezone


class BorrowBookForm(forms.Form):
    """Form for borrowing a book"""
    
    book_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class ReturnBookForm(forms.ModelForm):
    """Form for returning a book"""
    
    class Meta:
        model = BorrowRecord
        fields = []


class BorrowHistoryFilterForm(forms.Form):
    """Form for filtering borrow history"""
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(BorrowRecord.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    book_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by book title...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class OverdueManagementForm(forms.Form):
    """Form for managing overdue books"""
    
    borrow_record_id = forms.IntegerField(widget=forms.HiddenInput())
    fine_amount = forms.DecimalField(
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'step': '0.01'
        })
    )
    fine_paid = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
