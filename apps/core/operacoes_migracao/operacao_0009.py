"""Operações históricas de dados da migration 0009."""

from django.db import migrations


ESTADOS = [
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
]


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    tabela_estado, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="estado",
        defaults={
            "ds_descricao": "Estado",
            "sn_ativo": True,
        },
    )

    codigos_existentes = set(
        ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global=tabela_estado,
        ).values_list("cd_valor", flat=True)
    )

    novos_estados = [
        ValorAuxiliarGlobal(
            cd_tabela_auxiliar_global=tabela_estado,
            cd_valor=sigla,
            ds_valor=nome,
            sn_ativo=True,
        )
        for sigla, nome in ESTADOS
        if sigla not in codigos_existentes
    ]

    ValorAuxiliarGlobal.objects.bulk_create(
        novos_estados,
        batch_size=100,
    )


def unseed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    tabela_estado = TabelaAuxiliarGlobal.objects.filter(
        ds_tabela="estado",
    ).first()

    if tabela_estado is None:
        return

    ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global=tabela_estado,
        cd_valor__in=[sigla for sigla, _ in ESTADOS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_global_auxiliary_tables"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]