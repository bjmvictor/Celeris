from django.db import migrations


IMPLEMENTED_ACCESS_KEYS = {
    "atendimento:atendimentos",
    "atendimento:fila-medica",
    "atendimento:pep",
    "atendimento:demanda-espontanea",
}


def activate_implemented_screens(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=IMPLEMENTED_ACCESS_KEYS).update(active=True)


def restore_legacy_state(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(access_key__in=IMPLEMENTED_ACCESS_KEYS).update(active=False)


class Migration(migrations.Migration):
    dependencies = [("core", "0041_normalizar_destinos_navegacao")]

    operations = [migrations.RunPython(activate_implemented_screens, restore_legacy_state)]
