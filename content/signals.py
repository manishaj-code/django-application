"""Remove image files from storage when they are replaced or their row is deleted."""

from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Content


def _delete_file_on_commit(file_field):
    if not file_field:
        return
    storage, name = file_field.storage, file_field.name
    transaction.on_commit(lambda: storage.delete(name))


@receiver(post_delete, sender=Content)
def delete_image_with_content(sender, instance, **kwargs):
    _delete_file_on_commit(instance.featured_image)


@receiver(pre_save, sender=Content)
def delete_replaced_image(sender, instance, **kwargs):
    if not instance.pk:
        return
    old = sender.objects.filter(pk=instance.pk).values_list("featured_image", flat=True).first()
    if old and old != instance.featured_image.name:
        _delete_file_on_commit(sender(pk=instance.pk, featured_image=old).featured_image)
