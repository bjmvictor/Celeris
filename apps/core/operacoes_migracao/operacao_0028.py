"""Operações históricas de dados da migration 0028."""

from django.db import migrations


ACCESS_KEYS_REMOVIDAS = {
    "atendimento:atendimentos",
}


def desativar_telas(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=ACCESS_KEYS_REMOVIDAS).update(active=False)


def reativar_telas(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=ACCESS_KEYS_REMOVIDAS).update(active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0027_desativar_telas_substituidas_pelo_pep"),
    ]

    operations = [
        migrations.RunPython(desativar_telas, reativar_telas),
    ]
