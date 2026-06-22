from django.db import migrations


def forwards(apps, schema_editor):
    Prestador = apps.get_model("atendimento", "Prestador")
    for provider in Prestador.objects.exclude(ds_especialidade=""):
        if not provider.ds_especialidades:
            provider.ds_especialidades = [provider.ds_especialidade]
            provider.save(update_fields=["ds_especialidades"])


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0013_prestador_cd_banco_prestador_ds_bairro_comercial_and_more"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
