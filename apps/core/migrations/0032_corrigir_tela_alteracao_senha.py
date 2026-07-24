from django.db import migrations


def corrigir_tela_alteracao_senha(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenField = apps.get_model("core", "ScreenField")
    tela = ScreenDefinition.objects.filter(slug="ti-alteracao-senha-usuario").first()
    if not tela:
        return
    tela.title = "Alteração de senha"
    tela.parent_label = "Gerenciamento de usuários"
    tela.allow_query = True
    tela.allow_insert = False
    tela.allow_update = True
    tela.allow_delete = False
    tela.save(update_fields=["title", "parent_label", "allow_query", "allow_insert", "allow_update", "allow_delete"])
    ScreenField.objects.filter(screen=tela, field_name="username").update(
        label="Usuário",
        consultable=True,
        editable=True,
        primary_key=False,
        visible=True,
    )
    ScreenField.objects.filter(screen=tela, field_name="password").update(
        label="Nova senha",
        consultable=False,
        editable=True,
        primary_key=False,
        visible=True,
    )
    ScreenField.objects.filter(screen=tela, field_name="must_change_password").update(
        label="Alterar no próximo login",
        consultable=True,
        editable=True,
        primary_key=False,
        visible=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_desativar_modulos_nao_implementados"),
    ]

    operations = [
        migrations.RunPython(corrigir_tela_alteracao_senha, migrations.RunPython.noop),
    ]
