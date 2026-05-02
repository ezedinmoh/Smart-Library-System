from django.core.management.base import BaseCommand
from apps.books.models import Category, Book
from apps.users.models import User
from django.core.files.base import ContentFile
import requests


class Command(BaseCommand):
    help = 'Seed database with software engineering books and download covers'

    def download_cover(self, isbn, title):
        """Download cover from Open Library or Google Books"""
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        
        # Try Open Library first
        url = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                return ContentFile(response.content), f"{clean_isbn}.jpg"
        except:
            pass
        
        # Try Google Books
        try:
            api_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    image_links = data["items"][0].get("volumeInfo", {}).get("imageLinks", {})
                    for size in ["extraLarge", "large", "medium", "thumbnail"]:
                        if size in image_links:
                            img_url = image_links[size].replace("http://", "https://")
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                return ContentFile(img_response.content), f"{clean_isbn}.jpg"
        except:
            pass
        
        return None, None

    def handle(self, *args, **options):
        # Delete existing books
        self.stdout.write(self.style.WARNING('Deleting existing books...'))
        Book.objects.all().delete()
        
        # Create categories
        categories_data = [
            {'name': 'Software Engineering', 'description': 'Software engineering principles and practices'},
            {'name': 'Programming', 'description': 'Programming languages and development'},
            {'name': 'Algorithms', 'description': 'Data structures and algorithms'},
            {'name': 'Web Development', 'description': 'Web technologies and frameworks'},
            {'name': 'Database', 'description': 'Database design and management'},
            {'name': 'DevOps', 'description': 'DevOps and system administration'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat.name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        # Software Engineering Books
        books_data = [
            {
                'isbn': '978-0134685991',
                'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'author': 'Robert C. Martin',
                'category': 'Software Engineering',
                'total_copies': 5,
                'publisher': 'Prentice Hall',
                'pages': 464,
                'description': 'Even bad code can function. But if code isn\'t clean, it can bring a development organization to its knees.',
                'language': 'en',
            },
            {
                'isbn': '978-0135957059',
                'title': 'The Pragmatic Programmer: Your Journey to Mastery',
                'author': 'David Thomas, Andrew Hunt',
                'category': 'Software Engineering',
                'total_copies': 4,
                'publisher': 'Addison-Wesley',
                'pages': 352,
                'description': 'The Pragmatic Programmer is one of those rare tech books you\'ll read, re-read, and read again over the years.',
                'language': 'en',
            },
            {
                'isbn': '978-0132350884',
                'title': 'Clean Architecture: A Craftsman\'s Guide to Software Structure',
                'author': 'Robert C. Martin',
                'category': 'Software Engineering',
                'total_copies': 4,
                'publisher': 'Prentice Hall',
                'pages': 432,
                'description': 'Building upon the success of best-sellers The Clean Coder and Clean Code, legendary software craftsman Robert C. Martin shows how to bring greater professionalism and discipline to application architecture.',
                'language': 'en',
            },
            {
                'isbn': '978-0201633610',
                'title': 'Design Patterns: Elements of Reusable Object-Oriented Software',
                'author': 'Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides',
                'category': 'Software Engineering',
                'total_copies': 3,
                'publisher': 'Addison-Wesley',
                'pages': 416,
                'description': 'Capturing a wealth of experience about the design of object-oriented software, four top-notch designers present a catalog of simple and succinct solutions to commonly occurring design problems.',
                'language': 'en',
            },
            {
                'isbn': '978-0137081073',
                'title': 'The Clean Coder: A Code of Conduct for Professional Programmers',
                'author': 'Robert C. Martin',
                'category': 'Software Engineering',
                'total_copies': 4,
                'publisher': 'Prentice Hall',
                'pages': 256,
                'description': 'In The Clean Coder, legendary software expert Robert C. Martin introduces the disciplines, techniques, tools, and practices of true software craftsmanship.',
                'language': 'en',
            },
            {
                'isbn': '978-0596007126',
                'title': 'Head First Design Patterns',
                'author': 'Eric Freeman, Elisabeth Robson',
                'category': 'Software Engineering',
                'total_copies': 5,
                'publisher': 'O\'Reilly Media',
                'pages': 694,
                'description': 'You\'ll learn how to use design patterns to solve common problems and create flexible, maintainable code.',
                'language': 'en',
            },
            {
                'isbn': '978-0132181273',
                'title': 'Domain-Driven Design: Tackling Complexity in the Heart of Software',
                'author': 'Eric Evans',
                'category': 'Software Engineering',
                'total_copies': 3,
                'publisher': 'Addison-Wesley',
                'pages': 560,
                'description': 'Eric Evans has written a fantastic book on how you can make the design of your software match your mental model of the problem domain you are addressing.',
                'language': 'en',
            },
            {
                'isbn': '978-0596517748',
                'title': 'JavaScript: The Good Parts',
                'author': 'Douglas Crockford',
                'category': 'Programming',
                'total_copies': 4,
                'publisher': 'O\'Reilly Media',
                'pages': 176,
                'description': 'Most programming languages contain good and bad parts, but JavaScript has more than its share of the bad.',
                'language': 'en',
            },
            {
                'isbn': '978-1491950296',
                'title': 'Building Microservices: Designing Fine-Grained Systems',
                'author': 'Sam Newman',
                'category': 'Software Engineering',
                'total_copies': 4,
                'publisher': 'O\'Reilly Media',
                'pages': 280,
                'description': 'Distributed systems have become more fine-grained in the past 10 years, shifting from code-heavy monolithic applications to smaller, self-contained microservices.',
                'language': 'en',
            },
            {
                'isbn': '978-0262033848',
                'title': 'Introduction to Algorithms',
                'author': 'Thomas H. Cormen, Charles E. Leiserson',
                'category': 'Algorithms',
                'total_copies': 5,
                'publisher': 'MIT Press',
                'pages': 1312,
                'description': 'Some books on algorithms are rigorous but incomplete; others cover masses of material but lack rigor. Introduction to Algorithms uniquely combines rigor and comprehensiveness.',
                'language': 'en',
            },
        ]

        total = len(books_data)
        success_count = 0
        
        for i, book_data in enumerate(books_data, 1):
            category_name = book_data.pop('category')
            category = categories.get(category_name)
            book_data['category'] = category
            book_data['available_copies'] = book_data['total_copies']
            
            self.stdout.write(f"\n[{i}/{total}] Processing: {book_data['title']}")
            
            # Try to download cover
            cover_content, cover_filename = self.download_cover(book_data['isbn'], book_data['title'])
            
            try:
                book, created = Book.objects.get_or_create(
                    isbn=book_data['isbn'],
                    defaults=book_data
                )
                
                if cover_content and cover_filename:
                    book.cover_image.save(cover_filename, cover_content, save=True)
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Book created with cover'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ✓ Book created (no cover found)'))
                
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'\n\nCompleted! {success_count}/{total} books added successfully.'))
