from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0039_classesenhaatendimento_ds_icone_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="sn_obito",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="paciente",
            name="dh_obito",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
