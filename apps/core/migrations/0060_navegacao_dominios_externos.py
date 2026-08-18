from django.db import migrations


def adicionar_tela_dominios_externos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modulo = Module.objects.filter(code="GLOBAL").first()
    if not modulo:
        return
    configuracao = Screen.objects.filter(
        module=modulo,
        screen_type="grupo",
        title__iexact="Configuração do Sistema",
    ).first()
    if not configuracao:
        configuracao = Screen.objects.create(
            module=modulo,
            title="Configuração do Sistema",
            slug="global-configuracao-sistema",
            screen_type="grupo",
            roles=["TI"],
            active=True,
            order=50,
        )
    tela, _ = Screen.objects.update_or_create(
        access_key="core:dominios_externos",
        defaults={
            "module": modulo,
            "parent": configuracao,
            "parent_label": configuracao.title,
            "title": "Domínios externos",
            "slug": "global-configuracao-dominios-externos",
            "navigation_url": "",
            "icon": "globe",
            "roles": ["TI"],
            "screen_type": "configuracao",
            "table_name": "dominio_externo_permitido",
            "description": "Domínios HTTPS autorizados para integrações externas e exibição no PEP.",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": True,
            "active": True,
            "order": 30,
        },
    )
    grupo_ti, _ = Group.objects.get_or_create(name="TI")
    papel, _ = Papel.objects.get_or_create(grupo=grupo_ti, defaults={"sn_ativo": True})
    PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
    PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_alter_user_groups_alter_user_is_active_and_more"),
        ("core", "0059_auditoriacertificadodigital"),
    ]

    operations = [
        migrations.RunPython(adicionar_tela_dominios_externos, migrations.RunPython.noop),
    ]
