"""
Custom authentication backend for case-insensitive username login
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class CaseInsensitiveUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows case-insensitive username login.
    Users can login with 'ezedin', 'Ezedin', 'EZEDIN', etc.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        try:
            # Case-insensitive username lookup
            user = User.objects.get(username__iexact=username)
            
            # Check password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
