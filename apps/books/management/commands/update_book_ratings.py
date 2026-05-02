from django.core.management.base import BaseCommand
from django.db.models import Avg
from apps.books.models import Book


class Command(BaseCommand):
    help = 'Update book ratings based on reviews'

    def handle(self, *args, **options):
        books = Book.objects.all()
        updated_count = 0
        
        for book in books:
            reviews = book.reviews.all()
            if reviews.exists():
                avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
                if avg_rating:
                    book.rating = round(avg_rating, 2)
                    book.save(update_fields=['rating'])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated rating for "{book.title}": {book.rating}'
                        )
                    )
            else:
                if book.rating != 0:
                    book.rating = 0
                    book.save(update_fields=['rating'])
                    self.stdout.write(
                        self.style.WARNING(
                            f'Reset rating for "{book.title}" (no reviews)'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully updated ratings for {updated_count} books'
            )
        )
