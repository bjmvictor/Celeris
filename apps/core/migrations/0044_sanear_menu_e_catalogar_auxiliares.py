from django.db import migrations
from django.utils.text import slugify


REMOVED_ACCESS_KEYS = {
    "atendimento:fila-medica",
    "atendimento:pep",
    "atendimento:demanda-espontanea",
}

REMOVED_SLUGS = {
    "bi-dashboard-geral",
    "pacientes-historico",
    "bi-financeiro",
    "relacionamento-campanhas",
    "relacionamento-leads",
    "relacionamento-satisfacao",
}


def sanitize_navigation(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    AuxiliaryTable = apps.get_model("core", "TabelaAuxiliarGlobal")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    Screen.objects.filter(access_key__in=REMOVED_ACCESS_KEYS).delete()
    Screen.objects.filter(slug__in=REMOVED_SLUGS).delete()

    Screen.objects.filter(access_key="atendimento:atendimentos").update(
        title="Consulta de atendimentos",
        screen_type="consulta",
        parent=None,
        parent_label="",
        table_name="atendimento",
        allow_query=True,
        allow_insert=False,
        allow_update=False,
        allow_delete=False,
        active=True,
    )

    global_module = Module.objects.get(code="GLOBAL")
    Screen.objects.filter(
        module=global_module,
        screen_type="grupo",
        title__in=("Relacionamento", "Relacionamentos"),
        children__isnull=True,
    ).delete()

    auxiliary_group = Screen.objects.filter(
        module=global_module, title="Tabelas Auxiliares", screen_type="grupo", parent__isnull=True
    ).first()
    if not auxiliary_group:
        auxiliary_group = Screen.objects.create(
            module=global_module,
            title="Tabelas Auxiliares",
            slug="global-tabelas-auxiliares",
            screen_type="grupo",
            icon="table-2",
            roles=["TI"],
            active=True,
            order=80,
        )

    ti_group, _ = Group.objects.get_or_create(name="TI")
    ti_role, _ = Papel.objects.get_or_create(grupo=ti_group, defaults={"sn_ativo": True})
    PapelModulo.objects.get_or_create(papel=ti_role, modulo=global_module)

    for order, table in enumerate(AuxiliaryTable.objects.filter(sn_ativo=True).order_by("ds_tabela"), start=1):
        url = f"/global/tabelas/auxiliares/{table.ds_tabela}/"
        if table.ds_tabela == "sexo":
            screen = Screen.objects.filter(access_key="core:global_sexo").first()
        else:
            screen = Screen.objects.filter(access_key=url).first() or Screen.objects.filter(navigation_url=url).first()
        title = table.ds_descricao or table.ds_tabela.replace("_", " ").title()
        if not screen:
            base_slug = f"global-aux-{slugify(table.ds_tabela)}"
            candidate = base_slug
            suffix = 2
            while Screen.objects.filter(slug=candidate).exists():
                candidate = f"{base_slug}-{suffix}"
                suffix += 1
            screen = Screen.objects.create(
                module=global_module,
                title=title,
                slug=candidate,
                access_key=url,
                navigation_url=url,
                icon="list",
                roles=["TI"],
                screen_type="configuracao",
                parent=auxiliary_group,
                parent_label="Tabelas Auxiliares",
                table_name="valor_auxiliar",
                description=f"Valores da tabela auxiliar {table.ds_tabela}.",
                allow_query=True,
                allow_insert=True,
                allow_update=True,
                allow_delete=False,
                active=True,
                order=order * 10,
            )
        else:
            screen.module = global_module
            screen.parent = auxiliary_group
            screen.parent_label = "Tabelas Auxiliares"
            screen.title = title
            screen.table_name = "valor_auxiliar"
            screen.screen_type = "configuracao"
            screen.roles = ["TI"]
            screen.allow_query = True
            screen.allow_insert = True
            screen.allow_update = True
            screen.allow_delete = False
            screen.active = True
            screen.order = order * 10
            if table.ds_tabela != "sexo":
                screen.access_key = url
                screen.navigation_url = url
            screen.save()
        PapelTela.objects.get_or_create(papel=ti_role, tela=screen)

    Screen.objects.filter(parent=auxiliary_group, title="Outras tabelas auxiliares").update(
        order=(AuxiliaryTable.objects.filter(sn_ativo=True).count() + 1) * 10
    )


class Migration(migrations.Migration):
    dependencies = [("core", "0043_catalogo_minimo_especialidades")]

    operations = [migrations.RunPython(sanitize_navigation, migrations.RunPython.noop)]
