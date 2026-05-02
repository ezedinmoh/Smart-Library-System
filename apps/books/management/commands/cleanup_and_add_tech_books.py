"""
Management command to seed database with public domain books from Project Gutenberg
These books are legally free to use and distribute
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book, Category
import requests
from io import BytesIO
from datetime import date


class Command(BaseCommand):
    help = 'Seed database with public domain books from Project Gutenberg'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing books before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            confirm = input('This will delete ALL existing books. Are you sure? (yes/no): ')
            if confirm.lower() == 'yes':
                Book.objects.all().delete()
                self.stdout.write(self.style.WARNING('Cleared all existing books'))
            else:
                self.stdout.write('Cancelled')
                return

        # Create categories
        fiction, _ = Category.objects.get_or_create(
            name='Classic Fiction',
            defaults={'description': 'Timeless works of fiction'}
        )
        
        philosophy, _ = Category.objects.get_or_create(
            name='Philosophy',
            defaults={'description': 'Philosophical works'}
        )
        
        science, _ = Category.objects.get_or_create(
            name='Science',
            defaults={'description': 'Scientific works'}
        )
        
        adventure, _ = Category.objects.get_or_create(
            name='Adventure',
            defaults={'description': 'Adventure and exploration'}
        )

        # Public domain books from Project Gutenberg
        books_data = [
            {
                'isbn': '978-0000000001',
                'title': 'Pride and Prejudice',
                'author': 'Jane Austen',
                'description': 'A romantic novel of manners that critiques the British landed gentry at the end of the 18th century.',
                'category': fiction,
                'gutenberg_id': '1342',
                'publication_date': date(1813, 1, 28),
                'pages': 432,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000002',
                'title': 'Alice\'s Adventures in Wonderland',
                'author': 'Lewis Carroll',
                'description': 'A young girl named Alice falls through a rabbit hole into a fantasy world of anthropomorphic creatures.',
                'category': fiction,
                'gutenberg_id': '11',
                'publication_date': date(1865, 11, 26),
                'pages': 200,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000003',
                'title': 'The Adventures of Sherlock Holmes',
                'author': 'Arthur Conan Doyle',
                'description': 'A collection of twelve short stories featuring the famous detective Sherlock Holmes.',
                'category': fiction,
                'gutenberg_id': '1661',
                'publication_date': date(1892, 10, 14),
                'pages': 307,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000004',
                'title': 'Frankenstein',
                'author': 'Mary Shelley',
                'description': 'A young scientist creates a sapient creature in an unorthodox scientific experiment.',
                'category': fiction,
                'gutenberg_id': '84',
                'publication_date': date(1818, 1, 1),
                'pages': 280,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000005',
                'title': 'Moby Dick',
                'author': 'Herman Melville',
                'description': 'The narrative of Captain Ahab\'s obsessive quest to kill the white whale Moby Dick.',
                'category': adventure,
                'gutenberg_id': '2701',
                'publication_date': date(1851, 10, 18),
                'pages': 635,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000006',
                'title': 'The Picture of Dorian Gray',
                'author': 'Oscar Wilde',
                'description': 'A philosophical novel about a young man who sells his soul for eternal youth and beauty.',
                'category': fiction,
                'gutenberg_id': '174',
                'publication_date': date(1890, 7, 1),
                'pages': 254,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000007',
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'description': 'A critique of the American Dream set in the Jazz Age.',
                'category': fiction,
                'gutenberg_id': '64317',
                'publication_date': date(1925, 4, 10),
                'pages': 180,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000008',
                'title': 'Dracula',
                'author': 'Bram Stoker',
                'description': 'An epistolary novel about the vampire Count Dracula\'s attempt to move to England.',
                'category': fiction,
                'gutenberg_id': '345',
                'publication_date': date(1897, 5, 26),
                'pages': 418,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000009',
                'title': 'The Adventures of Tom Sawyer',
                'author': 'Mark Twain',
                'description': 'A boy growing up along the Mississippi River in the 1840s.',
                'category': adventure,
                'gutenberg_id': '74',
                'publication_date': date(1876, 6, 1),
                'pages': 274,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000010',
                'title': 'The Metamorphosis',
                'author': 'Franz Kafka',
                'description': 'A man wakes up one morning to find himself transformed into a giant insect.',
                'category': fiction,
                'gutenberg_id': '5200',
                'publication_date': date(1915, 10, 1),
                'pages': 201,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000011',
                'title': 'A Tale of Two Cities',
                'author': 'Charles Dickens',
                'description': 'A historical novel set in London and Paris before and during the French Revolution.',
                'category': fiction,
                'gutenberg_id': '98',
                'publication_date': date(1859, 4, 30),
                'pages': 448,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000012',
                'title': 'The Wonderful Wizard of Oz',
                'author': 'L. Frank Baum',
                'description': 'A young girl is swept away to a magical land and must find her way home.',
                'category': adventure,
                'gutenberg_id': '55',
                'publication_date': date(1900, 5, 17),
                'pages': 259,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000013',
                'title': 'The Republic',
                'author': 'Plato',
                'description': 'A Socratic dialogue concerning justice and the order of the just city-state.',
                'category': philosophy,
                'gutenberg_id': '1497',
                'publication_date': date(1901, 1, 1),  # Original ~380 BC, using translation date
                'pages': 416,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000014',
                'title': 'The Prince',
                'author': 'Niccolò Machiavelli',
                'description': 'A political treatise on how to acquire and maintain political power.',
                'category': philosophy,
                'gutenberg_id': '1232',
                'publication_date': date(1532, 1, 1),
                'pages': 140,
                'language': 'en',
                'publisher': 'Public Domain',
            },
            {
                'isbn': '978-0000000015',
                'title': 'The Origin of Species',
                'author': 'Charles Darwin',
                'description': 'The foundation of evolutionary biology and natural selection.',
                'category': science,
                'gutenberg_id': '1228',
                'publication_date': date(1859, 11, 24),
                'pages': 502,
                'language': 'en',
                'publisher': 'Public Domain',
            },
        ]

        created = 0
        skipped = 0
        errors = 0

        for book_data in books_data:
            try:
                gutenberg_id = book_data.pop('gutenberg_id')
                
                # Check if book already exists
                if Book.objects.filter(isbn=book_data['isbn']).exists():
                    self.stdout.write(self.style.WARNING(f'Skipped: {book_data["title"]} (already exists)'))
                    skipped += 1
                    continue

                # Create book with 3 copies
                book = Book.objects.create(
                    **book_data,
                    total_copies=3,
                    available_copies=3
                )

                # Download cover image from Open Library
                try:
                    cover_url = f'https://covers.openlibrary.org/b/isbn/{book.isbn}-L.jpg'
                    response = requests.get(cover_url, timeout=10)
                    if response.status_code == 200:
                        book.cover_image.save(
                            f'{book.isbn}.jpg',
                            ContentFile(response.content),
                            save=False
                        )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Could not download cover: {str(e)}'))

                # Download PDF from Project Gutenberg
                try:
                    pdf_url = f'https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}-pdf.pdf'
                    self.stdout.write(f'  Downloading PDF from: {pdf_url}')
                    response = requests.get(pdf_url, timeout=30)
                    if response.status_code == 200:
                        book.pdf_file.save(
                            f'{book.isbn}.pdf',
                            ContentFile(response.content),
                            save=False
                        )
                        self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded'))
                    else:
                        # Try alternative URL format
                        pdf_url = f'https://www.gutenberg.org/ebooks/{gutenberg_id}.pdf.noimages'
                        response = requests.get(pdf_url, timeout=30)
                        if response.status_code == 200:
                            book.pdf_file.save(
                                f'{book.isbn}.pdf',
                                ContentFile(response.content),
                                save=False
                            )
                            self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded (alternative URL)'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Could not download PDF: {str(e)}'))

                book.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {book.title} by {book.author}'))
                created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error creating {book_data.get("title", "unknown")}: {str(e)}'))
                errors += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Created: {created} books'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped} books'))
        self.stdout.write(self.style.ERROR(f'Errors: {errors} books'))
        self.stdout.write('='*60)
        self.stdout.write('\nAll books are from Project Gutenberg and are in the public domain.')
        self.stdout.write('They are free to use, distribute, and modify.')
