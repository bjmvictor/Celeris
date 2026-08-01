"""Operações históricas de dados da migration 0031."""

from django.db import migrations


MODULOS_NAO_IMPLEMENTADOS = {"COMPRAS", "FINANCEIRO", "RH"}


def desativar_modulos(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Module.objects.filter(code__in=MODULOS_NAO_IMPLEMENTADOS).update(active=False)
    ScreenDefinition.objects.filter(module__code__in=MODULOS_NAO_IMPLEMENTADOS).update(active=False)


def reativar_modulos(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Module.objects.filter(code__in=MODULOS_NAO_IMPLEMENTADOS).update(active=True)
    ScreenDefinition.objects.filter(module__code__in=MODULOS_NAO_IMPLEMENTADOS).update(active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_trava_edicao"),
    ]

    operations = [
        migrations.RunPython(desativar_modulos, reativar_modulos),
    ]
