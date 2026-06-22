from django.db import migrations


MAPPINGS = [
    ("MEDICO", "CRM"),
    ("BIOMEDICO", "CRBM"),
    ("ENFERMEIRO", "COREN"),
    ("TECNICO_ENFERMAGEM", "COREN"),
    ("FISIOTERAPEUTA", "CREFITO"),
    ("PSICOLOGO", "CRP"),
    ("NUTRICIONISTA", "CRN"),
    ("FONOAUDIOLOGO", "CREFONO"),
    ("FARMACEUTICO", "CRF"),
    ("DENTISTA", "CRO"),
]


def seed(apps, schema_editor):
    TipoPrestadorConselho = apps.get_model("core", "TipoPrestadorConselho")
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    provider_table = TabelaAuxiliarGlobal.objects.get(ds_tabela="tipo_prestador")
    for provider_type, council in MAPPINGS:
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=provider_table,
            cd_valor=provider_type,
            defaults={
                "ds_valor": provider_type.replace("_", " "),
                "sn_ativo": True,
            },
        )
        TipoPrestadorConselho.objects.update_or_create(
            tp_prestador=provider_type,
            defaults={"ds_conselho": council, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_tipoprestadorconselho_alter_module_table_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
