from django.core.management.base import BaseCommand
from apps.users.models import User
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = 'Activate all users and mark their emails as verified'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all inactive users
        inactive_users = User.objects.filter(is_active=False)
        inactive_count = inactive_users.count()
        
        # Get all users without verified email addresses
        users_without_verified_email = []
        for user in User.objects.all():
            email_address = EmailAddress.objects.filter(user=user, email=user.email).first()
            if not email_address or not email_address.verified:
                users_without_verified_email.append(user)
        
        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('USER VERIFICATION REPORT'))
        self.stdout.write('='*100 + '\n')
        
        self.stdout.write(f'Inactive users: {inactive_count}')
        self.stdout.write(f'Users without verified email: {len(users_without_verified_email)}')
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
            
            if inactive_count > 0:
                self.stdout.write('Would activate these users:')
                for user in inactive_users:
                    self.stdout.write(f'  - {user.username} ({user.email})')
            
            if users_without_verified_email:
                self.stdout.write('\nWould verify emails for these users:')
                for user in users_without_verified_email:
                    self.stdout.write(f'  - {user.username} ({user.email})')
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write('Run without --dry-run to apply changes')
            self.stdout.write('='*100 + '\n')
        else:
            # Activate all inactive users
            if inactive_count > 0:
                self.stdout.write(f'\nActivating {inactive_count} inactive user(s)...')
                for user in inactive_users:
                    user.is_active = True
                    user.save()
                    self.stdout.write(f'  ✓ Activated: {user.username}')
            
            # Create/update EmailAddress records for all users
            verified_count = 0
            for user in users_without_verified_email:
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={'primary': True, 'verified': True}
                )
                
                if not created and not email_address.verified:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()
                
                verified_count += 1
                self.stdout.write(f'  ✓ Verified: {user.username} ({user.email})')
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write(self.style.SUCCESS(f'COMPLETE: Activated {inactive_count} users, Verified {verified_count} emails'))
            self.stdout.write('='*100 + '\n')
