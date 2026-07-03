from django.db import migrations


SCREEN_CSS = (
    ".generated-clinical-form{display:grid;gap:12px}"
    ".generated-clinical-form label{display:grid;gap:4px;font-weight:700}"
    ".generated-clinical-form input,.generated-clinical-form select,.generated-clinical-form textarea"
    "{width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:5px;background:#fff;color:#111}"
    ".generated-clinical-form .provider-checkbox{display:flex;align-items:center}"
    ".generated-clinical-form .provider-checkbox input{width:auto}"
)


def field(name, label, field_type="text", row=1, col=1, col_span=1, row_span=1, **extra):
    return {
        "id": name,
        "name": name,
        "label": label,
        "type": field_type,
        "placeholder": extra.pop("placeholder", ""),
        "required": extra.pop("required", False),
        "readonly": extra.pop("readonly", False),
        "options": extra.pop("options", ""),
        "sourceTable": extra.pop("sourceTable", ""),
        "sourceQuery": extra.pop("sourceQuery", ""),
        "binding": extra.pop("binding", ""),
        "imageUrl": extra.pop("imageUrl", ""),
        "col": col,
        "row": row,
        "colSpan": col_span,
        "rowSpan": row_span,
        **extra,
    }


def screen_html(fields, columns, rows):
    parts = []
    for item in fields:
        position = (
            f'style="grid-column:{item["col"]} / span {item["colSpan"]};'
            f'grid-row:{item["row"]} / span {item["rowSpan"]}"'
        )
        label = item["label"]
        name = item["name"]
        required = " required" if item.get("required") else ""
        readonly = " readonly" if item.get("readonly") else ""
        value = f' value="{{{{ {item["binding"]} }}}}"' if item.get("binding") else ""
        if item["type"] == "textarea":
            control = f'<textarea data-document-field="true" name="campo_{name}" rows="5"{required}{readonly}></textarea>'
        elif item["type"] == "select":
            options = "".join(
                f'<option value="{option.strip()}">{option.strip()}</option>'
                for option in item.get("options", "").split(",")
                if option.strip()
            )
            control = f'<select data-document-field="true" name="campo_{name}"{required}><option value=""></option>{options}</select>'
        elif item["type"] == "checkbox":
            parts.append(
                f'<label class="provider-checkbox" {position}>'
                f'<input data-document-field="true" name="campo_{name}" type="checkbox"><span>{label}</span></label>'
            )
            continue
        else:
            control = (
                f'<input data-document-field="true" name="campo_{name}" type="{item["type"]}"'
                f'{value}{required}{readonly}>'
            )
        parts.append(f"<label {position}>{label}{control}</label>")
    return (
        f'<section class="generated-clinical-form" style="grid-template-columns:repeat({columns},minmax(0,1fr));'
        f'grid-template-rows:repeat({rows},minmax(52px,auto))">{"".join(parts)}</section>'
    )


def print_html(title, fields, columns, rows):
    parts = []
    for item in fields:
        value = f'{{{{ {item["binding"]} }}}}' if item.get("binding") else f'{{{{ campo.{item["name"]} }}}}'
        position = (
            f'grid-column:{item["col"]} / span {item["colSpan"]};'
            f'grid-row:{item["row"]} / span {item["rowSpan"]}'
        )
        parts.append(
            f'<div style="{position};padding:5px;border-bottom:1px solid #d1d5db">'
            f'<strong>{item["label"]}:</strong> <span>{value}</span></div>'
        )
    return (
        '<main style="width:210mm;min-height:297mm;margin:auto;padding:18mm;background:#fff;color:#111">'
        f'<h1 style="font-size:20px;text-align:center;margin:0 0 16px">{title}</h1>'
        f'<section style="display:grid;grid-template-columns:repeat({columns},minmax(0,1fr));'
        f'grid-template-rows:repeat({rows},minmax(36px,auto));gap:8px">{"".join(parts)}</section></main>'
    )


def cadastrar_documentos(apps, schema_editor):
    PastaDocumento = apps.get_model("atendimento", "PastaDocumento")
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")

    def folder(name, folder_type="GERAL", order=20):
        item, _ = PastaDocumento.objects.get_or_create(
            cd_empresa=None,
            cd_pasta_pai=None,
            nm_pasta=name,
            defaults={
                "tp_pasta": folder_type,
                "nr_ordem": order,
                "sn_sistema": True,
                "sn_editavel": False,
                "sn_ativo": True,
            },
        )
        return item

    folders = {
        "headers": folder("Cabeçalhos", "CABECALHOS", 0),
        "footers": folder("Rodapés", "RODAPES", 1),
        "fields": folder("Campos reutilizáveis", "GERAL", 2),
        "admission": folder("Documentos de admissão", "ADMISSAO", 3),
        "evolution": folder("Evoluções clínicas", "GERAL", 4),
        "prescription": folder("Prescrições e exames", "GERAL", 5),
        "discharge": folder("Documentos de alta", "ALTA", 6),
    }

    common_defaults = {
        "cd_empresa": None,
        "nr_versao": 1,
        "sn_versao_atual": True,
        "sn_sistema": True,
        "sn_editavel": False,
        "sn_ativo": True,
    }

    header, _ = ModeloDocumento.objects.update_or_create(
        cd_empresa=None,
        tp_documento="ADMINISTRATIVO",
        nm_modelo="Cabeçalho clínico padrão Celeris",
        nr_versao=1,
        defaults={
            **common_defaults,
            "cd_pasta": folders["headers"],
            "tp_elemento": "CABECALHO",
            "ds_html_impressao": (
                '<header class="reusable-document-header" style="display:grid;grid-template-columns:1fr 2fr;'
                'gap:12px;align-items:center;border-bottom:2px solid #1d4ed8;padding:0 0 8px;margin-bottom:12px">'
                '<div style="font-size:20px;font-weight:800;color:#1d4ed8">CELERIS</div>'
                '<div><strong>{{ empresa.nome }}</strong><br><span>Documento clínico assistencial</span>'
                '<br><strong>Paciente:</strong> {{ paciente.nome }} · <strong>Prontuário:</strong> {{ paciente.codigo }}'
                '<br><strong>Atendimento:</strong> {{ atendimento.codigo }} · {{ atendimento.data_hora }}</div></header>'
            ),
            "ds_css_impressao": ".reusable-document-header{max-height:55mm;overflow:hidden}",
            "ds_alteracoes_versao": "Modelo demonstrativo inicial.",
        },
    )
    footer, _ = ModeloDocumento.objects.update_or_create(
        cd_empresa=None,
        tp_documento="ADMINISTRATIVO",
        nm_modelo="Rodapé clínico padrão Celeris",
        nr_versao=1,
        defaults={
            **common_defaults,
            "cd_pasta": folders["footers"],
            "tp_elemento": "RODAPE",
            "ds_html_impressao": (
                '<footer class="reusable-document-footer" style="border-top:1px solid #94a3b8;margin-top:14px;'
                'padding-top:6px;font-size:10px;color:#475569;display:flex;justify-content:space-between">'
                '<span>Atendimento {{ atendimento.codigo }}</span><span>Emitido pelo Celeris</span></footer>'
            ),
            "ds_css_impressao": ".reusable-document-footer{max-height:35mm;overflow:hidden}",
            "ds_alteracoes_versao": "Modelo demonstrativo inicial.",
        },
    )

    reusable = [
        ("Nome do paciente", "nome_paciente", "Nome do paciente", "paciente.nome"),
        ("Prontuário do paciente", "prontuario", "Prontuário", "paciente.codigo"),
        ("Código do atendimento", "codigo_atendimento", "Atendimento", "atendimento.codigo"),
        ("Data de nascimento", "data_nascimento", "Data de nascimento", "paciente.nascimento"),
        ("Prestador responsável", "prestador_responsavel", "Prestador", "prestador.nome"),
    ]
    for title, name, label, binding in reusable:
        fields = [field(name, label, readonly=True, binding=binding)]
        ModeloDocumento.objects.update_or_create(
            cd_empresa=None,
            tp_documento="ADMINISTRATIVO",
            nm_modelo=title,
            nr_versao=1,
            defaults={
                **common_defaults,
                "cd_pasta": folders["fields"],
                "tp_elemento": "CAMPO",
                "ds_html_tela": screen_html(fields, 1, 1),
                "ds_css_tela": SCREEN_CSS,
                "ds_projeto_tela": {"grid": {"columns": 1, "rows": 1}, "formFields": fields},
                "ds_alteracoes_versao": "Campo reutilizável demonstrativo.",
            },
        )

    documents = [
        (
            "Exemplo clínico — Admissão e anamnese",
            "FICHA_ATENDIMENTO",
            "admission",
            2,
            7,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("queixa_principal", "Queixa principal", "textarea", 2, 1, 2, required=True),
                field("historia_doenca", "História da doença atual", "textarea", 3, 1, 2, required=True),
                field("antecedentes", "Antecedentes pessoais e familiares", "textarea", 4, 1, 2),
                field("alergias", "Alergias", "textarea", 5, 1),
                field("medicacoes_uso", "Medicações em uso", "textarea", 5, 2),
                field("exame_fisico", "Exame físico", "textarea", 6, 1, 2),
                field("hipotese_diagnostica", "Hipótese diagnóstica", "textarea", 7, 1),
                field("conduta", "Conduta", "textarea", 7, 2, required=True),
            ],
        ),
        (
            "Exemplo clínico — Evolução médica",
            "EVOLUCAO",
            "evolution",
            2,
            5,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("estado_clinico", "Estado clínico", "select", 2, 1, options="Estável, Em melhora, Sem alteração, Em piora, Crítico", required=True),
                field("data_hora", "Data e hora", row=2, col=2, readonly=True, binding="atendimento.data_hora"),
                field("evolucao", "Evolução clínica", "textarea", 3, 1, 2, 2, required=True),
                field("conduta", "Conduta e plano terapêutico", "textarea", 5, 1, 2, required=True),
            ],
        ),
        (
            "Exemplo clínico — Prescrição medicamentosa",
            "PRESCRICAO",
            "prescription",
            2,
            6,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("medicamento", "Medicamento", row=2, col=1, required=True),
                field("concentracao", "Concentração/apresentação", row=2, col=2, required=True),
                field("dose", "Dose", row=3, col=1, required=True),
                field("via", "Via de administração", "select", 3, 2, options="Oral, Intravenosa, Intramuscular, Subcutânea, Tópica, Inalatória, Outra", required=True),
                field("frequencia", "Frequência", row=4, col=1, required=True),
                field("duracao", "Duração", row=4, col=2),
                field("se_necessario", "Administrar se necessário", "checkbox", 5, 1),
                field("orientacoes", "Orientações", "textarea", 6, 1, 2),
            ],
        ),
        (
            "Exemplo clínico — Solicitação de exames",
            "SOLICITACAO_EXAME",
            "prescription",
            2,
            5,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("categoria", "Categoria", "select", 2, 1, options="Laboratorial, Imagem, Cardiológico, Anatomia patológica, Outro", required=True),
                field("urgencia", "Prioridade", "select", 2, 2, options="Rotina, Urgente, Emergência", required=True),
                field("exames", "Exames solicitados", "textarea", 3, 1, 2, required=True),
                field("indicacao_clinica", "Indicação clínica", "textarea", 4, 1, 2, required=True),
                field("observacoes", "Observações e preparo", "textarea", 5, 1, 2),
            ],
        ),
        (
            "Exemplo clínico — Resumo de alta",
            "RESUMO_ALTA",
            "discharge",
            2,
            7,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("diagnostico_alta", "Diagnóstico de alta", "textarea", 2, 1, 2, required=True),
                field("resumo_clinico", "Resumo clínico e evolução", "textarea", 3, 1, 2, 2, required=True),
                field("procedimentos", "Procedimentos realizados", "textarea", 5, 1, 2),
                field("condicao_alta", "Condição na alta", "select", 6, 1, options="Melhorado, Curado, Estável, Transferido, Alta a pedido, Evasão", required=True),
                field("destino", "Destino", row=6, col=2, required=True),
                field("orientacoes", "Orientações, sinais de alerta e retorno", "textarea", 7, 1, 2, required=True),
            ],
        ),
        (
            "Exemplo clínico — Atestado médico",
            "ATESTADO",
            "discharge",
            2,
            5,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("cpf_paciente", "CPF", row=1, col=2, readonly=True, binding="paciente.cpf"),
                field("data_inicio", "Início do afastamento", "date", 2, 1, required=True),
                field("dias_afastamento", "Dias de afastamento", "number", 2, 2, required=True),
                field("finalidade", "Finalidade", "select", 3, 1, 2, options="Trabalho, Escola, Acompanhamento, Outra", required=True),
                field("autoriza_cid", "Paciente autoriza informar CID", "checkbox", 4, 1),
                field("cid", "CID", row=4, col=2),
                field("observacoes", "Observações", "textarea", 5, 1, 2),
            ],
        ),
        (
            "Exemplo clínico — Encaminhamento",
            "ENCAMINHAMENTO",
            "discharge",
            2,
            5,
            [
                field("nome_paciente", "Paciente", row=1, col=1, readonly=True, binding="paciente.nome"),
                field("codigo_atendimento", "Atendimento", row=1, col=2, readonly=True, binding="atendimento.codigo"),
                field("especialidade_destino", "Especialidade ou serviço de destino", row=2, col=1, col_span=2, required=True),
                field("resumo_clinico", "Resumo clínico", "textarea", 3, 1, 2, required=True),
                field("exames_tratamentos", "Exames e tratamentos realizados", "textarea", 4, 1, 2),
                field("motivo", "Motivo e objetivo do encaminhamento", "textarea", 5, 1, 2, required=True),
            ],
        ),
    ]

    for title, document_type, folder_key, columns, rows, fields in documents:
        ModeloDocumento.objects.update_or_create(
            cd_empresa=None,
            tp_documento=document_type,
            nm_modelo=title,
            nr_versao=1,
            defaults={
                **common_defaults,
                "cd_pasta": folders[folder_key],
                "cd_cabecalho": header,
                "cd_rodape": footer,
                "tp_elemento": "DOCUMENTO",
                "ds_html_tela": screen_html(fields, columns, rows),
                "ds_css_tela": SCREEN_CSS,
                "ds_projeto_tela": {"grid": {"columns": columns, "rows": rows}, "formFields": fields},
                "ds_html_impressao": print_html(title, fields, columns, rows),
                "ds_css_impressao": "@page{size:A4;margin:12mm}body{font-family:Arial,sans-serif;color:#111}",
                "ds_alteracoes_versao": "Modelo clínico demonstrativo inicial; exige validação institucional antes do uso assistencial.",
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0028_perfis_assistenciais_e_alta"),
    ]

    operations = [
        migrations.RunPython(cadastrar_documentos, migrations.RunPython.noop),
    ]
