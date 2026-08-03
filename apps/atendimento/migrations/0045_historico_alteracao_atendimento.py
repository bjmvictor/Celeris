import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_garantir_empresa_celeris_e_acesso_administrativo"),
        ("atendimento", "0044_atendimento_dh_inicio_editavel"),
        ("core", "0044_sanear_menu_e_catalogar_auxiliares"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricoAlteracaoAtendimento",
            fields=[
                ("cd_historico_alteracao_atendimento", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_observacao", models.TextField()),
                ("ds_alteracoes", models.JSONField(default=dict)),
                ("ds_antes", models.JSONField(default=dict)),
                ("ds_depois", models.JSONField(default=dict)),
                ("dh_alteracao", models.DateTimeField(auto_now_add=True)),
                (
                    "cd_atendimento",
                    models.ForeignKey(
                        db_column="cd_atendimento",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="historico_alteracoes",
                        to="atendimento.atendimento",
                    ),
                ),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_motivo_alteracao",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_motivo_alteracao",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.valorauxiliarglobal",
                    ),
                ),
                (
                    "cd_usuario",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_usuario",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "historico_alteracao_atendimento",
                "ordering": ("-dh_alteracao",),
            },
        ),
    ]
