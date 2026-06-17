from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_accent_model_choice_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="screenfield",
            name="lookup_display_field",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="screenfield",
            name="lookup_table",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="screenfield",
            name="lookup_value_field",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
