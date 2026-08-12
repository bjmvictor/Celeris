from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0048_classificacao_avancada"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="ds_municipio_nascimento",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="paciente",
            name="ds_orientacao_sexual",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="paciente",
            name="ds_pais_nascimento",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="paciente",
            name="sg_uf_nascimento",
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name="prestador",
            name="cd_cbo",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
