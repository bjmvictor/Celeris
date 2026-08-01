import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0039 = import_module("apps.atendimento.migrations.0039_classesenhaatendimento_ds_icone_and_more")

class Migration(migrations.Migration):

    replaces = [('atendimento', '0038_integrar_senhas_paineis'), ('atendimento', '0039_classesenhaatendimento_ds_icone_and_more'), ('atendimento', '0040_paciente_obito'), ('atendimento', '0041_alter_modelodocumento_tp_documento')]

    dependencies = [
        ('accounts', '0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more'),
        ('atendimento', '0037_totem_senhas'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='tiposenhaatendimento',
            name='cd_setor_atendimento',
            field=models.ForeignKey(blank=True, db_column='cd_setor_atendimento', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tipos_senha', to='accounts.setor'),
        ),
        migrations.AlterField(
            model_name='senhaatendimento',
            name='ds_status',
            field=models.CharField(choices=[('AGUARDANDO', 'Aguardando'), ('CHAMADA', 'Chamada'), ('EM_CLASSIFICACAO', 'Em classificação'), ('CLASSIFICADA', 'Classificada'), ('RECEPCIONADA', 'Recepcionada'), ('CANCELADA', 'Cancelada')], default='AGUARDANDO', max_length=24),
        ),
        migrations.AlterField(
            model_name='chamadapainel',
            name='cd_atendimento',
            field=models.ForeignKey(blank=True, db_column='cd_atendimento', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='chamadas_painel', to='atendimento.atendimento'),
        ),
        migrations.AlterField(
            model_name='chamadapainel',
            name='cd_setor',
            field=models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor'),
        ),
        migrations.AddField(
            model_name='chamadapainel',
            name='cd_senha_atendimento',
            field=models.ForeignKey(blank=True, db_column='cd_senha_atendimento', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='chamadas_painel', to='atendimento.senhaatendimento'),
        ),
        migrations.AddField(
            model_name='classesenhaatendimento',
            name='ds_icone',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='agendamento',
            name='cd_agenda_profissional',
            field=models.ForeignKey(blank=True, db_column='cd_escala', null=True, on_delete=django.db.models.deletion.PROTECT, to='atendimento.agendaprofissional'),
        ),
        migrations.AlterField(
            model_name='agendaprofissional',
            name='cd_agenda_profissional',
            field=models.BigAutoField(db_column='cd_escala', primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='agendaprofissional',
            name='ds_agenda',
            field=models.CharField(db_column='nm_escala', max_length=160),
        ),
        migrations.AlterField(
            model_name='classesenhaatendimento',
            name='cd_tipo_senha',
            field=models.ForeignKey(blank=True, db_column='cd_tipo_senha', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes', to='atendimento.tiposenhaatendimento'),
        ),
        migrations.AlterModelTable(
            name='agendaprofissional',
            table='escala',
        ),
        migrations.CreateModel(
            name='ProtocoloSenhaAtendimento',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_protocolo_senha', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_protocolo', models.CharField(max_length=120)),
                ('ds_protocolo', models.CharField(blank=True, max_length=500)),
                ('sn_ativo', models.BooleanField(default=True)),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'protocolo_senha',
                'ordering': ('nm_protocolo',),
                'unique_together': {('cd_empresa', 'nm_protocolo')},
            },
        ),
        migrations.AddField(
            model_name='tiposenhaatendimento',
            name='cd_protocolo',
            field=models.ForeignKey(blank=True, db_column='cd_protocolo', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tipos_senha', to='atendimento.protocolosenhaatendimento'),
        ),
        migrations.CreateModel(
            name='RegraSubdivisaoSenha',
            fields=[
                ('dh_criacao', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('dh_atualizacao', models.DateTimeField(auto_now=True)),
                ('cd_regra_subdivisao', models.BigAutoField(primary_key=True, serialize=False)),
                ('nr_prioridade', models.PositiveSmallIntegerField(default=5)),
                ('nr_idade_minima', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('nr_idade_maxima', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('ds_icone', models.CharField(blank=True, max_length=40)),
                ('sn_ativo', models.BooleanField(default=True)),
                ('cd_classe_senha', models.ForeignKey(db_column='cd_classe_senha', on_delete=django.db.models.deletion.PROTECT, related_name='regras_subdivisao', to='atendimento.classesenhaatendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_tipo_senha', models.ForeignKey(db_column='cd_tipo_senha', on_delete=django.db.models.deletion.CASCADE, related_name='regras_subdivisao', to='atendimento.tiposenhaatendimento')),
                ('cd_usuario_atualizacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_atualizados', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_criacao', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(app_label)s_%(class)s_criados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'regra_subdivisao_senha',
                'ordering': ('nr_prioridade', 'cd_classe_senha__nm_classe_senha'),
                'unique_together': {('cd_tipo_senha', 'cd_classe_senha')},
            },
        ),
        migrations.RunPython(
            code=migracao_0039.migrar_regras_e_telas,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='paciente',
            name='sn_obito',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='paciente',
            name='dh_obito',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='modelodocumento',
            name='tp_documento',
            field=models.CharField(choices=[('COMPROVANTE_AGENDAMENTO', 'Comprovante de agendamento'), ('COMPROVANTE_CHAMADO', 'Comprovante de chamado'), ('FICHA_ATENDIMENTO', 'Ficha de atendimento'), ('ETIQUETA_ATENDIMENTO', 'Etiqueta de atendimento'), ('PRESCRICAO', 'Prescrição'), ('SOLICITACAO_EXAME', 'Solicitação de exame'), ('EVOLUCAO', 'Evolução'), ('RESUMO_ALTA', 'Resumo de alta'), ('RECEITUARIO', 'Receituário'), ('ATESTADO', 'Atestado'), ('ENCAMINHAMENTO', 'Encaminhamento'), ('ADMINISTRATIVO', 'Administrativo')], max_length=40),
        ),
    ]
