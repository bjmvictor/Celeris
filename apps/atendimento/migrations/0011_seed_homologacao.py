from django.db import migrations


def preservar_sequencia_sem_dados_artificiais(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0010_prescricao_evolucaoatendimento"),
        ("core", "0015_seed_erp_auxiliaries"),
    ]

    operations = [migrations.RunPython(preservar_sequencia_sem_dados_artificiais, migrations.RunPython.noop)]
