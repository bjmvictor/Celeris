from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0003_convenio_prestador_agenda"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="ds_cor_raca",
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
