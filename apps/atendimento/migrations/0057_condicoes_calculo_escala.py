from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0056_migrar_motivos_para_catalogo_tematico"),
    ]

    operations = [
        migrations.AddField(
            model_name="escalaclinica",
            name="ds_condicoes_calculo",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
