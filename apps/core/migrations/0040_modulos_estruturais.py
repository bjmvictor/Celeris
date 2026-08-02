from django.db import migrations, models


SYSTEM_MODULE_CODES = {"GLOBAL", "TI"}


def protect_system_modules(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Module.objects.filter(code__in=SYSTEM_MODULE_CODES).update(is_system=True)


def unprotect_system_modules(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Module.objects.filter(code__in=SYSTEM_MODULE_CODES).update(is_system=False)


class Migration(migrations.Migration):
    dependencies = [("core", "0039_icones_sistema")]

    operations = [
        migrations.AddField(
            model_name="module",
            name="is_system",
            field=models.BooleanField(
                default=False,
                help_text="Impede alterações pela interface de configuração.",
                verbose_name="módulo estrutural",
            ),
        ),
        migrations.RunPython(protect_system_modules, unprotect_system_modules),
    ]
