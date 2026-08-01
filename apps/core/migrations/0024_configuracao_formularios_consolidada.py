import django.db.migrations.operations.special
import django.db.models.deletion
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0024 = import_module("apps.core.migrations.0024_refresh_minimum_auxiliary_values")
migracao_0025 = import_module("apps.core.migrations.0025_configuracao_campo_formulario")

class Migration(migrations.Migration):

    replaces = [('core', '0024_refresh_minimum_auxiliary_values'), ('core', '0025_configuracao_campo_formulario')]

    dependencies = [
        ('accounts', '0013_sync_recent_role_screens'),
        ('core', '0023_seed_minimum_test_auxiliary_values'),
    ]

    operations = [
        migrations.RunPython(
            code=migracao_0024.remover_valores_teste_legados,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name='ConfiguracaoCampoFormulario',
            fields=[
                ('cd_configuracao_campo_formulario', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_formulario', models.CharField(max_length=80)),
                ('cd_campo', models.CharField(max_length=120)),
                ('sn_obrigatorio', models.BooleanField(default=False)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.CASCADE, related_name='configuracoes_campos_formularios', to='accounts.empresa')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, db_column='cd_usuario_atualizacao', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='configuracoes_formularios_atualizadas', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, db_column='cd_usuario_criacao', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='configuracoes_formularios_criadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'configuracao_campo_formulario',
                'ordering': ('cd_formulario', 'cd_campo'),
                'unique_together': {('cd_empresa', 'cd_formulario', 'cd_campo')},
            },
        ),
        migrations.RunPython(
            code=migracao_0025.cadastrar_tela_configuracao_formularios,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
