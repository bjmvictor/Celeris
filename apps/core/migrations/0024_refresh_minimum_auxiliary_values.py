from django.db import migrations


MINIMUM_ITEMS = 30


def refresh_minimum_values(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")

    for table in TabelaAuxiliarGlobal.objects.filter(sn_ativo=True).order_by("ds_tabela"):
        if table.ds_tabela in {"cep", "bairro"}:
            continue
        current_count = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global=table,
            sn_ativo=True,
        ).count()
        next_number = 1
        while current_count < MINIMUM_ITEMS:
            code = f"TESTE_{next_number:03d}"
            if not ValorAuxiliarGlobal.objects.filter(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
            ).exists():
                defaults = {
                    "ds_valor": f"{table.ds_descricao or table.ds_tabela} Teste {next_number:03d}".upper(),
                    "sn_ativo": True,
                }
                if table.ds_tabela == "cidade":
                    defaults["ds_grupo"] = "SP"
                ValorAuxiliarGlobal.objects.create(
                    cd_tabela_auxiliar_global=table,
                    cd_valor=code,
                    **defaults,
                )
                current_count += 1
            next_number += 1


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_sync_recent_role_screens"),
        ("core", "0023_seed_minimum_test_auxiliary_values"),
    ]

    operations = [
        migrations.RunPython(refresh_minimum_values, migrations.RunPython.noop),
    ]
