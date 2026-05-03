from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import User, UserProfile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the user's profile when the user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


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


@receiver(pre_save, sender=UserProfile)
def delete_old_profile_picture(sender, instance, **kwargs):
    """Delete the old profile picture from storage when it is replaced."""
    if not instance.pk:
        return  # new record — nothing to delete
    try:
        old = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return
    if old.profile_picture and old.profile_picture != instance.profile_picture:
        _delete_file(old.profile_picture)


@receiver(post_delete, sender=UserProfile)
def delete_profile_picture_on_delete(sender, instance, **kwargs):
    """Delete the profile picture from storage when the profile is deleted."""
    _delete_file(instance.profile_picture)
