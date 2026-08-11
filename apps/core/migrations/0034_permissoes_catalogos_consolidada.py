import django.db.migrations.operations.special
from importlib import import_module

from django.db import migrations

migracao_0034 = import_module("apps.core.operacoes_migracao.operacao_0034")
migracao_0035 = import_module("apps.core.operacoes_migracao.operacao_0035")
migracao_0036 = import_module("apps.core.operacoes_migracao.operacao_0036")
migracao_0037 = import_module("apps.core.operacoes_migracao.operacao_0037")

class Migration(migrations.Migration):

    replaces = [('core', '0034_sync_navigation_roles'), ('core', '0035_normalize_navigation_catalog'), ('core', '0036_normalizar_catalogos_iniciais'), ('core', '0037_mesclar_grupos_navegacao_duplicados')]

    dependencies = [
        ('accounts', '0015_sync_navigation_role_catalog'),
        ('core', '0033_navigation_tree'),
    ]

    operations = [
        migrations.RunPython(
            code=migracao_0034.sync_navigation_roles,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0035.normalize_navigation_catalog,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0037.mesclar_grupos_navegacao,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
