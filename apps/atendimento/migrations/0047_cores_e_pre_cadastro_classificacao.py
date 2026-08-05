from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


CORES_PADRAO = (
    ("VERMELHO", "Vermelho", "#dc2626", 1),
    ("LARANJA", "Laranja", "#f97316", 2),
    ("AMARELO", "Amarelo", "#eab308", 3),
    ("VERDE", "Verde", "#22c55e", 4),
    ("AZUL", "Azul", "#3b82f6", 5),
)


def cadastrar_cores_padrao(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Cor = apps.get_model("atendimento", "CorClassificacaoRisco")
    for empresa in Empresa.objects.all():
        for codigo, nome, hexadecimal, prioridade in CORES_PADRAO:
            Cor.objects.update_or_create(
                cd_empresa_id=empresa.pk,
                cd_cor=codigo,
                defaults={
                    "nm_cor": nome,
                    "ds_cor_hex": hexadecimal,
                    "nr_prioridade": prioridade,
                    "sn_ativo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0046_configuracao_painel_e_armazenamento_clinico"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CorClassificacaoRisco",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_cor_classificacao", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_cor", models.CharField(max_length=30)),
                ("nm_cor", models.CharField(max_length=80)),
                ("ds_cor_hex", models.CharField(default="#22c55e", max_length=7)),
                ("nr_prioridade", models.PositiveSmallIntegerField(default=5)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_usuario_atualizacao",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_atualizados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "cd_usuario_criacao",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_criados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "cor_classificacao_risco",
                "ordering": ("nr_prioridade", "nm_cor"),
                "unique_together": {("cd_empresa", "cd_cor")},
            },
        ),
        migrations.AddField(
            model_name="classesenhaatendimento",
            name="cd_cor_classificacao",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_cor_classificacao",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="classes_senha",
                to="atendimento.corclassificacaorisco",
            ),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="cd_cor_classificacao",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_cor_classificacao",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="senhas_atendimento",
                to="atendimento.corclassificacaorisco",
            ),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="cd_pre_atendimento",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_pre_atendimento",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="senhas_atendimento",
                to="atendimento.preatendimento",
            ),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="ds_dados_classificacao",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="dt_nascimento_pre_cadastro",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="nm_mae_pre_cadastro",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="nm_pre_cadastro",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.RunPython(cadastrar_cores_padrao, migrations.RunPython.noop),
    ]
