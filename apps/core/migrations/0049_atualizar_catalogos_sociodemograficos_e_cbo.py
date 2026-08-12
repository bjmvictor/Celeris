from importlib import import_module

from django.db import migrations


catalogos_paciente = import_module("apps.core.operacoes_migracao.operacao_0011")
catalogo_cbo = import_module("apps.core.operacoes_migracao.operacao_0012")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_alter_valorauxiliarglobal_ds_grupo_and_more"),
    ]

    operations = [
        migrations.RunPython(catalogos_paciente.seed, migrations.RunPython.noop),
        migrations.RunPython(catalogo_cbo.seed_cbo, migrations.RunPython.noop),
    ]
