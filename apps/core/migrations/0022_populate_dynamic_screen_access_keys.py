from django.db import migrations


def populate_access_keys(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    for screen in ScreenDefinition.objects.filter(access_key__isnull=True).exclude(
        slug__in={"pacientes-cadastro", "cadastros-profissionais"}
    ):
        screen.access_key = f"/telas/{screen.slug}/"
        screen.save(update_fields=["access_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0021_screendefinition_access_key"),
    ]

    operations = [
        migrations.RunPython(populate_access_keys, migrations.RunPython.noop),
    ]
