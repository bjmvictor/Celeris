import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0043 = import_module("apps.atendimento.migrations.0043_seed_paineis_chamada")
migracao_0044 = import_module("apps.atendimento.migrations.0044_maquina_chamada_tipo")

class Migration(migrations.Migration):

    replaces = [('atendimento', '0042_iconechamada_classesenhaatendimento_cd_icone_chamada_and_more'), ('atendimento', '0043_seed_paineis_chamada'), ('atendimento', '0044_maquina_chamada_tipo')]

    dependencies = [
        ('accounts', '0015_sync_navigation_role_catalog'),
        ('atendimento', '0041_alter_modelodocumento_tp_documento'),
        ('core', '0032_corrigir_tela_alteracao_senha'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IconeChamada',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_icone_chamada', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_icone', models.CharField(max_length=80)),
                ('ds_svg', models.TextField(blank=True)),
                ('sn_ativo', models.BooleanField(default=True)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'icone_chamada',
                'ordering': ('nm_icone',),
                'unique_together': {('cd_empresa', 'nm_icone')},
            },
        ),
        migrations.AddField(
            model_name='classesenhaatendimento',
            name='cd_icone_chamada',
            field=models.ForeignKey(blank=True, db_column='cd_icone_chamada', null=True, on_delete=django.db.models.deletion.SET_NULL, to='atendimento.iconechamada'),
        ),
        migrations.CreateModel(
            name='MaquinaChamada',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_maquina_chamada', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_maquina', models.CharField(max_length=120)),
                ('nm_sala', models.CharField(blank=True, max_length=120)),
                ('tp_sala', models.CharField(choices=[('CONSULTORIO', 'Consultório'), ('SALA', 'Sala'), ('GUICHE', 'Guichê'), ('TRIAGEM', 'Triagem'), ('OUTRO', 'Outro')], default='CONSULTORIO', max_length=20)),
                ('nr_sala', models.CharField(blank=True, max_length=20)),
                ('sn_ativo', models.BooleanField(default=True)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_setor', models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'maquina_chamada',
                'ordering': ('nm_maquina',),
                'unique_together': {('cd_empresa', 'nm_maquina')},
            },
        ),
        migrations.RunPython(
            code=migracao_0043.seed_paineis_chamada,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='maquinachamada',
            name='tp_maquina',
            field=models.CharField(choices=[('ESTACAO', 'Estação'), ('PAINEL', 'Painel')], default='ESTACAO', max_length=20),
        ),
        migrations.RunPython(
            code=migracao_0044.classify_existing_machines,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
