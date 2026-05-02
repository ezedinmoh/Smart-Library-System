"""
Management command to create test data for payment testing
Creates overdue books with fines for testing the payment system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.borrow.models import BorrowRecord
from apps.users.models import User
from apps.books.models import Book


class Command(BaseCommand):
    help = 'Create test overdue books with fines for payment testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating test payment data...'))
        
        # Get or create a test student
        try:
            student = User.objects.filter(role='student').first()
            if not student:
                self.stdout.write(self.style.ERROR('No student users found. Please create a student user first.'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'Using student: {student.username}'))
            
            # Get borrowed books for this student
            borrowed_books = BorrowRecord.objects.filter(
                user=student,
                status='borrowed'
            )
            
            if not borrowed_books.exists():
                self.stdout.write(self.style.ERROR('No borrowed books found for this student.'))
                self.stdout.write(self.style.WARNING('Please borrow some books first, then run this command.'))
                return
            
            # Make some books overdue with different fine amounts
            test_cases = [
                {'days_overdue': 5, 'fine': 10.00},
                {'days_overdue': 10, 'fine': 20.00},
                {'days_overdue': 3, 'fine': 6.00},
            ]
            
            created_count = 0
            for i, record in enumerate(borrowed_books[:len(test_cases)]):
                test_case = test_cases[i]
                
                # Set due date in the past (bypass validation by using update)
                days_overdue = test_case['days_overdue']
                fine_amount = test_case['fine']
                
                BorrowRecord.objects.filter(pk=record.pk).update(
                    due_date=timezone.now().date() - timedelta(days=days_overdue),
                    status='overdue',
                    fine_amount=fine_amount,
                    fine_paid=False
                )
                
                # Refresh from database
                record.refresh_from_db()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created overdue book: "{record.book.title}" - '
                        f'{days_overdue} days overdue - '
                        f'Fine: ETB {fine_amount}'
                    )
                )
                created_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} overdue books with fines!'))
            self.stdout.write(self.style.WARNING(f'\nYou can now test payments at: http://localhost:8000/borrow/my-books/'))
            self.stdout.write(self.style.WARNING(f'Login as: {student.username}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
