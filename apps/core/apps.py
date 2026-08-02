from django.apps import AppConfig
from importlib import import_module


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Base"

    def ready(self):
        import_module("apps.core.signals")
