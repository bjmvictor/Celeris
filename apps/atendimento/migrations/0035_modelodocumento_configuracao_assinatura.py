from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0034_escalaclinica_expressao_calculo"),
    ]

    operations = [
        migrations.AddField(
            model_name="modelodocumento",
            name="sn_exibe_assinatura",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="modelodocumento",
            name="sn_exibe_conselho_assinatura",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="modelodocumento",
            name="tp_alinhamento_assinatura",
            field=models.CharField(
                choices=[
                    ("ESQUERDA", "Esquerda"),
                    ("CENTRO", "Centralizada"),
                    ("DIREITA", "Direita"),
                ],
                default="CENTRO",
                max_length=10,
            ),
        ),
    ]
