from django.db import migrations


MODULES = [
    ("PACIENTES", "Pacientes"),
    ("CADASTROS", "Cadastros"),
    ("FINANCEIRO", "Financeiro"),
    ("ESTOQUE", "Estoque"),
    ("COMPRAS", "Compras"),
    ("FISCAL", "Fiscal"),
    ("RH", "RH"),
    ("RELACIONAMENTO", "Relacionamento"),
    ("BI", "Indicadores"),
]


SCREENS = [
    ("PACIENTES", "Cadastro de Paciente", "pacientes-cadastro", "formulario", "", "paciente", 10),
    ("PACIENTES", "Responsaveis", "pacientes-responsaveis", "formulario", "Cadastros", "responsavel", 20),
    ("PACIENTES", "Historico do Paciente", "pacientes-historico", "consulta", "Consultas", "paciente", 30),
    ("PACIENTES", "Relatorio de Pacientes", "pacientes-relatorio", "relatorio", "Relatorios", "paciente", 40),
    ("CADASTROS", "Convenios", "cadastros-convenios", "formulario", "Tabelas", "convenio", 10),
    ("CADASTROS", "Planos", "cadastros-planos", "formulario", "Tabelas", "plano", 20),
    ("CADASTROS", "Profissionais", "cadastros-profissionais", "formulario", "Tabelas", "profissional", 30),
    ("CADASTROS", "Procedimentos", "cadastros-procedimentos", "formulario", "Tabelas", "procedimento", 40),
    ("CADASTROS", "Salas e Recursos", "cadastros-salas-recursos", "formulario", "Tabelas", "recurso", 50),
    ("FINANCEIRO", "Contas a Receber", "financeiro-contas-receber", "formulario", "Movimentacao", "conta_receber", 10),
    ("FINANCEIRO", "Contas a Pagar", "financeiro-contas-pagar", "formulario", "Movimentacao", "conta_pagar", 20),
    ("FINANCEIRO", "Fluxo de Caixa", "financeiro-fluxo-caixa", "dashboard", "Indicadores", "movimento_financeiro", 30),
    ("FINANCEIRO", "Relatorio Financeiro", "financeiro-relatorio", "relatorio", "Relatorios", "movimento_financeiro", 40),
    ("ESTOQUE", "Produtos", "estoque-produtos", "formulario", "Cadastros", "produto", 10),
    ("ESTOQUE", "Entradas", "estoque-entradas", "formulario", "Movimentacao", "estoque_movimento", 20),
    ("ESTOQUE", "Saidas", "estoque-saidas", "formulario", "Movimentacao", "estoque_movimento", 30),
    ("ESTOQUE", "Inventario", "estoque-inventario", "relatorio", "Relatorios", "estoque_saldo", 40),
    ("COMPRAS", "Fornecedores", "compras-fornecedores", "formulario", "Cadastros", "fornecedor", 10),
    ("COMPRAS", "Solicitacoes", "compras-solicitacoes", "formulario", "Movimentacao", "solicitacao_compra", 20),
    ("COMPRAS", "Pedidos de Compra", "compras-pedidos", "formulario", "Movimentacao", "pedido_compra", 30),
    ("FISCAL", "Notas Fiscais", "fiscal-notas", "formulario", "Documentos", "nota_fiscal", 10),
    ("FISCAL", "XML de Notas", "fiscal-xml-notas", "consulta", "Documentos", "nota_fiscal_xml", 20),
    ("FISCAL", "Relatorio Fiscal", "fiscal-relatorio", "relatorio", "Relatorios", "nota_fiscal", 30),
    ("RH", "Colaboradores", "rh-colaboradores", "formulario", "Cadastros", "colaborador", 10),
    ("RH", "Escalas", "rh-escalas", "formulario", "Movimentacao", "escala", 20),
    ("RH", "Produtividade", "rh-produtividade", "relatorio", "Relatorios", "produtividade", 30),
    ("RELACIONAMENTO", "Leads", "relacionamento-leads", "formulario", "Comercial", "lead", 10),
    ("RELACIONAMENTO", "Campanhas", "relacionamento-campanhas", "formulario", "Comercial", "campanha", 20),
    ("RELACIONAMENTO", "Pesquisa de Satisfacao", "relacionamento-satisfacao", "relatorio", "Relatorios", "pesquisa_satisfacao", 30),
    ("BI", "Dashboard Geral", "bi-dashboard-geral", "dashboard", "", "indicador", 10),
    ("BI", "Agenda e Atendimento", "bi-agenda-atendimento", "dashboard", "Dashboards", "indicador_atendimento", 20),
    ("BI", "Financeiro", "bi-financeiro", "dashboard", "Dashboards", "indicador_financeiro", 30),
]


FIELDS = [
    ("cd_", "Codigo", "number", True, True, False, True, 10),
    ("ds_", "Descricao", "text", True, True, True, False, 20),
    ("sn_ativo", "Ativo", "checkbox", False, True, True, False, 30),
]


def seed_erp(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenField = apps.get_model("core", "ScreenField")
    modules = {}
    for code, title in MODULES:
        modules[code], _ = Module.objects.update_or_create(
            code=code,
            defaults={"title": title, "active": True},
        )

    for code, title, slug, screen_type, parent_label, table_name, order in SCREENS:
        screen, _ = ScreenDefinition.objects.update_or_create(
            slug=slug,
            defaults={
                "module": modules[code],
                "title": title,
                "screen_type": screen_type,
                "parent_label": parent_label,
                "table_name": table_name,
                "allow_query": screen_type in {"formulario", "consulta", "relatorio"},
                "allow_insert": screen_type == "formulario",
                "allow_update": screen_type == "formulario",
                "allow_delete": False,
                "active": True,
                "order": order,
            },
        )
        if screen_type == "formulario" and not ScreenField.objects.filter(screen=screen).exists():
            prefix = table_name[:2] if table_name else "tb"
            for field_name, label, field_type, required, consultable, editable, primary_key, field_order in FIELDS:
                ScreenField.objects.create(
                    screen=screen,
                    label=label,
                    table_name=table_name,
                    field_name=f"{field_name}{prefix}" if field_name.endswith("_") else field_name,
                    field_type=field_type,
                    required=required,
                    consultable=consultable,
                    editable=editable,
                    primary_key=primary_key,
                    visible=True,
                    order=field_order,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_screendefinition_capabilities"),
    ]

    operations = [
        migrations.RunPython(seed_erp, migrations.RunPython.noop),
    ]
