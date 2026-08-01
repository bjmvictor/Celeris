"""Operações históricas de dados da migration 0024."""

from django.db import migrations


def cadastrar_telas_agendamento(apps, schema_editor):
    AgendaProfissional = apps.get_model("atendimento", "AgendaProfissional")
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    for escala in AgendaProfissional.objects.filter(ds_dias_semana=[]).iterator():
        escala.ds_dias_semana = [escala.nr_dia_semana]
        escala.save(update_fields=["ds_dias_semana"])

    modulo, _ = Module.objects.get_or_create(
        code="ATENDIMENTO",
        defaults={"title": "Atendimento", "active": True},
    )
    telas = [
        ("Agendar", "acesso-atendimento-agendar", "atendimento:agendar", 10, ["TI", "Recepcionista"]),
        ("Agendamentos", "acesso-atendimento-agendamentos-operacionais", "atendimento:agendamentos-operacionais", 20, ["TI", "Recepcionista"]),
        ("Escalas", "acesso-atendimento-escalas", "atendimento:escalas", 30, ["TI"]),
        ("Geração de agendas", "acesso-atendimento-gerar-agenda", "atendimento:gerar-agenda", 40, ["TI", "Recepcionista"]),
    ]
    for titulo, slug, chave, ordem, papeis in telas:
        tela, _ = ScreenDefinition.objects.update_or_create(
            access_key=chave,
            defaults={
                "module": modulo,
                "title": titulo,
                "slug": slug,
                "screen_type": "configuracao",
                "parent_label": "Agendamento",
                "table_name": "agenda_profissional" if chave == "atendimento:escalas" else "agenda_gerada",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": chave in {"atendimento:escalas", "atendimento:gerar-agenda"},
                "active": True,
                "order": ordem,
            },
        )
        for nome_papel in papeis:
            grupo, _ = Group.objects.get_or_create(name=nome_papel)
            papel, _ = Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
            PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0023_agendagerada_horarioagenda_and_more"),
    ]

    operations = [
        migrations.RunPython(cadastrar_telas_agendamento, migrations.RunPython.noop),
    ]
