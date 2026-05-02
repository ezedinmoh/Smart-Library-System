from django.core.management.base import BaseCommand
from django.db.models import Avg
from apps.books.models import Book


class Command(BaseCommand):
    help = 'Fix book ratings to match actual reviews. Resets rating to 0 for books with no reviews.'

    def handle(self, *args, **options):
        books = Book.objects.prefetch_related('reviews').all()
        fixed = 0

        for book in books:
            review_count = book.reviews.count()

            if review_count == 0:
                correct_rating = 0.00
            else:
                avg = book.reviews.aggregate(Avg('rating'))['rating__avg']
                correct_rating = round(avg, 2) if avg else 0.00

            if book.rating != correct_rating:
                self.stdout.write(
                    f'  Fixing "{book.title}": {book.rating} → {correct_rating} '
                    f'({review_count} review{"s" if review_count != 1 else ""})'
                )
                book.rating = correct_rating
                Book.objects.filter(pk=book.pk).update(rating=correct_rating)
                fixed += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Fixed {fixed} book{"s" if fixed != 1 else ""}.'
        ))
