from django.db import migrations


TABLE_VALUES = {
    "genero": [
        ("", ""),
        ("FEMININO", "FEMININO"),
        ("MASCULINO", "MASCULINO"),
        ("NAO_BINARIO", "NÃO BINÁRIO"),
        ("TRANSGENERO", "TRANSGÊNERO"),
        ("OUTRO", "OUTRO"),
    ],
    "cor_raca": [
        ("BRANCA", "BRANCA"),
        ("PRETA", "PRETA"),
        ("PARDA", "PARDA"),
        ("AMARELA", "AMARELA"),
        ("INDIGENA", "INDÍGENA"),
        ("NAO_INFORMADA", "NÃO INFORMADA"),
    ],
    "pais": [
        ("BRASIL", "BRASIL"),
        ("ARGENTINA", "ARGENTINA"),
        ("BOLIVIA", "BOLÍVIA"),
        ("CHILE", "CHILE"),
        ("COLOMBIA", "COLÔMBIA"),
        ("PARAGUAI", "PARAGUAI"),
        ("PERU", "PERU"),
        ("PORTUGAL", "PORTUGAL"),
        ("URUGUAI", "URUGUAI"),
        ("VENEZUELA", "VENEZUELA"),
        ("OUTRO", "OUTRO"),
    ],
}

CITY_VALUES = [
    ("AC", "RIO_BRANCO", "RIO BRANCO"),
    ("AL", "MACEIO", "MACEIÓ"),
    ("AP", "MACAPA", "MACAPÁ"),
    ("AM", "MANAUS", "MANAUS"),
    ("BA", "SALVADOR", "SALVADOR"),
    ("BA", "FEIRA_DE_SANTANA", "FEIRA DE SANTANA"),
    ("CE", "FORTALEZA", "FORTALEZA"),
    ("DF", "BRASILIA", "BRASÍLIA"),
    ("ES", "VITORIA", "VITÓRIA"),
    ("ES", "VILA_VELHA", "VILA VELHA"),
    ("GO", "GOIANIA", "GOIÂNIA"),
    ("MA", "SAO_LUIS", "SÃO LUÍS"),
    ("MT", "CUIABA", "CUIABÁ"),
    ("MS", "CAMPO_GRANDE", "CAMPO GRANDE"),
    ("MG", "BELO_HORIZONTE", "BELO HORIZONTE"),
    ("MG", "UBERLANDIA", "UBERLÂNDIA"),
    ("PA", "BELEM", "BELÉM"),
    ("PB", "JOAO_PESSOA", "JOÃO PESSOA"),
    ("PR", "CURITIBA", "CURITIBA"),
    ("PR", "LONDRINA", "LONDRINA"),
    ("PE", "RECIFE", "RECIFE"),
    ("PE", "JABOATAO_DOS_GUARARAPES", "JABOATÃO DOS GUARARAPES"),
    ("PI", "TERESINA", "TERESINA"),
    ("RJ", "RIO_DE_JANEIRO", "RIO DE JANEIRO"),
    ("RJ", "NITEROI", "NITERÓI"),
    ("RN", "NATAL", "NATAL"),
    ("RS", "PORTO_ALEGRE", "PORTO ALEGRE"),
    ("RS", "CAXIAS_DO_SUL", "CAXIAS DO SUL"),
    ("RO", "PORTO_VELHO", "PORTO VELHO"),
    ("RR", "BOA_VISTA", "BOA VISTA"),
    ("SC", "FLORIANOPOLIS", "FLORIANÓPOLIS"),
    ("SC", "JOINVILLE", "JOINVILLE"),
    ("SP", "SAO_PAULO", "SÃO PAULO"),
    ("SP", "CAMPINAS", "CAMPINAS"),
    ("SP", "SANTOS", "SANTOS"),
    ("SE", "ARACAJU", "ARACAJU"),
    ("TO", "PALMAS", "PALMAS"),
]


def seed(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for table_name, values in TABLE_VALUES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": table_name.replace("_", " ").title(), "sn_ativo": True},
        )
        for code, description in values:
            if not code:
                continue
            ValorAuxiliarGlobal.objects.get_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": True},
            )
    city_table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="cidade",
        defaults={"ds_descricao": "Cidades", "sn_ativo": True},
    )
    for state, code, description in CITY_VALUES:
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=city_table,
            cd_valor=code,
            defaults={"ds_valor": description, "ds_grupo": state, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_auxiliary_value_group"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
