from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import Lower
from apps.users.models import User


class Command(BaseCommand):
    help = 'Check for duplicate usernames (case-insensitive) and display them'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🔍 Checking for duplicate usernames (case-insensitive)...\n'))
        
        # Find usernames that have duplicates when compared case-insensitively
        duplicates = (
            User.objects
            .annotate(lower_username=Lower('username'))
            .values('lower_username')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('✅ No duplicate usernames found!\n'))
            return
        
        self.stdout.write(self.style.ERROR(f'❌ Found {len(duplicates)} duplicate username(s):\n'))
        
        for dup in duplicates:
            username_lower = dup['lower_username']
            count = dup['count']
            
            # Get all users with this username (case-insensitive)
            users = User.objects.filter(username__iexact=username_lower).order_by('created_at')
            
            self.stdout.write(self.style.WARNING(f'\n📋 Username: "{username_lower}" ({count} accounts)'))
            self.stdout.write('-' * 80)
            
            for i, user in enumerate(users, 1):
                self.stdout.write(f'\n  {i}. Username: {user.username}')
                self.stdout.write(f'     Email: {user.email}')
                self.stdout.write(f'     Role: {user.get_role_display()}')
                self.stdout.write(f'     ID: {user.id}')
                self.stdout.write(f'     Created: {user.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
                self.stdout.write(f'     Last Login: {user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never"}')
                self.stdout.write(f'     Active: {"Yes" if user.is_active else "No"}')
        
        self.stdout.write(self.style.WARNING('\n\n💡 Recommendations:'))
        self.stdout.write('   1. Review the accounts above and decide which ones to keep')
        self.stdout.write('   2. Consider merging data or deleting duplicate accounts')
        self.stdout.write('   3. Use the Django admin or shell to delete unwanted accounts')
        self.stdout.write('   4. Future registrations will prevent case-insensitive duplicates\n')
        
        self.stdout.write(self.style.WARNING('\n📝 To delete a user account, use:'))
        self.stdout.write('   python manage.py shell')
        self.stdout.write('   >>> from apps.users.models import User')
        self.stdout.write('   >>> User.objects.get(id=<USER_ID>).delete()\n')
