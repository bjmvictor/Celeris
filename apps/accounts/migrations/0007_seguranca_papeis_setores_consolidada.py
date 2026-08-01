import apps.core.validators
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0009 = import_module("apps.accounts.migrations.0009_seed_role_access")
migracao_0010 = import_module("apps.accounts.migrations.0010_sync_ti_dynamic_access")
migracao_0011 = import_module("apps.accounts.migrations.0011_setor_setorusuario")

class Migration(migrations.Migration):

    replaces = [('accounts', '0007_user_clinical_security_fields'), ('accounts', '0008_papel_papeltela_papelmodulo'), ('accounts', '0009_seed_role_access'), ('accounts', '0010_sync_ti_dynamic_access'), ('accounts', '0011_setor_setorusuario'), ('accounts', '0012_usuario_prestador_unico')]

    dependencies = [
        ('accounts', '0006_empresa_cd_usuario_atualizacao_and_more'),
        ('atendimento', '0017_patient_provider_review'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('core', '0021_screendefinition_access_key'),
        ('core', '0022_populate_dynamic_screen_access_keys'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='can_change_patient',
            field=models.BooleanField(default=False, verbose_name='altera paciente'),
        ),
        migrations.AddField(
            model_name='user',
            name='can_configure_system',
            field=models.BooleanField(default=False, verbose_name='configura sistema'),
        ),
        migrations.AddField(
            model_name='user',
            name='can_create_users',
            field=models.BooleanField(default=False, verbose_name='cria usuários'),
        ),
        migrations.AddField(
            model_name='user',
            name='can_deactivate_users',
            field=models.BooleanField(default=False, verbose_name='desativa usuários'),
        ),
        migrations.AddField(
            model_name='user',
            name='can_manage_auxiliary_tables',
            field=models.BooleanField(default=False, verbose_name='gerencia tabelas auxiliares'),
        ),
        migrations.AddField(
            model_name='user',
            name='can_register_patient',
            field=models.BooleanField(default=False, verbose_name='cadastra paciente'),
        ),
        migrations.AddField(
            model_name='user',
            name='cd_prestador',
            field=models.ForeignKey(blank=True, db_column='cd_prestador', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='usuarios', to='atendimento.prestador'),
        ),
        migrations.AddField(
            model_name='user',
            name='ds_idioma',
            field=models.CharField(blank=True, max_length=40, verbose_name='idioma'),
        ),
        migrations.AddField(
            model_name='user',
            name='ds_profissao',
            field=models.CharField(blank=True, max_length=120, verbose_name='profissão'),
        ),
        migrations.AddField(
            model_name='user',
            name='dt_nascimento',
            field=models.DateField(blank=True, null=True, verbose_name='data de nascimento'),
        ),
        migrations.AddField(
            model_name='user',
            name='invalid_login_attempts',
            field=models.PositiveIntegerField(default=0, verbose_name='tentativas inválidas'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_blocked',
            field=models.BooleanField(default=False, verbose_name='usuário bloqueado'),
        ),
        migrations.AddField(
            model_name='user',
            name='nr_celular',
            field=models.CharField(blank=True, max_length=30, verbose_name='celular'),
        ),
        migrations.AddField(
            model_name='user',
            name='nr_cpf',
            field=models.CharField(blank=True, max_length=14, validators=[apps.core.validators.validate_cpf], verbose_name='CPF'),
        ),
        migrations.AddField(
            model_name='user',
            name='nr_matricula_rh',
            field=models.CharField(blank=True, max_length=40, verbose_name='matrícula RH'),
        ),
        migrations.AddField(
            model_name='user',
            name='password_expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='senha expira em'),
        ),
        migrations.CreateModel(
            name='Papel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ds_descricao', models.CharField(blank=True, max_length=240, verbose_name='descrição')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('grupo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='papel', to='auth.group')),
            ],
            options={
                'db_table': 'papel',
                'ordering': ('grupo__name',),
            },
        ),
        migrations.CreateModel(
            name='PapelTela',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('papel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telas', to='accounts.papel')),
                ('tela', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='papeis', to='core.screendefinition')),
            ],
            options={
                'db_table': 'papel_tela',
                'unique_together': {('papel', 'tela')},
            },
        ),
        migrations.CreateModel(
            name='PapelModulo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modulo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='papeis', to='core.module')),
                ('papel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modulos', to='accounts.papel')),
            ],
            options={
                'db_table': 'papel_modulo',
                'unique_together': {('papel', 'modulo')},
            },
        ),
        migrations.RunPython(
            code=migracao_0009.seed_role_access,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0010.sync_ti_access,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name='Setor',
            fields=[
                ('cd_setor', models.BigAutoField(primary_key=True, serialize=False, verbose_name='codigo')),
                ('nm_setor', models.CharField(max_length=120, verbose_name='nome')),
                ('tp_setor', models.CharField(choices=[('EMPRESA', 'Setor da empresa'), ('ATENDIMENTO', 'Setor de atendimento')], max_length=20, verbose_name='tipo')),
                ('ds_observacao', models.CharField(blank=True, max_length=240, verbose_name='observacao')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='data de criacao')),
                ('dh_atualizacao', models.DateTimeField(auto_now=True, verbose_name='data de alteracao')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, related_name='setores', to='accounts.empresa')),
            ],
            options={
                'db_table': 'setor',
                'ordering': ('cd_empresa', 'tp_setor', 'nm_setor'),
                'unique_together': {('cd_empresa', 'tp_setor', 'nm_setor')},
            },
        ),
        migrations.CreateModel(
            name='SetorUsuario',
            fields=[
                ('cd_setor_usuario', models.BigAutoField(primary_key=True, serialize=False, verbose_name='codigo')),
                ('cd_setor', models.ForeignKey(db_column='cd_setor', on_delete=django.db.models.deletion.CASCADE, to='accounts.setor')),
                ('cd_usuario', models.ForeignKey(db_column='cd_usuario', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'setor_usuario',
                'unique_together': {('cd_setor', 'cd_usuario')},
            },
        ),
        migrations.AddField(
            model_name='setor',
            name='usuarios',
            field=models.ManyToManyField(blank=True, related_name='setores', through='accounts.SetorUsuario', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(
            code=migracao_0011.seed_setores,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(condition=models.Q(('cd_prestador__isnull', False)), fields=('cd_prestador',), name='usuario_prestador_unico'),
        ),
    ]
