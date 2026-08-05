from django.db import migrations


def reorganizar_classificacao(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    atendimento = Module.objects.get(code="ATENDIMENTO")
    modulo_paineis = Module.objects.filter(code="TOTEM_SENHAS").first()

    classificacao, _ = Screen.objects.update_or_create(
        slug="atendimento-classificacao",
        defaults={
            "module": atendimento,
            "parent": None,
            "parent_label": "",
            "title": "Classificação",
            "screen_type": "grupo",
            "icon": "shield",
            "active": True,
            "order": 35,
        },
    )
    tabelas, _ = Screen.objects.update_or_create(
        slug="atendimento-classificacao-tabelas",
        defaults={
            "module": atendimento,
            "parent": classificacao,
            "parent_label": "",
            "title": "Tabelas",
            "screen_type": "grupo",
            "active": True,
            "order": 80,
        },
    )
    chamadas, _ = Screen.objects.update_or_create(
        slug="atendimento-classificacao-chamadas",
        defaults={
            "module": atendimento,
            "parent": classificacao,
            "parent_label": "",
            "title": "Chamadas",
            "screen_type": "grupo",
            "active": True,
            "order": 70,
        },
    )

    destinos = (
        ("atendimento:fila-classificacao", classificacao, "Classificação de Risco", 10),
        ("atendimento:classes-senha", tabelas, "Classes", 10),
        ("atendimento:protocolos-senha", tabelas, "Protocolos", 20),
        ("atendimento:icones-chamada", tabelas, "Ícones", 30),
        ("atendimento:configurar-senhas", chamadas, "Configurar senhas", 10),
        ("atendimento:maquinas-chamada", chamadas, "Máquinas", 20),
        ("atendimento:paineis-chamada", chamadas, "Painéis", 30),
    )
    for chave, pai, titulo, ordem in destinos:
        tela = Screen.objects.filter(access_key=chave).first()
        if not tela:
            continue
        tela.module = atendimento
        tela.parent = pai
        tela.parent_label = ""
        tela.title = titulo
        tela.order = ordem
        tela.active = True
        tela.save(update_fields=("module", "parent", "parent_label", "title", "order", "active", "updated_at"))

    cores, _ = Screen.objects.update_or_create(
        access_key="atendimento:cores-classificacao",
        defaults={
            "module": atendimento,
            "parent": tabelas,
            "parent_label": "",
            "title": "Cores",
            "slug": "atendimento-classificacao-cores",
            "screen_type": "formulario",
            "table_name": "cor_classificacao_risco",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": True,
            "active": True,
            "order": 40,
        },
    )

    if modulo_paineis:
        papeis = list(PapelModulo.objects.filter(modulo=modulo_paineis).values_list("papel_id", flat=True))
        for papel_id in papeis:
            PapelModulo.objects.get_or_create(papel_id=papel_id, modulo=atendimento)
        modulo_paineis.delete()

    for papel_modulo in PapelModulo.objects.filter(modulo=atendimento).select_related("papel"):
        if papel_modulo.papel.grupo.name == "TI":
            PapelTela.objects.get_or_create(papel=papel_modulo.papel, tela=cores)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_garantir_empresa_celeris_e_acesso_administrativo"),
        ("atendimento", "0047_cores_e_pre_cadastro_classificacao"),
        ("core", "0046_integrar_cadastros_ao_atendimento"),
    ]

    operations = [
        migrations.RunPython(reorganizar_classificacao, migrations.RunPython.noop),
    ]
