from django.db import migrations


def seed_provider_types(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="tipo_prestador",
        defaults={"ds_descricao": "Tipos de prestador", "sn_ativo": True},
    )
    values = [
        ("MEDICO", "MÉDICO"),
        ("BIOMEDICO", "BIOMÉDICO"),
        ("ENFERMEIRO", "ENFERMEIRO"),
        ("TECNICO_ENFERMAGEM", "TÉCNICO DE ENFERMAGEM"),
        ("FISIOTERAPEUTA", "FISIOTERAPEUTA"),
        ("PSICOLOGO", "PSICÓLOGO"),
        ("NUTRICIONISTA", "NUTRICIONISTA"),
        ("FONOAUDIOLOGO", "FONOAUDIÓLOGO"),
        ("FARMACEUTICO", "FARMACÊUTICO"),
        ("DENTISTA", "DENTISTA"),
        ("OUTRO", "OUTRO"),
    ]
    for code, description in values:
        ValorAuxiliarGlobal.objects.update_or_create(
            cd_tabela_auxiliar_global=table,
            cd_valor=code,
            defaults={"ds_valor": description, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_seed_patient_auxiliaries"),
    ]

    operations = [
        migrations.RunPython(seed_provider_types, migrations.RunPython.noop),
    ]
