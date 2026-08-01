"""Operações históricas de dados da migration 0034."""

from django.db import migrations


def sync_navigation_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    for screen in ScreenDefinition.objects.filter(active=True).exclude(access_key__isnull=True).exclude(access_key=""):
        for role_name in screen.roles or []:
            group, _ = Group.objects.get_or_create(name=role_name)
            role, _ = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=role, modulo=screen.module)
            PapelTela.objects.get_or_create(papel=role, tela=screen)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_sync_navigation_role_catalog"),
        ("core", "0033_navigation_tree"),
    ]

    operations = [
        migrations.RunPython(sync_navigation_roles, migrations.RunPython.noop),
    ]
