from django.db import migrations


PERGUNTAS_PADRAO = (
    (10, "Paciente admitido diretamente na sala de estabilização?", "SIM_NAO"),
    (20, "Paciente reclassificado após permanência superior a 24 horas na unidade?", "SIM_NAO"),
    (30, "Possui hipertensão arterial?", "SIM_NAO"),
    (40, "Possui diabetes?", "SIM_NAO"),
    (50, "É tabagista?", "SIM_NAO"),
    (60, "Possui doença renal crônica?", "SIM_NAO"),
    (70, "Possui histórico familiar de doença arterial coronariana precoce?", "SIM_NAO"),
)


FLUXOS_INICIAIS = (
    ("Dor", "Dor abdominal", "Avaliar intensidade, início, localização, irradiação e sinais associados.", 10),
    ("Dor", "Dor torácica", "Avaliar sinais vitais, intensidade da dor e fatores de risco cardiovascular.", 20),
    ("Trauma", "Traumatismo cranioencefálico", "Avaliar Glasgow, mecanismo do trauma e sinais neurológicos.", 10),
    ("Trauma", "Queda", "Avaliar altura, mecanismo, dor, limitação funcional e uso de anticoagulantes.", 20),
    ("Clínica geral", "Cefaleia", "Avaliar início súbito, intensidade, déficit neurológico e sinais de alarme.", 10),
    ("Clínica geral", "Diarreia", "Avaliar duração, frequência, sinais de desidratação e presença de sangue.", 20),
    ("Queixas respiratórias", "Falta de ar", "Avaliar saturação, frequência respiratória e esforço respiratório.", 10),
    ("Queixas respiratórias", "Obstrução nasal", "Avaliar duração, secreção, febre e dificuldade respiratória.", 20),
    ("Intoxicações", "Exposição a substância tóxica", "Identificar substância, via, quantidade e horário da exposição.", 10),
    ("Queimaduras", "Queimadura", "Avaliar agente, extensão, profundidade, localização e comprometimento de via aérea.", 10),
)


def criar_catalogo(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Pergunta = apps.get_model("atendimento", "PerguntaClassificacao")
    Fluxo = apps.get_model("atendimento", "FluxoClassificacao")
    for empresa in Empresa.objects.all():
        for ordem, nome, tipo in PERGUNTAS_PADRAO:
            Pergunta.objects.update_or_create(
                cd_empresa=empresa,
                nm_pergunta=nome,
                defaults={
                    "tp_resposta": tipo,
                    "nr_ordem": ordem,
                    "sn_padrao": True,
                    "sn_editavel": False,
                    "sn_ativo": True,
                },
            )
        for grupo, nome, orientacao, ordem in FLUXOS_INICIAIS:
            Fluxo.objects.update_or_create(
                cd_empresa=empresa,
                nm_grupo=grupo,
                nm_fluxo=nome,
                defaults={
                    "ds_orientacao": orientacao,
                    "nr_ordem": ordem,
                    "sn_ativo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0050_dados_complementares_classificacao")]
    operations = [migrations.RunPython(criar_catalogo, migrations.RunPython.noop)]
