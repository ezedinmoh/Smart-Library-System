from django.core.management.base import BaseCommand
from apps.users.models import User, UserProfile


class Command(BaseCommand):
    help = 'Ensure all users have profiles'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(user=user)
                users_without_profile.append(user.username)
                self.stdout.write(self.style.SUCCESS(f'Created profile for {user.username}'))
        
        if users_without_profile:
            self.stdout.write(self.style.SUCCESS(f'\nCreated profiles for {len(users_without_profile)} users'))
        else:
            self.stdout.write(self.style.SUCCESS('All users already have profiles'))
