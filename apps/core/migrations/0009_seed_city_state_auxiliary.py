from django.db import migrations


VALUES = {
    "estado": [
        ("AC", "ACRE"),
        ("AL", "ALAGOAS"),
        ("AP", "AMAPÁ"),
        ("AM", "AMAZONAS"),
        ("BA", "BAHIA"),
        ("CE", "CEARÁ"),
        ("DF", "DISTRITO FEDERAL"),
        ("ES", "ESPÍRITO SANTO"),
        ("GO", "GOIÁS"),
        ("MA", "MARANHÃO"),
        ("MT", "MATO GROSSO"),
        ("MS", "MATO GROSSO DO SUL"),
        ("MG", "MINAS GERAIS"),
        ("PA", "PARÁ"),
        ("PB", "PARAÍBA"),
        ("PR", "PARANÁ"),
        ("PE", "PERNAMBUCO"),
        ("PI", "PIAUÍ"),
        ("RJ", "RIO DE JANEIRO"),
        ("RN", "RIO GRANDE DO NORTE"),
        ("RS", "RIO GRANDE DO SUL"),
        ("RO", "RONDÔNIA"),
        ("RR", "RORAIMA"),
        ("SC", "SANTA CATARINA"),
        ("SP", "SÃO PAULO"),
        ("SE", "SERGIPE"),
        ("TO", "TOCANTINS"),
    ],
    "cidade": [
        ("SAO_PAULO", "SÃO PAULO"),
        ("RIO_DE_JANEIRO", "RIO DE JANEIRO"),
        ("BELO_HORIZONTE", "BELO HORIZONTE"),
        ("CURITIBA", "CURITIBA"),
        ("PORTO_ALEGRE", "PORTO ALEGRE"),
        ("BRASILIA", "BRASÍLIA"),
    ],
}


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for table_name, values in VALUES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": table_name.replace("_", " ").title(), "sn_ativo": True},
        )
        for code, description in values:
            ValorAuxiliarGlobal.objects.get_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_global_auxiliary_tables"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
