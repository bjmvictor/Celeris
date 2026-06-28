from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0011_setor_setorusuario"),
        ("atendimento", "0018_painel_chamada"),
    ]

    operations = [
        migrations.AlterField(
            model_name="atendimento",
            name="ds_status",
            field=models.CharField(choices=[("AGENDADO", "Agendado"), ("RECEPCIONADO", "Recepcionado"), ("ABERTO", "Aberto"), ("AGUARDANDO_CLASSIFICACAO", "Aguardando classificação"), ("EM_CLASSIFICACAO", "Em classificação"), ("AGUARDANDO_CONSULTA", "Aguardando consulta"), ("EM_ATENDIMENTO", "Em atendimento"), ("AGUARDANDO_EXAMES", "Aguardando exames"), ("RETORNO_EXAMES", "Retorno de exames"), ("EM_OBSERVACAO", "Em observação"), ("ALTA_MEDICA", "Alta médica"), ("ALTA_HOSPITALAR", "Alta hospitalar"), ("FINALIZADO", "Finalizado"), ("ENCAMINHADO", "Encaminhado"), ("INTERNADO", "Internado"), ("ALTA", "Alta"), ("CANCELADO", "Cancelado"), ("EVADIU", "Evadiu"), ("OBITO", "Óbito")], default="ABERTO", max_length=40),
        ),
        migrations.AddField(
            model_name="atendimento",
            name="cd_setor_atual",
            field=models.ForeignKey(blank=True, db_column="cd_setor_atual", null=True, on_delete=django.db.models.deletion.PROTECT, to="accounts.setor"),
        ),
        migrations.AddField(
            model_name="atendimento",
            name="cd_usuario_cancelamento",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="atendimentos_cancelados", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(model_name="atendimento", name="dh_alta_hospitalar", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_alta_medica", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_cancelamento", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_fim_atendimento", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_fim_classificacao", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_inicio_atendimento", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_inicio_classificacao", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="dh_recepcao", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="atendimento", name="ds_motivo_atendimento", field=models.TextField(blank=True)),
        migrations.AddField(model_name="atendimento", name="ds_motivo_cancelamento", field=models.TextField(blank=True)),
        migrations.AddField(model_name="atendimento", name="ds_observacao_recepcao", field=models.TextField(blank=True)),
        migrations.AddField(model_name="atendimento", name="ds_procedimento_principal", field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name="atendimento", name="ds_queixa_principal", field=models.TextField(blank=True)),
        migrations.AddField(model_name="atendimento", name="sn_ativo", field=models.BooleanField(default=True)),
        migrations.CreateModel(
            name="AtendimentoFluxo",
            fields=[
                ("cd_atendimento_fluxo", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_status_anterior", models.CharField(blank=True, max_length=40)),
                ("ds_status_novo", models.CharField(max_length=40)),
                ("dh_evento", models.DateTimeField(default=django.utils.timezone.now)),
                ("ds_observacao", models.TextField(blank=True)),
                ("ds_origem", models.CharField(blank=True, max_length=80)),
                ("cd_atendimento", models.ForeignKey(db_column="cd_atendimento", on_delete=django.db.models.deletion.CASCADE, related_name="fluxos", to="atendimento.atendimento")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_prestador", models.ForeignKey(blank=True, db_column="cd_prestador", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.prestador")),
                ("cd_setor", models.ForeignKey(blank=True, db_column="cd_setor", null=True, on_delete=django.db.models.deletion.PROTECT, to="accounts.setor")),
                ("cd_usuario", models.ForeignKey(blank=True, db_column="cd_usuario", null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "atendimento_fluxo", "ordering": ("-dh_evento",)},
        ),
        migrations.CreateModel(
            name="AtendimentoPrestador",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_atendimento_prestador", models.BigAutoField(primary_key=True, serialize=False)),
                ("tp_papel", models.CharField(choices=[("MEDICO", "Médico"), ("ENFERMAGEM", "Enfermagem"), ("LABORATORIO", "Laboratório"), ("FISIOTERAPIA", "Fisioterapia"), ("NUTRICAO", "Nutrição"), ("PSICOLOGIA", "Psicologia"), ("OUTRO", "Outro profissional")], default="MEDICO", max_length=30)),
                ("dh_inicio", models.DateTimeField(default=django.utils.timezone.now)),
                ("dh_fim", models.DateTimeField(blank=True, null=True)),
                ("sn_responsavel_principal", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_atendimento", models.ForeignKey(db_column="cd_atendimento", on_delete=django.db.models.deletion.CASCADE, related_name="prestadores_vinculados", to="atendimento.atendimento")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_prestador", models.ForeignKey(db_column="cd_prestador", on_delete=django.db.models.deletion.PROTECT, to="atendimento.prestador")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "atendimento_prestador", "ordering": ("-sn_responsavel_principal", "dh_inicio")},
        ),
        migrations.CreateModel(
            name="AtendimentoProcedimento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_atendimento_procedimento", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_procedimento", models.CharField(max_length=160)),
                ("nr_quantidade", models.DecimalField(decimal_places=2, default=1, max_digits=8)),
                ("vl_procedimento", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("dh_lancamento", models.DateTimeField(default=django.utils.timezone.now)),
                ("sn_principal", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_atendimento", models.ForeignKey(db_column="cd_atendimento", on_delete=django.db.models.deletion.CASCADE, related_name="procedimentos", to="atendimento.atendimento")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_prestador_executante", models.ForeignKey(blank=True, db_column="cd_prestador_executante", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.prestador")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_lancamento", models.ForeignKey(blank=True, db_column="cd_usuario_lancamento", null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "atendimento_procedimento", "ordering": ("-sn_principal", "-dh_lancamento")},
        ),
    ]
