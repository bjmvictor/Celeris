from django.db import migrations


def cleanup(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    TabelaAuxiliarGlobal.objects.filter(ds_tabela__in=("cep", "bairro")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_cep"),
    ]

    operations = [
        migrations.RunPython(cleanup, migrations.RunPython.noop),
    ]
