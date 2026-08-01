"""Operações históricas de dados da migration 0024."""

from django.db import migrations


def remover_valores_teste_legados(apps, schema_editor):
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    Cep = apps.get_model("core", "Cep")

    ValorAuxiliarGlobal.objects.filter(cd_valor__startswith="TESTE_").delete()
    Cep.objects.filter(
        ds_logradouro__startswith="RUA TESTE ",
        ds_bairro__startswith="BAIRRO TESTE ",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_sync_recent_role_screens"),
        ("core", "0023_seed_minimum_test_auxiliary_values"),
    ]

    operations = [
        migrations.RunPython(remover_valores_teste_legados, migrations.RunPython.noop),
    ]
