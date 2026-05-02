"""
Management command to test payment email notifications
Tests both payment success and failure emails
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.payments.models import Payment
from apps.borrow.models import BorrowRecord
from apps.users.models import User
from apps.users.notifications import notify_payment_success, notify_payment_failure
import uuid


class Command(BaseCommand):
    help = 'Test payment email notifications (success and failure)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='both',
            choices=['success', 'failure', 'both'],
            help='Type of email to test (success, failure, or both)'
        )

    def handle(self, *args, **options):
        email_type = options['type']
        
        self.stdout.write(self.style.WARNING('Testing payment email notifications...\n'))
        
        # Get a student with overdue books
        student = User.objects.filter(role='student').first()
        if not student:
            self.stdout.write(self.style.ERROR('No student users found.'))
            return
        
        # Get an overdue borrow record
        overdue_record = BorrowRecord.objects.filter(
            user=student,
            status='overdue',
            fine_amount__gt=0
        ).first()
        
        if not overdue_record:
            self.stdout.write(self.style.ERROR('No overdue books with fines found.'))
            self.stdout.write(self.style.WARNING('Run: python manage.py create_test_payment_data'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Using student: {student.username} ({student.email})'))
        self.stdout.write(self.style.SUCCESS(f'Book: "{overdue_record.book.title}"'))
        self.stdout.write(self.style.SUCCESS(f'Fine: ETB {overdue_record.fine_amount}\n'))
        
        # Test payment success email
        if email_type in ['success', 'both']:
            self.stdout.write(self.style.WARNING('📧 Testing Payment Success Email...'))
            
            # Create a mock completed payment
            payment = Payment.objects.create(
                user=student,
                borrow_record=overdue_record,
                amount=overdue_record.fine_amount,
                currency='ETB',
                payment_method='stripe',
                transaction_id=f'TEST-SUCCESS-{uuid.uuid4().hex[:8].upper()}',
                status='completed'
            )
            
            # Send success email
            try:
                notify_payment_success(payment)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Payment success email sent!\n'
                        f'  Transaction ID: {payment.transaction_id}\n'
                        f'  Amount: {payment.amount} {payment.currency}\n'
                        f'  Check your console for the email output.\n'
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error sending success email: {str(e)}\n'))
            
            # Clean up test payment
            payment.delete()
        
        # Test payment failure email
        if email_type in ['failure', 'both']:
            self.stdout.write(self.style.WARNING('📧 Testing Payment Failure Email...'))
            
            # Create a mock failed payment
            payment = Payment.objects.create(
                user=student,
                borrow_record=overdue_record,
                amount=overdue_record.fine_amount,
                currency='ETB',
                payment_method='stripe',
                transaction_id=f'TEST-FAILED-{uuid.uuid4().hex[:8].upper()}',
                status='failed'
            )
            
            # Send failure email
            try:
                notify_payment_failure(payment)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Payment failure email sent!\n'
                        f'  Transaction ID: {payment.transaction_id}\n'
                        f'  Amount: {payment.amount} {payment.currency}\n'
                        f'  Check your console for the email output.\n'
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error sending failure email: {str(e)}\n'))
            
            # Clean up test payment
            payment.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                '✅ Email notification test complete!\n'
                'Check the console output above for the email content.'
            )
        )
