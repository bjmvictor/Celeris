from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0033_editor_pep_assistencial"),
    ]

    operations = [
        migrations.AddField(
            model_name="escalaclinica",
            name="ds_expressao_calculo",
            field=models.CharField(blank=True, max_length=1000),
        ),
    ]
