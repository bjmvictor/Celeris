from importlib import import_module

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Contas"

    def ready(self):
        import_module("apps.accounts.signals")
