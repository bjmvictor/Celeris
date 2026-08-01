"""Operações históricas de dados da migration 0030."""

from django.db import migrations


SIGNATURE_HTML = (
    '<section data-celeris-signature="true" style="margin-top:28px;break-inside:avoid;text-align:center">'
    '<div style="height:58px;border-bottom:1px solid #111;margin:0 auto 7px;max-width:105mm"></div>'
    '<strong>{{ prestador.nome }}</strong><br>'
    '<span>{{ prestador.conselho }} {{ prestador.numero_conselho }}</span><br>'
    '<small>Assinatura digital: {{ prestador.nome }} · {{ prestador.conselho }} {{ prestador.numero_conselho }}</small>'
    "</section>"
)


def add_signature(html):
    if 'data-celeris-signature="true"' in (html or ""):
        return html
    if "</main>" in (html or ""):
        return html.replace("</main>", f"{SIGNATURE_HTML}</main>", 1)
    return f"{html or ''}{SIGNATURE_HTML}"


def padronizar_documentos(apps, schema_editor):
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    PastaDocumento = apps.get_model("atendimento", "PastaDocumento")

    names = {
        "Exemplo clínico — Admissão e anamnese": "Admissão e anamnese",
        "Exemplo clínico — Evolução médica": "Evolução médica",
        "Exemplo clínico — Prescrição medicamentosa": "Prescrição medicamentosa",
        "Exemplo clínico — Solicitação de exames": "Solicitação de exames",
        "Exemplo clínico — Resumo de alta": "Resumo de alta",
        "Exemplo clínico — Atestado médico": "Atestado médico",
        "Exemplo clínico — Encaminhamento": "Encaminhamento",
    }
    standard_documents = ModeloDocumento.objects.filter(
        cd_empresa__isnull=True,
        nm_modelo__in=names,
        tp_elemento="DOCUMENTO",
    )
    for document in standard_documents.iterator():
        document.nm_modelo = names[document.nm_modelo]
        document.ds_alteracoes_versao = "Modelo clínico padrão Celeris"
        document.ds_css_tela = (
            (document.ds_css_tela or "")
            .replace(".generated-clinical-form{display:grid;gap:12px}", ".generated-clinical-form{display:grid;column-gap:18px;row-gap:14px}")
            .replace(
                ".generated-clinical-form input,.generated-clinical-form select,.generated-clinical-form textarea{",
                ".generated-clinical-form input,.generated-clinical-form select,.generated-clinical-form textarea{box-sizing:border-box;",
            )
            + ".generated-clinical-form :disabled{cursor:not-allowed;background:#e9eef5;color:#475569;opacity:1}"
        )
        document.ds_html_tela = (document.ds_html_tela or "").replace(
            " readonly>",
            ' disabled tabindex="-1" aria-disabled="true">',
        )
        document.ds_html_impressao = add_signature(
            (document.ds_html_impressao or "")
            .replace("minmax(36px,auto));gap:8px", "minmax(44px,auto));column-gap:16px;row-gap:14px")
            .replace("padding:5px;border-bottom", "min-height:44px;padding:8px 6px 14px;border-bottom")
        )
        document.save(
            update_fields=[
                "nm_modelo",
                "ds_alteracoes_versao",
                "ds_css_tela",
                "ds_html_tela",
                "ds_html_impressao",
            ]
        )

    ModeloDocumento.objects.filter(
        cd_empresa__isnull=True,
        nm_modelo__in=["Cabeçalho clínico padrão Celeris", "Rodapé clínico padrão Celeris"],
    ).update(ds_alteracoes_versao="Modelo clínico padrão Celeris")

    fields_folder = PastaDocumento.objects.filter(
        cd_empresa__isnull=True,
        nm_pasta="Campos reutilizáveis",
    ).first()
    ModeloDocumento.objects.update_or_create(
        cd_empresa=None,
        tp_documento="ADMINISTRATIVO",
        nm_modelo="Assinatura do prestador responsável",
        nr_versao=1,
        defaults={
            "cd_pasta": fields_folder,
            "tp_elemento": "CAMPO",
            "ds_html_tela": "",
            "ds_css_tela": "",
            "ds_projeto_tela": {"grid": {"columns": 1, "rows": 1}, "formFields": []},
            "ds_html_impressao": SIGNATURE_HTML,
            "ds_css_impressao": "",
            "ds_projeto_impressao": {},
            "ds_alteracoes_versao": "Modelo clínico padrão Celeris",
            "sn_versao_atual": True,
            "sn_sistema": True,
            "sn_editavel": False,
            "sn_ativo": True,
        },
    )
    ModeloDocumento.objects.filter(cd_empresa__isnull=True, sn_sistema=True).update(
        ds_alteracoes_versao="Modelo clínico padrão Celeris"
    )
    for document in ModeloDocumento.objects.filter(tp_elemento="DOCUMENTO").iterator():
        signed_html = add_signature(document.ds_html_impressao)
        if signed_html != document.ds_html_impressao:
            document.ds_html_impressao = signed_html
            document.save(update_fields=["ds_html_impressao"])


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0029_seed_documentos_clinicos_demonstrativos"),
    ]

    operations = [
        migrations.RunPython(padronizar_documentos, migrations.RunPython.noop),
    ]
