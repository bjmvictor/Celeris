"""Operações históricas de dados da migration 0023."""

from django.db import migrations


DESCRICOES_TABELAS = {
    "banco": "Bancos",
    "cidade": "Cidades",
    "conselho_profissional": "Conselhos profissionais",
    "cor_raca": "Cor/raça",
    "estado": "Estados",
    "genero": "Gêneros",
    "grau_instrucao": "Graus de instrução",
    "identidade_genero": "Identidades de gênero",
    "idioma": "Idiomas",
    "meio_comunicacao": "Meios de comunicação",
    "meio_transporte": "Meios de transporte",
    "orgao_emissor": "Órgãos emissores",
    "origem": "Origens de atendimento",
    "orientacao_sexual": "Orientações sexuais",
    "pais": "Países",
    "parentesco": "Parentescos",
    "profissao": "Profissões",
    "religiao": "Religiões",
    "setor_exame": "Setores de exame",
    "tipo_identificador_pessoa": "Tipos de identificador de pessoa",
    "tipo_logradouro": "Tipos de logradouro",
    "tipo_moradia": "Tipos de moradia",
    "tipo_ocorrencia": "Tipos de ocorrência",
    "tipo_prestador": "Tipos de prestador",
    "tipo_sanguineo": "Tipos sanguíneos",
    "tipo_vinculo": "Tipos de vínculo",
    "vulnerabilidade_social": "Vulnerabilidades sociais",
}


def cadastrar_tabelas_auxiliares(apps):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")

    for nome_tabela, descricao in DESCRICOES_TABELAS.items():
        TabelaAuxiliarGlobal.objects.update_or_create(
            ds_tabela=nome_tabela,
            defaults={"ds_descricao": descricao, "sn_ativo": True},
        )


def cadastrar_catalogos(apps, schema_editor):
    cadastrar_tabelas_auxiliares(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_populate_dynamic_screen_access_keys"),
    ]

    operations = [
        migrations.RunPython(cadastrar_catalogos, migrations.RunPython.noop),
    ]
