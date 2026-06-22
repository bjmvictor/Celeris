from django.db import migrations


TABLES = {
    "grau_instrucao": [
        ("NAO_ALFABETIZADO", "NÃO ALFABETIZADO"),
        ("FUNDAMENTAL_INCOMPLETO", "ENSINO FUNDAMENTAL INCOMPLETO"),
        ("FUNDAMENTAL_COMPLETO", "ENSINO FUNDAMENTAL COMPLETO"),
        ("MEDIO_INCOMPLETO", "ENSINO MÉDIO INCOMPLETO"),
        ("MEDIO_COMPLETO", "ENSINO MÉDIO COMPLETO"),
        ("SUPERIOR_INCOMPLETO", "ENSINO SUPERIOR INCOMPLETO"),
        ("SUPERIOR_COMPLETO", "ENSINO SUPERIOR COMPLETO"),
        ("POS_GRADUACAO", "PÓS-GRADUAÇÃO"),
    ],
    "identidade_genero": [
        ("MULHER_CIS", "MULHER CISGÊNERO"),
        ("HOMEM_CIS", "HOMEM CISGÊNERO"),
        ("MULHER_TRANS", "MULHER TRANSGÊNERO"),
        ("HOMEM_TRANS", "HOMEM TRANSGÊNERO"),
        ("NAO_BINARIO", "NÃO BINÁRIO"),
        ("OUTRA", "OUTRA"),
        ("NAO_INFORMADA", "NÃO INFORMADA"),
    ],
    "banco": [
        ("001", "BANCO DO BRASIL"),
        ("033", "SANTANDER"),
        ("104", "CAIXA ECONÔMICA FEDERAL"),
        ("237", "BRADESCO"),
        ("260", "NUBANK"),
        ("341", "ITAÚ"),
        ("756", "SICOOB"),
    ],
}


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for table_name, values in TABLES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": table_name.replace("_", " ").title(), "sn_ativo": True},
        )
        for code, description in values:
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": True},
            )
    TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="cep",
        defaults={"ds_descricao": "CEPs", "sn_ativo": True},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_seed_erp_auxiliaries"),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
