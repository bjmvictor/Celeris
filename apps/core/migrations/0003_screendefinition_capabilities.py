from django.db import migrations, models


def update_screen_capabilities(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenDefinition.objects.filter(slug="ti-alteracao-senha-usuario").update(
        allow_query=False,
        allow_insert=False,
        allow_update=True,
        allow_delete=False,
    )
    ScreenDefinition.objects.filter(slug="ti-cadastro-copia-usuario").update(
        allow_query=True,
        allow_insert=True,
        allow_update=True,
        allow_delete=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_screendefinition_screenfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="screendefinition",
            name="allow_delete",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="allow_insert",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="allow_query",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="allow_update",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(update_screen_capabilities, migrations.RunPython.noop),
    ]
