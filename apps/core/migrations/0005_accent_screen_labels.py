from django.db import migrations


TITLE_REPLACEMENTS = {
    "Historico do Paciente": "Histórico do Paciente",
    "Relatorio de Pacientes": "Relatório de Pacientes",
    "Convenios": "Convênios",
    "Relatorio Financeiro": "Relatório Financeiro",
    "Inventario": "Inventário",
    "Relatorio Fiscal": "Relatório Fiscal",
    "Pesquisa de Satisfacao": "Pesquisa de Satisfação",
    "Cadastro / Copia de usuario": "Cadastro / Cópia de usuário",
    "Alteracao de senha": "Alteração de senha",
}

PARENT_REPLACEMENTS = {
    "Relatorios": "Relatórios",
    "Gerenciamento de Usuarios": "Gerenciamento de Usuários",
}

FIELD_REPLACEMENTS = {
    "Codigo": "Código",
    "Descricao": "Descrição",
    "Usuario": "Usuário",
}


def apply_replacements(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenField = apps.get_model("core", "ScreenField")

    for old_value, new_value in TITLE_REPLACEMENTS.items():
        ScreenDefinition.objects.filter(title=old_value).update(title=new_value)
    for old_value, new_value in PARENT_REPLACEMENTS.items():
        ScreenDefinition.objects.filter(parent_label=old_value).update(parent_label=new_value)
    for old_value, new_value in FIELD_REPLACEMENTS.items():
        ScreenField.objects.filter(label=old_value).update(label=new_value)


def revert_replacements(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenField = apps.get_model("core", "ScreenField")

    for old_value, new_value in TITLE_REPLACEMENTS.items():
        ScreenDefinition.objects.filter(title=new_value).update(title=old_value)
    for old_value, new_value in PARENT_REPLACEMENTS.items():
        ScreenDefinition.objects.filter(parent_label=new_value).update(parent_label=old_value)
    for old_value, new_value in FIELD_REPLACEMENTS.items():
        ScreenField.objects.filter(label=new_value).update(label=old_value)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_seed_clinic_erp_screens"),
    ]

    operations = [
        migrations.RunPython(apply_replacements, revert_replacements),
    ]
