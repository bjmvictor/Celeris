from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import IconeSistema, Module, ScreenDefinition
from .navigation_cache import invalidate_navigation_cache


@receiver(post_save, sender=Module)
@receiver(post_delete, sender=Module)
@receiver(post_save, sender=ScreenDefinition)
@receiver(post_delete, sender=ScreenDefinition)
@receiver(post_save, sender=IconeSistema)
@receiver(post_delete, sender=IconeSistema)
def navigation_catalog_changed(**kwargs):
    invalidate_navigation_cache()
