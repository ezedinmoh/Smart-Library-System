from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, UserProfile
from apps.books.models import Book, Category, BookReview
from apps.borrow.models import BorrowRecord, BookRequest
from apps.dashboard.utils import log_activity
import random


class Command(BaseCommand):
    help = 'Create comprehensive test data for the library system'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))
        
        # Get or create required users
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@library.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        if created:
            admin.set_password('Admin@123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('✅ Created admin user'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Found existing admin user'))
        
        student, created = User.objects.get_or_create(
            username='ezedin',
            defaults={
                'email': 'ezedin@library.com',
                'role': 'student',
                'first_name': 'Ezedin',
                'last_name': 'Mohammed'
            }
        )
        if created:
            student.set_password('Ezedin@123')
            student.save()
            self.stdout.write(self.style.SUCCESS('✅ Created student user'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Found existing student user'))
        
        librarian, created = User.objects.get_or_create(
            username='Library',
            defaults={
                'email': 'library.staff@library.com',
                'role': 'librarian',
                'first_name': 'Library',
                'last_name': 'Staff'
            }
        )
        if created:
            librarian.set_password('library@123')
            librarian.save()
            self.stdout.write(self.style.SUCCESS('✅ Created librarian user'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Found existing librarian user'))
        
        # Create additional test users
        self.create_additional_users()
        
        # Get existing books
        books = list(Book.objects.all())
        if not books:
            self.stdout.write(self.style.ERROR('No books found! Run seed_books first.'))
            return
        
        self.stdout.write(f'Found {len(books)} books')
        
        # Reset book availability
        for book in books:
            book.available_copies = book.total_copies
            book.save()
        
        # Create test data
        self.create_borrow_records(student, librarian, books)
        self.create_book_requests(student, librarian, books)
        self.create_reviews(student, books)
        self.create_activity_logs(admin, librarian, student)
        self.update_user_profiles()
        
        self.stdout.write(self.style.SUCCESS('✅ Test data created successfully!'))

    def create_additional_users(self):
        """Create 5 additional users for each role"""
        self.stdout.write('Creating additional users...')
        
        student_names = [
            ('Alice', 'Johnson', 'alice'),
            ('Bob', 'Smith', 'bob'),
            ('Carol', 'Williams', 'carol'),
            ('David', 'Brown', 'david'),
            ('Emma', 'Davis', 'emma'),
        ]
        
        for first, last, username in student_names:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@student.com',
                    password='Student@123',
                    first_name=first,
                    last_name=last,
                    role='student'
                )
                user.profile.total_books_read = random.randint(0, 30)
                user.profile.update_reading_badge()
                self.stdout.write(f'  Created student: {username}')
        
        librarian_names = [
            ('John', 'Librarian', 'john_lib'),
            ('Sarah', 'Keeper', 'sarah_lib'),
        ]
        
        for first, last, username in librarian_names:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    email=f'{username}@library.com',
                    password='Librarian@123',
                    first_name=first,
                    last_name=last,
                    role='librarian'
                )
                self.stdout.write(f'  Created librarian: {username}')

    def create_borrow_records(self, student, librarian, books):
        """Create borrow records with various statuses"""
        self.stdout.write('Creating borrow records...')
        
        today = timezone.now()
        
        # Create 7 returned books for the main student (for reviews)
        for i in range(7):
            book = books[i]
            borrow_date = today - timedelta(days=random.randint(30, 90))
            due_date = borrow_date + timedelta(days=14)
            return_date = due_date - timedelta(days=random.randint(1, 5))
            
            BorrowRecord.objects.create(
                user=student,
                book=book,
                borrow_date=borrow_date,
                due_date=due_date,
                return_date=return_date,
                status='returned',
                issued_by=librarian,
                returned_to=librarian
            )
            self.stdout.write(f'  Returned: {book.title}')
        
        # Create 2 currently borrowed books
        for i in range(7, 9):
            book = books[i]
            borrow_date = today - timedelta(days=random.randint(1, 10))
            due_date = borrow_date + timedelta(days=14)
            
            BorrowRecord.objects.create(
                user=student,
                book=book,
                borrow_date=borrow_date,
                due_date=due_date,
                status='borrowed',
                issued_by=librarian
            )
            book.available_copies -= 1
            book.save()
            self.stdout.write(f'  Borrowed: {book.title}')
        
        # Create 2 overdue books with fines
        for i in range(9, 11):
            book = books[i]
            borrow_date = today - timedelta(days=random.randint(20, 40))
            due_date = borrow_date + timedelta(days=14)
            days_overdue = (today.date() - due_date.date()).days
            
            BorrowRecord.objects.create(
                user=student,
                book=book,
                borrow_date=borrow_date,
                due_date=due_date,
                status='overdue',
                fine_amount=days_overdue * 2,
                fine_paid=random.choice([True, False]),
                issued_by=librarian
            )
            book.available_copies -= 1
            book.save()
            self.stdout.write(f'  Overdue: {book.title} (Fine: ETB {days_overdue * 2})')
        
        # Create records for other students
        students = User.objects.filter(role='student').exclude(id=student.id)
        book_index = 11
        
        for other_student in students:
            if book_index >= len(books):
                break
            
            # Each student gets 1-2 returned books
            for j in range(min(2, len(books) - book_index)):
                book = books[book_index]
                borrow_date = today - timedelta(days=random.randint(15, 60))
                due_date = borrow_date + timedelta(days=14)
                return_date = due_date - timedelta(days=random.randint(1, 5))
                
                BorrowRecord.objects.create(
                    user=other_student,
                    book=book,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    return_date=return_date,
                    status='returned',
                    issued_by=librarian,
                    returned_to=librarian
                )
                book_index += 1

    def create_book_requests(self, student, librarian, books):
        """Create book requests with various statuses"""
        self.stdout.write('Creating book requests...')
        
        today = timezone.now()
        
        # 3 Pending requests
        for i in range(3):
            BookRequest.objects.create(
                user=student,
                book=books[i + 15],
                status='pending',
                request_date=today - timedelta(hours=random.randint(1, 48))
            )
            self.stdout.write(f'  Pending: {books[i + 15].title}')
        
        # 2 Ready for pickup
        for i in range(2):
            BookRequest.objects.create(
                user=student,
                book=books[i + 18],
                status='ready',
                request_date=today - timedelta(days=2),
                approved_by=librarian,
                approved_date=today - timedelta(days=1)
            )
            self.stdout.write(f'  Ready: {books[i + 18].title}')
        
        # 2 Fulfilled
        for i in range(2):
            BookRequest.objects.create(
                user=student,
                book=books[i + 20],
                status='fulfilled',
                request_date=today - timedelta(days=10),
                approved_by=librarian,
                approved_date=today - timedelta(days=8)
            )
        
        # 1 Rejected
        BookRequest.objects.create(
            user=student,
            book=books[22],
            status='rejected',
            request_date=today - timedelta(days=5),
            approved_by=librarian,
            approved_date=today - timedelta(days=3),
            rejection_reason='Book is under maintenance'
        )
        self.stdout.write(f'  Rejected: {books[22].title}')
        
        # 1 Cancelled
        BookRequest.objects.create(
            user=student,
            book=books[21],
            status='cancelled',
            request_date=today - timedelta(days=4),
            cancellation_reason='Changed my mind'
        )
        self.stdout.write(f'  Cancelled: {books[21].title}')

    def create_reviews(self, student, books):
        """Create book reviews for returned books"""
        self.stdout.write('Creating book reviews...')
        
        # Get returned books for the student
        returned_records = BorrowRecord.objects.filter(
            user=student,
            status='returned'
        )[:3]
        
        for record in returned_records:
            BookReview.objects.create(
                user=student,
                book=record.book,
                rating=random.randint(4, 5),
                review_text=f"Excellent book! {record.book.title} was very informative and well-written. Highly recommended!"
            )
            self.stdout.write(f'  Review: {record.book.title}')
    
    def create_activity_logs(self, admin, librarian, student):
        """Create activity logs"""
        self.stdout.write('Creating activity logs...')
        
        activities = [
            (admin, 'book_added', 'Added new book to library'),
            (admin, 'user_created', 'Created new student account'),
            (librarian, 'book_borrowed', 'Issued book to student'),
            (librarian, 'book_returned', 'Processed book return'),
            (admin, 'backup_created', 'Created database backup'),
            (librarian, 'request_approved', 'Approved book request'),
            (student, 'review_added', 'Added book review'),
            (admin, 'reminder_sent', 'Sent due date reminders'),
        ]
        
        for user, action, description in activities:
            log_activity(user, action, description, None)
        
        self.stdout.write(f'  Created {len(activities)} activity logs')
    
    def update_user_profiles(self):
        """Update user profiles with reading data"""
        self.stdout.write('Updating user profiles...')
        
        students = User.objects.filter(role='student')
        
        for student in students:
            returned_count = BorrowRecord.objects.filter(
                user=student,
                status='returned'
            ).count()
            
            active_count = BorrowRecord.objects.filter(
                user=student,
                status__in=['borrowed', 'overdue']
            ).count()
            
            student.profile.total_books_read = returned_count
            student.profile.currently_borrowed = active_count
            student.profile.update_reading_badge()
            student.profile.save()
            
            self.stdout.write(f'  Updated: {student.username} ({returned_count} read, {active_count} active)')
