from django.db import migrations


LEGACY_DUPLICATE_SLUGS = {"pacientes-cadastro", "cadastros-profissionais"}


def normalize_navigation_destinations(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    ScreenDefinition.objects.filter(slug__in=LEGACY_DUPLICATE_SLUGS).update(active=False)

    missing = (
        ScreenDefinition.objects.exclude(screen_type="grupo")
        .filter(access_key__isnull=True, navigation_url="")
        .order_by("pk")
    )
    for screen in missing:
        screen.access_key = f"/telas/{screen.slug}/"
        screen.save(update_fields=("access_key",))


def restore_legacy_destinations(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(slug__in=LEGACY_DUPLICATE_SLUGS).update(active=True)
    ScreenDefinition.objects.filter(access_key__startswith="/telas/").update(access_key=None)


class Migration(migrations.Migration):
    dependencies = [("core", "0040_modulos_estruturais")]

    operations = [
        migrations.RunPython(normalize_navigation_destinations, restore_legacy_destinations),
    ]
