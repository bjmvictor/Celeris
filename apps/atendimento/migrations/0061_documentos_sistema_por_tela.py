from django.db import migrations


DOCUMENTOS = {
    "COMPROVANTE_AGENDAMENTO": {
        "nome": "Comprovante de agendamento",
        "telas": ("atendimento:agendar", "atendimento:agendamentos-operacionais"),
        "html": """
            <section style="width:100%;font-family:Arial,sans-serif;font-size:12px">
              <h1 style="text-align:center">COMPROVANTE DE AGENDAMENTO</h1>
              <p><strong>Paciente:</strong> {{ paciente.nome }}</p>
              <p><strong>Data:</strong> {{ agendamento.data }} <strong>Horário:</strong> {{ agendamento.hora }}</p>
              <p><strong>Prestador:</strong> {{ agendamento.prestador }}</p>
              <p><strong>Especialidade:</strong> {{ agendamento.especialidade }}</p>
              <p><strong>Tipo:</strong> {{ agendamento.tipo }}</p>
              <p><strong>Protocolo:</strong> {{ agendamento.codigo }}</p>
            </section>
        """,
    },
    "FICHA_ATENDIMENTO": {
        "nome": "Ficha de atendimento",
        "telas": ("atendimento:recepcao",),
        "html": """
            <section style="width:100%;font-family:Arial,sans-serif;font-size:12px">
              <h1 style="text-align:center">FICHA DE ATENDIMENTO</h1>
              <p><strong>Atendimento:</strong> {{ atendimento.codigo }}</p>
              <p><strong>Paciente:</strong> {{ paciente.nome }} <strong>Prontuário:</strong> {{ paciente.codigo }}</p>
              <p><strong>Data:</strong> {{ atendimento.data_hora }}</p>
              <p><strong>Tipo:</strong> {{ atendimento.tipo }}</p>
            </section>
        """,
    },
    "ETIQUETA_ATENDIMENTO": {
        "nome": "Etiqueta de atendimento",
        "telas": ("atendimento:recepcao",),
        "html": """
            <section style="width:100%;font-family:Arial,sans-serif;font-size:11px">
              <strong>{{ paciente.nome }}</strong><br>
              Prontuário: {{ paciente.codigo }} · Atendimento: {{ atendimento.codigo }}<br>
              Nascimento: {{ paciente.nascimento }}
            </section>
        """,
    },
    "COMPROVANTE_CHAMADO": {
        "nome": "Comprovante de chamado",
        "telas": ("tickets:solicitar", "tickets:atender"),
        "html": """
            <section style="width:100%;font-family:Arial,sans-serif;font-size:12px">
              <h1 style="text-align:center">COMPROVANTE DE CHAMADO</h1>
              <p><strong>Código:</strong> {{ chamado.codigo }}</p>
              <p><strong>Título:</strong> {{ chamado.titulo }}</p>
              <p><strong>Descrição:</strong> {{ chamado.descricao }}</p>
              <p><strong>Solicitante:</strong> {{ chamado.solicitante }}</p>
              <p><strong>Data:</strong> {{ chamado.data_hora }}</p>
            </section>
        """,
    },
}


def configurar_documentos(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    Vinculo = apps.get_model("atendimento", "ModeloDocumentoTelaImpressao")
    Tela = apps.get_model("core", "ScreenDefinition")
    telas = {
        tela.access_key: tela
        for tela in Tela.objects.filter(
            access_key__in={chave for dados in DOCUMENTOS.values() for chave in dados["telas"]}
        )
    }
    for empresa in Empresa.objects.all():
        for tipo, dados in DOCUMENTOS.items():
            modelo = ModeloDocumento.objects.filter(
                cd_empresa=empresa,
                tp_documento=tipo,
                tp_elemento="DOCUMENTO",
                sn_versao_atual=True,
                sn_ativo=True,
            ).order_by("cd_modelo_documento").first()
            if not modelo:
                modelo = ModeloDocumento.objects.create(
                    cd_empresa=empresa,
                    nm_modelo=dados["nome"],
                    tp_documento=tipo,
                    tp_elemento="DOCUMENTO",
                    ds_html_impressao=dados["html"].strip(),
                    ds_html_tela=dados["html"].strip(),
                    sn_exibe_assinatura=False,
                    sn_exibe_conselho_assinatura=False,
                    sn_sistema=True,
                    sn_editavel=True,
                    sn_versao_atual=True,
                    sn_ativo=True,
                )
            for chave in dados["telas"]:
                tela = telas.get(chave)
                if tela:
                    Vinculo.objects.update_or_create(
                        cd_empresa=empresa,
                        cd_modelo_documento=modelo,
                        cd_tela=tela,
                        defaults={"sn_ativo": True},
                    )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0060_escalas_recomendadas_fluxos"),
    ]

    operations = [
        migrations.RunPython(configurar_documentos, migrations.RunPython.noop),
    ]
