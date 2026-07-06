from django.db import migrations


ACCESS_KEYS_REMOVIDAS = {
    "atendimento:fila-medica",
    "atendimento:demanda-espontanea",
}


def desativar_telas(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=ACCESS_KEYS_REMOVIDAS).update(active=False)


def reativar_telas(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=ACCESS_KEYS_REMOVIDAS).update(active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_sync_recent_role_screens"),
        ("core", "0026_restaurar_obrigatorios_escala"),
    ]

    operations = [
        migrations.RunPython(desativar_telas, reativar_telas),
    ]
