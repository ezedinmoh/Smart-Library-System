"""
Upload local media files directly to Cloudinary and update DB records.
Usage:
    python manage.py upload_to_cloudinary
    python manage.py upload_to_cloudinary --covers-only
    python manage.py upload_to_cloudinary --pdfs-only
    python manage.py upload_to_cloudinary --force   (re-upload even if already set)
"""
import os
import time
import cloudinary
import cloudinary.uploader
from django.core.management.base import BaseCommand
from apps.books.models import Book
from decouple import config


class Command(BaseCommand):
    help = 'Upload local cover images and PDFs to Cloudinary and update DB'

    def add_arguments(self, parser):
        parser.add_argument('--covers-only', action='store_true')
        parser.add_argument('--pdfs-only', action='store_true')
        parser.add_argument('--force', action='store_true', help='Re-upload even if already has a value')

    def setup_cloudinary(self):
        cloudinary.config(
            cloud_name=config('CLOUDINARY_CLOUD_NAME'),
            api_key=config('CLOUDINARY_API_KEY'),
            api_secret=config('CLOUDINARY_API_SECRET'),
            secure=True,
            timeout=60,
            chunk_size=6000000,
        )

    def upload_with_retry(self, local_path, folder, resource_type, retries=5, delay=5):
        """Upload to Cloudinary with retry on connection errors."""
        public_id = os.path.splitext(os.path.basename(local_path))[0]
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                result = cloudinary.uploader.upload(
                    local_path,
                    folder=folder,
                    public_id=public_id,
                    overwrite=True,
                    resource_type=resource_type,
                    timeout=120,
                )
                return result
            except Exception as e:
                last_error = e
                if attempt < retries:
                    self.stdout.write(self.style.WARNING(
                        '    Attempt %d failed (%s), retrying in %ds...' % (attempt, type(e).__name__, delay)
                    ))
                    time.sleep(delay)
                    delay = min(delay * 2, 30)  # exponential backoff, max 30s
        raise last_error

    def handle(self, *args, **options):
        covers_only = options['covers_only']
        pdfs_only   = options['pdfs_only']
        force       = options['force']

        self.setup_cloudinary()

        books = Book.objects.all().order_by('title')
        total = books.count()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '='*60 + '\n  UPLOADING TO CLOUDINARY (%d books)\n' % total + '='*60
        ))

        cover_uploaded = cover_skipped = cover_failed = 0
        pdf_uploaded   = pdf_skipped   = pdf_failed   = 0

        for book in books:

            # ── COVER IMAGE ──────────────────────────────────────────
            if not pdfs_only:
                if book.cover_image and book.cover_image.name and not force:
                    # Check if it's already a Cloudinary URL
                    try:
                        url = book.cover_image.url
                        if 'cloudinary.com' in url:
                            cover_skipped += 1
                            self.stdout.write('  [COVER SKIP] %s — already on Cloudinary' % book.title)
                            continue
                    except Exception:
                        pass

                # Try to find the local file
                local_path = None
                candidates = [
                    book.cover_image.name if book.cover_image and book.cover_image.name else '',
                    'media/' + (book.cover_image.name if book.cover_image and book.cover_image.name else ''),
                    'media/covers/%s.jpg' % book.isbn,
                    'media/covers/%s.jpeg' % book.isbn,
                    'media/covers/%s.png' % book.isbn,
                ]
                for path in candidates:
                    if path and os.path.exists(path):
                        local_path = path
                        break

                if local_path:
                    try:
                        result = self.upload_with_retry(local_path, 'covers', 'image')
                        new_name = 'covers/' + os.path.basename(local_path)
                        Book.objects.filter(pk=book.pk).update(cover_image=new_name)
                        cover_uploaded += 1
                        self.stdout.write(self.style.SUCCESS(
                            '  [COVER OK] %s\n    -> %s' % (book.title, result['secure_url'])
                        ))
                    except Exception as e:
                        cover_failed += 1
                        self.stdout.write(self.style.ERROR('  [COVER FAIL] %s — %s' % (book.title, e)))
                else:
                    cover_failed += 1
                    self.stdout.write(self.style.WARNING(
                        '  [COVER MISSING] %s (ISBN: %s) — no local file found' % (book.title, book.isbn)
                    ))

            # ── PDF FILE ─────────────────────────────────────────────
            if not covers_only:
                if book.pdf_file and book.pdf_file.name and not force:
                    try:
                        url = book.pdf_file.url
                        if 'cloudinary.com' in url:
                            pdf_skipped += 1
                            self.stdout.write('  [PDF   SKIP] %s — already on Cloudinary' % book.title)
                            continue
                    except Exception:
                        pass

                local_path = None
                candidates = [
                    book.pdf_file.name if book.pdf_file and book.pdf_file.name else '',
                    'media/' + (book.pdf_file.name if book.pdf_file and book.pdf_file.name else ''),
                    'media/pdfs/%s.pdf' % book.isbn,
                ]
                for path in candidates:
                    if path and os.path.exists(path):
                        local_path = path
                        break

                if local_path:
                    try:
                        result = self.upload_with_retry(local_path, 'pdfs', 'raw')
                        new_name = 'pdfs/' + os.path.basename(local_path)
                        Book.objects.filter(pk=book.pk).update(pdf_file=new_name)
                        pdf_uploaded += 1
                        self.stdout.write(self.style.SUCCESS(
                            '  [PDF   OK] %s\n    -> %s' % (book.title, result['secure_url'])
                        ))
                    except Exception as e:
                        pdf_failed += 1
                        self.stdout.write(self.style.ERROR('  [PDF   FAIL] %s — %s' % (book.title, e)))
                else:
                    pdf_failed += 1
                    self.stdout.write(self.style.WARNING(
                        '  [PDF   MISSING] %s (ISBN: %s) — no local file found' % (book.title, book.isbn)
                    ))

        # Summary
        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '='*60 + '\n  SUMMARY\n' + '='*60
        ))
        if not pdfs_only:
            self.stdout.write(self.style.SUCCESS('  Covers uploaded : %d' % cover_uploaded))
            self.stdout.write(self.style.WARNING('  Covers skipped  : %d' % cover_skipped))
            self.stdout.write(self.style.ERROR(  '  Covers failed   : %d' % cover_failed))
        if not covers_only:
            self.stdout.write(self.style.SUCCESS('  PDFs uploaded   : %d' % pdf_uploaded))
            self.stdout.write(self.style.WARNING('  PDFs skipped    : %d' % pdf_skipped))
            self.stdout.write(self.style.ERROR(  '  PDFs failed     : %d' % pdf_failed))
        self.stdout.write('')
