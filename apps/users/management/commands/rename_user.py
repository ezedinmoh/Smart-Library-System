from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User


class Command(BaseCommand):
    help = 'Rename a user account (change username)'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='User ID to rename')
        parser.add_argument('new_username', type=str, help='New username')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rename without confirmation',
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        new_username = options['new_username']
        force = options['force']
        
        # Get the user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise CommandError(f'User with ID {user_id} does not exist')
        
        # Display current info
        self.stdout.write(self.style.WARNING('\n📋 Current User Information:'))
        self.stdout.write(f'   Username: {user.username}')
        self.stdout.write(f'   Email: {user.email}')
        self.stdout.write(f'   Role: {user.get_role_display()}')
        self.stdout.write(f'   ID: {user.id}')
        
        # Check if new username already exists (case-insensitive)
        if User.objects.filter(username__iexact=new_username).exists():
            raise CommandError(f'Username "{new_username}" is already taken (case-insensitive)')
        
        # Confirm
        if not force:
            self.stdout.write(self.style.WARNING(f'\n⚠️  You are about to rename:'))
            self.stdout.write(f'   From: {user.username}')
            self.stdout.write(f'   To:   {new_username}')
            
            confirm = input('\nAre you sure? Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('\n❌ Operation cancelled\n'))
                return
        
        # Rename
        old_username = user.username
        user.username = new_username
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully renamed user!'))
        self.stdout.write(f'   Old username: {old_username}')
        self.stdout.write(f'   New username: {new_username}')
        self.stdout.write(f'   User ID: {user.id}\n')
