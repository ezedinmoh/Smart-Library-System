"""
Management command to upload PDF files to books
Usage: python manage.py upload_pdfs
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from apps.books.models import Book
import os


class Command(BaseCommand):
    help = 'Upload PDF files to books from media/pdfs_to_upload/ directory'

    def handle(self, *args, **options):
        # Directory where you should place your PDF files
        pdf_dir = 'media/pdfs_to_upload'
        
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            self.stdout.write(self.style.WARNING(
                f'Created directory: {pdf_dir}\n'
                f'Please place your PDF files there with naming format: ISBN.pdf\n'
                f'Example: 9780134685991.pdf for a book with ISBN 9780134685991'
            ))
            return
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            self.stdout.write(self.style.WARNING(
                f'No PDF files found in {pdf_dir}\n'
                f'Please add PDF files with naming format: ISBN.pdf'
            ))
            return
        
        uploaded = 0
        skipped = 0
        errors = 0
        
        for pdf_filename in pdf_files:
            # Extract ISBN from filename (remove .pdf extension)
            isbn = pdf_filename[:-4]
            
            try:
                book = Book.objects.get(isbn=isbn)
                
                # Check if book already has a PDF
                if book.pdf_file:
                    self.stdout.write(self.style.WARNING(
                        f'Skipped: {book.title} (ISBN: {isbn}) - Already has PDF'
                    ))
                    skipped += 1
                    continue
                
                # Upload the PDF
                pdf_path = os.path.join(pdf_dir, pdf_filename)
                with open(pdf_path, 'rb') as pdf_file:
                    book.pdf_file.save(pdf_filename, File(pdf_file), save=True)
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Uploaded PDF for: {book.title} (ISBN: {isbn})'
                ))
                uploaded += 1
                
            except Book.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'✗ No book found with ISBN: {isbn}'
                ))
                errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Error uploading {pdf_filename}: {str(e)}'
                ))
                errors += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Uploaded: {uploaded}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped}'))
        self.stdout.write(self.style.ERROR(f'Errors: {errors}'))
        self.stdout.write('='*50)
