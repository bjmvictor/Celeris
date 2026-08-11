from django.db import migrations


def limpar_navegacao(apps, schema_editor):
    Screen = apps.get_model("core", "ScreenDefinition")
    tela = Screen.objects.filter(access_key="atendimento:classes-senha").first()
    if not tela:
        return

    grupo_oculto, _ = Screen.objects.update_or_create(
        slug="atendimento-classificacao-legado-oculto",
        defaults={
            "module_id": tela.module_id,
            "parent_id": tela.parent_id,
            "title": "Compatibilidade de classificação",
            "screen_type": "grupo",
            "active": False,
            "order": 999,
        },
    )
    tela.parent_id = grupo_oculto.pk
    tela.active = True
    tela.save(update_fields=["parent", "active", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0053_escalas_iniciais_classificacao"),
        ("core", "0050_configuracoes_classificacao"),
    ]
    operations = [migrations.RunPython(limpar_navegacao, migrations.RunPython.noop)]
