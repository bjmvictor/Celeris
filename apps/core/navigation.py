def item(label, route_name=None, children=None, url=None):
    return {
        "label": label,
        "route_name": route_name,
        "url": url,
        "children": children or [],
    }


MODULES = [
    {
        "code": "ATENDIMENTO",
        "title": "Atendimento",
        "icon": "clipboard-plus",
        "items": [
            item(
                "Agendamento",
                children=[
                    item("Agendar", "atendimento:agendar"),
                    item("Atender", "atendimento:atender-agendamento"),
                    item("Consultar", "atendimento:consultar-agendamento"),
                    item("Agendas", "atendimento:agendas"),
                    item("Gerar agenda", "atendimento:gerar-agenda"),
                    item("Cadastro de paciente", "atendimento:cadastro-paciente-agendamento"),
                    item(
                        "Tabelas",
                        children=[
                            item("Convênios", "atendimento:convenios-agendamento"),
                            item("Tipos de Atendimento", "atendimento:tipos-atendimento-agendamento"),
                            item("Especialidades", "atendimento:especialidades-agendamento"),
                        ],
                    ),
                ],
            ),
            item(
                "Atendimento",
                children=[
                    item("Atendimento", "atendimento:atendimento"),
                    item("Consulta de atendimento", "atendimento:consulta-atendimento"),
                    item("Cadastro de paciente", "atendimento:cadastro-paciente-atendimento"),
                    item(
                        "Tabelas",
                        children=[
                            item("Convênios", "atendimento:convenios-atendimento"),
                            item("Tipos de Atendimento", "atendimento:tipos-atendimento-atendimento"),
                            item("Especialidades", "atendimento:especialidades-atendimento"),
                        ],
                    ),
                ],
            ),
            item(
                "Tabelas",
                children=[
                    item("Convênios", "atendimento:convenios"),
                    item("Tipos de Atendimento", "atendimento:tipos-atendimento"),
                    item("Especialidades", "atendimento:especialidades"),
                    item("Profissionais", "atendimento:profissionais"),
                    item("Escalas", "atendimento:escalas"),
                    item("Salas", "atendimento:salas"),
                ],
            ),
            item(
                "Relatórios",
                children=[
                    item("Agendamentos", "atendimento:relatorio-agendamentos"),
                    item("Atendimentos", "atendimento:relatorio-atendimentos"),
                    item("Produtividade", "atendimento:relatorio-produtividade"),
                ],
            ),
        ],
    },
    {
        "code": "TI",
        "title": "TI",
        "icon": "monitor",
        "items": [
            item("Chamados", "tickets:list"),
            item("Inventário de Agentes", "ti:agentes"),
        ],
    },
    {
        "code": "PACIENTES",
        "title": "Pacientes",
        "icon": "users",
        "items": [],
    },
    {
        "code": "CADASTROS",
        "title": "Cadastros",
        "icon": "table",
        "items": [],
    },
    {
        "code": "FINANCEIRO",
        "title": "Financeiro",
        "icon": "coins",
        "items": [],
    },
    {
        "code": "ESTOQUE",
        "title": "Estoque",
        "icon": "shirt",
        "items": [],
    },
    {
        "code": "COMPRAS",
        "title": "Compras",
        "icon": "handshake",
        "items": [],
    },
    {
        "code": "FISCAL",
        "title": "Fiscal",
        "icon": "table",
        "items": [],
    },
    {
        "code": "RH",
        "title": "RH",
        "icon": "users",
        "items": [],
    },
    {
        "code": "RELACIONAMENTO",
        "title": "Relacionamento",
        "icon": "headset",
        "items": [],
    },
    {
        "code": "BI",
        "title": "Indicadores",
        "icon": "activity",
        "items": [],
    },
    {
        "code": "GLOBAL",
        "title": "Global",
        "icon": "table",
        "items": [
            item(
                "Tabelas",
                children=[
                    item(
                        "Auxiliares",
                        children=[
                            item("Tipo sanguíneo", "core:global_tipo_sanguineo"),
                            item("Sexo", "core:global_sexo"),
                            item("Estado civil", "core:global_estado_civil"),
                            item("Naturalidade", "core:global_naturalidade"),
                            item("Nacionalidade", "core:global_nacionalidade"),
                            item("Cidade", "core:global_cidade"),
                            item("Estado", "core:global_estado"),
                            item("Motivos de alteração", "core:global_motivo_alteracao"),
                        ],
                    ),
                ],
            ),
        ],
    },
    {
        "code": "CONFIGURACAO",
        "title": "Configuração do Sistema",
        "icon": "wrench",
        "items": [
            item(
                "Configurar Telas",
                children=[
                    item("Telas", "core:system_screens"),
                    item("Campos", "core:system_fields"),
                ],
            ),
            item("Empresas", "core:system_companies"),
        ],
    },
]
