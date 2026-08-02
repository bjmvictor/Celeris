from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("atendimento", "0043_alter_anexoclinico_ds_arquivo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="atendimento",
            name="dh_inicio",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
