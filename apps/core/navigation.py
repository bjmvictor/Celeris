def item(label, route_name=None, children=None, url=None, roles=None, access_key=None):
    return {
        "label": label,
        "route_name": route_name,
        "url": url,
        "children": children or [],
        "roles": roles or [],
        "access_key": access_key or route_name or url,
    }


def _ordenar_grupos_padrao(items):
    for menu_item in items:
        if menu_item.get("children"):
            _ordenar_grupos_padrao(menu_item["children"])
    items.sort(key=lambda menu_item: (
        2 if menu_item.get("label") in {"Relatórios", "Relatorios"} else
        1 if menu_item.get("label") == "Tabelas" else
        0
    ))


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
            item(
                            "Documentos eletrônicos",
                            children=[
                                item("Editor de documentos", "atendimento:modelos-documento", roles=["TI"]),
                            ],
                            roles=["TI"],
                        ),
            item("Perfis assistenciais", "atendimento:perfis-assistenciais", roles=["TI"]),
            item("Recepção", "atendimento:recepcao", roles=["TI", "Recepcionista"]),
            item("Classificação de Risco", "atendimento:fila-classificacao", roles=["TI", "Enfermeiro"]),
        ],
    },
    {
        "code": "CADASTROS",
        "title": "Cadastros",
        "icon": "form",
        "items": [
            item("Prestadores", "atendimento:cadastro-profissional-novo", roles=["TI"]),
            item(
                "Tabelas",
                children=[
                    item("Convênios", "atendimento:convenios", roles=["TI", "Recepcionista"]),
                ],
                roles=["TI", "Recepcionista"],
            ),
        ],
    },
    {
        "code": "TOTEM_SENHAS",
        "title": "Painéis de Chamada",
        "icon": "presentation",
        "items": [
            item("Configurar senhas", "atendimento:configurar-senhas", roles=["TI"]),
            item(
                "Tabelas",
                children=[
                    item("Classes", "atendimento:classes-senha", roles=["TI"]),
                    item("Protocolos", "atendimento:protocolos-senha", roles=["TI"]),
                    item("Ícones", "atendimento:icones-chamada", roles=["TI"]),
                    item("Máquinas", "atendimento:maquinas-chamada", roles=["TI"]),
                ],
                roles=["TI"],
            ),
        ],
    },
    {
        "code": "ALMOXARIFADO",
        "title": "Almoxarifado",
        "icon": "package",
        "items": [
            item(
                "Movimentações",
                children=[
                    item("Entrada", url="/almoxarifado/movimentacoes/entrada/", roles=["TI", "Almoxarifado"]),
                    item("Saída", url="/almoxarifado/movimentacoes/saida/", roles=["TI", "Almoxarifado"]),
                    item("Devoluções", url="/almoxarifado/movimentacoes/devolucao/", roles=["TI", "Almoxarifado"]),
                    item("Transferência entre estoques", url="/almoxarifado/movimentacoes/transferencia/", roles=["TI", "Almoxarifado"]),
                    item("Fracionamento", url="/almoxarifado/movimentacoes/fracionamento/", roles=["TI", "Almoxarifado"]),
                    item("Acerto de estoque", url="/almoxarifado/movimentacoes/acerto/", roles=["TI", "Almoxarifado"]),
                ],
                roles=["TI", "Almoxarifado"],
            ),
            item(
                "Solicitações",
                children=[
                    item("Atender", "estoque:atender_solicitacoes", roles=["TI", "Almoxarifado"]),
                    item("Solicitar", "estoque:solicitar_produtos", roles=["TI", "Almoxarifado"]),
                    item("Devolução", url="/almoxarifado/solicitacoes/solicitar/?tipo=DEVOLUCAO", roles=["TI", "Almoxarifado"]),
                    item("Solicitação de compras", url="/almoxarifado/solicitacoes/solicitar/?tipo=COMPRA", roles=["TI", "Almoxarifado"]),
                    item("Cancelamento de solicitação", "estoque:atender_solicitacoes", roles=["TI", "Almoxarifado"]),
                ],
                roles=["TI", "Almoxarifado"],
            ),
            item(
                "Tabelas",
                children=[
                    item(
                        "Gerais",
                        children=[
                            item("Estoques", "estoque:estoques", roles=["TI", "Almoxarifado"]),
                            item("Unidades", "estoque:unidades", roles=["TI", "Almoxarifado"]),
                            item("Cotas / Consumo", "estoque:cotas_consumo", roles=["TI", "Almoxarifado"]),
                            item("Saldos por estoque", "estoque:saldos_produto", roles=["TI", "Almoxarifado"]),
                            item("Motivos de baixa", url="/almoxarifado/tabelas/gerais/motivos-baixa/", roles=["TI", "Almoxarifado"]),
                            item("Motivos de devolução / solicitação", url="/almoxarifado/tabelas/gerais/motivos-devolucao-solicitacao/", roles=["TI", "Almoxarifado"]),
                            item("Programação de reposição", url="/almoxarifado/tabelas/gerais/programacao-reposicao/", roles=["TI", "Almoxarifado"]),
                            item("Motivos de cancelamento", url="/almoxarifado/tabelas/gerais/motivos-cancelamento/", roles=["TI", "Almoxarifado"]),
                            item("Caráter de produto", url="/almoxarifado/tabelas/gerais/carater-produto/", roles=["TI", "Almoxarifado"]),
                            item("Classes de produto", url="/almoxarifado/tabelas/gerais/classes-produto/", roles=["TI", "Almoxarifado"]),
                        ],
                        roles=["TI", "Almoxarifado"],
                    ),
                    item(
                        "Produtos",
                        children=[
                            item("Produtos", "estoque:produtos", roles=["TI", "Almoxarifado"]),
                            item("Classificação", "estoque:classificacoes_produto", roles=["TI", "Almoxarifado"]),
                            item("Alteração / exclusão de produtos", "estoque:produtos", roles=["TI", "Almoxarifado"]),
                            item("Solicitação de cadastro de produtos", "estoque:solicitar_produtos", roles=["TI", "Almoxarifado"]),
                            item("Recebimento de cadastro de produtos", "estoque:atender_solicitacoes", roles=["TI", "Almoxarifado"]),
                        ],
                        roles=["TI", "Almoxarifado"],
                    ),
                ],
                roles=["TI", "Almoxarifado"],
            ),
        ],
    },
    {
        "code": "SUPORTE",
        "title": "Suporte",
        "icon": "hammer",
        "items": [
            item(
                "Solicitação",
                children=[
                    item("Atender", "tickets:atender", roles=["TI", "Suporte"]),
                    item("Solicitar", "tickets:solicitar", roles=["TI", "Suporte"]),
                ],
                roles=["TI", "Suporte"],
            ),
            item(
                "Tabelas",
                children=[
                    item("Prioridades", "tickets:prioridades", roles=["TI", "Suporte"]),
                    item("Motivos de serviço", "tickets:motivos_servico", roles=["TI", "Suporte"]),
                    item("Motivos de conclusão", "tickets:motivos_conclusao", roles=["TI", "Suporte"]),
                    item("Oficinas", "tickets:oficinas", roles=["TI", "Suporte"]),
                    item("Usuário x oficina", "tickets:usuario_oficina", roles=["TI"]),
                ],
                roles=["TI", "Suporte"],
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
                "Tabelas Auxiliares",
                children=[
                    item("Estados", url="/global/tabelas/auxiliares/estado/", roles=["TI"]),
                    item("Cidades", url="/global/tabelas/auxiliares/cidade/", roles=["TI"]),
                    item("Tipos de Logradouro", url="/global/tabelas/auxiliares/tipo_logradouro/", roles=["TI"]),
                    item("Especialidades", url="/global/tabelas/auxiliares/especialidade/", roles=["TI"]),
                    item("CIDs", url="/global/tabelas/auxiliares/cids/", roles=["TI"]),
                    item("Motivos de alta", url="/global/tabelas/auxiliares/motivos_alta/", roles=["TI"]),
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
                "Painéis de Chamada",
                children=[
                    item(
                        "Tabelas",
                        children=[
                            item("Classes", "atendimento:classes-senha", roles=["TI"]),
                            item("Protocolos", "atendimento:protocolos-senha", roles=["TI"]),
                            item("Ícones", "atendimento:icones-chamada", roles=["TI"]),
                            item("Máquinas", "atendimento:maquinas-chamada", roles=["TI"]),
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
                    item("Alteração de senha", "ti:alteracao_senha_usuario", roles=["TI"], access_key="usuarios"),
                    item("Cópia de usuário", "copia_usuario", roles=["TI"]),
                    item("Papéis", "perfis", roles=["TI"]),
                    item("Permissões", "permissoes", roles=["TI"]),
                    item(
                        "Acessos",
                        children=[
                            item("Usuário x oficina", "tickets:usuario_oficina", roles=["TI"]),
                        ],
                        roles=["TI"],
                    ),
                    item("Sessões e travas", "core:sessoes_travas", roles=["TI"]),
                ],
                roles=["TI"],
            ),
        ],
    },
]

for module in MODULES:
    _ordenar_grupos_padrao(module["items"])
