"""Operações históricas de dados da migration 0013."""

from django.db import migrations


SCREENS = [
    ("ATENDIMENTO", "Editor de documentos", "acesso-atendimento-editor-documentos", "atendimento:modelos-documento", "Documentos", 50, ["TI"]),
    ("ATENDIMENTO", "Perfis assistenciais", "acesso-atendimento-perfis-assistenciais", "atendimento:perfis-assistenciais", "Configurações", 60, ["TI"]),
    ("ATENDIMENTO", "PEP", "acesso-atendimento-pep", "atendimento:pep", "Assistencial", 100, ["TI", "Enfermeiro", "Médico"]),
    ("ATENDIMENTO", "Demanda espontânea", "acesso-atendimento-demanda-espontanea", "atendimento:demanda-espontanea", "Recepção", 130, ["TI", "Recepcionista"]),
    ("GLOBAL", "Empresas", "acesso-global-empresas", "core:system_companies", "Empresa", 5, ["TI"]),
    ("GLOBAL", "Setores", "acesso-global-setores", "core:setores", "Empresa", 6, ["TI"]),
    ("GLOBAL", "Setores de Atendimento", "acesso-global-setores-atendimento", "core:setores_atendimento", "Empresa", 7, ["TI"]),
    ("GLOBAL", "Painel de Chamada", "acesso-global-painel-chamada", "atendimento:paineis-chamada", "Empresa", 8, ["TI"]),
    ("ADMINISTRACAO", "Cópia de usuário", "acesso-administracao-copia-usuario", "copia_usuario", "", 15, ["TI"]),
]


def sync_recent_screens(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    for module_code, title, slug, access_key, parent_label, order, role_names in SCREENS:
        module = Module.objects.get(code=module_code)
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
        ("accounts", "0012_usuario_prestador_unico"),
        ("atendimento", "0035_modelodocumento_configuracao_assinatura"),
        ("core", "0021_screendefinition_access_key"),
    ]

    operations = [
        migrations.RunPython(sync_recent_screens, migrations.RunPython.noop),
    ]
