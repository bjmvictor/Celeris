from django.db import migrations


ORDEM_CORES = {
    "VERDE": 1,
    "AMARELO": 2,
    "LARANJA": 3,
    "VERMELHO": 4,
    "AZUL": 5,
}


def ordenar_cores_classificacao(apps, schema_editor):
    CorClassificacaoRisco = apps.get_model("atendimento", "CorClassificacaoRisco")
    for codigo, ordem in ORDEM_CORES.items():
        CorClassificacaoRisco.objects.filter(cd_cor__iexact=codigo).update(nr_prioridade=ordem)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0061_documentos_sistema_por_tela"),
    ]

    operations = [
        migrations.RunPython(ordenar_cores_classificacao, migrations.RunPython.noop),
    ]
