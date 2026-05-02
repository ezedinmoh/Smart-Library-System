from django.core.management.base import BaseCommand
from apps.users.models import User
from allauth.account.models import EmailAddress, EmailConfirmation


class Command(BaseCommand):
    help = 'Clean up unverified users and their email confirmations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all inactive users (use with caution)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Delete specific user by username',
        )

    def handle(self, *args, **options):
        if options['username']:
            # Delete specific user
            try:
                user = User.objects.get(username=options['username'])
                username = user.username
                user.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted user: {username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User not found: {options["username"]}')
                )
        elif options['all']:
            # Delete all inactive users
            inactive_users = User.objects.filter(is_active=False)
            count = inactive_users.count()
            
            if count == 0:
                self.stdout.write(self.style.WARNING('No inactive users found.'))
                return
            
            # Show users to be deleted
            self.stdout.write(f'\nFound {count} inactive user(s):')
            for user in inactive_users:
                self.stdout.write(f'  - {user.username} ({user.email})')
            
            confirm = input('\nAre you sure you want to delete these users? (yes/no): ')
            if confirm.lower() == 'yes':
                inactive_users.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {count} inactive user(s)')
                )
            else:
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
        else:
            # Show statistics
            total_users = User.objects.count()
            inactive_users = User.objects.filter(is_active=False).count()
            pending_confirmations = EmailConfirmation.objects.count()
            
            self.stdout.write('\n=== User Statistics ===')
            self.stdout.write(f'Total users: {total_users}')
            self.stdout.write(f'Inactive users: {inactive_users}')
            self.stdout.write(f'Pending email confirmations: {pending_confirmations}')
            
            if inactive_users > 0:
                self.stdout.write('\nInactive users:')
                for user in User.objects.filter(is_active=False):
                    self.stdout.write(f'  - {user.username} ({user.email})')
            
            if pending_confirmations > 0:
                self.stdout.write('\nPending confirmations:')
                for conf in EmailConfirmation.objects.all():
                    self.stdout.write(
                        f'  - {conf.email_address.email} (key: {conf.key[:20]}...)'
                    )
            
            self.stdout.write('\nUsage:')
            self.stdout.write('  python manage.py cleanup_unverified_users --all')
            self.stdout.write('  python manage.py cleanup_unverified_users --username <username>')
