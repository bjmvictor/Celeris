from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


DOCUMENTOS = (
    (
        "PRESCREVER",
        "PRESCRICAO",
        "Prescrição médica",
        "<h2>Prescrição médica</h2><p><strong>Paciente:</strong> {{ paciente.nome }}</p><section>{{ documento.conteudo }}</section>",
    ),
    (
        "EXAMES",
        "SOLICITACAO_EXAME",
        "Solicitação de exames",
        "<h2>Solicitação de exames</h2><p><strong>Paciente:</strong> {{ paciente.nome }}</p><section>{{ documento.conteudo }}</section>",
    ),
)


def configurar_modelos_documentais(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    ItemMenu = apps.get_model("atendimento", "ItemMenuAssistencial")

    for empresa in Empresa.objects.all():
        for acao, tipo, nome, corpo in DOCUMENTOS:
            modelo = ModeloDocumento.objects.filter(
                cd_empresa=empresa,
                tp_documento=tipo,
                tp_elemento="DOCUMENTO",
                sn_versao_atual=True,
                sn_ativo=True,
            ).order_by("-nr_versao", "pk").first()
            if not modelo:
                modelo = ModeloDocumento.objects.create(
                    cd_empresa=empresa,
                    nm_modelo=nome,
                    tp_documento=tipo,
                    tp_elemento="DOCUMENTO",
                    ds_html_tela=corpo,
                    ds_html_impressao=corpo,
                    sn_exibe_assinatura=True,
                    tp_finalidade_assinatura="MEDICO",
                    sn_sistema=True,
                    sn_editavel=True,
                    sn_versao_atual=True,
                    sn_ativo=True,
                )
            ItemMenu.objects.filter(cd_empresa=empresa, ds_acao=acao).update(
                tp_item="DOCUMENTO",
                cd_modelo_documento=modelo,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0066_prescricao_estruturada_documentos_pep"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitacaoexame",
            name="cd_documento_clinico",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_documento_clinico",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="solicitacoes_exames_estruturadas",
                to="atendimento.documentoclinico",
            ),
        ),
        migrations.AddField(
            model_name="prescricao",
            name="cd_documento_clinico",
            field=models.OneToOneField(
                blank=True,
                db_column="cd_documento_clinico",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="prescricao_estruturada",
                to="atendimento.documentoclinico",
            ),
        ),
        migrations.RunPython(configurar_modelos_documentais, migrations.RunPython.noop),
    ]
