import requests
from django.core.management.base import BaseCommand
from apps.books.models import Book


class Command(BaseCommand):
    help = 'Check which book cover images and PDF files are uploaded and accessible'

    def add_arguments(self, parser):
        parser.add_argument('--missing-only', action='store_true')
        parser.add_argument('--covers-only', action='store_true')
        parser.add_argument('--pdfs-only', action='store_true')
        parser.add_argument('--verify-url', action='store_true')

    def check_url(self, url):
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            return r.status_code == 200
        except Exception:
            return False

    def handle(self, *args, **options):
        missing_only = options['missing_only']
        covers_only  = options['covers_only']
        pdfs_only    = options['pdfs_only']
        verify_url   = options['verify_url']

        books = Book.objects.all().order_by('title')
        total = books.count()

        self.stdout.write(self.style.MIGRATE_HEADING(
            '\n' + '='*70 + '\n  BOOK FILE STATUS CHECK  (%d books total)\n' % total + '='*70
        ))

        cover_ok = cover_missing = cover_broken = 0
        pdf_ok   = pdf_missing   = pdf_broken   = 0
        missing_cover_books = []
        missing_pdf_books   = []
        broken_cover_books  = []
        broken_pdf_books    = []

        for book in books:
            if not pdfs_only:
                if book.cover_image and book.cover_image.name:
                    try:
                        url = book.cover_image.url
                        if verify_url:
                            if self.check_url(url):
                                cover_ok += 1
                                if not missing_only:
                                    self.stdout.write(self.style.SUCCESS('  [COVER OK] %s' % book.title))
                            else:
                                cover_broken += 1
                                broken_cover_books.append((book, url))
                                self.stdout.write(self.style.ERROR('  [COVER BROKEN] %s\n    %s' % (book.title, url)))
                        else:
                            cover_ok += 1
                            if not missing_only:
                                self.stdout.write(self.style.SUCCESS('  [COVER OK] %s\n    %s' % (book.title, url)))
                    except Exception as e:
                        cover_broken += 1
                        broken_cover_books.append((book, str(e)))
                        self.stdout.write(self.style.ERROR('  [COVER ERROR] %s -- %s' % (book.title, e)))
                else:
                    cover_missing += 1
                    missing_cover_books.append(book)
                    self.stdout.write(self.style.WARNING('  [COVER MISSING] %s (ISBN: %s)' % (book.title, book.isbn)))

            if not covers_only:
                if book.pdf_file and book.pdf_file.name:
                    try:
                        url = book.pdf_file.url
                        if verify_url:
                            if self.check_url(url):
                                pdf_ok += 1
                                if not missing_only:
                                    self.stdout.write(self.style.SUCCESS('  [PDF   OK] %s' % book.title))
                            else:
                                pdf_broken += 1
                                broken_pdf_books.append((book, url))
                                self.stdout.write(self.style.ERROR('  [PDF   BROKEN] %s\n    %s' % (book.title, url)))
                        else:
                            pdf_ok += 1
                            if not missing_only:
                                self.stdout.write(self.style.SUCCESS('  [PDF   OK] %s\n    %s' % (book.title, url)))
                    except Exception as e:
                        pdf_broken += 1
                        broken_pdf_books.append((book, str(e)))
                        self.stdout.write(self.style.ERROR('  [PDF   ERROR] %s -- %s' % (book.title, e)))
                else:
                    pdf_missing += 1
                    missing_pdf_books.append(book)
                    self.stdout.write(self.style.WARNING('  [PDF   MISSING] %s (ISBN: %s)' % (book.title, book.isbn)))

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*70 + '\n  SUMMARY\n' + '='*70))
        self.stdout.write('  Total books : %d' % total)

        if not pdfs_only:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('  Covers uploaded : %d' % cover_ok))
            self.stdout.write(self.style.WARNING('  Covers missing  : %d' % cover_missing))
            if verify_url:
                self.stdout.write(self.style.ERROR('  Covers broken   : %d' % cover_broken))

        if not covers_only:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('  PDFs uploaded   : %d' % pdf_ok))
            self.stdout.write(self.style.WARNING('  PDFs missing    : %d' % pdf_missing))
            if verify_url:
                self.stdout.write(self.style.ERROR('  PDFs broken     : %d' % pdf_broken))

        if missing_cover_books and not pdfs_only:
            self.stdout.write(self.style.MIGRATE_HEADING(
                '\n' + '='*70 + '\n  BOOKS WITH NO COVER (%d)\n' % len(missing_cover_books) + '='*70
            ))
            for b in missing_cover_books:
                self.stdout.write('  - [%s] %s by %s' % (b.isbn, b.title, b.author))

        if missing_pdf_books and not covers_only:
            self.stdout.write(self.style.MIGRATE_HEADING(
                '\n' + '='*70 + '\n  BOOKS WITH NO PDF (%d)\n' % len(missing_pdf_books) + '='*70
            ))
            for b in missing_pdf_books:
                self.stdout.write('  - [%s] %s by %s' % (b.isbn, b.title, b.author))

        if verify_url:
            if broken_cover_books and not pdfs_only:
                self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*70 + '\n  BROKEN COVER URLS\n' + '='*70))
                for b, url in broken_cover_books:
                    self.stdout.write(self.style.ERROR('  - %s\n    %s' % (b.title, url)))
            if broken_pdf_books and not covers_only:
                self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*70 + '\n  BROKEN PDF URLS\n' + '='*70))
                for b, url in broken_pdf_books:
                    self.stdout.write(self.style.ERROR('  - %s\n    %s' % (b.title, url)))

        self.stdout.write('')
