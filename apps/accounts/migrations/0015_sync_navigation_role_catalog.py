from django.db import migrations


MODULES = {
    "ALMOXARIFADO": "Almoxarifado",
    "SUPORTE": "Suporte",
    "TI": "TI",
    "GLOBAL": "Global",
}


SCREENS = [
    ("ALMOXARIFADO", "Estoques", "acesso-almoxarifado-tabelas-gerais-estoques", "estoque:estoques", "Tabelas > Gerais", 10, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Unidades", "acesso-almoxarifado-tabelas-gerais-unidades", "estoque:unidades", "Tabelas > Gerais", 20, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Cotas / Consumo", "acesso-almoxarifado-tabelas-gerais-cotas-consumo", "estoque:cotas_consumo", "Tabelas > Gerais", 30, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Saldos por estoque", "acesso-almoxarifado-tabelas-gerais-saldos", "estoque:saldos_produto", "Tabelas > Gerais", 40, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Motivos de baixa", "acesso-almoxarifado-tabelas-gerais-motivos-baixa", "/almoxarifado/tabelas/gerais/motivos-baixa/", "Tabelas > Gerais", 50, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Motivos de devolução / solicitação", "acesso-almoxarifado-tabelas-gerais-motivos-devolucao-solicitacao", "/almoxarifado/tabelas/gerais/motivos-devolucao-solicitacao/", "Tabelas > Gerais", 60, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Programação de reposição", "acesso-almoxarifado-tabelas-gerais-programacao-reposicao", "/almoxarifado/tabelas/gerais/programacao-reposicao/", "Tabelas > Gerais", 70, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Motivos de cancelamento", "acesso-almoxarifado-tabelas-gerais-motivos-cancelamento", "/almoxarifado/tabelas/gerais/motivos-cancelamento/", "Tabelas > Gerais", 80, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Caráter de produto", "acesso-almoxarifado-tabelas-gerais-carater-produto", "/almoxarifado/tabelas/gerais/carater-produto/", "Tabelas > Gerais", 90, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Classes de produto", "acesso-almoxarifado-tabelas-gerais-classes-produto", "/almoxarifado/tabelas/gerais/classes-produto/", "Tabelas > Gerais", 100, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Produtos", "acesso-almoxarifado-tabelas-produtos-produtos", "estoque:produtos", "Tabelas > Produtos", 110, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Classificação", "acesso-almoxarifado-tabelas-produtos-classificacao", "estoque:classificacoes_produto", "Tabelas > Produtos", 120, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Solicitação de cadastro de produtos", "acesso-almoxarifado-tabelas-produtos-solicitacao-cadastro", "estoque:solicitar_produtos", "Tabelas > Produtos", 130, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Recebimento de cadastro de produtos", "acesso-almoxarifado-tabelas-produtos-recebimento-cadastro", "estoque:atender_solicitacoes", "Tabelas > Produtos", 140, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Entrada", "acesso-almoxarifado-movimentacoes-entrada", "/almoxarifado/movimentacoes/entrada/", "Movimentações", 150, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Saída", "acesso-almoxarifado-movimentacoes-saida", "/almoxarifado/movimentacoes/saida/", "Movimentações", 160, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Devoluções", "acesso-almoxarifado-movimentacoes-devolucao", "/almoxarifado/movimentacoes/devolucao/", "Movimentações", 170, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Transferência entre estoques", "acesso-almoxarifado-movimentacoes-transferencia", "/almoxarifado/movimentacoes/transferencia/", "Movimentações", 180, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Fracionamento", "acesso-almoxarifado-movimentacoes-fracionamento", "/almoxarifado/movimentacoes/fracionamento/", "Movimentações", 190, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Acerto de estoque", "acesso-almoxarifado-movimentacoes-acerto", "/almoxarifado/movimentacoes/acerto/", "Movimentações", 200, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Devolução", "acesso-almoxarifado-solicitacoes-devolucao", "/almoxarifado/solicitacoes/solicitar/?tipo=DEVOLUCAO", "Solicitações", 210, ["TI", "Almoxarifado"]),
    ("ALMOXARIFADO", "Solicitação de compras", "acesso-almoxarifado-solicitacoes-compras", "/almoxarifado/solicitacoes/solicitar/?tipo=COMPRA", "Solicitações", 220, ["TI", "Almoxarifado"]),
    ("SUPORTE", "Solicitar", "acesso-suporte-solicitacao-solicitar", "tickets:solicitar", "Solicitação", 10, ["TI", "Suporte"]),
    ("SUPORTE", "Atender", "acesso-suporte-solicitacao-atender", "tickets:atender", "Solicitação", 20, ["TI", "Suporte"]),
    ("SUPORTE", "Prioridades", "acesso-suporte-tabelas-prioridades", "tickets:prioridades", "Tabelas", 30, ["TI", "Suporte"]),
    ("SUPORTE", "Motivos de serviço", "acesso-suporte-tabelas-motivos-servico", "tickets:motivos_servico", "Tabelas", 40, ["TI", "Suporte"]),
    ("SUPORTE", "Motivos de conclusão", "acesso-suporte-tabelas-motivos-conclusao", "tickets:motivos_conclusao", "Tabelas", 50, ["TI", "Suporte"]),
    ("SUPORTE", "Oficinas", "acesso-suporte-tabelas-oficinas", "tickets:oficinas", "Tabelas", 60, ["TI", "Suporte"]),
    ("SUPORTE", "Usuário x oficina", "acesso-suporte-tabelas-usuario-oficina", "tickets:usuario_oficina", "Tabelas", 70, ["TI"]),
    ("GLOBAL", "CIDs", "acesso-global-cids", "/global/tabelas/auxiliares/cids/", "Auxiliares", 45, ["TI"]),
    ("GLOBAL", "Motivos de alta", "acesso-global-motivos-alta", "/global/tabelas/auxiliares/motivos_alta/", "Auxiliares", 46, ["TI"]),
    ("TI", "Usuário x oficina", "acesso-ti-acessos-usuario-oficina", "tickets:usuario_oficina", "Usuários e acessos > Acessos", 40, ["TI"]),
    ("TI", "Sessões e travas", "acesso-ti-sessoes-travas", "core:sessoes_travas", "Usuários e acessos", 50, ["TI"]),
]


def sync_catalog(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modules = {}
    for code, title in MODULES.items():
        modules[code], _ = Module.objects.update_or_create(
            code=code,
            defaults={"title": title, "active": True},
        )

    seen_access_keys = set()
    for module_code, title, slug, access_key, parent_label, order, role_names in SCREENS:
        if access_key in seen_access_keys:
            continue
        seen_access_keys.add(access_key)
        module = modules[module_code]
        screen, _ = ScreenDefinition.objects.update_or_create(
            access_key=access_key,
            defaults={
                "module": module,
                "title": title,
                "slug": slug,
                "screen_type": "configuracao",
                "parent_label": parent_label,
                "allow_query": True,
                "allow_insert": False,
                "allow_update": False,
                "allow_delete": False,
                "active": True,
                "order": order,
            },
        )
        for role_name in role_names:
            group, _ = Group.objects.get_or_create(name=role_name)
            role, _ = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=role, modulo=module)
            PapelTela.objects.get_or_create(papel=role, tela=screen)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more"),
        ("core", "0030_trava_edicao"),
    ]

    operations = [
        migrations.RunPython(sync_catalog, migrations.RunPython.noop),
    ]
