"""Operações históricas de dados da migration 0044."""

from django.db import migrations, models


def classify_existing_machines(apps, schema_editor):
    MaquinaChamada = apps.get_model("atendimento", "MaquinaChamada")
    PainelChamada = apps.get_model("atendimento", "PainelChamada")
    for company_id, machine_name in PainelChamada.objects.filter(sn_ativo=True).values_list("cd_empresa_id", "nm_maquina"):
        MaquinaChamada.objects.filter(
            cd_empresa_id=company_id,
            nm_maquina__iexact=machine_name,
        ).update(tp_maquina="PAINEL")


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0043_seed_paineis_chamada")]

    operations = [
        migrations.AddField(
            model_name="maquinachamada",
            name="tp_maquina",
            field=models.CharField(choices=[("ESTACAO", "Estação"), ("PAINEL", "Painel")], default="ESTACAO", max_length=20),
        ),
        migrations.RunPython(classify_existing_machines, migrations.RunPython.noop),
    ]
