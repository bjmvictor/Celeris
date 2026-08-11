"""Cadastra tipos de prestador e ocupações CBO."""

from django.db import migrations

from apps.core.operacoes_migracao.ocupacoes_cbo_0012 import (
    OCUPACOES_CBO,
)


TIPOS_PRESTADOR = [
    ("MEDICO", "MÉDICO"),
    ("BIOMEDICO", "BIOMÉDICO"),
    ("ENFERMEIRO", "ENFERMEIRO"),
    ("TECNICO_ENFERMAGEM", "TÉCNICO DE ENFERMAGEM"),
    ("AUXILIAR_ENFERMAGEM", "AUXILIAR DE ENFERMAGEM"),
    ("FISIOTERAPEUTA", "FISIOTERAPEUTA"),
    ("PSICOLOGO", "PSICÓLOGO"),
    ("NUTRICIONISTA", "NUTRICIONISTA"),
    ("FONOAUDIOLOGO", "FONOAUDIÓLOGO"),
    ("FARMACEUTICO", "FARMACÊUTICO"),
    ("DENTISTA", "CIRURGIÃO-DENTISTA"),
    ("TERAPEUTA_OCUPACIONAL", "TERAPEUTA OCUPACIONAL"),
    ("ASSISTENTE_SOCIAL", "ASSISTENTE SOCIAL"),
    ("TECNICO_RADIOLOGIA", "TÉCNICO EM RADIOLOGIA"),
    ("TECNICO_LABORATORIO", "TÉCNICO DE LABORATÓRIO"),
    ("OUTRO", "OUTRO"),
]


def seed_provider_types(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_tipo, _ = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .get_or_create(
            ds_tabela="tipo_prestador",
            defaults={
                "ds_descricao": "Tipos de prestador",
                "sn_ativo": True,
            },
        )
    )

    for codigo, descricao in TIPOS_PRESTADOR:
        (
            ValorAuxiliarGlobal.objects
            .using(db_alias)
            .update_or_create(
                cd_tabela_auxiliar_global=tabela_tipo,
                cd_valor=codigo,
                defaults={
                    "ds_valor": descricao,
                    "ds_grupo": "",
                    "sn_ativo": True,
                },
            )
        )


def seed_cbo(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_cbo, _ = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .get_or_create(
            ds_tabela="cbo",
            defaults={
                "ds_descricao": (
                    "Classificação Brasileira de Ocupações"
                ),
                "sn_ativo": True,
            },
        )
    )

    codigos_existentes = set(
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_cbo,
        )
        .values_list(
            "cd_valor",
            flat=True,
        )
    )

    novas_ocupacoes = [
        ValorAuxiliarGlobal(
            cd_tabela_auxiliar_global=tabela_cbo,
            cd_valor=codigo,
            ds_valor=descricao,
            ds_grupo=familia,
            sn_ativo=True,
        )
        for codigo, descricao, familia
        in OCUPACOES_CBO
        if codigo not in codigos_existentes
    ]

    ValorAuxiliarGlobal.objects.using(
        db_alias
    ).bulk_create(
        novas_ocupacoes,
        batch_size=500,
    )


def unseed_provider_types(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_tipo = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            ds_tabela="tipo_prestador",
        )
        .first()
    )

    if tabela_tipo is None:
        return

    codigos = [
        codigo
        for codigo, _ in TIPOS_PRESTADOR
    ]

    (
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_tipo,
            cd_valor__in=codigos,
        )
        .delete()
    )


def unseed_cbo(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_cbo = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            ds_tabela="cbo",
        )
        .first()
    )

    if tabela_cbo is None:
        return

    codigos = [
        codigo
        for codigo, _, _
        in OCUPACOES_CBO
    ]

    (
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_cbo,
            cd_valor__in=codigos,
        )
        .delete()
    )


def seed(apps, schema_editor):
    seed_provider_types(
        apps,
        schema_editor,
    )
    seed_cbo(
        apps,
        schema_editor,
    )


def unseed(apps, schema_editor):
    unseed_cbo(
        apps,
        schema_editor,
    )
    unseed_provider_types(
        apps,
        schema_editor,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0011_seed_patient_auxiliaries",
        ),
    ]

    operations = [
        migrations.RunPython(
            seed,
            unseed,
        ),
    ]