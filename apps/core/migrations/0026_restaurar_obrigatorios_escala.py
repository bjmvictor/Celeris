from django.db import migrations


OBRIGATORIOS_ESCALA = {
    "ds_agenda",
    "tp_escala",
    "cd_prestador",
    "ds_especialidade",
    "cd_setor_atendimento",
    "tp_horario",
    "ds_dias_semana",
    "hr_inicio",
    "hr_fim",
    "nr_tempo_atendimento",
    "qt_horarios_dia",
    "ds_tipo_agendamento",
}


def restaurar_obrigatorios_escala(apps, schema_editor):
    Configuracao = apps.get_model("core", "ConfiguracaoCampoFormulario")
    empresas = Configuracao.objects.filter(cd_formulario="cadastro_escala").values_list("cd_empresa_id", flat=True).distinct()
    for empresa_id in empresas:
        configuracoes = Configuracao.objects.filter(
            cd_empresa_id=empresa_id,
            cd_formulario="cadastro_escala",
        )
        if configuracoes.filter(sn_obrigatorio=True).exists():
            continue
        configuracoes.filter(cd_campo__in=OBRIGATORIOS_ESCALA).update(sn_obrigatorio=True)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0037_totem_senhas"),
        ("core", "0025_configuracao_campo_formulario"),
    ]

    operations = [
        migrations.RunPython(restaurar_obrigatorios_escala, migrations.RunPython.noop),
    ]
