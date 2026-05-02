"""
Management command to add more technical/programming books with verified PDF links
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book, Category
import requests
from datetime import date


class Command(BaseCommand):
    help = 'Add more technical and programming books with verified PDF links'

    def handle(self, *args, **options):
        # Create categories
        programming, _ = Category.objects.get_or_create(
            name='Programming',
            defaults={'description': 'Programming and software development'}
        )
        
        computer_science, _ = Category.objects.get_or_create(
            name='Computer Science',
            defaults={'description': 'Computer science fundamentals'}
        )
        
        web_dev, _ = Category.objects.get_or_create(
            name='Web Development',
            defaults={'description': 'Web development and design'}
        )
        
        data_science, _ = Category.objects.get_or_create(
            name='Data Science',
            defaults={'description': 'Data science and machine learning'}
        )

        # Technical books with verified PDF links
        books_data = [
            {
                'isbn': '978-0000200001',
                'title': 'Python Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive Python programming guide with over 700 pages covering beginner to advanced topics.',
                'category': programming,
                'pdf_url': 'https://goalkicker.com/PythonBook/PythonNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 700,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200002',
                'title': 'JavaScript Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete JavaScript guide with over 400 pages covering modern JavaScript development.',
                'category': web_dev,
                'pdf_url': 'https://goalkicker.com/JavaScriptBook/JavaScriptNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 400,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200003',
                'title': 'Java Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive Java programming guide with over 900 pages covering all aspects of Java development.',
                'category': programming,
                'pdf_url': 'https://goalkicker.com/JavaBook/JavaNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 900,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200004',
                'title': 'C++ Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete C++ programming guide covering modern C++ features and best practices.',
                'category': programming,
                'pdf_url': 'https://goalkicker.com/CPlusPlusBook/CPlusPlusNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 700,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200005',
                'title': 'SQL Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive SQL guide covering database queries, optimization, and best practices.',
                'category': data_science,
                'pdf_url': 'https://goalkicker.com/SQLBook/SQLNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 300,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200006',
                'title': 'Git Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete guide to Git version control system with practical examples and workflows.',
                'category': computer_science,
                'pdf_url': 'https://goalkicker.com/GitBook/GitNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200007',
                'title': 'HTML5 Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Modern HTML5 guide covering semantic markup, APIs, and web standards.',
                'category': web_dev,
                'pdf_url': 'https://goalkicker.com/HTML5Book/HTML5NotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 250,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200008',
                'title': 'CSS Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive CSS guide covering layouts, animations, and modern CSS features.',
                'category': web_dev,
                'pdf_url': 'https://goalkicker.com/CSSBook/CSSNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 300,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200009',
                'title': 'Algorithms Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Data structures and algorithms guide with implementations and complexity analysis.',
                'category': computer_science,
                'pdf_url': 'https://goalkicker.com/AlgorithmsBook/AlgorithmsNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000200010',
                'title': 'React JS Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete React.js guide covering components, hooks, state management, and best practices.',
                'category': web_dev,
                'pdf_url': 'https://goalkicker.com/ReactJSBook/ReactJSNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
        ]

        created = 0
        skipped = 0
        errors = 0

        for book_data in books_data:
            try:
                pdf_url = book_data.pop('pdf_url')
                
                # Check if book already exists
                if Book.objects.filter(isbn=book_data['isbn']).exists():
                    self.stdout.write(self.style.WARNING(f'Skipped: {book_data["title"]} (already exists)'))
                    skipped += 1
                    continue

                # Create book with 5 copies
                book = Book.objects.create(
                    **book_data,
                    total_copies=5,
                    available_copies=5
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

                # Download PDF
                try:
                    self.stdout.write(f'  Downloading PDF from: {pdf_url}')
                    response = requests.get(pdf_url, timeout=60, allow_redirects=True)
                    if response.status_code == 200 and len(response.content) > 1000:
                        book.pdf_file.save(
                            f'{book.isbn}.pdf',
                            ContentFile(response.content),
                            save=False
                        )
                        self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded ({len(response.content) // 1024} KB)'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  ✗ Could not download PDF (status: {response.status_code})'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ✗ Could not download PDF: {str(e)}'))

                book.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {book.title}'))
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
        self.stdout.write('\nAll books are from GoalKicker.com and are free under CC BY-SA license.')
