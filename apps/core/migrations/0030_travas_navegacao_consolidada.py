import django.db.migrations.operations.special
import django.db.models.deletion
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0031 = import_module("apps.core.migrations.0031_desativar_modulos_nao_implementados")
migracao_0032 = import_module("apps.core.migrations.0032_corrigir_tela_alteracao_senha")
migracao_0033 = import_module("apps.core.migrations.0033_navigation_tree")

class Migration(migrations.Migration):

    replaces = [('core', '0030_trava_edicao'), ('core', '0031_desativar_modulos_nao_implementados'), ('core', '0032_corrigir_tela_alteracao_senha'), ('core', '0033_navigation_tree')]

    dependencies = [
        ('accounts', '0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more'),
        ('core', '0029_seed_cids_motivos_alta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TravaEdicao',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_trava_edicao', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_recurso_tipo', models.CharField(max_length=80)),
                ('ds_recurso_id', models.CharField(max_length=120)),
                ('ds_recurso_titulo', models.CharField(blank=True, max_length=180)),
                ('ds_identificador_guia', models.CharField(blank=True, max_length=120)),
                ('dh_expiracao', models.DateTimeField()),
                ('nr_tentativas_bloqueadas', models.PositiveIntegerField(default=0)),
                ('ds_ultimo_usuario_bloqueado', models.CharField(blank=True, max_length=150)),
                ('dh_ultimo_bloqueio', models.DateTimeField(blank=True, null=True)),
                ('ds_liberacao', models.CharField(blank=True, max_length=220)),
                ('sn_ativa', models.BooleanField(default=True)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.CASCADE, related_name='travas_edicao', to='accounts.empresa')),
                ('cd_usuario', models.ForeignKey(db_column='cd_usuario', on_delete=django.db.models.deletion.CASCADE, related_name='travas_edicao', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'trava_edicao',
                'ordering': ('-updated_at',),
                'indexes': [models.Index(fields=['cd_empresa', 'ds_recurso_tipo', 'ds_recurso_id', 'sn_ativa'], name='trava_edica_cd_empr_5e5033_idx'), models.Index(fields=['dh_expiracao', 'sn_ativa'], name='trava_edica_dh_expi_3d47a8_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='travaedicao',
            constraint=models.UniqueConstraint(condition=models.Q(('sn_ativa', True)), fields=('cd_empresa', 'ds_recurso_tipo', 'ds_recurso_id'), name='uq_trava_edicao_recurso_ativo'),
        ),
        migrations.RunPython(
            code=migracao_0031.desativar_modulos,
            reverse_code=migracao_0031.reativar_modulos,
        ),
        migrations.RunPython(
            code=migracao_0032.corrigir_tela_alteracao_senha,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='module',
            name='icon',
            field=models.CharField(blank=True, default='grid', max_length=50),
        ),
        migrations.AddField(
            model_name='module',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='module',
            options={'ordering': ('order', 'title')},
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='icon',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='navigation_url',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='core.screendefinition'),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='roles',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='screendefinition',
            name='screen_type',
            field=models.CharField(choices=[('grupo', 'Grupo'), ('formulario', 'Formulário'), ('relatorio', 'Relatório'), ('dashboard', 'Dashboard'), ('consulta', 'Consulta'), ('wizard', 'Wizard'), ('fila', 'Fila'), ('documento', 'Documento'), ('configuracao', 'Configuração')], default='formulario', max_length=30),
        ),
        migrations.AlterModelOptions(
            name='screendefinition',
            options={'ordering': ('module__order', 'module__title', 'parent__order', 'parent_label', 'order', 'title')},
        ),
        migrations.RunPython(
            code=migracao_0033.seed_navigation_tree,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
