from django.apps import AppConfig


class AtendimentoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.atendimento"
    verbose_name = "Atendimento"

    def ready(self):
        from . import signals  # noqa: F401
