from importlib import import_module

from django.db import migrations


migracao_0015 = import_module("apps.accounts.migrations.0015_sync_navigation_role_catalog")


class Migration(migrations.Migration):
    replaces = [("accounts", "0015_sync_navigation_role_catalog")]

    dependencies = [
        ("accounts", "0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more"),
        ("core", "0030_trava_edicao"),
    ]

    operations = [
        migrations.RunPython(migracao_0015.sync_catalog, migrations.RunPython.noop),
    ]
