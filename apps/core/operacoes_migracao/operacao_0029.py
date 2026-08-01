"""Operações históricas de dados da migration 0029."""

from django.db import migrations


CID_VALUES = [
    ("A00", "Cólera"),
    ("A09", "Diarreia e gastroenterite de origem infecciosa presumível"),
    ("B34", "Doenças por vírus, de localização não especificada"),
    ("E11", "Diabetes mellitus não-insulino-dependente"),
    ("I10", "Hipertensão essencial primária"),
    ("J06", "Infecções agudas das vias aéreas superiores de localizações múltiplas e não especificadas"),
    ("J18", "Pneumonia por microrganismo não especificada"),
    ("K35", "Apendicite aguda"),
    ("M54", "Dorsalgia"),
    ("R10", "Dor abdominal e pélvica"),
    ("R50", "Febre de origem desconhecida"),
    ("S06", "Traumatismo intracraniano"),
    ("S72", "Fratura do fêmur"),
    ("Z00", "Exame geral e investigação de pessoas sem queixas ou diagnóstico relatado"),
]


MOTIVOS_ALTA = [
    ("MELHORA_CLINICA", "Melhora clínica"),
    ("ALTA_A_PEDIDO", "Alta a pedido"),
    ("TRANSFERENCIA", "Transferência"),
    ("ENCAMINHAMENTO", "Encaminhamento"),
    ("EVASAO", "Evasão"),
    ("OBITO", "Óbito"),
]


def seed_discharge_auxiliaries(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")

    cids, _ = TabelaAuxiliarGlobal.objects.update_or_create(
        ds_tabela="cids",
        defaults={"ds_descricao": "CIDS", "sn_ativo": True},
    )
    for code, description in CID_VALUES:
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=cids,
            cd_valor=code,
            defaults={"ds_valor": description, "sn_ativo": True},
        )

    motivos, _ = TabelaAuxiliarGlobal.objects.update_or_create(
        ds_tabela="motivos_alta",
        defaults={"ds_descricao": "Motivos de alta", "sn_ativo": True},
    )
    for code, description in MOTIVOS_ALTA:
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=motivos,
            cd_valor=code,
            defaults={"ds_valor": description, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_desativar_tela_atendimentos_pep"),
    ]

    operations = [
        migrations.RunPython(seed_discharge_auxiliaries, migrations.RunPython.noop),
    ]
