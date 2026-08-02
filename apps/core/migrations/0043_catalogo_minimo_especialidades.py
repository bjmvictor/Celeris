from django.db import migrations


def seed_minimum_specialties(apps, schema_editor):
    Table = apps.get_model("core", "TabelaAuxiliarGlobal")
    Value = apps.get_model("core", "ValorAuxiliarGlobal")
    table, _ = Table.objects.get_or_create(
        ds_tabela="especialidade",
        defaults={"ds_descricao": "Especialidades", "sn_ativo": True},
    )
    Value.objects.update_or_create(
        cd_tabela_auxiliar_global=table,
        cd_valor="CLINICA_GERAL",
        defaults={"ds_valor": "Clínica Geral", "sn_ativo": True},
    )


def remove_minimum_specialties(apps, schema_editor):
    Value = apps.get_model("core", "ValorAuxiliarGlobal")
    Value.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="especialidade",
        cd_valor="CLINICA_GERAL",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0042_reativar_telas_implementadas")]

    operations = [migrations.RunPython(seed_minimum_specialties, remove_minimum_specialties)]
