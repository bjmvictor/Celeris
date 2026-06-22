from django.db import migrations


MODULES = {
    "ATENDIMENTO": ("Atendimento", "clipboard-plus"),
    "CADASTROS": ("Cadastros", "table"),
    "GLOBAL": ("Global", "globe"),
    "ADMINISTRACAO": ("Administração", "wrench"),
}

SCREENS = [
    ("ATENDIMENTO", "Agendamentos", "acesso-atendimento-agendamentos", "atendimento:agendar", 10, ["TI", "Recepcionista"]),
    ("ATENDIMENTO", "Recepção", "acesso-atendimento-recepcao", "atendimento:recepcao", 20, ["TI", "Recepcionista"]),
    ("ATENDIMENTO", "Atendimentos", "acesso-atendimento-atendimentos", "atendimento:atendimentos", 30, ["TI", "Recepcionista", "Enfermeiro", "Médico"]),
    ("ATENDIMENTO", "Classificação de Risco", "acesso-atendimento-classificacao", "atendimento:fila-classificacao", 40, ["TI", "Enfermeiro"]),
    ("ATENDIMENTO", "Consultas Médicas", "acesso-atendimento-consultas", "atendimento:fila-medica", 50, ["TI", "Médico"]),
    ("CADASTROS", "Pacientes", "acesso-cadastros-pacientes", "atendimento:cadastro-paciente-novo", 10, ["TI", "Recepcionista"]),
    ("CADASTROS", "Prestadores", "acesso-cadastros-prestadores", "atendimento:cadastro-profissional-novo", 20, ["TI"]),
    ("CADASTROS", "Convênios", "acesso-cadastros-convenios", "atendimento:convenios", 30, ["TI", "Recepcionista"]),
    ("GLOBAL", "Estados", "acesso-global-estados", "/global/tabelas/auxiliares/estado/", 10, ["TI"]),
    ("GLOBAL", "Cidades", "acesso-global-cidades", "/global/tabelas/auxiliares/cidade/", 20, ["TI"]),
    ("GLOBAL", "Tipos de Logradouro", "acesso-global-logradouros", "/global/tabelas/auxiliares/tipo_logradouro/", 30, ["TI"]),
    ("GLOBAL", "Especialidades", "acesso-global-especialidades", "/global/tabelas/auxiliares/especialidade/", 40, ["TI"]),
    ("GLOBAL", "Conselhos Profissionais", "acesso-global-conselhos", "/global/tabelas/auxiliares/conselho_profissional/", 50, ["TI"]),
    ("GLOBAL", "Órgãos Emissores", "acesso-global-orgaos", "/global/tabelas/auxiliares/orgao_emissor/", 60, ["TI"]),
    ("GLOBAL", "Bancos", "acesso-global-bancos", "/global/tabelas/auxiliares/banco/", 70, ["TI"]),
    ("GLOBAL", "Nacionalidades", "acesso-global-nacionalidades", "/global/tabelas/auxiliares/pais/", 80, ["TI"]),
    ("GLOBAL", "Tipos de Prestador", "acesso-global-tipos-prestador", "/global/tabelas/auxiliares/tipo_prestador/", 90, ["TI"]),
    ("GLOBAL", "Tipos de Vínculo", "acesso-global-tipos-vinculo", "/global/tabelas/auxiliares/tipo_vinculo/", 100, ["TI"]),
    ("GLOBAL", "Outras tabelas auxiliares", "acesso-global-outras-tabelas", "core:global_tables", 110, ["TI"]),
    ("GLOBAL", "Importação de dados", "acesso-global-integracoes", "core:global_integrations", 120, ["TI"]),
    ("GLOBAL", "CEPs", "acesso-global-ceps", "core:global_ceps", 130, ["TI"]),
    ("GLOBAL", "Tipo de Prestador x Conselho", "acesso-global-prestador-conselho", "core:tipo_prestador_conselho", 140, ["TI"]),
    ("ADMINISTRACAO", "Usuários", "acesso-administracao-usuarios", "usuarios", 10, ["TI"]),
    ("ADMINISTRACAO", "Papéis", "acesso-administracao-papeis", "perfis", 20, ["TI"]),
    ("ADMINISTRACAO", "Permissões", "acesso-administracao-permissoes", "permissoes", 30, ["TI"]),
]


def seed_role_access(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modules = {}
    for code, (title, _icon) in MODULES.items():
        modules[code], _ = Module.objects.update_or_create(
            code=code,
            defaults={"title": title, "active": True},
        )

    role_screens = {}
    for module_code, title, slug, access_key, order, role_names in SCREENS:
        screen, _ = ScreenDefinition.objects.update_or_create(
            slug=slug,
            defaults={
                "module": modules[module_code],
                "title": title,
                "access_key": access_key,
                "screen_type": "configuracao",
                "allow_query": True,
                "allow_insert": False,
                "allow_update": False,
                "allow_delete": False,
                "active": True,
                "order": order,
            },
        )
        for role_name in role_names:
            role_screens.setdefault(role_name, []).append(screen)

    for role_name, screens in role_screens.items():
        group, _ = Group.objects.get_or_create(name=role_name)
        role, _ = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
        for screen in screens:
            PapelModulo.objects.get_or_create(papel=role, modulo=screen.module)
            PapelTela.objects.get_or_create(papel=role, tela=screen)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_papel_papeltela_papelmodulo"),
    ]

    operations = [
        migrations.RunPython(seed_role_access, migrations.RunPython.noop),
    ]
