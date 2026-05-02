from django.core.management.base import BaseCommand
from apps.books.models import Book
from apps.users.models import User
from apps.borrow.models import BorrowRecord
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate QR codes for all existing books'

    def handle(self, *args, **kwargs):
        books = Book.objects.all()
        count = 0
        
        for book in books:
            if not book.qr_code:
                try:
                    book.generate_qr_code()
                    book.save()
                    count += 1
                    self.stdout.write(f'Generated QR code for: {book.title}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error for {book.title}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} QR codes'))
