from django.db import migrations


DEFAULT_TABLES = {
    "carater-produto": {
        "nome": "Caráter de produto",
        "valores": [
            ("PADRAO", "Padrão"),
            ("CONTROLADO", "Controlado"),
            ("EMERGENCIAL", "Emergencial"),
            ("ALTO_CUSTO", "Alto custo"),
            ("CONSIGNADO", "Consignado"),
        ],
    },
    "classes-produto": {
        "nome": "Classes de produto",
        "valores": [
            ("MEDICAMENTO", "Medicamento"),
            ("MATERIAL_MEDICO", "Material médico"),
            ("MATERIAL_EXPEDIENTE", "Material de expediente"),
            ("SANEANTE", "Saneante"),
            ("DIETA", "Dieta"),
            ("OPME", "OPME"),
        ],
    },
}


def seed_product_tables(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    TabelaEstoque = apps.get_model("estoque", "TabelaEstoque")
    ValorTabelaEstoque = apps.get_model("estoque", "ValorTabelaEstoque")

    for empresa in Empresa.objects.all():
        for chave, config in DEFAULT_TABLES.items():
            tabela, _ = TabelaEstoque.objects.get_or_create(
                cd_empresa=empresa,
                ds_chave=chave,
                defaults={"ds_nome": config["nome"], "sn_ativo": True},
            )
            for codigo, valor in config["valores"]:
                ValorTabelaEstoque.objects.get_or_create(
                    cd_empresa=empresa,
                    cd_tabela=tabela,
                    cd_valor=codigo,
                    defaults={"ds_valor": valor, "sn_ativo": True},
                )


class Migration(migrations.Migration):
    dependencies = [
        ("estoque", "0001_initial"),
        ("accounts", "0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_product_tables, migrations.RunPython.noop),
    ]
