from django.db import migrations


def integrar_cadastros(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")

    atendimento = Module.objects.get(code="ATENDIMENTO")
    modulo_cadastros = Module.objects.filter(code="CADASTROS").first()
    grupo_cadastros, _ = Screen.objects.update_or_create(
        slug="atendimento-cadastros",
        defaults={
            "module": atendimento,
            "parent": None,
            "parent_label": "",
            "title": "Cadastros",
            "screen_type": "grupo",
            "icon": "",
            "active": True,
            "order": 25,
        },
    )

    destinos = (
        ("atendimento:cadastro-paciente-novo", "Pacientes", 10),
        ("atendimento:cadastro-profissional-novo", "Prestadores", 20),
        ("atendimento:convenios", "Convênios", 30),
        ("/telas/cadastros-planos/", "Planos", 40),
        ("/telas/cadastros-procedimentos/", "Procedimentos", 50),
        ("/telas/cadastros-salas-recursos/", "Salas e Recursos", 60),
    )
    for chave, titulo, ordem in destinos:
        tela = Screen.objects.filter(access_key=chave).first()
        if not tela:
            continue
        tela.module = atendimento
        tela.parent = grupo_cadastros
        tela.parent_label = ""
        tela.title = titulo
        tela.order = ordem
        tela.active = True
        tela.save(
            update_fields=("module", "parent", "parent_label", "title", "order", "active", "updated_at")
        )

    Screen.objects.filter(
        module=atendimento,
        title__in=("Pacientes",),
        screen_type="grupo",
    ).exclude(pk=grupo_cadastros.pk).delete()
    if modulo_cadastros:
        modulo_cadastros.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0045_atualizar_navegacao_atendimento"),
    ]

    operations = [
        migrations.RunPython(integrar_cadastros, migrations.RunPython.noop),
    ]
