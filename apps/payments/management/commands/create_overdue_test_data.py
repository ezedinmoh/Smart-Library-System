"""
Management command to create overdue borrow records with fines for testing payment system
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.books.models import Book
from apps.borrow.models import BorrowRecord
from apps.dashboard.models import SystemSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 9 overdue borrow records with fines for user "test" to test payment system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating overdue test data for payment testing...'))
        
        try:
            # Get the test user
            test_user = User.objects.get(username='test')
            self.stdout.write(self.style.SUCCESS(f'✓ Found user: {test_user.username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ User "test" not found. Please create the user first.'))
            return
        
        # Temporarily increase max books allowed for test user
        from apps.users.models import UserProfile
        profile = test_user.profile
        original_max_books = profile.max_books_allowed
        profile.max_books_allowed = 15  # Temporarily increase to 15
        profile.save()
        self.stdout.write(f'  Temporarily increased max books from {original_max_books} to 15')
        
        # Return all existing borrowed/overdue books for test user to free up space
        existing_records = BorrowRecord.objects.filter(
            user=test_user,
            status__in=['borrowed', 'overdue']
        )
        
        if existing_records.exists():
            self.stdout.write(f'  Returning {existing_records.count()} existing books...')
            for record in existing_records:
                # Return the book
                BorrowRecord.objects.filter(id=record.id).update(
                    status='returned',
                    return_date=timezone.now().date()
                )
                # Increase available copies
                Book.objects.filter(id=record.book.id).update(
                    available_copies=record.book.available_copies + 1
                )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Returned {existing_records.count()} books'))
        
        # Get system settings for fine calculation
        settings = SystemSettings.get_settings()
        fine_per_day = settings.fine_per_day
        self.stdout.write(f'  Fine per day: ETB {fine_per_day}')
        
        # Get books with available copies
        available_books = Book.objects.filter(available_copies__gt=0)[:9]
        
        if available_books.count() < 9:
            self.stdout.write(self.style.ERROR(f'✗ Not enough available books. Found {available_books.count()}, need 9.'))
            return
        
        self.stdout.write(f'✓ Found {available_books.count()} available books')
        
        # Create 9 overdue records with different overdue periods
        overdue_days_list = [1, 2, 3, 4, 5, 7, 10, 14, 20]  # Different overdue periods
        created_count = 0
        
        for i, book in enumerate(available_books):
            overdue_days = overdue_days_list[i]
            
            # Calculate dates
            borrow_date = timezone.now().date() - timedelta(days=14 + overdue_days)  # Borrowed 14 days ago + overdue days
            due_date = borrow_date + timedelta(days=14)  # Due date was 14 days after borrow
            
            # Calculate fine
            fine_amount = Decimal(str(overdue_days)) * fine_per_day
            
            # Create borrow record using update to bypass validation
            record = BorrowRecord.objects.create(
                user=test_user,
                book=book,
                borrow_date=borrow_date,
                due_date=due_date,
                status='borrowed',  # Will update to overdue after
                fine_amount=Decimal('0'),
                fine_paid=False,
            )
            
            # Update to overdue status and set fine using update() to bypass validation
            BorrowRecord.objects.filter(id=record.id).update(
                status='overdue',
                fine_amount=fine_amount
            )
            
            # Decrease available copies
            Book.objects.filter(id=book.id).update(available_copies=book.available_copies - 1)
            
            # Refresh from database
            record.refresh_from_db()
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created overdue record #{created_count}: '
                    f'{book.title[:40]} - '
                    f'{overdue_days} days overdue - '
                    f'Fine: ETB {fine_amount}'
                )
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully created {created_count} overdue records!'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        # Restore original max books
        profile.max_books_allowed = original_max_books
        profile.save()
        self.stdout.write(f'✓ Restored max books to {original_max_books}')
        self.stdout.write('')
        
        self.stdout.write('Test the payment system:')
        self.stdout.write('1. Login as user "test"')
        self.stdout.write('2. Go to "My Books" page')
        self.stdout.write('3. Click "Pay Fine" on any overdue book')
        self.stdout.write('4. Use Stripe test card: 4242 4242 4242 4242')
        self.stdout.write('5. Expiry: 12/34, CVC: 123, ZIP: 12345')
        self.stdout.write('6. Or use Chapa test phone: 0900000000')
        self.stdout.write('')
        
        # Show summary
        total_fines = sum(Decimal(str(days)) * fine_per_day for days in overdue_days_list)
        self.stdout.write(f'Total fines created: ETB {total_fines}')
        self.stdout.write(f'USD equivalent (approx): ${float(total_fines) * 0.018:.2f}')
