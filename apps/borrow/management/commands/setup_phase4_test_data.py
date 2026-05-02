"""
Setup test data for Phase 4 email notifications testing
Creates users, books, and various borrow scenarios
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, UserProfile
from apps.books.models import Book, Category
from apps.borrow.models import BorrowRecord, BookRequest


class Command(BaseCommand):
    help = 'Setup test data for Phase 4 email notifications'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up Phase 4 test data...'))
        
        # Create test category
        category, _ = Category.objects.get_or_create(
            name='Test Books',
            defaults={'description': 'Books for testing'}
        )
        
        # Create test books
        books = []
        for i in range(5):
            # Use valid ISBN-13 format (13 digits)
            isbn = f'978000000{i+1:04d}'  # Creates 9780000000001, 9780000000002, etc.
            book, created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    'title': f'Test Book {i+1}',
                    'author': f'Test Author {i+1}',
                    'category': category,
                    'total_copies': 2,
                    'available_copies': 2,
                    'publication_date': timezone.now().date(),
                    'description': f'Test book for Phase 4 testing'
                }
            )
            books.append(book)
            if created:
                self.stdout.write(f'  ✓ Created book: {book.title}')
        
        # Create test student users
        students = []
        for i in range(3):
            username = f'teststudent{i+1}'
            email = f'teststudent{i+1}@test.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Test',
                    'last_name': f'Student{i+1}',
                    'role': 'student',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('test123')
                user.save()
                UserProfile.objects.get_or_create(user=user)
                self.stdout.write(f'  ✓ Created student: {username} (password: test123)')
            
            students.append(user)
        
        # Create test librarian
        librarian, created = User.objects.get_or_create(
            username='testlibrarian',
            defaults={
                'email': 'testlibrarian@test.com',
                'first_name': 'Test',
                'last_name': 'Librarian',
                'role': 'librarian',
                'is_active': True
            }
        )
        
        if created:
            librarian.set_password('test123')
            librarian.save()
            UserProfile.objects.get_or_create(user=librarian)
            self.stdout.write(f'  ✓ Created librarian: testlibrarian (password: test123)')
        
        # Scenario 1: Book borrowed (for approval test)
        book1 = books[0]
        book1.available_copies = 1
        book1.save()
        
        record1, created = BorrowRecord.objects.get_or_create(
            user=students[0],
            book=book1,
            defaults={
                'due_date': timezone.now().date() + timedelta(days=14),
                'status': 'borrowed',
                'issued_by': librarian
            }
        )
        if created:
            students[0].profile.currently_borrowed = 1
            students[0].profile.save()
            self.stdout.write(f'  ✓ Created borrow: {students[0].username} borrowed {book1.title}')
        
        # Scenario 2: Book due in 3 days (for due soon test)
        book2 = books[1]
        book2.available_copies = 1
        book2.save()
        
        record2, created = BorrowRecord.objects.get_or_create(
            user=students[1],
            book=book2,
            defaults={
                'due_date': timezone.now().date() + timedelta(days=3),
                'status': 'borrowed',
                'issued_by': librarian
            }
        )
        if created:
            students[1].profile.currently_borrowed = 1
            students[1].profile.save()
            self.stdout.write(f'  ✓ Created due soon: {students[1].username} - {book2.title} (due in 3 days)')
        
        # Scenario 3: Overdue book (for overdue test)
        book3 = books[2]
        book3.available_copies = 1
        book3.save()
        
        record3, created = BorrowRecord.objects.get_or_create(
            user=students[2],
            book=book3,
            defaults={
                'due_date': timezone.now().date() - timedelta(days=5),
                'status': 'overdue',
                'fine_amount': 10.00,  # 5 days * ETB 2
                'issued_by': librarian
            }
        )
        if created:
            students[2].profile.currently_borrowed = 1
            students[2].profile.total_fines = 10.00
            students[2].profile.save()
            self.stdout.write(f'  ✓ Created overdue: {students[2].username} - {book3.title} (5 days overdue)')
        
        # Scenario 4: Pending book request (for approval/rejection test)
        book4 = books[3]
        request1, created = BookRequest.objects.get_or_create(
            user=students[0],
            book=book4,
            defaults={
                'status': 'pending'
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created pending request: {students[0].username} requested {book4.title}')
        
        # Scenario 5: Another pending request (for rejection test)
        book5 = books[4]
        request2, created = BookRequest.objects.get_or_create(
            user=students[1],
            book=book5,
            defaults={
                'status': 'pending'
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created pending request: {students[1].username} requested {book5.title}')
        
        # Scenario 6: Pending request for waitlist test (book unavailable)
        request3, created = BookRequest.objects.get_or_create(
            user=students[2],
            book=book1,  # This book is already borrowed
            defaults={
                'status': 'pending'
            }
        )
        if created:
            self.stdout.write(f'  ✓ Created waitlist request: {students[2].username} requested {book1.title} (unavailable)')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Phase 4 test data setup complete!'))
        self.stdout.write(self.style.SUCCESS('\nTest Accounts Created:'))
        self.stdout.write('  Students: teststudent1, teststudent2, teststudent3')
        self.stdout.write('  Librarian: testlibrarian')
        self.stdout.write('  Password for all: test123')
        self.stdout.write('\nTest Scenarios Created:')
        self.stdout.write('  1. Borrowed book (for approval email test)')
        self.stdout.write('  2. Book due in 3 days (for due soon email test)')
        self.stdout.write('  3. Overdue book with fine (for overdue/fine email test)')
        self.stdout.write('  4. Pending request (for approval email test)')
        self.stdout.write('  5. Pending request (for rejection email test)')
        self.stdout.write('  6. Waitlist request (for waitlist email test)')
