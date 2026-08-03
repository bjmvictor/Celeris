from django.db import migrations


def atualizar_navegacao_atendimento(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modulo = Module.objects.get(code="ATENDIMENTO")
    pacientes = Screen.objects.filter(
        module=modulo,
        screen_type="grupo",
        title__iexact="Pacientes",
    ).first()
    if not pacientes:
        pacientes = Screen.objects.create(
            module=modulo,
            title="Pacientes",
            slug="atendimento-pacientes",
            screen_type="grupo",
            order=30,
            active=True,
        )

    Screen.objects.filter(
        module=modulo,
        title__in=("Agenda e Atendimento", "Responsaveis", "Responsáveis", "Relatorio de Pacientes", "Relatório de Pacientes"),
    ).update(active=False)
    Screen.objects.filter(
        module=modulo,
        access_key__in=("bi-agenda-atendimento", "pacientes-responsaveis", "pacientes-relatorio"),
    ).update(active=False)

    cadastro = Screen.objects.filter(access_key="atendimento:cadastro-paciente-novo").first()
    if not cadastro:
        cadastro = Screen.objects.create(
            module=modulo,
            parent=pacientes,
            title="Cadastro de pacientes",
            slug="atendimento-pacientes-cadastro",
            access_key="atendimento:cadastro-paciente-novo",
            screen_type="formulario",
            table_name="paciente",
            order=10,
        )
    cadastro.module = modulo
    cadastro.parent = pacientes
    cadastro.parent_label = "Pacientes"
    cadastro.title = "Cadastro de pacientes"
    cadastro.navigation_url = ""
    cadastro.allow_query = True
    cadastro.allow_insert = True
    cadastro.allow_update = True
    cadastro.allow_delete = False
    cadastro.active = True
    cadastro.save()

    Screen.objects.filter(
        module=modulo,
        title__in=("Cadastro de Paciente", "Cadastro de paciente"),
    ).exclude(pk=cadastro.pk).update(active=False)

    consulta, _ = Screen.objects.update_or_create(
        access_key="atendimento:atendimentos",
        defaults={
            "module": modulo,
            "parent": None,
            "parent_label": "",
            "title": "Consulta de atendimentos",
            "slug": "atendimento-consulta-atendimentos",
            "screen_type": "consulta",
            "table_name": "atendimento",
            "allow_query": True,
            "allow_insert": False,
            "allow_update": False,
            "allow_delete": False,
            "active": True,
            "order": 30,
        },
    )
    alteracao, _ = Screen.objects.update_or_create(
        access_key="atendimento:alteracao-atendimento",
        defaults={
            "module": modulo,
            "parent": None,
            "parent_label": "",
            "title": "Alteração de atendimento",
            "slug": "atendimento-alteracao-atendimento",
            "screen_type": "formulario",
            "table_name": "atendimento",
            "allow_query": True,
            "allow_insert": False,
            "allow_update": True,
            "allow_delete": False,
            "active": True,
            "order": 40,
        },
    )

    for group_name in ("TI", "Recepcionista", "Enfermeiro", "Médico"):
        group = Group.objects.filter(name=group_name).first()
        if not group:
            continue
        papel = Papel.objects.filter(grupo=group, sn_ativo=True).first()
        if not papel:
            continue
        PapelTela.objects.get_or_create(papel=papel, tela=consulta)
        PapelTela.objects.get_or_create(papel=papel, tela=alteracao)
        PapelTela.objects.get_or_create(papel=papel, tela=cadastro)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_garantir_empresa_celeris_e_acesso_administrativo"),
        ("core", "0044_sanear_menu_e_catalogar_auxiliares"),
    ]

    operations = [migrations.RunPython(atualizar_navegacao_atendimento, migrations.RunPython.noop)]
