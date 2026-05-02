# Management command to create project users
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, UserProfile
from allauth.account.models import EmailAddress


class Command(BaseCommand):
    help = 'Create 5 admin users and 5 librarian users for the project team'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Define admin users (case-insensitive usernames)
        admins = [
            {'username': 'Ezedin', 'password': 'Admin@123', 'email': 'ezedin@library.com', 'first_name': 'Ezedin', 'last_name': 'Admin'},
            {'username': 'Wubet', 'password': 'Admin@123', 'email': 'wubet@library.com', 'first_name': 'Wubet', 'last_name': 'Admin'},
            {'username': 'Mahlete', 'password': 'Admin@123', 'email': 'mahlete@library.com', 'first_name': 'Mahlete', 'last_name': 'Admin'},
            {'username': 'Mubarek', 'password': 'Admin@123', 'email': 'mubarek@library.com', 'first_name': 'Mubarek', 'last_name': 'Admin'},
            {'username': 'Hana', 'password': 'Admin@123', 'email': 'hana@library.com', 'first_name': 'Hana', 'last_name': 'Admin'},
        ]
        
        # Define librarian users (username + '1')
        librarians = [
            {'username': 'Ezedin1', 'password': 'Librarian@123', 'email': 'ezedin1@library.com', 'first_name': 'Ezedin', 'last_name': 'Librarian'},
            {'username': 'Wubet1', 'password': 'Librarian@123', 'email': 'wubet1@library.com', 'first_name': 'Wubet', 'last_name': 'Librarian'},
            {'username': 'Mahlete1', 'password': 'Librarian@123', 'email': 'mahlete1@library.com', 'first_name': 'Mahlete', 'last_name': 'Librarian'},
            {'username': 'Mubarek1', 'password': 'Librarian@123', 'email': 'mubarek1@library.com', 'first_name': 'Mubarek', 'last_name': 'Librarian'},
            {'username': 'Hana1', 'password': 'Librarian@123', 'email': 'hana1@library.com', 'first_name': 'Hana', 'last_name': 'Librarian'},
        ]
        
        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('PROJECT USERS CREATION'))
        self.stdout.write('='*100 + '\n')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
            
            self.stdout.write(self.style.SUCCESS('Would create 5 ADMIN users:'))
            for admin in admins:
                self.stdout.write(f'  - Username: {admin["username"]}, Email: {admin["email"]}, Password: {admin["password"]}')
            
            self.stdout.write(self.style.SUCCESS('\nWould create 5 LIBRARIAN users:'))
            for librarian in librarians:
                self.stdout.write(f'  - Username: {librarian["username"]}, Email: {librarian["email"]}, Password: {librarian["password"]}')
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write('Run without --dry-run to create these users')
            self.stdout.write('='*100 + '\n')
        else:
            created_admins = 0
            created_librarians = 0
            skipped = 0
            
            with transaction.atomic():
                # Create admin users
                self.stdout.write(self.style.SUCCESS('\nCreating ADMIN users:'))
                for admin_data in admins:
                    # Check if user already exists (case-insensitive)
                    if User.objects.filter(username__iexact=admin_data['username']).exists():
                        self.stdout.write(self.style.WARNING(f'  ⚠ Skipped: {admin_data["username"]} (already exists)'))
                        skipped += 1
                        continue
                    
                    # Create user
                    user = User.objects.create_user(
                        username=admin_data['username'],
                        email=admin_data['email'],
                        password=admin_data['password'],
                        first_name=admin_data['first_name'],
                        last_name=admin_data['last_name'],
                        role='admin',
                        is_active=True,  # Admins are active by default
                        is_staff=True,   # Admins can access Django admin
                        is_superuser=True  # Admins have all permissions
                    )
                    
                    # Create user profile
                    UserProfile.objects.get_or_create(user=user)
                    
                    # Mark email as verified
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=user.email,
                        defaults={'primary': True, 'verified': True}
                    )
                    
                    created_admins += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {user.username} ({user.email}) - Password: {admin_data["password"]}'))
                
                # Create librarian users
                self.stdout.write(self.style.SUCCESS('\nCreating LIBRARIAN users:'))
                for librarian_data in librarians:
                    # Check if user already exists (case-insensitive)
                    if User.objects.filter(username__iexact=librarian_data['username']).exists():
                        self.stdout.write(self.style.WARNING(f'  ⚠ Skipped: {librarian_data["username"]} (already exists)'))
                        skipped += 1
                        continue
                    
                    # Create user
                    user = User.objects.create_user(
                        username=librarian_data['username'],
                        email=librarian_data['email'],
                        password=librarian_data['password'],
                        first_name=librarian_data['first_name'],
                        last_name=librarian_data['last_name'],
                        role='librarian',
                        is_active=True,  # Librarians are active by default
                        is_staff=False   # Librarians don't need Django admin access
                    )
                    
                    # Create user profile
                    UserProfile.objects.get_or_create(user=user)
                    
                    # Mark email as verified
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=user.email,
                        defaults={'primary': True, 'verified': True}
                    )
                    
                    created_librarians += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {user.username} ({user.email}) - Password: {librarian_data["password"]}'))
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write(self.style.SUCCESS(f'COMPLETE: Created {created_admins} admins, {created_librarians} librarians'))
            if skipped > 0:
                self.stdout.write(self.style.WARNING(f'Skipped {skipped} existing users'))
            self.stdout.write('='*100 + '\n')
            
            # Display login instructions
            self.stdout.write(self.style.SUCCESS('\n📋 LOGIN CREDENTIALS:\n'))
            self.stdout.write(self.style.SUCCESS('ADMINS:'))
            for admin in admins:
                self.stdout.write(f'  Username: {admin["username"]} | Password: {admin["password"]}')
            
            self.stdout.write(self.style.SUCCESS('\nLIBRARIANS:'))
            for librarian in librarians:
                self.stdout.write(f'  Username: {librarian["username"]} | Password: {librarian["password"]}')
            
            self.stdout.write('\n' + '='*100)
            self.stdout.write(self.style.SUCCESS('✅ All users can now login and change their passwords in their profile page'))
            self.stdout.write('='*100 + '\n')
