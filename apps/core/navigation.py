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
            item(
                "Agendamento",
                children=[
                    item("Agendar", "atendimento:agendar", roles=["TI", "Recepcionista"]),
                    item("Agendamentos", "atendimento:agendamentos-operacionais", roles=["TI", "Recepcionista"]),
                    item("Escalas", "atendimento:escalas", roles=["TI"]),
                    item("Geração de agendas", "atendimento:gerar-agenda", roles=["TI", "Recepcionista"]),
                ],
                roles=["TI", "Recepcionista"],
            ),
            item("Editor de documentos", "atendimento:modelos-documento", roles=["TI"]),
            item("Perfis assistenciais", "atendimento:perfis-assistenciais", roles=["TI"]),
            item("Recepção", "atendimento:recepcao", roles=["TI", "Recepcionista"]),
            item("Atendimentos", "atendimento:atendimentos", roles=["TI", "Recepcionista", "Enfermeiro", "Médico"]),
            item("PEP", "atendimento:pep", roles=["TI", "Enfermeiro", "Médico"]),
            item("Classificação de Risco", "atendimento:fila-classificacao", roles=["TI", "Enfermeiro"]),
        ],
    },
    {
        "code": "CADASTROS",
        "title": "Cadastros",
        "icon": "table",
        "items": [
            item("Prestadores", "atendimento:cadastro-profissional-novo", roles=["TI"]),
            item("Convênios", "atendimento:convenios", roles=["TI", "Recepcionista"]),
        ],
    },
    {
        "code": "TOTEM_SENHAS",
        "title": "Totem de Senhas",
        "icon": "clipboard-plus",
        "items": [
            item("Gerar senha", "atendimento:gerar-senha-totem", roles=["TI", "Recepcionista"]),
            item("Configurar", "atendimento:configurar-senhas", roles=["TI"]),
            item(
                "Tabelas",
                children=[
                    item("Classes", "atendimento:classes-senha", roles=["TI"]),
                    item("Protocolos", "atendimento:protocolos-senha", roles=["TI"]),
                ],
                roles=["TI"],
            ),
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
            item(
                "Formulários",
                children=[
                    item("Configurar formulários", "core:configurar_formularios", roles=["TI"]),
                ],
                roles=["TI"],
            ),
            item(
                "Totem de Senhas",
                children=[
                    item(
                        "Tabelas",
                        children=[
                            item("Classes", "atendimento:classes-senha", roles=["TI"]),
                            item("Protocolos", "atendimento:protocolos-senha", roles=["TI"]),
                        ],
                        roles=["TI"],
                    ),
                ],
                roles=["TI"],
            ),
            item("CEPs", "core:global_ceps", roles=["TI"]),
            item("Tipo de Prestador x Conselho", "core:tipo_prestador_conselho", roles=["TI"]),
        ],
    },
    {
        "code": "TI",
        "title": "TI",
        "icon": "monitor",
        "items": [
            item(
                "Usuários e acessos",
                children=[
                    item("Usuários", "usuario_novo", roles=["TI"], access_key="usuarios"),
                    item("Cópia de usuário", "copia_usuario", roles=["TI"]),
                    item("Papéis", "perfis", roles=["TI"]),
                    item("Permissões", "permissoes", roles=["TI"]),
                ],
                roles=["TI"],
            ),
        ],
    },
]
