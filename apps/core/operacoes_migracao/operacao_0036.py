"""Cadastra catálogos essenciais ainda não definidos."""

from django.db import migrations


CATALOGOS = {
    "estado_civil": {
        "descricao": "Estados civis",
        "valores": [
            ("SOLTEIRO", "Solteiro(a)"),
            ("CASADO", "Casado(a)"),
            ("DIVORCIADO", "Divorciado(a)"),
            ("VIUVO", "Viúvo(a)"),
            ("UNIAO_ESTAVEL", "União estável"),
            ("NAO_INFORMADO", "Não informado"),
        ],
    },
    "motivo_alteracao": {
        "descricao": "Motivos de alteração cadastral",
        "valores": [
            ("CORRECAO_CADASTRAL", "Correção cadastral"),
            (
                "ATUALIZACAO_DOCUMENTAL",
                "Atualização documental",
            ),
            (
                "SOLICITACAO_PACIENTE",
                "Solicitação do paciente",
            ),
            (
                "REVISAO_ATENDIMENTO",
                "Revisão de atendimento",
            ),
            ("OUTROS", "Outros"),
        ],
    },
    "tipo_sanguineo": {
        "descricao": "Tipos sanguíneos",
        "valores": [
            ("A_POSITIVO", "A+"),
            ("A_NEGATIVO", "A-"),
            ("B_POSITIVO", "B+"),
            ("B_NEGATIVO", "B-"),
            ("AB_POSITIVO", "AB+"),
            ("AB_NEGATIVO", "AB-"),
            ("O_POSITIVO", "O+"),
            ("O_NEGATIVO", "O-"),
        ],
    },
    "idioma": {
        "descricao": "Idiomas",
        "valores": [
            ("PT_BR", "Português - Brasil"),
            ("EN_US", "Inglês"),
            ("ES", "Espanhol"),
        ],
    },
}


def normalizar_catalogos(apps, schema_editor):
    """Compatibiliza a limpeza histórica e mantém somente catálogos úteis."""
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    Cep = apps.get_model("core", "Cep")

    ValorAuxiliarGlobal.objects.filter(cd_valor__startswith="TESTE_").delete()
    Cep.objects.filter(
        ds_logradouro__startswith="RUA TESTE ",
        ds_bairro__startswith="BAIRRO TESTE ",
    ).delete()

    sexo, _ = TabelaAuxiliarGlobal.objects.update_or_create(
        ds_tabela="sexo",
        defaults={"ds_descricao": "Sexos", "sn_ativo": True},
    )
    for codigo, descricao in (
        ("F", "Feminino"),
        ("M", "Masculino"),
        ("I", "Intersexo"),
        ("N", "Não informado"),
    ):
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=sexo,
            cd_valor=codigo,
            defaults={"ds_valor": descricao, "ds_grupo": "", "sn_ativo": True},
        )


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

    for chave, configuracao in CATALOGOS.items():
        tabela, _ = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .get_or_create(
                ds_tabela=chave,
                defaults={
                    "ds_descricao": configuracao["descricao"],
                    "sn_ativo": True,
                },
            )
        )

        for codigo, descricao in configuracao["valores"]:
            (
                ValorAuxiliarGlobal.objects
                .using(db_alias)
                .update_or_create(
                    cd_tabela_auxiliar_global=tabela,
                    cd_valor=codigo,
                    defaults={
                        "ds_valor": descricao,
                        "ds_grupo": "",
                        "sn_ativo": True,
                    },
                )
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

    for chave, configuracao in CATALOGOS.items():
        tabela = (
            TabelaAuxiliarGlobal.objects
            .using(db_alias)
            .filter(ds_tabela=chave)
            .first()
        )

        if tabela is None:
            continue

        codigos = [
            codigo
            for codigo, _ in configuracao["valores"]
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
        ("core", "0035_normalize_navigation_catalog"),
    ]

    operations = [
        migrations.RunPython(
            seed,
            unseed,
        ),
    ]
