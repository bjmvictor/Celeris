import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0051_catalogo_inicial_classificacao"),
        ("core", "0050_configuracoes_classificacao"),
    ]
    operations = [
        migrations.CreateModel(
            name="ModeloDocumentoTelaImpressao",
            fields=[
                ("cd_modelo_documento_tela", models.BigAutoField(primary_key=True, serialize=False)),
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_modelo_documento", models.ForeignKey(db_column="cd_modelo_documento", on_delete=django.db.models.deletion.CASCADE, related_name="telas_impressao", to="atendimento.modelodocumento")),
                ("cd_tela", models.ForeignKey(db_column="cd_tela", on_delete=django.db.models.deletion.PROTECT, related_name="modelos_documento_impressao", to="core.screendefinition")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "modelo_documento_tela_impressao", "ordering": ("cd_tela__module__order", "cd_tela__order", "cd_tela__title")},
        ),
        migrations.AddConstraint(
            model_name="modelodocumentotelaimpressao",
            constraint=models.UniqueConstraint(fields=("cd_empresa", "cd_modelo_documento", "cd_tela"), name="modelo_documento_tela_impressao_unica"),
        ),
    ]
