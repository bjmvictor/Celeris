"""Cadastra profissões CBO e demais tabelas auxiliares."""

import re
import unicodedata

from django.db import migrations

from apps.core.operacoes_migracao.ocupacoes_cbo_0012 import (
    OCUPACOES_CBO,
)


TABLES = {
    "orgao_emissor": [
        "SSP",
        "DETRAN",
        "CRM",
        "COREN",
        "CRBM",
        "CRO",
        "OUTRO",
    ],
    "tipo_logradouro": [
        "RUA",
        "AVENIDA",
        "TRAVESSA",
        "ALAMEDA",
        "RODOVIA",
        "ANEL VIÁRIO",
        "AEROPORTO",
        "ENGENHO",
        "ZONA RURAL",
        "OUTRO",
    ],
    "tipo_vinculo": [
        "CLT",
        "CNPJ",
        "COOPERADO",
        "PRESTADOR DE SERVIÇO",
        "SÓCIO",
        "AUTÔNOMO",
        "OUTRO",
    ],
    "religiao": [
        "CATÓLICA",
        "EVANGÉLICA",
        "ESPÍRITA",
        "UMBANDA",
        "CANDOMBLÉ",
        "SEM RELIGIÃO",
        "OUTRA",
    ],
    "tipo_moradia": [
        "PRÓPRIA",
        "ALUGADA",
        "CEDIDA",
        "SITUAÇÃO DE RUA",
        "OUTRA",
    ],
    "parentesco": [
        "MÃE",
        "PAI",
        "FILHO(A)",
        "CÔNJUGE",
        "IRMÃO(Ã)",
        "RESPONSÁVEL",
        "OUTRO",
    ],
    "meio_comunicacao": [
        "TELEFONE",
        "CELULAR",
        "E-MAIL",
        "APLICATIVO",
        "OUTRO",
    ],
    "meio_transporte": [
        "A PÉ",
        "CARRO",
        "MOTO",
        "ÔNIBUS",
        "AMBULÂNCIA",
        "OUTRO",
    ],
    "vulnerabilidade_social": [
        "NENHUMA",
        "BAIXA",
        "MODERADA",
        "ALTA",
        "EXTREMA",
    ],
    "tipo_identificador_pessoa": [
        "CPF",
        "CNS",
        "RG",
        "PASSAPORTE",
        "OUTRO",
    ],
    "origem": [
        "AGENDAMENTO",
        "EMERGÊNCIA",
        "AMBULATORIAL",
        "ENCAMINHAMENTO",
        "TRANSFERÊNCIA",
    ],
    "setor_exame": [
        "LABORATÓRIO",
        "OUTRO",
    ],
    "tipo_ocorrencia": [
        "ASSISTENCIAL",
        "ADMINISTRATIVA",
        "SEGURANÇA",
        "OUTRA",
    ],
}


TABLE_DESCRIPTIONS = {
    "orgao_emissor": "Órgãos emissores",
    "tipo_logradouro": "Tipos de logradouro",
    "tipo_vinculo": "Tipos de vínculo",
    "religiao": "Religiões",
    "tipo_moradia": "Tipos de moradia",
    "parentesco": "Parentescos",
    "meio_comunicacao": "Meios de comunicação",
    "meio_transporte": "Meios de transporte",
    "vulnerabilidade_social": "Vulnerabilidades sociais",
    "tipo_identificador_pessoa": "Tipos de identificador de pessoa",
    "origem": "Origens",
    "setor_exame": "Setores de exame",
    "tipo_ocorrencia": "Tipos de ocorrência",
}


def code(value):
    normalized = unicodedata.normalize(
        "NFD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    return re.sub(
        r"[^A-Z0-9]+",
        "_",
        normalized.upper(),
    ).strip("_")[:40]


def seed_professions(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_profissao, _ = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .get_or_create(
            ds_tabela="profissao",
            defaults={
                "ds_descricao": "Profissões",
                "sn_ativo": True,
            },
        )
    )

    codigos_existentes = set(
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_profissao,
        )
        .values_list(
            "cd_valor",
            flat=True,
        )
    )

    novas_profissoes = [
        ValorAuxiliarGlobal(
            cd_tabela_auxiliar_global=tabela_profissao,
            cd_valor=codigo_cbo,
            ds_valor=descricao,
            ds_grupo=familia_cbo,
            sn_ativo=True,
        )
        for codigo_cbo, descricao, familia_cbo
        in OCUPACOES_CBO
        if codigo_cbo not in codigos_existentes
    ]

    ValorAuxiliarGlobal.objects.using(
        db_alias
    ).bulk_create(
        novas_profissoes,
        batch_size=500,
    )


def seed_simple_tables(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    for table_name, descriptions in TABLES.items():
        table, _ = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .get_or_create(
                ds_tabela=table_name,
                defaults={
                    "ds_descricao": TABLE_DESCRIPTIONS.get(
                        table_name,
                        table_name.replace(
                            "_",
                            " ",
                        ).title(),
                    ),
                    "sn_ativo": True,
                },
            )
        )

        for description in descriptions:
            (
                ValorAuxiliarGlobal.objects
                .using(db_alias)
                .update_or_create(
                    cd_tabela_auxiliar_global=table,
                    cd_valor=code(description),
                    defaults={
                        "ds_valor": description,
                        "ds_grupo": "",
                        "sn_ativo": True,
                    },
                )
            )


def seed(apps, schema_editor):
    seed_professions(
        apps,
        schema_editor,
    )

    seed_simple_tables(
        apps,
        schema_editor,
    )


def unseed_professions(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    tabela_profissao = (
        TabelaAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            ds_tabela="profissao",
        )
        .first()
    )

    if tabela_profissao is None:
        return

    codigos_cbo = [
        codigo_cbo
        for codigo_cbo, _, _
        in OCUPACOES_CBO
    ]

    (
        ValorAuxiliarGlobal.objects
        .using(db_alias)
        .filter(
            cd_tabela_auxiliar_global=tabela_profissao,
            cd_valor__in=codigos_cbo,
        )
        .delete()
    )


def unseed_simple_tables(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    for table_name, descriptions in TABLES.items():
        table = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .filter(
                ds_tabela=table_name,
            )
            .first()
        )

        if table is None:
            continue

        codigos = [
            code(description)
            for description in descriptions
        ]

        (
            ValorAuxiliarGlobal.objects
            .using(db_alias)
            .filter(
                cd_tabela_auxiliar_global=table,
                cd_valor__in=codigos,
            )
            .delete()
        )


def unseed(apps, schema_editor):
    unseed_simple_tables(
        apps,
        schema_editor,
    )

    unseed_professions(
        apps,
        schema_editor,
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0014_seed_tipo_prestador_conselho",
        ),
    ]

    operations = [
        migrations.RunPython(
            seed,
            unseed,
        ),
    ]