from django.db import migrations, models


HTML_FICHA_CLASSIFICACAO = """
<section style="width:100%;font-family:Arial,sans-serif;font-size:11px">
  <h1 style="margin:0 0 10px;text-align:center;font-size:16px">FICHA DE CLASSIFICAÇÃO DE RISCO</h1>
  <p><strong>Paciente:</strong> {{ paciente.nome }} &nbsp; <strong>Prontuário:</strong> {{ paciente.codigo }}</p>
  <p><strong>Nascimento:</strong> {{ paciente.nascimento }} &nbsp; <strong>Idade:</strong> {{ paciente.idade }} &nbsp; <strong>Sexo:</strong> {{ paciente.sexo }}</p>
  <p><strong>Senha:</strong> {{ classificacao.senha }} &nbsp; <strong>Entrada:</strong> {{ classificacao.data_hora_entrada }} &nbsp; <strong>Classificação:</strong> {{ classificacao.data_hora }}</p>
  <p><strong>Cor:</strong> {{ classificacao.cor }} &nbsp; <strong>Prioridade:</strong> {{ classificacao.prioridade }} &nbsp; <strong>Especialidade:</strong> {{ classificacao.especialidade }}</p>
  <hr>
  <p><strong>Queixa principal:</strong><br>{{ classificacao.queixa_principal }}</p>
  <p><strong>Observações:</strong><br>{{ classificacao.observacao }}</p>
  <p><strong>Medicamentos:</strong> {{ classificacao.medicamentos }}</p>
  <p><strong>Alergias:</strong> {{ classificacao.alergias }}</p>
  <p><strong>Sinais vitais:</strong> PA {{ classificacao.pressao_arterial }} | FC {{ classificacao.frequencia_cardiaca }} | FR {{ classificacao.frequencia_respiratoria }} | SAT {{ classificacao.saturacao }}% | TEMP {{ classificacao.temperatura }}°C | HGT {{ classificacao.hgt }}</p>
  <p><strong>Fluxo:</strong> {{ classificacao.fluxo }}</p>
  <p><strong>Perguntas complementares:</strong><br>{{ classificacao.perguntas }}</p>
  <p><strong>Escalas:</strong><br>{{ classificacao.escalas }}</p>
  <p><strong>Responsável:</strong> {{ classificacao.prestador }} &nbsp; <strong>Usuário:</strong> {{ classificacao.usuario }}</p>
</section>
""".strip()


def criar_fichas_classificacao(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    Vinculo = apps.get_model("atendimento", "ModeloDocumentoTelaImpressao")
    Tela = apps.get_model("core", "ScreenDefinition")
    tela = Tela.objects.filter(access_key="atendimento:fila-classificacao").first()
    for empresa in Empresa.objects.all():
        modelo = ModeloDocumento.objects.filter(
            cd_empresa=empresa,
            tp_documento="FICHA_CLASSIFICACAO",
            tp_elemento="DOCUMENTO",
            sn_versao_atual=True,
        ).first()
        if not modelo:
            modelo = ModeloDocumento.objects.create(
                cd_empresa=empresa,
                nm_modelo="Ficha de classificação de risco",
                tp_documento="FICHA_CLASSIFICACAO",
                tp_elemento="DOCUMENTO",
                ds_html_impressao=HTML_FICHA_CLASSIFICACAO,
                ds_html_tela=HTML_FICHA_CLASSIFICACAO,
                sn_exibe_assinatura=False,
                sn_exibe_conselho_assinatura=False,
                sn_sistema=True,
                sn_editavel=True,
                sn_versao_atual=True,
                sn_ativo=True,
            )
        if tela:
            Vinculo.objects.get_or_create(
                cd_empresa=empresa,
                cd_modelo_documento=modelo,
                cd_tela=tela,
                defaults={"sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0058_grupos_fluxos_classificacao"),
        ("core", "0056_ocultar_fila_classificacao_e_expor_escalas"),
    ]

    operations = [
        migrations.AlterField(
            model_name="modelodocumento",
            name="tp_documento",
            field=models.CharField(
                choices=[
                    ("COMPROVANTE_AGENDAMENTO", "Comprovante de agendamento"),
                    ("COMPROVANTE_CHAMADO", "Comprovante de chamado"),
                    ("FICHA_CLASSIFICACAO", "Ficha de classificação"),
                    ("FICHA_ATENDIMENTO", "Ficha de atendimento"),
                    ("ETIQUETA_ATENDIMENTO", "Etiqueta de atendimento"),
                    ("PRESCRICAO", "Prescrição"),
                    ("SOLICITACAO_EXAME", "Solicitação de exame"),
                    ("EVOLUCAO", "Evolução"),
                    ("RESUMO_ALTA", "Resumo de alta"),
                    ("RECEITUARIO", "Receituário"),
                    ("ATESTADO", "Atestado"),
                    ("ENCAMINHAMENTO", "Encaminhamento"),
                    ("ADMINISTRATIVO", "Administrativo"),
                ],
                max_length=40,
            ),
        ),
        migrations.RunPython(criar_fichas_classificacao, migrations.RunPython.noop),
    ]
