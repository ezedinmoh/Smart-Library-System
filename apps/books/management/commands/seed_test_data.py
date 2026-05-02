"""
Comprehensive test data seed command.
Creates users (all roles), books with covers, borrow records,
book requests, payments, and reviews — all testable features.

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --clear   # wipe existing test data first
"""
import os
import requests
from io import BytesIO
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.books.models import Book, Category, BookReview
from apps.borrow.models import BorrowRecord, BookRequest
from apps.payments.models import Payment, StripePayment, ChapaPayment
from apps.users.models import UserProfile
from apps.dashboard.models import SystemSettings

User = get_user_model()
PASSWORD = 'Pass@123'


class Command(BaseCommand):
    help = 'Seed comprehensive test data covering all features'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Delete existing test data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_test_data()

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('  SEEDING TEST DATA'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60))

        with transaction.atomic():
            self._seed_system_settings()
            users = self._seed_users()
            categories = self._seed_categories()
            books = self._seed_books(categories)
            self._seed_borrow_records(users, books)
            self._seed_book_requests(users, books)
            self._seed_payments(users, books)
            self._seed_reviews(users, books)

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  ALL TEST DATA SEEDED SUCCESSFULLY'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60))
        self.stdout.write('\nTest accounts (password: Pass@123):')
        self.stdout.write('  Admin    : admin_test / admin_test@library.com')
        self.stdout.write('  Librarian: lib_test   / lib_test@library.com')
        self.stdout.write('  Student  : stu_test1  / stu_test1@library.com')
        self.stdout.write('  Student  : stu_test2  / stu_test2@library.com')
        self.stdout.write('  Student  : stu_test3  / stu_test3@library.com')
        self.stdout.write('  (student with fines, overdue, payments, reviews)\n')

    # ── Clear ────────────────────────────────────────────────────────────────
    def _clear_test_data(self):
        test_usernames = [
            'admin_test', 'lib_test',
            'stu_test1', 'stu_test2', 'stu_test3', 'stu_test4', 'stu_test5'
        ]
        deleted = User.objects.filter(username__in=test_usernames).delete()
        self.stdout.write(self.style.WARNING(f'Cleared existing test users: {deleted[0]} objects'))

    # ── System Settings ──────────────────────────────────────────────────────
    def _seed_system_settings(self):
        s = SystemSettings.get_settings()
        s.fine_per_day = Decimal('2.00')
        s.max_borrow_days = 14
        s.default_borrow_limit = 7
        s.etb_to_usd_rate = Decimal('0.0180')
        s.save()
        self.stdout.write(self.style.SUCCESS('✓ System settings configured'))

    # ── Users ────────────────────────────────────────────────────────────────
    def _seed_users(self):
        self.stdout.write('\nCreating users...')
        users = {}

        specs = [
            # (username, email, role, first, last)
            ('admin_test',  'admin_test@library.com',  'admin',     'Admin',   'Test'),
            ('lib_test',    'lib_test@library.com',    'librarian', 'Lib',     'Test'),
            ('stu_test1',   'stu_test1@library.com',   'student',   'Alice',   'Student'),
            ('stu_test2',   'stu_test2@library.com',   'student',   'Bob',     'Student'),
            ('stu_test3',   'stu_test3@library.com',   'student',   'Carol',   'Student'),
            ('stu_test4',   'stu_test4@library.com',   'student',   'David',   'Student'),
            ('stu_test5',   'stu_test5@library.com',   'student',   'Eve',     'Student'),
        ]

        for username, email, role, first, last in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'role': role,
                    'first_name': first,
                    'last_name': last,
                    'is_active': True,
                }
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created {role}: {username}'))
            else:
                # Update password in case it changed
                user.set_password(PASSWORD)
                user.is_active = True
                user.save()
                self.stdout.write(f'  ~ Exists: {username} (password updated)')

            # Ensure profile exists
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.max_books_allowed = 7
            profile.save()

            users[username] = user

        return users

    # ── Categories ───────────────────────────────────────────────────────────
    def _seed_categories(self):
        self.stdout.write('\nCreating categories...')
        cat_data = [
            ('Fiction',          'Novels, short stories, and literary fiction'),
            ('Science Fiction',  'Futuristic and speculative fiction'),
            ('Technology',       'Programming, software, and tech books'),
            ('History',          'Historical events and biographies'),
            ('Science',          'Natural sciences and research'),
            ('Self-Help',        'Personal development and motivation'),
            ('Mystery',          'Detective and thriller novels'),
        ]
        categories = {}
        for name, desc in cat_data:
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': desc})
            categories[name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {name}'))
        return categories

    # ── Books ────────────────────────────────────────────────────────────────
    def _seed_books(self, categories):
        self.stdout.write('\nCreating books...')
        book_data = [
            # (isbn, title, author, category, copies, language, pages, description)
            ('9780743273565', 'The Great Gatsby',         'F. Scott Fitzgerald', 'Fiction',         5, 'en', 180,
             'A story of the fabulously wealthy Jay Gatsby and his love for Daisy Buchanan.'),
            ('9780061935466', 'To Kill a Mockingbird',    'Harper Lee',          'Fiction',         4, 'en', 281,
             'The story of racial injustice and the loss of innocence in the American South.'),
            ('9780441013593', 'Dune',                     'Frank Herbert',       'Science Fiction', 3, 'en', 412,
             'A science fiction epic set in a distant future amidst a feudal interstellar society.'),
            ('9780132350884', 'Clean Code',               'Robert C. Martin',    'Technology',      6, 'en', 431,
             'A handbook of agile software craftsmanship.'),
            ('9781593279288', 'Python Crash Course',      'Eric Matthes',        'Technology',      5, 'en', 544,
             'A hands-on, project-based introduction to programming.'),
            ('9780062316097', 'Sapiens',                  'Yuval Noah Harari',   'History',         4, 'en', 443,
             'A brief history of humankind from the Stone Age to the present.'),
            ('9780553380163', 'A Brief History of Time',  'Stephen Hawking',     'Science',         3, 'en', 212,
             'A landmark volume in science writing by one of the great minds of our time.'),
            ('9780735211292', 'Atomic Habits',            'James Clear',         'Self-Help',       6, 'en', 320,
             'An easy and proven way to build good habits and break bad ones.'),
            ('9780307474278', 'The Da Vinci Code',        'Dan Brown',           'Mystery',         4, 'en', 454,
             'A murder mystery thriller involving secret societies and religious history.'),
            ('9780451524935', '1984',                     'George Orwell',       'Fiction',         5, 'en', 328,
             'A dystopian social science fiction novel about totalitarianism.'),
        ]

        books = {}
        for isbn, title, author, cat_name, copies, lang, pages, desc in book_data:
            # Use update_or_create with direct DB write to bypass model's save() override
            # which triggers Cloudinary QR code upload
            existing = Book.objects.filter(isbn=isbn).first()
            if existing:
                self.stdout.write(f'  ~ Exists: "{title}"')
                books[isbn] = existing
                continue

            # Insert directly bypassing save() to avoid Cloudinary QR upload
            book = Book(
                isbn=isbn,
                title=title,
                author=author,
                category=categories.get(cat_name),
                total_copies=copies,
                available_copies=copies,
                language=lang,
                pages=pages,
                description=desc,
                publisher='Test Publisher',
                publication_date=timezone.now().date() - timedelta(days=365),
            )
            # Use queryset insert to bypass model save() and full_clean()
            Book.objects.bulk_create([book])
            book = Book.objects.get(isbn=isbn)

            # Download cover (goes to Cloudinary if active, skips gracefully on timeout)
            cover_saved = self._download_cover(book)
            status = '✓ cover' if cover_saved else '(no cover - VPN blocked)'
            self.stdout.write(self.style.SUCCESS(f'  ✓ "{title}" {status}'))
            books[isbn] = book

        return books

    def _download_cover(self, book):
        """Try to download cover from Open Library, generate placeholder if fails"""
        try:
            # Try Open Library by title
            search_url = f'https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg'
            r = requests.get(search_url, timeout=8)
            if r.status_code == 200 and len(r.content) > 5000:
                book.cover_image.save(f'{book.isbn}.jpg', ContentFile(r.content), save=True)
                return True
        except Exception:
            pass

        # Generate a simple colored placeholder
        try:
            from PIL import Image, ImageDraw, ImageFont
            colors_map = {
                'Fiction': '#3B82F6', 'Science Fiction': '#8B5CF6',
                'Technology': '#10B981', 'History': '#F59E0B',
                'Science': '#06B6D4', 'Self-Help': '#F97316',
                'Mystery': '#EF4444',
            }
            cat_name = book.category.name if book.category else 'Fiction'
            bg_color = colors_map.get(cat_name, '#6B7280')

            img = Image.new('RGB', (400, 600), color=bg_color)
            draw = ImageDraw.Draw(img)

            # Dark overlay at bottom
            draw.rectangle([(0, 400), (400, 600)], fill='#00000088')

            # Title text (wrap)
            words = book.title.split()
            lines, line = [], []
            for word in words:
                if len(' '.join(line + [word])) <= 20:
                    line.append(word)
                else:
                    if line:
                        lines.append(' '.join(line))
                    line = [word]
            if line:
                lines.append(' '.join(line))

            try:
                font_title = ImageFont.truetype('arial.ttf', 36)
                font_author = ImageFont.truetype('arial.ttf', 24)
            except Exception:
                font_title = ImageFont.load_default()
                font_author = ImageFont.load_default()

            y = 420
            for line in lines[:3]:
                draw.text((20, y), line, fill='white', font=font_title)
                y += 44

            draw.text((20, y + 10), book.author, fill='#D1D5DB', font=font_author)

            buf = BytesIO()
            img.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            book.cover_image.save(f'{book.isbn}.jpg', ContentFile(buf.read()), save=True)
            return True
        except Exception:
            return False

    # ── Borrow Records ───────────────────────────────────────────────────────
    def _seed_borrow_records(self, users, books):
        self.stdout.write('\nCreating borrow records...')
        book_list = list(books.values())

        # stu_test1: currently borrowing 2 books (active)
        self._create_borrow(users['stu_test1'], book_list[0], status='borrowed',
                            days_ago=5, due_in=9, issued_by=users['lib_test'])
        self._create_borrow(users['stu_test1'], book_list[1], status='borrowed',
                            days_ago=3, due_in=11, issued_by=users['lib_test'])

        # stu_test2: 1 overdue book with fine
        self._create_borrow(users['stu_test2'], book_list[2], status='overdue',
                            days_ago=20, due_in=-6, fine=12.00, issued_by=users['lib_test'])

        # stu_test3: returned books (for reviews) + 1 active
        self._create_borrow(users['stu_test3'], book_list[3], status='returned',
                            days_ago=30, due_in=-16, returned_days_ago=14,
                            issued_by=users['lib_test'], returned_to=users['lib_test'])
        self._create_borrow(users['stu_test3'], book_list[4], status='returned',
                            days_ago=60, due_in=-46, returned_days_ago=44,
                            issued_by=users['lib_test'], returned_to=users['lib_test'])
        self._create_borrow(users['stu_test3'], book_list[5], status='borrowed',
                            days_ago=2, due_in=12, issued_by=users['lib_test'])

        # stu_test4: overdue with paid fine
        self._create_borrow(users['stu_test4'], book_list[6], status='overdue',
                            days_ago=25, due_in=-11, fine=22.00, fine_paid=True,
                            issued_by=users['lib_test'])

        # stu_test5: returned with unpaid fine
        self._create_borrow(users['stu_test5'], book_list[7], status='returned',
                            days_ago=40, due_in=-26, returned_days_ago=20,
                            fine=20.00, fine_paid=False,
                            issued_by=users['lib_test'], returned_to=users['lib_test'])

        self.stdout.write(self.style.SUCCESS('  ✓ Borrow records created'))

    def _create_borrow(self, user, book, status, days_ago, due_in,
                       fine=0, fine_paid=False, returned_days_ago=None,
                       issued_by=None, returned_to=None):
        # Check if already exists
        if BorrowRecord.objects.filter(user=user, book=book, status=status).exists():
            return

        borrow_date = timezone.now() - timedelta(days=days_ago)
        due_date = timezone.now().date() + timedelta(days=due_in)
        return_date = None
        if returned_days_ago is not None:
            return_date = timezone.now().date() - timedelta(days=returned_days_ago)

        record = BorrowRecord(
            user=user,
            book=book,
            borrow_date=borrow_date,
            due_date=due_date,
            return_date=return_date,
            status=status,
            fine_amount=Decimal(str(fine)),
            fine_paid=fine_paid,
            issued_by=issued_by,
            returned_to=returned_to,
        )
        # Save directly bypassing full_clean to avoid availability conflicts
        BorrowRecord.objects.bulk_create([record])

        # Update book availability for active borrows
        if status in ('borrowed', 'overdue'):
            Book.objects.filter(pk=book.pk, available_copies__gt=0).update(
                available_copies=book.available_copies - 1,
                times_borrowed=book.times_borrowed + 1
            )
        elif status == 'returned':
            Book.objects.filter(pk=book.pk).update(
                times_borrowed=book.times_borrowed + 1
            )

        # Update user profile
        if status in ('borrowed', 'overdue'):
            UserProfile.objects.filter(user=user).update(
                currently_borrowed=user.profile.currently_borrowed + 1
            )
        elif status == 'returned':
            UserProfile.objects.filter(user=user).update(
                total_books_read=user.profile.total_books_read + 1
            )

    # ── Book Requests ────────────────────────────────────────────────────────
    def _seed_book_requests(self, users, books):
        self.stdout.write('\nCreating book requests...')
        book_list = list(books.values())

        requests_data = [
            # (user, book, status, approved_by)
            (users['stu_test1'], book_list[6], 'pending',   None),
            (users['stu_test1'], book_list[7], 'pending',   None),
            (users['stu_test2'], book_list[8], 'pending',   None),
            (users['stu_test4'], book_list[9], 'rejected',  users['lib_test']),
            (users['stu_test5'], book_list[0], 'cancelled', None),
        ]

        for user, book, status, approved_by in requests_data:
            if BookRequest.objects.filter(user=user, book=book).exists():
                continue
            req = BookRequest(
                user=user,
                book=book,
                status=status,
                approved_by=approved_by,
                rejection_reason='Book not available for this semester.' if status == 'rejected' else '',
                cancellation_reason='Changed my mind.' if status == 'cancelled' else '',
            )
            if approved_by:
                req.approved_date = timezone.now() - timedelta(days=1)
            BookRequest.objects.bulk_create([req])

        self.stdout.write(self.style.SUCCESS('  ✓ Book requests created'))

    # ── Payments ─────────────────────────────────────────────────────────────
    def _seed_payments(self, users, books):
        self.stdout.write('\nCreating payments...')
        import uuid

        # Get overdue borrow records for payments
        overdue_records = BorrowRecord.objects.filter(
            user__in=[users['stu_test2'], users['stu_test4'], users['stu_test5']],
            fine_amount__gt=0
        )

        for record in overdue_records:
            if Payment.objects.filter(borrow_record=record).exists():
                continue

            method = 'stripe' if record.user == users['stu_test4'] else 'chapa'
            status = 'completed' if record.fine_paid else 'pending'

            payment = Payment.objects.create(
                user=record.user,
                borrow_record=record,
                amount=record.fine_amount,
                currency='ETB',
                payment_method=method,
                status=status,
                transaction_id=f'TEST-{method.upper()}-{uuid.uuid4().hex[:8].upper()}',
            )

            if method == 'stripe':
                StripePayment.objects.get_or_create(
                    payment=payment,
                    defaults={'stripe_payment_intent_id': f'pi_test_{uuid.uuid4().hex[:16]}'}
                )
            else:
                ChapaPayment.objects.get_or_create(
                    payment=payment,
                    defaults={'chapa_tx_ref': f'CHAPA-TEST-{uuid.uuid4().hex[:8].upper()}'}
                )

        self.stdout.write(self.style.SUCCESS('  ✓ Payments created'))

    # ── Reviews ──────────────────────────────────────────────────────────────
    def _seed_reviews(self, users, books):
        self.stdout.write('\nCreating book reviews...')
        book_list = list(books.values())

        # stu_test3 returned books[3] and books[4] — can review them
        reviews = [
            (users['stu_test3'], book_list[3], 5, 'Excellent book on clean coding practices! Changed how I write code.'),
            (users['stu_test3'], book_list[4], 4, 'Great introduction to Python. Very practical with real projects.'),
        ]

        for user, book, rating, text in reviews:
            if BookReview.objects.filter(user=user, book=book).exists():
                continue
            # Save directly bypassing validation (already verified they borrowed it)
            BookReview.objects.create(
                user=user,
                book=book,
                rating=rating,
                review_text=text,
            )
            # Update book rating
            from django.db.models import Avg
            avg = book.reviews.aggregate(Avg('rating'))['rating__avg']
            if avg:
                Book.objects.filter(pk=book.pk).update(rating=round(avg, 2))

        self.stdout.write(self.style.SUCCESS('  ✓ Reviews created'))
