from django.db import migrations


def adicionar_tela_certificados(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modulo = Module.objects.filter(code="GLOBAL").first()
    if not modulo:
        return
    empresa = Screen.objects.filter(
        module=modulo,
        screen_type="grupo",
        title__iexact="Empresa",
    ).first()
    if not empresa:
        empresa = Screen.objects.create(
            module=modulo,
            title="Empresa",
            slug="global-empresa",
            screen_type="grupo",
            active=True,
            order=20,
        )
    tela, _ = Screen.objects.update_or_create(
        access_key="core:certificados_digitais",
        defaults={
            "module": modulo,
            "parent": empresa,
            "parent_label": empresa.title,
            "title": "Certificados digitais",
            "slug": "global-empresa-certificados-digitais",
            "navigation_url": "",
            "icon": "badge-check",
            "roles": ["TI"],
            "screen_type": "configuracao",
            "table_name": "certificado_digital_empresa",
            "description": "Certificados A1 usados na assinatura permanente de documentos.",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": False,
            "active": True,
            "order": 40,
        },
    )
    grupo_ti, _ = Group.objects.get_or_create(name="TI")
    papel, _ = Papel.objects.get_or_create(grupo=grupo_ti, defaults={"sn_ativo": True})
    PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
    PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_alter_user_groups_alter_user_is_active_and_more"),
        ("core", "0057_certificadodigitalempresa_and_more"),
    ]

    operations = [migrations.RunPython(adicionar_tela_certificados, migrations.RunPython.noop)]
