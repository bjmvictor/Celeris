from django.db import migrations, models


def _svg(body):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )


ICONES_MODULOS = (
    ("grid", "Grade", _svg('<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>')),
    ("activity", "Atendimento", _svg('<path d="M22 12h-4l-3 8-6-16-3 8H2"/>')),
    ("users", "Usuários", _svg('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>')),
    ("user", "Profissional", _svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>')),
    ("stethoscope", "Clínico", _svg('<path d="M6 4v6a4 4 0 0 0 8 0V4"/><path d="M4 4h4"/><path d="M12 4h4"/><path d="M10 14v2a4 4 0 0 0 8 0v-1"/><circle cx="19" cy="13" r="2"/>')),
    ("clipboard-plus", "Prontuário", _svg('<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 14h6"/><path d="M12 11v6"/>')),
    ("calendar", "Agenda", _svg('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>')),
    ("boxes", "Caixas", _svg('<path d="M2.97 7.92 12 2.97l9.03 4.95L12 12.97 2.97 7.92Z"/><path d="M2.97 12.92 12 17.97l9.03-5.05"/><path d="M2.97 7.92v10.05L12 23.02l9.03-5.05V7.92"/><path d="M12 12.97v10.05"/>')),
    ("package", "Produto", _svg('<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><polyline points="3.29 7 12 12 20.71 7"/>')),
    ("shopping-cart", "Compras", _svg('<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>')),
    ("coins", "Financeiro", _svg('<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1.5a1.5 1.5 0 0 1 0 3H7V6Z"/><path d="M7 9h2a1.5 1.5 0 0 1 0 3H7V9Z"/>')),
    ("headset", "Suporte", _svg('<path d="M3 13a9 9 0 0 1 18 0"/><path d="M21 13v4a2 2 0 0 1-2 2h-2v-6h4Z"/><path d="M3 13v4a2 2 0 0 0 2 2h2v-6H3Z"/><path d="M13 21h3a3 3 0 0 0 3-3"/>')),
    ("wrench", "Ferramentas", _svg('<path d="M14.7 6.3a4 4 0 0 0-5 5L3 18v3h3l6.7-6.7a4 4 0 0 0 5-5l-2.4 2.4-3-3 2.4-2.4Z"/>')),
    ("monitor", "Tecnologia", _svg('<rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 22h8"/><path d="M12 18v4"/>')),
    ("globe", "Global", _svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18"/><path d="M12 3a15 15 0 0 0 0 18"/>')),
    ("table", "Tabelas", _svg('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>')),
    ("form", "Formulários", _svg('<path d="M4 14h6"/><path d="M4 2h10"/><rect x="4" y="18" width="16" height="4" rx="1"/><rect x="4" y="6" width="16" height="4" rx="1"/>')),
    ("ticket", "Senhas", _svg('<path d="M2 9a3 3 0 0 0 0 6v3a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-3a3 3 0 0 0 0-6V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>')),
    ("presentation", "Painéis", _svg('<path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/>')),
    ("briefcase", "Maleta", _svg('<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>')),
    ("car", "Carro", _svg('<path d="M5 17h14"/><path d="M6 17v2"/><path d="M18 17v2"/><path d="m4 13 2-6h12l2 6"/><path d="M3 13h18v4H3z"/><circle cx="7" cy="15" r="1"/><circle cx="17" cy="15" r="1"/>')),
    ("ambulance", "Ambulância", _svg('<path d="M3 17h18"/><path d="M5 17v2"/><path d="M18 17v2"/><path d="M4 7h9v10H4z"/><path d="M13 10h4l3 3v4h-7z"/><path d="M8.5 9v4"/><path d="M6.5 11h4"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>')),
)


def seed_icones_e_navegacao(apps, schema_editor):
    IconeSistema = apps.get_model("core", "IconeSistema")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Group = apps.get_model("auth", "Group")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    for codigo, nome, svg in ICONES_MODULOS:
        IconeSistema.objects.update_or_create(
            cd_icone=codigo,
            defaults={"nm_icone": nome, "ds_svg": svg, "sn_ativo": True},
        )

    modulo = Module.objects.filter(code="GLOBAL").first()
    if not modulo:
        return
    existing_config = Screen.objects.filter(access_key="core:system_screens").select_related("parent").first()
    papel_ids = list(PapelTela.objects.filter(tela=existing_config).values_list("papel_id", flat=True)) if existing_config else []
    has_existing_container = bool(
        existing_config
        and existing_config.parent
        and existing_config.parent.title.casefold() == "módulos e telas".casefold()
    )
    if has_existing_container:
        container = existing_config.parent
        configurar = existing_config
        configurar.title = "Configurar"
        configurar.screen_type = "configuracao"
        configurar.roles = ["TI"]
        configurar.active = True
        configurar.order = 10
        configurar.save()
    elif not existing_config:
        parent = Screen.objects.filter(module=modulo, title="Configuração do Sistema").first()
        container = Screen.objects.create(
            module=modulo,
            parent=parent,
            title="Módulos e Telas",
            slug="global-configuracao-modulos-telas",
            screen_type="grupo",
            active=True,
            order=10,
        )
    else:
        container = existing_config
        container.access_key = None
        container.navigation_url = ""
        container.screen_type = "grupo"
        container.allow_query = False
        container.allow_insert = False
        container.allow_update = False
        container.allow_delete = False
        container.save()

    if not has_existing_container:
        configurar, _ = Screen.objects.update_or_create(
            access_key="core:system_screens",
            defaults={
                "module": modulo,
                "parent": container,
                "title": "Configurar",
                "slug": "global-configuracao-modulos-telas-configurar",
                "screen_type": "configuracao",
                "roles": ["TI"],
                "active": True,
                "order": 10,
            },
        )
    icones, _ = Screen.objects.update_or_create(
        access_key="core:system_icons",
        defaults={
            "module": modulo,
            "parent": container,
            "title": "Ícones",
            "slug": "global-configuracao-modulos-telas-icones",
            "screen_type": "configuracao",
            "roles": ["TI"],
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": True,
            "active": True,
            "order": 20,
        },
    )

    for group in Group.objects.filter(name="TI"):
        papel, _ = Papel.objects.get_or_create(grupo=group)
        papel_ids.append(papel.pk)
    for papel_id in set(papel_ids):
        PapelModulo.objects.get_or_create(papel_id=papel_id, modulo=modulo)
        PapelTela.objects.get_or_create(papel_id=papel_id, tela=configurar)
        PapelTela.objects.get_or_create(papel_id=papel_id, tela=icones)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_garantir_empresa_celeris_e_acesso_administrativo"),
        ("core", "0038_corrigir_cadastro_usuarios"),
    ]

    operations = [
        migrations.CreateModel(
            name="IconeSistema",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("cd_icone_sistema", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_icone", models.CharField(max_length=50, unique=True)),
                ("nm_icone", models.CharField(max_length=80, unique=True)),
                ("ds_svg", models.TextField(blank=True)),
                ("sn_ativo", models.BooleanField(default=True)),
            ],
            options={"db_table": "icone_sistema", "ordering": ("nm_icone",)},
        ),
        migrations.RunPython(seed_icones_e_navegacao, migrations.RunPython.noop),
    ]
