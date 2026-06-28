from django.db import migrations


MINIMUM_ITEMS = 30


TABLE_DESCRIPTIONS = {
    "banco": "Bancos",
    "cidade": "Cidades",
    "conselho_profissional": "Conselhos profissionais",
    "cor_raca": "Cor/raca",
    "estado": "Estados",
    "genero": "Generos",
    "grau_instrucao": "Graus de instrucao",
    "identidade_genero": "Identidades de genero",
    "idioma": "Idiomas",
    "meio_comunicacao": "Meios de comunicacao",
    "meio_transporte": "Meios de transporte",
    "orgao_emissor": "Orgaos emissores",
    "origem": "Origens",
    "orientacao_sexual": "Orientacoes sexuais",
    "pais": "Paises",
    "parentesco": "Parentescos",
    "profissao": "Profissoes",
    "religiao": "Religioes",
    "setor_exame": "Setores de exame",
    "tipo_identificador_pessoa": "Tipos de identificador de pessoa",
    "tipo_logradouro": "Tipos de logradouro",
    "tipo_moradia": "Tipos de moradia",
    "tipo_ocorrencia": "Tipos de ocorrencia",
    "tipo_prestador": "Tipos de prestador",
    "tipo_sanguineo": "Tipos sanguineos",
    "tipo_vinculo": "Tipos de vinculo",
    "vulnerabilidade_social": "Vulnerabilidades sociais",
}


def normalize_code(value):
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    return re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_")[:40]


def seed_auxiliary_values(apps):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")

    for table_name, description in TABLE_DESCRIPTIONS.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": description, "sn_ativo": True},
        )
        if not table.ds_descricao:
            table.ds_descricao = description
            table.save(update_fields=["ds_descricao"])

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
                description = f"{table.ds_descricao or table.ds_tabela} Teste {next_number:03d}".upper()
                defaults = {"ds_valor": description, "sn_ativo": True}
                if table.ds_tabela == "cidade":
                    defaults["ds_grupo"] = "SP"
                ValorAuxiliarGlobal.objects.create(
                    cd_tabela_auxiliar_global=table,
                    cd_valor=code,
                    **defaults,
                )
                current_count += 1
            next_number += 1


def seed_ceps(apps):
    Cep = apps.get_model("core", "Cep")

    current_count = Cep.objects.filter(sn_ativo=True).count()
    next_number = 1
    while current_count < MINIMUM_ITEMS:
        cep = f"010{next_number:05d}"[:8]
        if not Cep.objects.filter(nr_cep=cep).exists():
            Cep.objects.create(
                nr_cep=cep,
                sg_estado="SP",
                cd_cidade="SAO_PAULO",
                ds_cidade="SAO PAULO",
                tp_logradouro="RUA",
                ds_logradouro=f"RUA TESTE {next_number:03d}",
                ds_bairro=f"BAIRRO TESTE {next_number:03d}",
                sn_ativo=True,
            )
            current_count += 1
        next_number += 1


def seed(apps, schema_editor):
    seed_auxiliary_values(apps)
    seed_ceps(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_populate_dynamic_screen_access_keys"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
