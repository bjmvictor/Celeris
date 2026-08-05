import apps.atendimento.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0045_historico_alteracao_atendimento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="anexoclinico",
            name="ds_arquivo",
            field=models.FileField(
                storage=apps.atendimento.models.ArmazenamentoClinicoPrivado(),
                upload_to=apps.atendimento.models.caminho_anexo_clinico,
            ),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_configuracao",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_midia_arquivo",
            field=models.FileField(blank=True, upload_to="painel_chamada/midia/%Y/%m/"),
        ),
    ]
