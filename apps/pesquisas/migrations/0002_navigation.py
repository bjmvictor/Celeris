from django.db import migrations


SCREENS = [
    ("Configuração", "Pesquisas", "pesquisas-configuracao", "pesquisas:configuracao", "settings", 10, ["TI"]),
    ("Configuração", "Perguntas e parâmetros", "pesquisas-perguntas-parametros", "pesquisas:perguntas_parametros", "list-checks", 20, ["TI"]),
    ("Configuração", "Cálculos e mensagens", "pesquisas-calculos-resultados", "pesquisas:calculos_resultados", "calculator", 30, ["TI"]),
    ("Aplicação", "Pesquisas disponíveis", "pesquisas-disponiveis", "pesquisas:disponiveis", "clipboard-list", 10, ["TI", "Recepcionista", "Enfermeiro", "Médico"]),
    ("Aplicação", "Resultados", "pesquisas-resultados", "pesquisas:resultados", "chart-column", 20, ["TI"]),
]


def seed_navigation(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    module, _ = Module.objects.update_or_create(
        code="PESQUISAS",
        defaults={"title": "Pesquisas", "icon": "clipboard-list", "order": 35, "active": True, "is_system": False},
    )
    groups = {}
    for order, title in enumerate(("Configuração", "Aplicação"), start=1):
        group, _ = Screen.objects.update_or_create(
            slug=f"pesquisas-grupo-{title.lower().replace('ç', 'c').replace('ã', 'a')}" if title != "Aplicação" else "pesquisas-grupo-aplicacao",
            defaults={
                "module": module, "title": title, "screen_type": "grupo", "roles": ["TI"],
                "active": True, "order": order * 10,
            },
        )
        groups[title] = group

    for parent_title, title, slug, access_key, icon, order, role_names in SCREENS:
        screen, _ = Screen.objects.update_or_create(
            access_key=access_key,
            defaults={
                "module": module, "parent": groups[parent_title], "parent_label": parent_title,
                "title": title, "slug": slug, "icon": icon, "roles": role_names,
                "screen_type": "configuracao" if parent_title == "Configuração" else "consulta",
                "allow_query": parent_title == "Aplicação", "allow_insert": False,
                "allow_update": parent_title == "Configuração", "allow_delete": False,
                "active": True, "order": order,
            },
        )
        for role_name in role_names:
            group, _ = Group.objects.get_or_create(name=role_name)
            role, _ = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=role, modulo=module)
            PapelTela.objects.get_or_create(papel=role, tela=screen)


def remove_navigation(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Module.objects.filter(code="PESQUISAS").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0044_sanear_menu_e_catalogar_auxiliares"),
        ("pesquisas", "0001_initial"),
    ]

    operations = [migrations.RunPython(seed_navigation, remove_navigation)]
