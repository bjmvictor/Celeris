import django.db.migrations.operations.special
from importlib import import_module

from django.db import migrations

migracao_0026 = import_module("apps.core.operacoes_migracao.operacao_0026")
migracao_0027 = import_module("apps.core.operacoes_migracao.operacao_0027")
migracao_0028 = import_module("apps.core.operacoes_migracao.operacao_0028")
migracao_0029 = import_module("apps.core.operacoes_migracao.operacao_0029")

class Migration(migrations.Migration):

    replaces = [('core', '0026_restaurar_obrigatorios_escala'), ('core', '0027_desativar_telas_substituidas_pelo_pep'), ('core', '0028_desativar_tela_atendimentos_pep'), ('core', '0029_seed_cids_motivos_alta')]

    dependencies = [
        ('accounts', '0013_sync_recent_role_screens'),
        ('atendimento', '0037_totem_senhas'),
        ('core', '0025_configuracao_campo_formulario'),
    ]

    operations = [
        migrations.RunPython(
            code=migracao_0026.restaurar_obrigatorios_escala,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0027.desativar_telas,
            reverse_code=migracao_0027.reativar_telas,
        ),
        migrations.RunPython(
            code=migracao_0028.desativar_telas,
            reverse_code=migracao_0028.reativar_telas,
        ),
        migrations.RunPython(
            code=migracao_0029.seed_cids,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0029.seed_motivos_alta,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
