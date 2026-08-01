"""Operações históricas de dados da migration 0031."""

from django.db import migrations


def ajustar_cabecalho(apps, schema_editor):
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    ModeloDocumento.objects.filter(
        cd_empresa__isnull=True,
        tp_elemento="CABECALHO",
        nm_modelo="Cabeçalho clínico padrão Celeris",
        sn_versao_atual=True,
    ).update(
        ds_html_impressao=(
            '<header class="reusable-document-header" style="display:grid;gap:5px;'
            'border-bottom:2px solid #1d4ed8;padding:0 0 8px;margin-bottom:12px">'
            '<div><strong style="font-size:20px;color:#1d4ed8">{{ empresa.nome }}</strong>'
            '<br><span>Documento clínico assistencial</span>'
            '<br><strong>Paciente:</strong> {{ paciente.nome }} · '
            '<strong>Prontuário:</strong> {{ paciente.codigo }}'
            '<br><strong>Atendimento:</strong> {{ atendimento.codigo }} · '
            '{{ atendimento.data_hora }}</div></header>'
        ),
        ds_alteracoes_versao="Modelo clínico padrão Celeris",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0030_padronizar_documentos_clinicos"),
    ]

    operations = [
        migrations.RunPython(ajustar_cabecalho, migrations.RunPython.noop),
    ]
