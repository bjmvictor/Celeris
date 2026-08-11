from django.db import migrations


CATALOGOS_INICIAIS = {
    "TipoAtendimento": (
        ("CONSULTA", "Consulta"),
        ("RETORNO", "Retorno"),
        ("URGENCIA_EMERGENCIA", "Urgência/Emergência"),
        ("DEMANDA_ESPONTANEA", "Demanda espontânea"),
    ),
    "TipoEscala": (
        ("AMBULATORIAL", "Ambulatorial"),
        ("PLANTAO", "Plantão"),
    ),
    "Plano": (
        ("SUS", "Sistema Único de Saúde (SUS)"),
        ("PARTICULAR", "Particular"),
    ),
}


def criar_catalogos_operacionais(apps, schema_editor):
    for nome_modelo, registros in CATALOGOS_INICIAIS.items():
        modelo = apps.get_model("core", nome_modelo)
        for codigo, descricao in registros:
            modelo.objects.update_or_create(
                cd_valor=codigo,
                defaults={"ds_valor": descricao, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [("core", "0054_catalogos_complementares_e_remocao_legada")]

    operations = [
        migrations.RunPython(criar_catalogos_operacionais, migrations.RunPython.noop),
    ]
