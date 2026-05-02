from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that connects social accounts to existing users
    when the email already exists, instead of raising an error.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Called after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        If the email already exists, connect the social account to that user.
        """
        # If the social account already exists, nothing to do
        if sociallogin.is_existing:
            return

        # Get email from social account
        if not sociallogin.email_addresses:
            return

        # Try to find an existing user with this email
        email = sociallogin.email_addresses[0].email.lower()

        try:
            # Check if email address exists in allauth EmailAddress table
            existing = EmailAddress.objects.get(email__iexact=email)
            # Connect this social account to the existing user
            sociallogin.connect(request, existing.user)
        except EmailAddress.DoesNotExist:
            # Check in the User model directly
            from apps.users.models import User
            try:
                user = User.objects.get(email__iexact=email)
                # Create EmailAddress record and connect
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        """
        Save a newly signed-up social login.
        Assign default role of student and activate immediately
        (social accounts are pre-verified by the OAuth provider).
        """
        user = super().save_user(request, sociallogin, form)
        # Assign default role if not set
        if not user.role:
            user.role = 'student'
        # Social accounts are verified by the OAuth provider — activate immediately
        user.is_active = True
        user.save()
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """Always allow auto signup for social accounts."""
        return True

    def is_open_for_signup(self, request, sociallogin):
        """Always open for social signup."""
        return True
    
    def get_login_redirect_url(self, request):
        """
        Redirect to role-specific dashboard after social login.
        """
        user = request.user
        
        if user.is_authenticated:
            if hasattr(user, 'is_admin') and user.is_admin:
                return '/dashboard/admin/'
            elif hasattr(user, 'is_librarian') and user.is_librarian:
                return '/dashboard/librarian/'
            elif hasattr(user, 'is_student') and user.is_student:
                return '/dashboard/student/'
        
        # Fallback to default
        return super().get_login_redirect_url(request)