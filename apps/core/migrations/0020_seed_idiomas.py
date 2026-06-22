from django.db import migrations


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="idioma",
        defaults={"ds_descricao": "Idiomas", "sn_ativo": True},
    )
    for code, description in (("PT_BR", "PORTUGUÊS - BRASIL"), ("EN_US", "INGLÊS"), ("ES", "ESPANHOL")):
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=table,
            cd_valor=code,
            defaults={"ds_valor": description, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0019_cleanup_legacy_cep_bairro_auxiliaries")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
