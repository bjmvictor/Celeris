from django.db import migrations


TABLES = {
    "bairro": ("Bairros", []),
    "conselho_profissional": (
        "Conselhos profissionais",
        [
            ("CRM", "CRM"),
            ("COREN", "COREN"),
            ("CRF", "CRF"),
            ("CRP", "CRP"),
            ("CRBM", "CRBM"),
            ("CREFITO", "CREFITO"),
            ("CRO", "CRO"),
            ("CREA", "CREA"),
            ("OAB", "OAB"),
        ],
    ),
    "orgao_emissor": (
        "Órgãos emissores",
        [
            ("SSP", "SSP"),
            ("SDS", "SDS"),
            ("SESP", "SESP"),
            ("IGP", "IGP"),
            ("PC", "POLÍCIA CIVIL"),
            ("DETRAN", "DETRAN"),
            ("MD", "MINISTÉRIO DA DEFESA"),
            ("EB", "EXÉRCITO BRASILEIRO"),
            ("MB", "MARINHA DO BRASIL"),
            ("FAB", "FORÇA AÉREA BRASILEIRA"),
            ("PF", "POLÍCIA FEDERAL"),
            ("MJ", "MINISTÉRIO DA JUSTIÇA"),
            ("CREA", "CREA"),
            ("OAB", "OAB"),
            ("CRM", "CRM"),
            ("COREN", "COREN"),
            ("CRF", "CRF"),
            ("CRP", "CRP"),
        ],
    ),
}


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for table_name, (description, values) in TABLES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": description, "sn_ativo": True},
        )
        if table.ds_descricao != description:
            table.ds_descricao = description
            table.save(update_fields=["ds_descricao"])
        for code, value in values:
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
                defaults={"ds_valor": value, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_seed_provider_auxiliaries"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
