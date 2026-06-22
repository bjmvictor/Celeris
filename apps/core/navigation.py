def item(label, route_name=None, children=None, url=None, roles=None, access_key=None):
    return {
        "label": label,
        "route_name": route_name,
        "url": url,
        "children": children or [],
        "roles": roles or [],
        "access_key": access_key or route_name or url,
    }


MODULES = [
    {
        "code": "ATENDIMENTO",
        "title": "Atendimento",
        "icon": "clipboard-plus",
        "items": [
            item("Agendamentos", "atendimento:agendar", roles=["TI", "Recepcionista"]),
            item("Recepção", "atendimento:recepcao", roles=["TI", "Recepcionista"]),
            item("Atendimentos", "atendimento:atendimentos", roles=["TI", "Recepcionista", "Enfermeiro", "Médico"]),
            item("Classificação de Risco", "atendimento:fila-classificacao", roles=["TI", "Enfermeiro"]),
            item("Consultas Médicas", "atendimento:fila-medica", roles=["TI", "Médico"]),
        ],
    },
    {
        "code": "CADASTROS",
        "title": "Cadastros",
        "icon": "table",
        "items": [
            item("Pacientes", "atendimento:cadastro-paciente-novo", roles=["TI", "Recepcionista"]),
            item(
                "Prestadores",
                "atendimento:profissionais",
                roles=["TI"],
                access_key="atendimento:cadastro-profissional-novo",
            ),
            item("Convênios", "atendimento:convenios", roles=["TI", "Recepcionista"]),
        ],
    },
    {
        "code": "GLOBAL",
        "title": "Global",
        "icon": "globe",
        "items": [
            item(
                "Auxiliares",
                children=[
                    item("Estados", url="/global/tabelas/auxiliares/estado/", roles=["TI"]),
                    item("Cidades", url="/global/tabelas/auxiliares/cidade/", roles=["TI"]),
                    item("Tipos de Logradouro", url="/global/tabelas/auxiliares/tipo_logradouro/", roles=["TI"]),
                    item("Especialidades", url="/global/tabelas/auxiliares/especialidade/", roles=["TI"]),
                    item("Conselhos Profissionais", url="/global/tabelas/auxiliares/conselho_profissional/", roles=["TI"]),
                    item("Órgãos Emissores", url="/global/tabelas/auxiliares/orgao_emissor/", roles=["TI"]),
                    item("Bancos", url="/global/tabelas/auxiliares/banco/", roles=["TI"]),
                    item("Nacionalidades", url="/global/tabelas/auxiliares/pais/", roles=["TI"]),
                    item("Tipos de Prestador", url="/global/tabelas/auxiliares/tipo_prestador/", roles=["TI"]),
                    item("Tipos de Vínculo", url="/global/tabelas/auxiliares/tipo_vinculo/", roles=["TI"]),
                    item("Outras tabelas auxiliares", "core:global_tables", roles=["TI"]),
                ],
                roles=["TI"],
            ),
            item(
                "Integrações",
                children=[
                    item("Importação de dados", "core:global_integrations", roles=["TI"]),
                ],
                roles=["TI"],
            ),
            item("CEPs", "core:global_ceps", roles=["TI"]),
            item("Tipo de Prestador x Conselho", "core:tipo_prestador_conselho", roles=["TI"]),
        ],
    },
    {
        "code": "ADMINISTRACAO",
        "title": "Administração",
        "icon": "wrench",
        "items": [
            item("Usuários", "usuarios", roles=["TI"]),
            item("Papéis", "perfis", roles=["TI"]),
            item("Permissões", "permissoes", roles=["TI"]),
        ],
    },
]
