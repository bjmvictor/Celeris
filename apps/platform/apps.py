from django.apps import AppConfig


class PlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.platform"
    verbose_name = "Platform"

    def ready(self):
        # Importing this module only installs a post_migrate hook.  It does not
        # import individual applications, which keeps the platform independent.
        from .registry import install_catalog_sync

        install_catalog_sync()
