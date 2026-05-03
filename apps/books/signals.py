from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Book
import logging

logger = logging.getLogger(__name__)


def _delete_file(field):
    """Delete a file from whatever storage backend is active (local or Cloudinary)."""
    if not field:
        return
    try:
        storage = field.storage
        name = field.name
        if name and storage.exists(name):
            storage.delete(name)
    except Exception as e:
        logger.warning(f"Could not delete file {getattr(field, 'name', '?')}: {e}")


@receiver(pre_save, sender=Book)
def delete_old_book_files(sender, instance, **kwargs):
    """Delete old cover image and PDF from storage when they are replaced."""
    if not instance.pk:
        return  # new book — nothing to delete
    try:
        old = Book.objects.get(pk=instance.pk)
    except Book.DoesNotExist:
        return

    if old.cover_image and old.cover_image != instance.cover_image:
        _delete_file(old.cover_image)

    if old.pdf_file and old.pdf_file != instance.pdf_file:
        _delete_file(old.pdf_file)


@receiver(post_delete, sender=Book)
def delete_book_files_on_delete(sender, instance, **kwargs):
    """Delete cover image and PDF from storage when the book is deleted."""
    _delete_file(instance.cover_image)
    _delete_file(instance.pdf_file)
