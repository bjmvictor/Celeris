"""Cadastra domínios sociodemográficos oficiais."""

from django.db import migrations

from apps.core.operacoes_migracao.paises_ibge_0011 import PAISES


DADOS_ESTATICOS = {
    "raca_cor": {
        "descricao": "Raça/Cor",
        "valores": [
            ("01", "BRANCA", True),
            ("02", "PRETA", True),
            ("03", "PARDA", True),
            ("04", "AMARELA", True),
            ("05", "INDÍGENA", True),
            ("99", "SEM INFORMAÇÃO", False),
        ],
    },
    "sexo": {
        "descricao": "Sexo",
        "valores": [
            ("M", "MASCULINO", True),
            ("F", "FEMININO", True),
            ("I", "INDETERMINADO", True),
        ],
    },
    "nacionalidade": {
        "descricao": "Nacionalidade",
        "valores": [
            ("BRASILEIRA", "BRASILEIRA", True),
            ("NATURALIZADA", "NATURALIZADA", True),
            ("ESTRANGEIRA", "ESTRANGEIRA", True),
        ],
    },
    "identidade_genero": {
        "descricao": "Identidade de gênero",
        "valores": [
            ("HOMEM_CIS", "HOMEM CISGÊNERO", True),
            ("MULHER_CIS", "MULHER CISGÊNERO", True),
            ("HOMEM_TRANS", "HOMEM TRANSGÊNERO", True),
            ("MULHER_TRANS", "MULHER TRANSGÊNERO", True),
            ("TRAVESTI", "TRAVESTI", True),
            ("NAO_BINARIO", "NÃO BINÁRIO", True),
            ("OUTRO", "OUTRO", True),
        ],
    },
    "orientacao_sexual": {
        "descricao": "Orientação sexual",
        "valores": [
            ("HETEROSSEXUAL", "HETEROSSEXUAL", True),
            ("GAY", "GAY", True),
            ("LESBICA", "LÉSBICA", True),
            ("BISSEXUAL", "BISSEXUAL", True),
            ("ASSEXUAL", "ASSEXUAL", True),
            ("PANSEXUAL", "PANSEXUAL", True),
            ("OUTRO", "OUTRO", True),
        ],
    },
    "pais": {
        "descricao": "País",
        "valores": [
            (codigo, nome, True)
            for codigo, nome in PAISES
        ],
    },
}


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    db_alias = schema_editor.connection.alias

    for nome_tabela, configuracao in DADOS_ESTATICOS.items():
        tabela, _ = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .get_or_create(
                ds_tabela=nome_tabela,
                defaults={
                    "ds_descricao": configuracao["descricao"],
                    "sn_ativo": True,
                },
            )
        )

        codigos_existentes = set(
            ValorAuxiliarGlobal.objects
            .using(db_alias)
            .filter(
                cd_tabela_auxiliar_global=tabela,
            )
            .values_list(
                "cd_valor",
                flat=True,
            )
        )

        novos_valores = [
            ValorAuxiliarGlobal(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=codigo,
                ds_valor=descricao,
                ds_grupo="",
                sn_ativo=ativo,
            )
            for codigo, descricao, ativo
            in configuracao["valores"]
            if codigo not in codigos_existentes
        ]

        ValorAuxiliarGlobal.objects.using(
            db_alias
        ).bulk_create(
            novos_valores,
            batch_size=500,
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

    db_alias = schema_editor.connection.alias

    for nome_tabela, configuracao in DADOS_ESTATICOS.items():
        tabela = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .filter(ds_tabela=nome_tabela)
            .first()
        )

        if tabela is None:
            continue

        codigos = [
            codigo
            for codigo, _, _
            in configuracao["valores"]
        ]

        (
            ValorAuxiliarGlobal.objects
            .using(db_alias)
            .filter(
                cd_tabela_auxiliar_global=tabela,
                cd_valor__in=codigos,
            )
            .delete()
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_add_group_and_seed_cities"),
    ]

    operations = [
        migrations.RunPython(
            seed,
            unseed,
        ),
    ]
