from django.db import migrations


def atualizar_navegacao_classificacao(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    PapelTela = apps.get_model("accounts", "PapelTela")

    atendimento = Module.objects.filter(code="ATENDIMENTO").first()
    if not atendimento:
        return

    classificacao = Screen.objects.filter(
        module=atendimento,
        slug="atendimento-classificacao",
    ).first()
    if not classificacao:
        return

    grupo_operacional_oculto, _ = Screen.objects.update_or_create(
        module=atendimento,
        slug="atendimento-classificacao-operacional-oculta",
        defaults={
            "parent": classificacao,
            "title": "Operação da classificação",
            "screen_type": "grupo",
            "active": False,
            "order": 999,
        },
    )
    Screen.objects.filter(access_key="atendimento:fila-classificacao").update(
        parent=grupo_operacional_oculto,
        active=True,
    )

    configuracao, _ = Screen.objects.update_or_create(
        module=atendimento,
        slug="atendimento-classificacao-configuracao",
        defaults={
            "parent": classificacao,
            "title": "Configuração",
            "screen_type": "grupo",
            "active": True,
            "order": 60,
        },
    )
    escala, _ = Screen.objects.update_or_create(
        access_key="atendimento:escalas-classificacao",
        defaults={
            "module": atendimento,
            "parent": configuracao,
            "title": "Escalas",
            "slug": "atendimento-classificacao-escalas",
            "screen_type": "formulario",
            "table_name": "escala_clinica",
            "allow_query": True,
            "allow_insert": True,
            "allow_update": True,
            "allow_delete": False,
            "active": True,
            "order": 30,
        },
    )

    papeis_ti = PapelTela.objects.filter(
        tela__module=atendimento,
        papel__grupo__name="TI",
    ).values_list("papel_id", flat=True).distinct()
    for papel_id in papeis_ti:
        PapelTela.objects.get_or_create(papel_id=papel_id, tela=escala)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_alter_user_groups_alter_user_is_active_and_more"),
        ("core", "0055_catalogos_operacionais_minimos"),
    ]

    operations = [
        migrations.RunPython(atualizar_navegacao_classificacao, migrations.RunPython.noop),
    ]
