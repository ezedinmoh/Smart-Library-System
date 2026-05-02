from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User, UserProfile
import re


class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with role selection"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+251912345678 or 0912345678',
            'pattern': '[+]?[0-9]{10,15}'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    # Role removed from public registration - all new users are students
    # Only admins can create admin/librarian users
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Your first name'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Your last name'
        })
        self.fields['address'].widget.attrs.update({
            'placeholder': 'Your address (optional)'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    
    def save(self, commit=True):
        """Override save to force role to student for public registration"""
        user = super().save(commit=False)
        user.role = 'student'  # Force all public registrations to student role
        if commit:
            user.save()
        return user
    
    def _post_clean(self):
        """Override to skip password validation against user attributes"""
        super()._post_clean()
        # Get the password from cleaned_data
        password = self.cleaned_data.get('password2')
        if password:
            # Only validate password with the validators from settings (which we've already filtered)
            # Skip the similarity check by not passing user data
            try:
                from django.contrib.auth.password_validation import validate_password
                # Pass None as user to skip user attribute similarity validation
                validate_password(password, user=None)
            except ValidationError as error:
                self.add_error('password2', error)
    
    def clean_email(self):
        """Validate email format and check for duplicates"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("Email is required.")
        
        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        
        # Strict email validation - only letters, numbers, dots, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$', email):
            raise ValidationError("Please enter a valid email address (only letters, numbers, dots, hyphens, and underscores allowed).")
        
        return email.lower()
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        
        if phone:
            # Remove spaces and hyphens
            phone_clean = phone.replace(' ', '').replace('-', '')
            
            # Check if it's a valid phone number (10-15 digits, optional + prefix)
            if not re.match(r'^[+]?[0-9]{10,15}$', phone_clean):
                raise ValidationError("Please enter a valid phone number (10-15 digits, optional + prefix).")
            
            return phone_clean
        
        return phone
    
    def clean_username(self):
        """Validate username format and case-insensitive uniqueness"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError("Username is required.")
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        
        # Minimum length
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        
        # Check for case-insensitive duplicate
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(f"Username '{username}' is already taken (usernames are case-insensitive).")
        
        return username
    
    def clean_first_name(self):
        """Validate first name - only letters and spaces"""
        first_name = self.cleaned_data.get('first_name')
        
        if first_name and not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError("First name can only contain letters and spaces.")
        
        return first_name
    
    def clean_last_name(self):
        """Validate last name - only letters and spaces"""
        last_name = self.cleaned_data.get('last_name')
        
        if last_name and not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError("Last name can only contain letters and spaces.")
        
        return last_name


class UserEditForm(forms.ModelForm):
    """Form for editing user profile"""
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'address']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[a-zA-Z0-9_]+',
                'minlength': '3'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[a-zA-Z\s]+'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[a-zA-Z\s]+'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True,
                'pattern': r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+251912345678 or 0912345678',
                'pattern': '[+]?[0-9]{10,15}'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_email(self):
        """Validate email format and check for duplicates"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("Email is required.")
        
        # Strict email validation - only letters, numbers, dots, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$', email):
            raise ValidationError("Please enter a valid email address (only letters, numbers, dots, hyphens, and underscores allowed).")
        
        # Check for duplicate email (exclude current user)
        if self.instance.pk:
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError("This email is already registered.")
        else:
            if User.objects.filter(email=email).exists():
                raise ValidationError("This email is already registered.")
        
        return email.lower()
    
    def clean_username(self):
        """Validate username format and case-insensitive uniqueness"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError("Username is required.")
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        
        # Minimum length
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        
        # Check for case-insensitive duplicate (exclude current user)
        if self.instance.pk:
            if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f"Username '{username}' is already taken (usernames are case-insensitive).")
        else:
            if User.objects.filter(username__iexact=username).exists():
                raise ValidationError(f"Username '{username}' is already taken (usernames are case-insensitive).")
        
        return username
    
    def clean_first_name(self):
        """Validate first name - only letters and spaces"""
        first_name = self.cleaned_data.get('first_name')
        
        if first_name and not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError("First name can only contain letters and spaces.")
        
        return first_name
    
    def clean_last_name(self):
        """Validate last name - only letters and spaces"""
        last_name = self.cleaned_data.get('last_name')
        
        if last_name and not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError("Last name can only contain letters and spaces.")
        
        return last_name

    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        
        if phone:
            # Remove spaces and hyphens
            phone_clean = phone.replace(' ', '').replace('-', '')
            
            # Check if it's a valid phone number (10-15 digits, optional + prefix)
            if not re.match(r'^[+]?[0-9]{10,15}$', phone_clean):
                raise ValidationError("Please enter a valid phone number (10-15 digits, optional + prefix).")
            
            return phone_clean
        
        return phone


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile picture"""
    
    class Meta:
        model = UserProfile
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }


class UserSearchForm(forms.Form):
    """Form for searching users"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username or email...'
        })
    )
    role = forms.ChoiceField(
        choices=[('', 'All Roles')] + list(User.ROLE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth import get_user_model

class CustomPasswordResetForm(DjangoPasswordResetForm):
    """
    Custom password reset form that allows inactive users to reset their password.
    This is useful for users who haven't verified their email yet.
    """
    
    def get_users(self, email):
        """
        Override to include inactive users in password reset.
        Original Django form only allows active users.
        """
        UserModel = get_user_model()
        email_field_name = UserModel.get_email_field_name()
        
        # Get ALL users with this email (active AND inactive)
        all_users = UserModel._default_manager.filter(
            **{
                "%s__iexact" % email_field_name: email,
            }
        )
        
        # Return users who have usable passwords
        def _unicode_ci_compare(s1, s2):
            """Case-insensitive comparison"""
            return s1.lower() == s2.lower()
        
        return (
            u for u in all_users
            if u.has_usable_password()
            and _unicode_ci_compare(email, getattr(u, email_field_name))
        )


class AdminUserCreationForm(UserCreationForm):
    """Form for admins to create users with role selection (admin/librarian/student)"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'user.email@example.com'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+251912345678 or 0912345678',
            'pattern': '[+]?[0-9]{10,15}'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address (optional)'}),
        required=False
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial='student',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the role for this user'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        """Validate email format and check for duplicates"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError("Email is required.")
        
        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        
        # Strict email validation - only letters, numbers, dots, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$', email):
            raise ValidationError("Please enter a valid email address (only letters, numbers, dots, hyphens, and underscores allowed).")
        
        return email.lower()
    
    def clean_phone_number(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone_number')
        
        if phone:
            # Remove spaces and hyphens
            phone_clean = phone.replace(' ', '').replace('-', '')
            
            # Check if it's a valid phone number (10-15 digits, optional + prefix)
            if not re.match(r'^[+]?[0-9]{10,15}$', phone_clean):
                raise ValidationError("Please enter a valid phone number (10-15 digits, optional + prefix).")
            
            return phone_clean
        
        return phone
    
    def clean_username(self):
        """Validate username format and case-insensitive uniqueness"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError("Username is required.")
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        
        # Minimum length
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        
        # Check for case-insensitive duplicate
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(f"Username '{username}' is already taken (usernames are case-insensitive).")
        
        return username
    
    def clean_first_name(self):
        """Validate first name - only letters and spaces"""
        first_name = self.cleaned_data.get('first_name')
        
        if first_name and not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError("First name can only contain letters and spaces.")
        
        return first_name
    
    def clean_last_name(self):
        """Validate last name - only letters and spaces"""
        last_name = self.cleaned_data.get('last_name')
        
        if last_name and not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError("Last name can only contain letters and spaces.")
        
        return last_name
