from django.db import migrations, models


def populate_war_name(apps, schema_editor):
    Prestador = apps.get_model("atendimento", "Prestador")
    for provider in Prestador.objects.filter(nm_guerra="").iterator():
        parts = provider.nm_prestador.split()
        provider.nm_guerra = " ".join(parts if len(parts) < 2 else (parts[0], parts[-1]))
        provider.save(update_fields=["nm_guerra"])


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0015_prestador_ds_chave_pix_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="prestador",
            name="nm_guerra",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.RunPython(populate_war_name, migrations.RunPython.noop),
    ]
