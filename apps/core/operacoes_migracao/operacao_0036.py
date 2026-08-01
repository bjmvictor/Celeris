"""Operações históricas de dados da migration 0036."""

from django.db import migrations


DESCRICOES_TABELAS = {
    "banco": "Bancos",
    "bairro": "Bairros",
    "cep": "CEPs",
    "cidade": "Cidades",
    "cids": "Classificação Internacional de Doenças (CID)",
    "conselho_profissional": "Conselhos profissionais",
    "cor_raca": "Cor/raça",
    "especialidade": "Especialidades",
    "estado": "Estados",
    "estado_civil": "Estados civis",
    "genero": "Gêneros",
    "grau_instrucao": "Graus de instrução",
    "identidade_genero": "Identidades de gênero",
    "idioma": "Idiomas",
    "meio_comunicacao": "Meios de comunicação",
    "meio_transporte": "Meios de transporte",
    "motivo_alteracao": "Motivos de alteração cadastral",
    "motivos_alta": "Motivos de alta",
    "nacionalidade": "Nacionalidades",
    "naturalidade": "Naturalidades",
    "orgao_emissor": "Órgãos emissores",
    "origem": "Origens do atendimento",
    "orientacao_sexual": "Orientações sexuais",
    "pais": "Países",
    "parentesco": "Parentescos",
    "profissao": "Profissões",
    "religiao": "Religiões",
    "setor_exame": "Setores de exames",
    "sexo": "Sexos",
    "tipo_identificador_pessoa": "Tipos de identificador de pessoa",
    "tipo_logradouro": "Tipos de logradouro",
    "tipo_moradia": "Tipos de moradia",
    "tipo_ocorrencia": "Tipos de ocorrência",
    "tipo_prestador": "Tipos de prestador",
    "tipo_sanguineo": "Tipos sanguíneos",
    "tipo_vinculo": "Tipos de vínculo",
    "vulnerabilidade_social": "Vulnerabilidades sociais",
}


VALORES_ESSENCIAIS = {
    "sexo": [
        ("F", "Feminino"),
        ("M", "Masculino"),
        ("I", "Intersexo"),
        ("N", "Não informado"),
    ],
    "estado_civil": [
        ("SOLTEIRO", "Solteiro(a)"),
        ("CASADO", "Casado(a)"),
        ("DIVORCIADO", "Divorciado(a)"),
        ("VIUVO", "Viúvo(a)"),
        ("UNIAO_ESTAVEL", "União estável"),
        ("NAO_INFORMADO", "Não informado"),
    ],
    "naturalidade": [
        ("BRASILEIRA", "Brasileira"),
        ("ESTRANGEIRA", "Estrangeira"),
    ],
    "nacionalidade": [
        ("BRASILEIRA", "Brasileira"),
        ("ESTRANGEIRA", "Estrangeira"),
    ],
    "motivo_alteracao": [
        ("CORRECAO_CADASTRAL", "Correção cadastral"),
        ("ATUALIZACAO_DOCUMENTAL", "Atualização documental"),
        ("SOLICITACAO_PACIENTE", "Solicitação do paciente"),
        ("REVISAO_ATENDIMENTO", "Revisão de atendimento"),
        ("OUTROS", "Outros"),
    ],
    "tipo_sanguineo": [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ],
    "idioma": [
        ("PT_BR", "Português - Brasil"),
        ("EN_US", "Inglês"),
        ("ES", "Espanhol"),
    ],
}


def normalizar_catalogos(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    Cep = apps.get_model("core", "Cep")

    ValorAuxiliarGlobal.objects.filter(cd_valor__startswith="TESTE_").delete()
    Cep.objects.filter(
        ds_logradouro__startswith="RUA TESTE ",
        ds_bairro__startswith="BAIRRO TESTE ",
    ).delete()

    for chave, descricao in DESCRICOES_TABELAS.items():
        tabela, _ = TabelaAuxiliarGlobal.objects.update_or_create(
            ds_tabela=chave,
            defaults={"ds_descricao": descricao, "sn_ativo": True},
        )
        for codigo, valor in VALORES_ESSENCIAIS.get(chave, []):
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=codigo,
                defaults={"ds_valor": valor, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0035_normalize_navigation_catalog"),
    ]

    operations = [
        migrations.RunPython(normalizar_catalogos, migrations.RunPython.noop),
    ]
