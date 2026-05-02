"""
Management command to seed database with free technical/programming books
These books are legally free to use under various open licenses
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book, Category
import requests
from datetime import date


class Command(BaseCommand):
    help = 'Seed database with free technical and programming books'

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

        # Free technical books with direct PDF links
        books_data = [
            {
                'isbn': '978-0000100001',
                'title': 'Eloquent JavaScript',
                'author': 'Marijn Haverbeke',
                'description': 'A modern introduction to programming with JavaScript, covering the language, browser programming, and Node.js.',
                'category': programming,
                'pdf_url': 'https://eloquentjavascript.net/Eloquent_JavaScript.pdf',
                'publication_date': date(2018, 12, 4),
                'pages': 472,
                'language': 'en',
                'publisher': 'No Starch Press (Open Source)',
            },
            {
                'isbn': '978-0000100002',
                'title': 'Think Python: How to Think Like a Computer Scientist',
                'author': 'Allen B. Downey',
                'description': 'An introduction to Python programming for beginners, emphasizing problem-solving and computational thinking.',
                'category': programming,
                'pdf_url': 'https://greenteapress.com/thinkpython2/thinkpython2.pdf',
                'publication_date': date(2015, 8, 1),
                'pages': 292,
                'language': 'en',
                'publisher': 'Green Tea Press (CC BY-NC)',
            },
            {
                'isbn': '978-0000100003',
                'title': 'Automate the Boring Stuff with Python',
                'author': 'Al Sweigart',
                'description': 'Practical programming for total beginners. Learn to write programs that do in minutes what would take hours to do by hand.',
                'category': programming,
                'pdf_url': 'https://automatetheboringstuff.com/2e/automate-online.pdf',
                'publication_date': date(2019, 11, 12),
                'pages': 592,
                'language': 'en',
                'publisher': 'No Starch Press (CC BY-NC-SA)',
            },
            {
                'isbn': '978-0000100004',
                'title': 'Pro Git',
                'author': 'Scott Chacon and Ben Straub',
                'description': 'The entire Pro Git book, written by Scott Chacon and Ben Straub. Everything you need to know about Git.',
                'category': programming,
                'pdf_url': 'https://github.com/progit/progit2/releases/download/2.1.360/progit.pdf',
                'publication_date': date(2014, 11, 18),
                'pages': 574,
                'language': 'en',
                'publisher': 'Apress (CC BY-NC-SA)',
            },
            {
                'isbn': '978-0000100005',
                'title': 'Introduction to Computing',
                'author': 'David Evans',
                'description': 'An introduction to computer science using Python, covering fundamental concepts and problem-solving.',
                'category': computer_science,
                'pdf_url': 'http://www.computingbook.org/FullText.pdf',
                'publication_date': date(2011, 8, 1),
                'pages': 350,
                'language': 'en',
                'publisher': 'University of Virginia (CC BY-NC-SA)',
            },
            {
                'isbn': '978-0000100006',
                'title': 'The Linux Command Line',
                'author': 'William Shotts',
                'description': 'A complete introduction to the Linux command line. Learn the shell and command-line tools.',
                'category': computer_science,
                'pdf_url': 'https://sourceforge.net/projects/linuxcommand/files/TLCL/19.01/TLCL-19.01.pdf/download',
                'publication_date': date(2019, 1, 28),
                'pages': 540,
                'language': 'en',
                'publisher': 'No Starch Press (CC BY-NC-ND)',
            },
            {
                'isbn': '978-0000100007',
                'title': 'Dive Into HTML5',
                'author': 'Mark Pilgrim',
                'description': 'An elaboration on HTML5 and its features, with practical examples and best practices.',
                'category': web_dev,
                'pdf_url': 'https://github.com/diveintomark/diveintohtml5/raw/master/diveintohtml5.pdf',
                'publication_date': date(2010, 8, 1),
                'pages': 280,
                'language': 'en',
                'publisher': 'O\'Reilly (CC BY)',
            },
            {
                'isbn': '978-0000100008',
                'title': 'Structure and Interpretation of Computer Programs',
                'author': 'Harold Abelson and Gerald Jay Sussman',
                'description': 'A classic computer science textbook teaching fundamental principles of computer programming.',
                'category': computer_science,
                'pdf_url': 'https://web.mit.edu/6.001/6.037/sicp.pdf',
                'publication_date': date(1996, 7, 25),
                'pages': 688,
                'language': 'en',
                'publisher': 'MIT Press (CC BY-SA)',
            },
            {
                'isbn': '978-0000100009',
                'title': 'Think Data Structures',
                'author': 'Allen B. Downey',
                'description': 'Algorithms and information retrieval in Java. Learn about data structures and their implementations.',
                'category': computer_science,
                'pdf_url': 'https://greenteapress.com/thinkdast/thinkdast.pdf',
                'publication_date': date(2017, 7, 1),
                'pages': 155,
                'language': 'en',
                'publisher': 'Green Tea Press (CC BY-NC)',
            },
            {
                'isbn': '978-0000100010',
                'title': 'Python Data Science Handbook',
                'author': 'Jake VanderPlas',
                'description': 'Essential tools for working with data in Python: NumPy, Pandas, Matplotlib, Scikit-Learn.',
                'category': data_science,
                'pdf_url': 'https://jakevdp.github.io/PythonDataScienceHandbook/PythonDataScienceHandbook.pdf',
                'publication_date': date(2016, 11, 21),
                'pages': 541,
                'language': 'en',
                'publisher': 'O\'Reilly (CC0)',
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

                # Create book with 5 copies (digital books can have more)
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
                        self.stdout.write(self.style.WARNING(f'  Could not download PDF (status: {response.status_code})'))
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
        self.stdout.write('\nAll books are free and open-source under various licenses.')
        self.stdout.write('They are free to use for educational purposes.')
