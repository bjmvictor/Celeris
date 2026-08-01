from django.db import migrations


def corrigir_cadastro_usuarios(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    modulo_ti = Module.objects.filter(code="TI").first()
    atualizacoes = {
        "title": "Cadastro de usuários",
        "parent_label": "Usuários e acessos",
    }
    if modulo_ti:
        atualizacoes["module"] = modulo_ti

    ScreenDefinition.objects.filter(access_key="usuarios").update(**atualizacoes)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_garantir_empresa_celeris_e_acesso_administrativo"),
        ("core", "0034_permissoes_catalogos_consolidada"),
    ]

    operations = [
        migrations.RunPython(corrigir_cadastro_usuarios, migrations.RunPython.noop),
    ]
