from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0049_cadastros_sociodemograficos_e_cbo"),
    ]

    operations = [
        migrations.AddField(
            model_name="preatendimento",
            name="ds_dados_classificacao",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
