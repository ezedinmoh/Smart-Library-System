"""
Comprehensive test command for all Phase 4 email notifications
Tests all 7 email types in sequence
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.borrow.models import BorrowRecord, BookRequest
from apps.users.models import User
from apps.users.notifications import (
    notify_request_approved,
    notify_request_rejected,
    notify_book_due_soon,
    notify_book_overdue,
    notify_fine_applied,
    notify_book_available_waitlist,
    send_welcome_email
)


class Command(BaseCommand):
    help = 'Test all Phase 4 email notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific email to test (approved, rejected, due_soon, overdue, fine, waitlist, welcome)',
        )
    
    def handle(self, *args, **options):
        specific_email = options.get('email')
        
        if specific_email:
            self._test_specific_email(specific_email)
        else:
            self._test_all_emails()
    
    def _test_all_emails(self):
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('TESTING ALL PHASE 4 EMAIL NOTIFICATIONS'))
        self.stdout.write(self.style.WARNING('='*60 + '\n'))
        
        # Test 1: Welcome Email
        self._test_welcome_email()
        
        # Test 2: Book Request Approved
        self._test_approved_email()
        
        # Test 3: Book Request Rejected
        self._test_rejected_email()
        
        # Test 4: Book Due Soon
        self._test_due_soon_email()
        
        # Test 5: Book Overdue
        self._test_overdue_email()
        
        # Test 6: Fine Applied
        self._test_fine_email()
        
        # Test 7: Book Available (Waitlist)
        self._test_waitlist_email()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ ALL PHASE 4 EMAIL TESTS COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        self.stdout.write('Check your terminal output above for all emails.')
        self.stdout.write('Each email should be clearly formatted and readable.\n')
    
    def _test_specific_email(self, email_type):
        self.stdout.write(self.style.WARNING(f'\nTesting {email_type} email...\n'))
        
        if email_type == 'welcome':
            self._test_welcome_email()
        elif email_type == 'approved':
            self._test_approved_email()
        elif email_type == 'rejected':
            self._test_rejected_email()
        elif email_type == 'due_soon':
            self._test_due_soon_email()
        elif email_type == 'overdue':
            self._test_overdue_email()
        elif email_type == 'fine':
            self._test_fine_email()
        elif email_type == 'waitlist':
            self._test_waitlist_email()
        else:
            self.stdout.write(self.style.ERROR(f'Unknown email type: {email_type}'))
            self.stdout.write('Valid types: welcome, approved, rejected, due_soon, overdue, fine, waitlist')
    
    def _test_welcome_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 1: WELCOME EMAIL'))
        self.stdout.write('-' * 60)
        
        user = User.objects.filter(username='teststudent1').first()
        if not user:
            self.stdout.write(self.style.ERROR('❌ Test user not found. Run: python manage.py setup_phase4_test_data'))
            return
        
        send_welcome_email(user)
        self.stdout.write(self.style.SUCCESS(f'✅ Welcome email sent to: {user.email}'))
        self.stdout.write('')
    
    def _test_approved_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 2: BOOK REQUEST APPROVED EMAIL'))
        self.stdout.write('-' * 60)
        
        request = BookRequest.objects.filter(status='pending').first()
        if not request:
            self.stdout.write(self.style.ERROR('❌ No pending requests found. Run: python manage.py setup_phase4_test_data'))
            return
        
        # Create a mock request object for testing
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.user = request.approved_by if request.approved_by else User.objects.filter(role='librarian').first()
        
        notify_request_approved(mock_request, request)
        self.stdout.write(self.style.SUCCESS(f'✅ Approval email sent to: {request.user.email}'))
        self.stdout.write(f'   Book: {request.book.title}')
        self.stdout.write('')
    
    def _test_rejected_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 3: BOOK REQUEST REJECTED EMAIL'))
        self.stdout.write('-' * 60)
        
        request = BookRequest.objects.filter(status='pending').last()
        if not request:
            self.stdout.write(self.style.ERROR('❌ No pending requests found. Run: python manage.py setup_phase4_test_data'))
            return
        
        # Create a mock request object for testing
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.user = request.approved_by if request.approved_by else User.objects.filter(role='librarian').first()
        
        # Set a test rejection reason
        test_reason = "Book is currently reserved for another user"
        request.rejection_reason = test_reason
        
        notify_request_rejected(mock_request, request, reason=test_reason)
        self.stdout.write(self.style.SUCCESS(f'✅ Rejection email sent to: {request.user.email}'))
        self.stdout.write(f'   Book: {request.book.title}')
        self.stdout.write(f'   Reason: {test_reason}')
        self.stdout.write('')
    
    def _test_due_soon_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 4: BOOK DUE SOON EMAIL'))
        self.stdout.write('-' * 60)
        
        # Find book due in 3 days
        record = BorrowRecord.objects.filter(
            status='borrowed',
            due_date=timezone.now().date() + timezone.timedelta(days=3)
        ).first()
        
        if not record:
            # Use any borrowed book for testing
            record = BorrowRecord.objects.filter(status='borrowed').first()
        
        if not record:
            self.stdout.write(self.style.ERROR('❌ No borrowed books found. Run: python manage.py setup_phase4_test_data'))
            return
        
        notify_book_due_soon(record)
        self.stdout.write(self.style.SUCCESS(f'✅ Due soon email sent to: {record.user.email}'))
        self.stdout.write(f'   Book: {record.book.title}')
        self.stdout.write(f'   Due date: {record.due_date}')
        self.stdout.write('')
    
    def _test_overdue_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 5: BOOK OVERDUE EMAIL'))
        self.stdout.write('-' * 60)
        
        record = BorrowRecord.objects.filter(status='overdue').first()
        
        if not record:
            self.stdout.write(self.style.ERROR('❌ No overdue books found. Run: python manage.py setup_phase4_test_data'))
            return
        
        notify_book_overdue(record)
        self.stdout.write(self.style.SUCCESS(f'✅ Overdue email sent to: {record.user.email}'))
        self.stdout.write(f'   Book: {record.book.title}')
        self.stdout.write(f'   Days overdue: {(timezone.now().date() - record.due_date).days}')
        self.stdout.write(f'   Fine: ETB {record.fine_amount}')
        self.stdout.write('')
    
    def _test_fine_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 6: FINE APPLIED EMAIL'))
        self.stdout.write('-' * 60)
        
        record = BorrowRecord.objects.filter(status='overdue', fine_amount__gt=0).first()
        
        if not record:
            self.stdout.write(self.style.ERROR('❌ No overdue books with fines found. Run: python manage.py setup_phase4_test_data'))
            return
        
        notify_fine_applied(record)
        self.stdout.write(self.style.SUCCESS(f'✅ Fine email sent to: {record.user.email}'))
        self.stdout.write(f'   Book: {record.book.title}')
        self.stdout.write(f'   Fine amount: ETB {record.fine_amount}')
        self.stdout.write('')
    
    def _test_waitlist_email(self):
        self.stdout.write(self.style.WARNING('📧 TEST 7: BOOK AVAILABLE (WAITLIST) EMAIL'))
        self.stdout.write('-' * 60)
        
        request = BookRequest.objects.filter(status='pending').first()
        
        if not request:
            self.stdout.write(self.style.ERROR('❌ No pending requests found. Run: python manage.py setup_phase4_test_data'))
            return
        
        notify_book_available_waitlist(request, position_in_queue=1, total_in_queue=3)
        self.stdout.write(self.style.SUCCESS(f'✅ Waitlist email sent to: {request.user.email}'))
        self.stdout.write(f'   Book: {request.book.title}')
        self.stdout.write(f'   Position: #1 of 3')
        self.stdout.write('')
