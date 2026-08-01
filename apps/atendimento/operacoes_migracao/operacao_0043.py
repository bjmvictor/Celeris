"""Operações históricas de dados da migration 0043."""

from django.db import migrations


ICONES_PADRAO = [
    ("Padrão", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M8 12h8"/></svg>'),
    ("Masculino", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="14" r="5"/><path d="M14 10 21 3"/><path d="M16 3h5v5"/></svg>'),
    ("Feminino", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="9" r="5"/><path d="M12 14v7"/><path d="M8 18h8"/></svg>'),
    ("Criança", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="7" r="4"/><path d="M6 21v-2a6 6 0 0 1 12 0v2"/><path d="M8 6h8"/></svg>'),
    ("Idoso", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="5" r="3"/><path d="M10 8v6l-3 7"/><path d="M10 14h4l3 7"/><path d="M16 11v10"/></svg>'),
    ("Gestante", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="5" r="3"/><path d="M8 21c0-5 1-10 4-10 4 0 6 4 6 8"/><path d="M6 13c2 2 7 2 9 0"/></svg>'),
    ("Cadeirante", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="4" r="2"/><path d="M9 6v7h6l3 6"/><circle cx="9" cy="17" r="5"/><path d="M12 10h4"/></svg>'),
    ("Ambulância", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 17h18"/><path d="M4 7h9v10H4z"/><path d="M13 10h4l3 3v4h-7z"/><path d="M8.5 9v4"/><path d="M6.5 11h4"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>'),
    ("Profissional", '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="7" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/><path d="M9 14l3 3 3-3"/></svg>'),
]


def seed_paineis_chamada(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Icone = apps.get_model("atendimento", "IconeChamada")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Group = apps.get_model("auth", "Group")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    for empresa in Empresa.objects.all():
        for nome, svg in ICONES_PADRAO:
            Icone.objects.get_or_create(
                cd_empresa_id=empresa.pk,
                nm_icone=nome,
                defaults={"ds_svg": svg, "sn_ativo": True},
            )

    modulo, _ = Module.objects.update_or_create(
        code="TOTEM_SENHAS",
        defaults={"title": "Painéis de Chamada", "active": True},
    )
    Screen.objects.filter(access_key__in=["acesso-totem-gerar-senha"], module=modulo).update(active=False)
    Screen.objects.filter(slug__in=["totem-gerar-senha"], module=modulo).update(active=False)
    telas = [
        ("Configurar", "paineis-configurar-senhas", "atendimento:configurar-senhas", "", 10, False),
        ("Classes", "paineis-classes-senha", "atendimento:classes-senha", "Tabelas", 20, True),
        ("Protocolos", "paineis-protocolos-senha", "atendimento:protocolos-senha", "Tabelas", 30, True),
        ("Ícones", "paineis-icones-chamada", "atendimento:icones-chamada", "Tabelas", 40, True),
        ("Máquinas", "paineis-maquinas-chamada", "atendimento:maquinas-chamada", "Tabelas", 50, True),
    ]
    for titulo, slug, acesso, parent, ordem, allow_delete in telas:
        tela, _ = Screen.objects.update_or_create(
            access_key=acesso,
            defaults={
                "module": modulo,
                "title": titulo,
                "slug": slug,
                "screen_type": "formulario",
                "parent_label": parent,
                "table_name": "",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": allow_delete,
                "active": True,
                "order": ordem,
            },
        )
        for grupo in Group.objects.filter(name="TI"):
            papel, _ = Papel.objects.get_or_create(grupo=grupo)
            PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
            PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):

    dependencies = [
        ("atendimento", "0042_iconechamada_classesenhaatendimento_cd_icone_chamada_and_more"),
        ("core", "0032_corrigir_tela_alteracao_senha"),
        ("accounts", "0015_sync_navigation_role_catalog"),
    ]

    operations = [
        migrations.RunPython(seed_paineis_chamada, migrations.RunPython.noop),
    ]
