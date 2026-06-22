from django.db import migrations


def sync_ti_access(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    group, _ = Group.objects.get_or_create(name="TI")
    role, _ = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
    for screen in ScreenDefinition.objects.filter(active=True, module__active=True).exclude(access_key__isnull=True):
        PapelModulo.objects.get_or_create(papel=role, modulo=screen.module)
        PapelTela.objects.get_or_create(papel=role, tela=screen)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_populate_dynamic_screen_access_keys"),
        ("accounts", "0009_seed_role_access"),
    ]

    operations = [
        migrations.RunPython(sync_ti_access, migrations.RunPython.noop),
    ]
