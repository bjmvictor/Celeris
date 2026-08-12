from django.db import migrations


def cadastrar_telas(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    PapelTela = apps.get_model("accounts", "PapelTela")
    atendimento = Module.objects.filter(code="ATENDIMENTO").first()
    if not atendimento:
        return
    classificacao = Screen.objects.filter(slug="atendimento-classificacao").first()
    if not classificacao:
        return
    configuracao, _ = Screen.objects.update_or_create(
        slug="atendimento-classificacao-configuracao",
        defaults={
            "module": atendimento,
            "parent": classificacao,
            "title": "Configuração",
            "screen_type": "grupo",
            "active": True,
            "order": 60,
        },
    )
    telas = []
    for chave, slug, titulo, tabela, ordem in (
        ("atendimento:perguntas-classificacao", "atendimento-classificacao-perguntas", "Perguntas", "pergunta_classificacao", 10),
        ("atendimento:fluxos-classificacao", "atendimento-classificacao-fluxos", "Fluxos e sintomas", "fluxo_classificacao", 20),
    ):
        tela, _ = Screen.objects.update_or_create(
            access_key=chave,
            defaults={
                "module": atendimento,
                "parent": configuracao,
                "title": titulo,
                "slug": slug,
                "screen_type": "formulario",
                "table_name": tabela,
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": True,
                "active": True,
                "order": ordem,
            },
        )
        telas.append(tela)
    configuracao_atendimento, _ = Screen.objects.update_or_create(
        slug="atendimento-configuracao",
        defaults={
            "module": atendimento,
            "parent": None,
            "title": "Configuração",
            "screen_type": "grupo",
            "active": True,
            "order": 85,
        },
    )
    tela_impressao, _ = Screen.objects.update_or_create(
        access_key="atendimento:documentos-telas-impressao",
        defaults={
            "module": atendimento,
            "parent": configuracao_atendimento,
            "title": "Documentos × telas de impressão",
            "slug": "atendimento-documentos-telas-impressao",
            "screen_type": "formulario",
            "table_name": "modelo_documento_tela_impressao",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": True,
            "active": True,
            "order": 10,
        },
    )
    telas.append(tela_impressao)
    papeis_ti = PapelTela.objects.filter(tela__module=atendimento, papel__grupo__name="TI").values_list("papel_id", flat=True).distinct()
    for papel_id in papeis_ti:
        for tela in telas:
            PapelTela.objects.get_or_create(papel_id=papel_id, tela=tela)

    global_modulo = Module.objects.filter(code="GLOBAL").first()
    if not global_modulo:
        return
    tabelas = Screen.objects.filter(module=global_modulo, screen_type="grupo", title__iexact="Tabelas").first()
    if not tabelas:
        tabelas = Screen.objects.create(
            module=global_modulo,
            title="Tabelas",
            slug="global-tabelas",
            screen_type="grupo",
            active=True,
            order=80,
        )
    auxiliares = Screen.objects.filter(module=global_modulo, parent=tabelas, screen_type="grupo", title__iexact="Auxiliares").first()
    if not auxiliares:
        auxiliares = Screen.objects.create(
            module=global_modulo,
            parent=tabelas,
            title="Auxiliares",
            slug="global-tabelas-auxiliares",
            screen_type="grupo",
            active=True,
            order=10,
        )
    catalogos = (
        ("nacionalidade", "Nacionalidades"),
        ("pais", "Países"),
        ("raca_cor", "Raças/cores"),
        ("identidade_genero", "Identidades de gênero"),
        ("orientacao_sexual", "Orientações sexuais"),
        ("cbo", "Classificação Brasileira de Ocupações (CBO)"),
    )
    telas_catalogo = []
    for ordem, (chave, titulo) in enumerate(catalogos, start=1):
        tela, _ = Screen.objects.update_or_create(
            slug=f"global-auxiliar-{chave.replace('_', '-')}",
            defaults={
                "module": global_modulo,
                "parent": auxiliares,
                "title": titulo,
                "screen_type": "formulario",
                "table_name": "valor_auxiliar_global",
                "access_key": f"core:global-auxiliar:{chave}",
                "navigation_url": f"/global/tabelas/auxiliares/{chave}/",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": True,
                "active": True,
                "order": ordem * 10,
            },
        )
        telas_catalogo.append(tela)
    papeis_global_ti = PapelTela.objects.filter(tela__module=global_modulo, papel__grupo__name="TI").values_list("papel_id", flat=True).distinct()
    for papel_id in papeis_global_ti:
        for tela in telas_catalogo:
            PapelTela.objects.get_or_create(papel_id=papel_id, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_alter_user_groups_alter_user_is_active_and_more"),
        ("core", "0049_atualizar_catalogos_sociodemograficos_e_cbo"),
    ]
    operations = [migrations.RunPython(cadastrar_telas, migrations.RunPython.noop)]
