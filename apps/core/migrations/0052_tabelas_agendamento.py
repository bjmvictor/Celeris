from django.db import migrations


def organizar_tabelas_agendamento(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    PapelTela = apps.get_model("accounts", "PapelTela")
    modulo = Module.objects.filter(code="ATENDIMENTO").first()
    if not modulo:
        return
    agendamento = Screen.objects.filter(module=modulo, title__iexact="Agendamento", screen_type="grupo").first()
    if not agendamento:
        agendamento = Screen.objects.create(
            module=modulo,
            title="Agendamento",
            slug="atendimento-agendamento",
            screen_type="grupo",
            order=10,
            active=True,
        )
    tabelas, _ = Screen.objects.update_or_create(
        slug="atendimento-agendamento-tabelas",
        defaults={
            "module": modulo,
            "parent": agendamento,
            "title": "Tabelas",
            "screen_type": "grupo",
            "order": 90,
            "active": True,
        },
    )
    telas = []
    for chave, titulo, ordem in (
        ("atendimento:tipos-atendimento-agendamento", "Tipos de Agendamentos", 10),
        ("atendimento:especialidades-agendamento", "Especialidades", 20),
    ):
        tela = Screen.objects.filter(access_key=chave).first()
        if tela:
            tela.parent = tabelas
            tela.title = titulo
            tela.order = ordem
            tela.active = True
            tela.save(update_fields=("parent", "title", "order", "active", "updated_at"))
            telas.append(tela)
    setores, _ = Screen.objects.update_or_create(
        access_key="atendimento:setores-atendimento-agendamento",
        defaults={
            "module": modulo,
            "parent": tabelas,
            "title": "Setores de Atendimento",
            "slug": "atendimento-agendamento-setores-atendimento",
            "screen_type": "formulario",
            "table_name": "setor",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": True,
            "active": True,
            "order": 30,
        },
    )
    telas.append(setores)
    papeis = PapelTela.objects.filter(papel__grupo__name="TI").values_list("papel_id", flat=True).distinct()
    for papel_id in papeis:
        for tela in telas:
            PapelTela.objects.get_or_create(papel_id=papel_id, tela=tela)


class Migration(migrations.Migration):
    dependencies = [("core", "0051_limpar_navegacao_classificacao")]
    operations = [migrations.RunPython(organizar_tabelas_agendamento, migrations.RunPython.noop)]
