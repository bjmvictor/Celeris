from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0002_empresa_usuarioempresa"),
    ]

    operations = [
        migrations.CreateModel(
            name="Paciente",
            fields=[
                ("cd_paciente", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_paciente", models.CharField(max_length=180)),
                ("nm_social", models.CharField(blank=True, max_length=180)),
                ("dt_nascimento", models.DateField(blank=True, null=True)),
                ("tp_sexo", models.CharField(blank=True, max_length=20)),
                ("tp_genero", models.CharField(blank=True, max_length=40)),
                ("tp_estado_civil", models.CharField(blank=True, max_length=40)),
                ("tp_sanguineo", models.CharField(blank=True, max_length=5)),
                ("nr_cpf", models.CharField(blank=True, max_length=14)),
                ("nr_rg", models.CharField(blank=True, max_length=30)),
                ("nr_cartao_sus", models.CharField(blank=True, max_length=30)),
                ("nr_convenio", models.CharField(blank=True, max_length=50)),
                ("nm_convenio", models.CharField(blank=True, max_length=120)),
                ("nr_telefone", models.CharField(blank=True, max_length=30)),
                ("nr_celular", models.CharField(blank=True, max_length=30)),
                ("ds_email", models.EmailField(blank=True, max_length=254)),
                ("nm_mae", models.CharField(blank=True, max_length=180)),
                ("nm_pai", models.CharField(blank=True, max_length=180)),
                ("nm_conjuge", models.CharField(blank=True, max_length=180)),
                ("ds_naturalidade", models.CharField(blank=True, max_length=120)),
                ("ds_nacionalidade", models.CharField(blank=True, max_length=120)),
                ("ds_profissao", models.CharField(blank=True, max_length=120)),
                ("ds_endereco", models.CharField(blank=True, max_length=220)),
                ("nr_endereco", models.CharField(blank=True, max_length=20)),
                ("ds_complemento", models.CharField(blank=True, max_length=120)),
                ("ds_bairro", models.CharField(blank=True, max_length=120)),
                ("ds_cidade", models.CharField(blank=True, max_length=120)),
                ("sg_estado", models.CharField(blank=True, max_length=2)),
                ("nr_cep", models.CharField(blank=True, max_length=10)),
                ("ds_observacao", models.TextField(blank=True)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("dh_criacao", models.DateTimeField(auto_now_add=True)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
            ],
            options={"db_table": "paciente", "ordering": ("nm_paciente",)},
        ),
        migrations.CreateModel(
            name="HistoricoAlteracaoPaciente",
            fields=[
                ("cd_historico_alteracao_paciente", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_observacao", models.TextField()),
                ("ds_alteracoes", models.JSONField(default=dict)),
                ("ds_antes", models.JSONField(default=dict)),
                ("ds_depois", models.JSONField(default=dict)),
                ("sn_desfeito", models.BooleanField(default=False)),
                ("dh_alteracao", models.DateTimeField(auto_now_add=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_paciente", models.ForeignKey(db_column="cd_paciente", on_delete=django.db.models.deletion.CASCADE, to="atendimento.paciente")),
                ("cd_usuario", models.ForeignKey(blank=True, db_column="cd_usuario", null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "historico_alteracao_paciente", "ordering": ("-dh_alteracao",)},
        ),
        migrations.CreateModel(
            name="Agendamento",
            fields=[
                ("cd_agendamento", models.BigAutoField(primary_key=True, serialize=False)),
                ("dh_agendamento", models.DateTimeField(blank=True, null=True)),
                ("ds_tipo_atendimento", models.CharField(blank=True, max_length=120)),
                ("ds_especialidade", models.CharField(blank=True, max_length=120)),
                ("ds_profissional", models.CharField(blank=True, max_length=120)),
                ("ds_observacao", models.TextField(blank=True)),
                ("sn_confirmado", models.BooleanField(default=False)),
                ("dh_criacao", models.DateTimeField(auto_now_add=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_paciente", models.ForeignKey(db_column="cd_paciente", on_delete=django.db.models.deletion.PROTECT, to="atendimento.paciente")),
            ],
            options={"db_table": "agendamento", "ordering": ("-dh_agendamento",)},
        ),
    ]
