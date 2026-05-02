"""
Management command to download PDFs for books that don't have them
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.books.models import Book
import requests


class Command(BaseCommand):
    help = 'Download PDFs for books that are missing them'

    def handle(self, *args, **options):
        # Mapping of ISBN to Gutenberg ID for public domain books
        gutenberg_mapping = {
            '978-0000000001': '1342',   # Pride and Prejudice
            '978-0000000002': '11',     # Alice's Adventures in Wonderland
            '978-0000000003': '1661',   # The Adventures of Sherlock Holmes
            '978-0000000004': '84',     # Frankenstein
            '978-0000000005': '2701',   # Moby Dick
            '978-0000000006': '174',    # The Picture of Dorian Gray
            '978-0000000007': '64317',  # The Great Gatsby
            '978-0000000008': '345',    # Dracula
            '978-0000000009': '74',     # The Adventures of Tom Sawyer
            '978-0000000010': '5200',   # The Metamorphosis
            '978-0000000011': '98',     # A Tale of Two Cities
            '978-0000000012': '55',     # The Wonderful Wizard of Oz
            '978-0000000013': '1497',   # The Republic
            '978-0000000014': '1232',   # The Prince
            '978-0000000015': '1228',   # The Origin of Species
        }

        # Technical books PDF URLs
        tech_books_urls = {
            '978-0000100003': 'https://automatetheboringstuff.com/2e/automate-online.pdf',
            '978-0000100005': 'http://www.computingbook.org/FullText.pdf',
            '978-0000100007': 'https://github.com/diveintomark/diveintohtml5/raw/master/diveintohtml5.pdf',
            '978-0000100010': 'https://jakevdp.github.io/PythonDataScienceHandbook/PythonDataScienceHandbook.pdf',
            '978-0000200007': 'https://goalkicker.com/HTML5Book/HTML5NotesForProfessionals.pdf',
            '978-0000200008': 'https://goalkicker.com/CSSBook/CSSNotesForProfessionals.pdf',
            '978-0000200009': 'https://goalkicker.com/AlgorithmsBook/AlgorithmsNotesForProfessionals.pdf',
            '978-0000200010': 'https://goalkicker.com/ReactJSBook/ReactJSNotesForProfessionals.pdf',
            '978-0000300001': 'https://goalkicker.com/DesignPatternsBook/DesignPatternsNotesForProfessionals.pdf',
            '978-0000300002': 'https://goalkicker.com/ObjectOrientedProgrammingBook/ObjectOrientedProgrammingNotesForProfessionals.pdf',
            '978-0000300004': 'https://goalkicker.com/DockerBook/DockerNotesForProfessionals.pdf',
            '978-0000300010': 'https://goalkicker.com/DataStructuresBook/DataStructuresNotesForProfessionals.pdf',
            '978-0000300019': 'https://goalkicker.com/PandasBook/PandasNotesForProfessionals.pdf',
            '978-0000300020': 'https://goalkicker.com/NumPyBook/NumPyNotesForProfessionals.pdf',
        }

        books_without_pdf = Book.objects.filter(pdf_file='')
        total = books_without_pdf.count()
        
        self.stdout.write(f'Found {total} books without PDFs')
        
        success = 0
        failed = 0

        for book in books_without_pdf:
            self.stdout.write(f'\nProcessing: {book.title}')
            
            try:
                # Check if it's a Gutenberg book
                if book.isbn in gutenberg_mapping:
                    gutenberg_id = gutenberg_mapping[book.isbn]
                    
                    # Try multiple URL formats
                    urls_to_try = [
                        f'https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.pdf',
                        f'https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}-pdf.pdf',
                        f'https://www.gutenberg.org/ebooks/{gutenberg_id}.pdf.noimages',
                    ]
                    
                    downloaded = False
                    for pdf_url in urls_to_try:
                        try:
                            self.stdout.write(f'  Trying: {pdf_url}')
                            response = requests.get(pdf_url, timeout=60, allow_redirects=True)
                            
                            if response.status_code == 200 and len(response.content) > 1000:
                                book.pdf_file.save(
                                    f'{book.isbn}.pdf',
                                    ContentFile(response.content),
                                    save=True
                                )
                                self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded ({len(response.content) // 1024} KB)'))
                                success += 1
                                downloaded = True
                                break
                        except Exception as e:
                            continue
                    
                    if not downloaded:
                        self.stdout.write(self.style.WARNING(f'  ✗ All URLs failed'))
                        failed += 1
                
                # Check if it's a technical book
                elif book.isbn in tech_books_urls:
                    pdf_url = tech_books_urls[book.isbn]
                    
                    self.stdout.write(f'  Downloading: {pdf_url}')
                    response = requests.get(pdf_url, timeout=60, allow_redirects=True)
                    
                    if response.status_code == 200 and len(response.content) > 1000:
                        book.pdf_file.save(
                            f'{book.isbn}.pdf',
                            ContentFile(response.content),
                            save=True
                        )
                        self.stdout.write(self.style.SUCCESS(f'  ✓ PDF downloaded ({len(response.content) // 1024} KB)'))
                        success += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'  ✗ Failed (status: {response.status_code})'))
                        failed += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  ✗ No PDF URL mapping found'))
                    failed += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                failed += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Success: {success} PDFs downloaded'))
        self.stdout.write(self.style.ERROR(f'Failed: {failed} PDFs'))
        self.stdout.write('='*60)
