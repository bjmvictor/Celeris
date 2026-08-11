"""Cadastra CID-10 e motivos de alta."""

from django.db import migrations

from apps.core.operacoes_migracao.cid10_0029 import (
    CID10,
)


MOTIVOS_ALTA = [
    ("MELHORA_CLINICA", "Melhora clínica"),
    ("ALTA_A_PEDIDO", "Alta a pedido"),
    ("TRANSFERENCIA", "Transferência"),
    ("ENCAMINHAMENTO", "Encaminhamento"),
    ("EVASAO", "Evasão"),
    ("OBITO", "Óbito"),
]


def seed_cids(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_cid, _ = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .update_or_create(
            ds_tabela="cids",
            defaults={
                "ds_descricao": "CID-10",
                "sn_ativo": True,
            },
        )
    )

    codigos_existentes = set(
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_cid,
        )
        .values_list(
            "cd_valor",
            flat=True,
        )
    )

    novos_cids = [
        ValorAuxiliarGlobal(
            cd_tabela_auxiliar_global=tabela_cid,
            cd_valor=codigo,
            ds_valor=descricao,
            ds_grupo=categoria,
            sn_ativo=True,
        )
        for codigo, descricao, categoria in CID10
        if codigo not in codigos_existentes
    ]

    ValorAuxiliarGlobal.objects.using(
        db_alias
    ).bulk_create(
        novos_cids,
        batch_size=1000,
    )


def seed_motivos_alta(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_motivos, _ = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .update_or_create(
            ds_tabela="motivos_alta",
            defaults={
                "ds_descricao": "Motivos de alta",
                "sn_ativo": True,
            },
        )
    )

    for codigo, descricao in MOTIVOS_ALTA:
        (
            ValorAuxiliarGlobal.objects
            .using(db_alias)
            .update_or_create(
                cd_tabela_auxiliar_global=tabela_motivos,
                cd_valor=codigo,
                defaults={
                    "ds_valor": descricao,
                    "ds_grupo": "",
                    "sn_ativo": True,
                },
            )
        )


def unseed_cids(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_cid = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .filter(ds_tabela="cids")
        .first()
    )

    if tabela_cid is None:
        return

    codigos = [
        codigo
        for codigo, _, _ in CID10
    ]

    (
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_cid,
            cd_valor__in=codigos,
        )
        .delete()
    )


def unseed_motivos_alta(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_motivos = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .filter(ds_tabela="motivos_alta")
        .first()
    )

    if tabela_motivos is None:
        return

    codigos = [
        codigo
        for codigo, _ in MOTIVOS_ALTA
    ]

    (
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_motivos,
            cd_valor__in=codigos,
        )
        .delete()
    )


def seed(apps, schema_editor):
    seed_cids(
        apps,
        schema_editor,
    )
    seed_motivos_alta(
        apps,
        schema_editor,
    )


def unseed(apps, schema_editor):
    unseed_motivos_alta(
        apps,
        schema_editor,
    )
    unseed_cids(
        apps,
        schema_editor,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0028_desativar_tela_atendimentos_pep",
        ),
    ]

    operations = [
        migrations.RunPython(
            seed,
            unseed,
        ),
    ]
