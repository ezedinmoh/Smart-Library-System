"""
Management command to add books for empty categories
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book, Category
import requests
from datetime import date


class Command(BaseCommand):
    help = 'Add books for empty categories'

    def handle(self, *args, **options):
        # Get or create categories
        software_eng, _ = Category.objects.get_or_create(
            name='Software Engineering',
            defaults={'description': 'Software engineering principles and practices'}
        )
        
        devops, _ = Category.objects.get_or_create(
            name='DevOps',
            defaults={'description': 'DevOps, CI/CD, and deployment'}
        )
        
        database, _ = Category.objects.get_or_create(
            name='Database',
            defaults={'description': 'Database design and management'}
        )
        
        algorithms, _ = Category.objects.get_or_create(
            name='Algorithms',
            defaults={'description': 'Algorithms and data structures'}
        )
        
        technology, _ = Category.objects.get_or_create(
            name='Technology',
            defaults={'description': 'Technology and computing'}
        )
        
        mathematics, _ = Category.objects.get_or_create(
            name='Mathematics',
            defaults={'description': 'Mathematics for programming'}
        )
        
        data_science, _ = Category.objects.get_or_create(
            name='Data Science',
            defaults={'description': 'Data science and machine learning'}
        )
        
        fiction, _ = Category.objects.get_or_create(
            name='Fiction',
            defaults={'description': 'Fiction and literature'}
        )

        # Books data with verified PDF links from GoalKicker and other sources
        books_data = [
            # Software Engineering (3 books)
            {
                'isbn': '978-0000300001',
                'title': 'Design Patterns Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive guide to software design patterns and best practices.',
                'category': software_eng,
                'pdf_url': 'https://goalkicker.com/DesignPatternsBook/DesignPatternsNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 150,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300002',
                'title': 'Object Oriented Programming Notes',
                'author': 'GoalKicker.com',
                'description': 'Object-oriented programming concepts and principles.',
                'category': software_eng,
                'pdf_url': 'https://goalkicker.com/ObjectOrientedProgrammingBook/ObjectOrientedProgrammingNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 120,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300003',
                'title': '.NET Framework Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete guide to .NET Framework development.',
                'category': software_eng,
                'pdf_url': 'https://goalkicker.com/DotNETFrameworkBook/DotNETFrameworkNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 300,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # DevOps (3 books)
            {
                'isbn': '978-0000300004',
                'title': 'Docker Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Complete guide to Docker containerization and deployment.',
                'category': devops,
                'pdf_url': 'https://goalkicker.com/DockerBook/DockerNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 100,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300005',
                'title': 'Bash Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Shell scripting and Bash programming guide.',
                'category': devops,
                'pdf_url': 'https://goalkicker.com/BashBook/BashNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 150,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300006',
                'title': 'PowerShell Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'PowerShell scripting and automation guide.',
                'category': devops,
                'pdf_url': 'https://goalkicker.com/PowerShellBook/PowerShellNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Database (3 books)
            {
                'isbn': '978-0000300007',
                'title': 'MongoDB Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'NoSQL database development with MongoDB.',
                'category': database,
                'pdf_url': 'https://goalkicker.com/MongoDBBook/MongoDBNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 100,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300008',
                'title': 'MySQL Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Relational database management with MySQL.',
                'category': database,
                'pdf_url': 'https://goalkicker.com/MySQLBook/MySQLNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 150,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300009',
                'title': 'PostgreSQL Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Advanced PostgreSQL database development.',
                'category': database,
                'pdf_url': 'https://goalkicker.com/PostgreSQLBook/PostgreSQLNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 130,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Algorithms (3 books)
            {
                'isbn': '978-0000300010',
                'title': 'Data Structures Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Comprehensive guide to data structures and their implementations.',
                'category': algorithms,
                'pdf_url': 'https://goalkicker.com/DataStructuresBook/DataStructuresNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 120,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300011',
                'title': 'R Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Statistical computing and data analysis with R.',
                'category': algorithms,
                'pdf_url': 'https://goalkicker.com/RBook/RNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 400,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300012',
                'title': 'MATLAB Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'MATLAB programming for numerical computing and algorithms.',
                'category': algorithms,
                'pdf_url': 'https://goalkicker.com/MATLABBook/MATLABNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 100,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Technology (3 books)
            {
                'isbn': '978-0000300013',
                'title': 'Android Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Android app development guide.',
                'category': technology,
                'pdf_url': 'https://goalkicker.com/AndroidBook/AndroidNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 500,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300014',
                'title': 'iOS Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'iOS app development with Swift and Objective-C.',
                'category': technology,
                'pdf_url': 'https://goalkicker.com/iOSBook/iOSNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300015',
                'title': 'Node.js Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Server-side JavaScript development with Node.js.',
                'category': technology,
                'pdf_url': 'https://goalkicker.com/NodeJSBook/NodeJSNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 300,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Mathematics (3 books)
            {
                'isbn': '978-0000300016',
                'title': 'LaTeX Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Document preparation and mathematical typesetting with LaTeX.',
                'category': mathematics,
                'pdf_url': 'https://goalkicker.com/LaTeXBook/LaTeXNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 100,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300017',
                'title': 'Excel VBA Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Excel VBA programming for data analysis and automation.',
                'category': mathematics,
                'pdf_url': 'https://goalkicker.com/ExcelVBABook/ExcelVBANotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 200,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300018',
                'title': 'Haskell Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Functional programming with Haskell.',
                'category': mathematics,
                'pdf_url': 'https://goalkicker.com/HaskellBook/HaskellNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 100,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Data Science (2 books)
            {
                'isbn': '978-0000300019',
                'title': 'Pandas Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Data analysis and manipulation with Python Pandas.',
                'category': data_science,
                'pdf_url': 'https://goalkicker.com/PandasBook/PandasNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 80,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300020',
                'title': 'NumPy Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Numerical computing with Python NumPy.',
                'category': data_science,
                'pdf_url': 'https://goalkicker.com/NumPyBook/NumPyNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 50,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            
            # Fiction (2 books)
            {
                'isbn': '978-0000300021',
                'title': 'Kotlin Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'Modern programming with Kotlin language.',
                'category': technology,
                'pdf_url': 'https://goalkicker.com/KotlinBook/KotlinNotesForProfessionals.pdf',
                'publication_date': date(2023, 1, 1),
                'pages': 150,
                'language': 'en',
                'publisher': 'GoalKicker (CC BY-SA)',
            },
            {
                'isbn': '978-0000300022',
                'title': 'Swift Notes for Professionals',
                'author': 'GoalKicker.com',
                'description': 'iOS and macOS development with Swift.',
                'category': technology,
                'pdf_url': 'https://goalkicker.com/SwiftBook/SwiftNotesForProfessionals.pdf',
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

                # Download PDF
                try:
                    self.stdout.write(f'  Downloading PDF: {book.title}')
                    response = requests.get(pdf_url, timeout=60, allow_redirects=True)
                    if response.status_code == 200 and len(response.content) > 1000:
                        book.pdf_file.save(
                            f'{book.isbn}.pdf',
                            ContentFile(response.content),
                            save=False
                        )
                        self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded ({len(response.content) // 1024} KB)'))
                    else:
                        self.stdout.write(self.style.WARNING(f'  ✗ PDF download failed'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ✗ PDF error: {str(e)}'))

                book.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {book.title}'))
                created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {book_data.get("title", "unknown")}: {str(e)}'))
                errors += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Created: {created} books'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped} books'))
        self.stdout.write(self.style.ERROR(f'Errors: {errors} books'))
        self.stdout.write('='*60)
