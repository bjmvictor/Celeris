import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0009 = import_module("apps.atendimento.migrations.0009_seed_perfis_clinicos")
migracao_0011 = import_module("apps.atendimento.migrations.0011_seed_homologacao")
migracao_0012 = import_module("apps.atendimento.migrations.0012_cleanup_perfis_homologacao")
migracao_0014 = import_module("apps.atendimento.migrations.0014_migrate_provider_specialties")
migracao_0015 = import_module("apps.atendimento.migrations.0015_prestador_ds_chave_pix_and_more")
migracao_0016 = import_module("apps.atendimento.migrations.0016_prestador_nm_guerra")
migracao_0017 = import_module("apps.atendimento.migrations.0017_patient_provider_review")

class Migration(migrations.Migration):

    replaces = [('atendimento', '0008_agendamento_ds_plano_agendamento_sn_encaixe_and_more'), ('atendimento', '0009_seed_perfis_clinicos'), ('atendimento', '0010_prescricao_evolucaoatendimento'), ('atendimento', '0011_seed_homologacao'), ('atendimento', '0012_cleanup_perfis_homologacao'), ('atendimento', '0013_prestador_cd_banco_prestador_ds_bairro_comercial_and_more'), ('atendimento', '0014_migrate_provider_specialties'), ('atendimento', '0015_prestador_ds_chave_pix_and_more'), ('atendimento', '0016_prestador_nm_guerra'), ('atendimento', '0017_patient_provider_review')]

    dependencies = [
        ('accounts', '0006_empresa_cd_usuario_atualizacao_and_more'),
        ('atendimento', '0007_agendamento_cd_usuario_atualizacao_and_more'),
        ('core', '0015_seed_erp_auxiliaries'),
        ('core', '0018_cep'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='agendamento',
            name='ds_plano',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='agendamento',
            name='sn_encaixe',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='agendamento',
            name='sn_particular',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='cd_convenio',
            field=models.ForeignKey(blank=True, db_column='cd_convenio', null=True, on_delete=django.db.models.deletion.PROTECT, to='atendimento.convenio'),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_destino',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_diagnostico',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_especialidade',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_hipotese_diagnostica',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_origem',
            field=models.CharField(choices=[('AGENDADO', 'Agendado'), ('DEMANDA_ESPONTANEA', 'Demanda espontânea'), ('ENCAIXE', 'Encaixe'), ('RETORNO', 'Retorno'), ('URGENCIA_EMERGENCIA', 'Urgência/Emergência')], default='DEMANDA_ESPONTANEA', max_length=30),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_plano',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_tipo_atendimento',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='atendimento',
            name='ds_unidade_setor',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='preatendimento',
            name='cd_prestador_responsavel',
            field=models.ForeignKey(blank=True, db_column='cd_prestador_responsavel', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='classificacoes_realizadas', to='atendimento.prestador'),
        ),
        migrations.AddField(
            model_name='preatendimento',
            name='dh_fim',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='preatendimento',
            name='dh_inicio',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='preatendimento',
            name='ds_cor_prioridade',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='preatendimento',
            name='ds_sintomas',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='agendamento',
            name='ds_status',
            field=models.CharField(choices=[('AGENDADO', 'Agendado'), ('CONFIRMADO', 'Confirmado'), ('RECEPCIONADO', 'Recepcionado'), ('FALTOU', 'Faltou'), ('REAGENDADO', 'Reagendado'), ('AGUARDANDO_PRE_ATENDIMENTO', 'Aguardando pré-atendimento'), ('AGUARDANDO_ATENDIMENTO', 'Aguardando atendimento'), ('EM_ATENDIMENTO', 'Em atendimento'), ('FINALIZADO', 'Finalizado'), ('CANCELADO', 'Cancelado')], default='AGENDADO', max_length=40),
        ),
        migrations.AlterField(
            model_name='atendimento',
            name='ds_status',
            field=models.CharField(choices=[('ABERTO', 'Aberto'), ('AGUARDANDO_CLASSIFICACAO', 'Aguardando classificação'), ('AGUARDANDO_CONSULTA', 'Aguardando consulta'), ('EM_ATENDIMENTO', 'Em atendimento'), ('AGUARDANDO_EXAMES', 'Aguardando exames'), ('FINALIZADO', 'Finalizado'), ('ENCAMINHADO', 'Encaminhado'), ('INTERNADO', 'Internado'), ('ALTA', 'Alta'), ('CANCELADO', 'Cancelado')], default='ABERTO', max_length=30),
        ),
        migrations.CreateModel(
            name='SolicitacaoExame',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_solicitacao_exame', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_exame', models.CharField(max_length=180)),
                ('ds_justificativa', models.TextField(blank=True)),
                ('ds_prioridade', models.CharField(choices=[('ROTINA', 'Rotina'), ('URGENTE', 'Urgente'), ('EMERGENCIA', 'Emergência')], default='ROTINA', max_length=20)),
                ('ds_status', models.CharField(choices=[('SOLICITADO', 'Solicitado'), ('COLETADO', 'Coletado'), ('EM_ANALISE', 'Em análise'), ('LIBERADO', 'Liberado'), ('CANCELADO', 'Cancelado')], default='SOLICITADO', max_length=20)),
                ('cd_atendimento', models.ForeignKey(db_column='cd_atendimento', on_delete=django.db.models.deletion.PROTECT, related_name='solicitacoes_exames', to='atendimento.atendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'solicitacao_exame',
                'ordering': ('-dh_criacao',),
            },
        ),
        migrations.CreateModel(
            name='ResultadoExame',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_resultado_exame', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_resultado', models.TextField(blank=True)),
                ('ds_anexo', models.FileField(blank=True, upload_to='resultados_exames/')),
                ('sn_liberado', models.BooleanField(default=False)),
                ('dh_liberacao', models.DateTimeField(blank=True, null=True)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_solicitacao_exame', models.OneToOneField(db_column='cd_solicitacao_exame', on_delete=django.db.models.deletion.PROTECT, related_name='resultado', to='atendimento.solicitacaoexame')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'resultado_exame',
            },
        ),
        migrations.RunPython(
            code=migracao_0009.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name='Prescricao',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_prescricao', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_prescricao', models.TextField()),
                ('ds_orientacoes', models.TextField(blank=True)),
                ('sn_ativa', models.BooleanField(default=True)),
                ('cd_atendimento', models.ForeignKey(db_column='cd_atendimento', on_delete=django.db.models.deletion.PROTECT, related_name='prescricoes', to='atendimento.atendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'prescricao',
                'ordering': ('-dh_criacao',),
            },
        ),
        migrations.CreateModel(
            name='EvolucaoAtendimento',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_evolucao_atendimento', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_evolucao', models.TextField()),
                ('cd_atendimento', models.ForeignKey(db_column='cd_atendimento', on_delete=django.db.models.deletion.PROTECT, related_name='evolucoes', to='atendimento.atendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_prestador', models.ForeignKey(db_column='cd_prestador', on_delete=django.db.models.deletion.PROTECT, to='atendimento.prestador')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'evolucao_atendimento',
                'ordering': ('-dh_criacao',),
            },
        ),
        migrations.RunPython(
            code=migracao_0011.preservar_sequencia_sem_dados_artificiais,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0012.cleanup,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='prestador',
            name='cd_banco',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_bairro_comercial',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_cidade_comercial',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_complemento_comercial',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_endereco_comercial',
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_especialidades',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_grau_instrucao',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_nacionalidade',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_naturalidade',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='dt_expedicao',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nm_agencia',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nm_mae',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nm_pai',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_agencia',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_cartao_sus',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_celular_2',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_cep_comercial',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_conta',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_endereco_comercial',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_rg',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sg_estado_comercial',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='prestador',
            name='tp_genero',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='tp_logradouro_comercial',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.RunPython(
            code=migracao_0014.forwards,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_chave_pix',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='prestador',
            name='ds_contato_principal',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nm_favorecido',
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_digito_agencia',
            field=models.CharField(blank=True, max_length=5),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_digito_conta',
            field=models.CharField(blank=True, max_length=5),
        ),
        migrations.AddField(
            model_name='prestador',
            name='nr_documento_favorecido',
            field=models.CharField(blank=True, max_length=18),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sn_mesmo_endereco',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sn_permite_agenda',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sn_permite_atendimento',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sn_permite_classificacao',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prestador',
            name='sn_permite_prescricao',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prestador',
            name='tp_conta',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.RunPython(
            code=migracao_0015.suggest_provider_permissions,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='prestador',
            name='nm_guerra',
            field=models.CharField(default='', max_length=120),
            preserve_default=False,
        ),
        migrations.RunPython(
            code=migracao_0016.populate_war_name,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='paciente',
            name='cd_cep',
            field=models.ForeignKey(blank=True, db_column='cd_cep', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pacientes', to='core.cep'),
        ),
        migrations.AddField(
            model_name='paciente',
            name='ds_orgao_emissor',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='paciente',
            name='dt_expedicao',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paciente',
            name='nr_celular_2',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='paciente',
            name='tp_logradouro',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='prestador',
            name='cd_cep',
            field=models.ForeignKey(blank=True, db_column='cd_cep', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='prestadores_residenciais', to='core.cep'),
        ),
        migrations.AddField(
            model_name='prestador',
            name='cd_cep_comercial',
            field=models.ForeignKey(blank=True, db_column='cd_cep_comercial', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='prestadores_comerciais', to='core.cep'),
        ),
        migrations.AddField(
            model_name='prestador',
            name='dt_nascimento',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(
            code=migracao_0017.link_existing_ceps,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
