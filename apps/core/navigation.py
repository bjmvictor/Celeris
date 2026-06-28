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
            item("Agendar", "atendimento:agendar", roles=["TI", "Recepcionista"]),
            item("Agendamentos", "atendimento:agendamentos-operacionais", roles=["TI", "Recepcionista"]),
            item("Modelos de documentos", "atendimento:modelos-documento", roles=["TI"]),
            item("Recepção", "atendimento:recepcao", roles=["TI", "Recepcionista"]),
            item("Atendimentos", "atendimento:atendimentos", roles=["TI", "Recepcionista", "Enfermeiro", "Médico"]),
            item("PEP", "atendimento:pep", roles=["TI", "Enfermeiro", "Médico"]),
            item("Classificação de Risco", "atendimento:fila-classificacao", roles=["TI", "Enfermeiro"]),
            item("Consultas Médicas", "atendimento:fila-medica", roles=["TI", "Médico"]),
            item("Demanda espontânea", "atendimento:demanda-espontanea", roles=["TI", "Recepcionista"]),
        ],
    },
    {
        "code": "CADASTROS",
        "title": "Cadastros",
        "icon": "table",
        "items": [
            item("Pacientes", "atendimento:cadastro-paciente-novo", roles=["TI", "Recepcionista"]),
            item("Prestadores", "atendimento:cadastro-profissional-novo", roles=["TI"]),
            item("Convênios", "atendimento:convenios", roles=["TI", "Recepcionista"]),
        ],
    },
    {
        "code": "GLOBAL",
        "title": "Global",
        "icon": "globe",
        "items": [
            item(
                "Empresa",
                children=[
                    item("Empresas", "core:system_companies", roles=["TI"]),
                    item("Setores", "core:setores", roles=["TI"]),
                    item("Setores de Atendimento", "core:setores_atendimento", roles=["TI"]),
                    item("Painel de Chamada", "atendimento:paineis-chamada", roles=["TI"]),
                ],
                roles=["TI"],
            ),
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
            item("Usuários", "usuario_novo", roles=["TI"], access_key="usuarios"),
            item("Cópia de usuário", "copia_usuario", roles=["TI"], access_key="usuarios"),
            item("Papéis", "perfis", roles=["TI"]),
            item("Permissões", "permissoes", roles=["TI"]),
        ],
    },
]
