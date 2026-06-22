from django.db import migrations


TABLES = {
    "profissao": ["MÉDICO", "ENFERMEIRO", "TÉCNICO DE ENFERMAGEM", "PROFESSOR", "ADMINISTRATIVO", "AUTÔNOMO", "OUTRO"],
    "orgao_emissor": ["SSP", "DETRAN", "CRM", "COREN", "CRBM", "CRO", "OUTRO"],
    "tipo_logradouro": ["RUA", "AVENIDA", "TRAVESSA", "ALAMEDA", "RODOVIA", "ANEL VIÁRIO", "AEROPORTO", "ACESSO", "ACAMPAMENTO", "OUTRO"],
    "tipo_vinculo": ["CLT", "ESTATUTÁRIO", "PRESTADOR DE SERVIÇO", "COOPERADO", "SÓCIO", "AUTÔNOMO", "OUTRO"],
    "religiao": ["CATÓLICA", "EVANGÉLICA", "ESPÍRITA", "UMBANDA", "CANDOMBLÉ", "SEM RELIGIÃO", "OUTRA"],
    "tipo_moradia": ["PRÓPRIA", "ALUGADA", "CEDIDA", "SITUAÇÃO DE RUA", "OUTRA"],
    "parentesco": ["MÃE", "PAI", "FILHO(A)", "CÔNJUGE", "IRMÃO(Ã)", "RESPONSÁVEL", "OUTRO"],
    "meio_comunicacao": ["TELEFONE", "CELULAR", "E-MAIL", "APLICATIVO", "OUTRO"],
    "meio_transporte": ["A PÉ", "CARRO", "MOTO", "ÔNIBUS", "AMBULÂNCIA", "OUTRO"],
    "orientacao_sexual": ["HETEROSSEXUAL", "HOMOSSEXUAL", "BISSEXUAL", "ASSEXUAL", "OUTRA", "NÃO INFORMADA"],
    "vulnerabilidade_social": ["NENHUMA", "BAIXA", "MODERADA", "ALTA", "EXTREMA"],
    "tipo_identificador_pessoa": ["CPF", "CNS", "RG", "PASSAPORTE", "OUTRO"],
    "origem": ["DEMANDA ESPONTÂNEA", "AGENDAMENTO", "ENCAMINHAMENTO", "TRANSFERÊNCIA"],
    "setor_exame": ["LABORATÓRIO", "IMAGEM", "CARDIOLOGIA", "ENDOSCOPIA", "OUTRO"],
    "tipo_ocorrencia": ["ASSISTENCIAL", "ADMINISTRATIVA", "SEGURANÇA", "OUTRA"],
}


def code(value):
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    return re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_")[:40]


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for table_name, descriptions in TABLES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": table_name.replace("_", " ").title(), "sn_ativo": True},
        )
        for description in descriptions:
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code(description),
                defaults={"ds_valor": description, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_seed_tipo_prestador_conselho"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
