from django.db import migrations, models
import django.db.models.deletion


CORES = (
    ("VERMELHO", "Vermelho", "#dc2626", 1),
    ("LARANJA", "Laranja", "#f97316", 2),
    ("AMARELO", "Amarelo", "#eab308", 3),
    ("VERDE", "Verde", "#22c55e", 4),
    ("AZUL", "Azul", "#3b82f6", 5),
)

PROTOCOLOS = (
    ("EMERG", "Emergência", "Atendimento imediato; encaminhar diretamente para a sala de estabilização."),
    ("URG", "Urgência", "Atendimento prioritário conforme avaliação clínica e sinais de risco."),
    ("PREF", "Atendimento preferencial", "Priorizar conforme legislação e condição clínica observada."),
    ("GERAL", "Atendimento geral", "Atendimento por ordem de prioridade e horário de chegada."),
)

ICONES = (
    ("Pessoa", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 21c.7-5 3.3-7 8-7s7.3 2 8 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'),
    ("Idoso", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="13" cy="4" r="2" fill="currentColor"/><path d="m12 7-2 6 3 2 1 6M10 13l-3 8M12 8l4 4h3M18 13v8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    ("Gestante", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="9" cy="4" r="2" fill="currentColor"/><path d="M9 7v14M5 11h8M13 9c4 1 5 4 5 7h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
    ("Criança", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 21v-4c0-3 2-5 5-5s5 2 5 5v4M9 5l-2-2M15 5l2-2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'),
    ("Acessibilidade", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="10" cy="4" r="2" fill="currentColor"/><path d="M9 8h5l2 5h3M11 8l-2 6h5l2 7M9 12a5 5 0 1 0 4 8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'),
)

PERGUNTAS = (
    (10, "Paciente admitido diretamente na sala de estabilização?", "SIM_NAO"),
    (20, "Paciente reclassificado após permanência superior a 24 horas na unidade?", "SIM_NAO"),
    (30, "Possui alergias conhecidas?", "SIM_NAO"),
    (40, "Utiliza medicamento contínuo?", "SIM_NAO"),
    (50, "Está com dor?", "SIM_NAO"),
    (60, "Possui hipertensão arterial?", "SIM_NAO"),
    (70, "Possui diabetes?", "SIM_NAO"),
)

FLUXOS = (
    ("Dor", "Dor abdominal", "Avaliar intensidade, início, localização, irradiação e sinais associados.", 10),
    ("Dor", "Dor torácica", "Avaliar sinais vitais, intensidade da dor e fatores de risco cardiovascular.", 20),
    ("Trauma", "Traumatismo cranioencefálico", "Avaliar Glasgow, mecanismo do trauma e sinais neurológicos.", 10),
    ("Clínica geral", "Cefaleia", "Avaliar início súbito, intensidade, déficit neurológico e sinais de alarme.", 10),
    ("Queixas respiratórias", "Falta de ar", "Avaliar saturação, frequência respiratória e esforço respiratório.", 10),
)


def preparar_catalogo(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Cor = apps.get_model("atendimento", "CorClassificacaoRisco")
    Protocolo = apps.get_model("atendimento", "ProtocoloSenhaAtendimento")
    Icone = apps.get_model("atendimento", "IconeChamada")
    Pergunta = apps.get_model("atendimento", "PerguntaClassificacao")
    Fluxo = apps.get_model("atendimento", "FluxoClassificacao")
    Tipo = apps.get_model("atendimento", "TipoSenhaAtendimento")
    Classe = apps.get_model("atendimento", "ClasseSenhaAtendimento")
    Regra = apps.get_model("atendimento", "RegraSubdivisaoSenha")

    for empresa in Empresa.objects.all():
        cores = {}
        for codigo, nome, hexadecimal, prioridade in CORES:
            cores[codigo], _ = Cor.objects.update_or_create(
                cd_empresa=empresa,
                cd_cor=codigo,
                defaults={"nm_cor": nome, "ds_cor_hex": hexadecimal, "nr_prioridade": prioridade, "sn_ativo": True},
            )
        protocolos = {}
        for sigla, nome, descricao in PROTOCOLOS:
            protocolos[sigla], _ = Protocolo.objects.update_or_create(
                cd_empresa=empresa,
                nm_protocolo=nome,
                defaults={"sg_protocolo": sigla, "ds_protocolo": descricao, "sn_ativo": True},
            )
        icones = {}
        for nome, svg in ICONES:
            icones[nome], _ = Icone.objects.update_or_create(
                cd_empresa=empresa,
                nm_icone=nome,
                defaults={"ds_svg": svg, "sn_ativo": True},
            )
        for ordem, nome, tipo_resposta in PERGUNTAS:
            Pergunta.objects.update_or_create(
                cd_empresa=empresa,
                nm_pergunta=nome,
                defaults={"tp_resposta": tipo_resposta, "nr_ordem": ordem, "sn_padrao": True, "sn_editavel": False, "sn_ativo": True},
            )
        for grupo, nome, orientacao, ordem in FLUXOS:
            Fluxo.objects.update_or_create(
                cd_empresa=empresa,
                nm_grupo=grupo,
                nm_fluxo=nome,
                defaults={"ds_orientacao": orientacao, "nr_ordem": ordem, "sn_ativo": True},
            )

        tipo_adulto, _ = Tipo.objects.update_or_create(
            cd_empresa=empresa,
            sg_tipo_senha="AD",
            defaults={"nm_tipo_senha": "Adulto", "nr_prioridade": 5, "nr_tempo_minimo": 30, "sn_ativo": True},
        )
        subdivisoes = (
            ("N", "Atendimento normal", 5, None, 74, "Pessoa", "GERAL", 60, "VERDE"),
            ("I", "Idoso a partir de 75 anos", 2, 75, None, "Idoso", "PREF", 30, "AMARELO"),
        )
        for sigla, nome, prioridade, idade_minima, idade_maxima, nome_icone, sigla_protocolo, tempo, codigo_cor in subdivisoes:
            classe, _ = Classe.objects.update_or_create(
                cd_tipo_senha=tipo_adulto,
                sg_classe_senha=sigla,
                defaults={
                    "cd_empresa": empresa,
                    "nm_classe_senha": nome,
                    "nr_prioridade": prioridade,
                    "nr_idade_minima": idade_minima,
                    "nr_idade_maxima": idade_maxima,
                    "cd_icone_chamada": icones[nome_icone],
                    "cd_cor_classificacao": cores[codigo_cor],
                    "sn_ativo": True,
                },
            )
            Regra.objects.update_or_create(
                cd_tipo_senha=tipo_adulto,
                cd_classe_senha=classe,
                defaults={
                    "cd_empresa": empresa,
                    "sg_regra": sigla,
                    "nr_prioridade": prioridade,
                    "nr_idade_minima": idade_minima,
                    "nr_idade_maxima": idade_maxima,
                    "cd_icone_chamada": icones[nome_icone],
                    "cd_protocolo": protocolos[sigla_protocolo],
                    "nr_tempo_limite": tempo,
                    "sn_ativo": True,
                },
            )


def migrar_configuracao_das_senhas(apps, schema_editor):
    Regra = apps.get_model("atendimento", "RegraSubdivisaoSenha")
    for regra in Regra.objects.select_related("cd_tipo_senha").all():
        tipo = regra.cd_tipo_senha
        regra.cd_protocolo_id = tipo.cd_protocolo_id
        regra.nr_tempo_limite = tipo.nr_tempo_minimo or 30
        regra.save(update_fields=["cd_protocolo", "nr_tempo_limite"])


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0053_escalas_iniciais_classificacao")]

    operations = [
        migrations.AddField(
            model_name="regrasubdivisaosenha",
            name="cd_protocolo",
            field=models.ForeignKey(blank=True, db_column="cd_protocolo", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="regras_subdivisao", to="atendimento.protocolosenhaatendimento"),
        ),
        migrations.AddField(
            model_name="regrasubdivisaosenha",
            name="nr_tempo_limite",
            field=models.PositiveSmallIntegerField(default=30),
        ),
        migrations.RunPython(migrar_configuracao_das_senhas, migrations.RunPython.noop),
        migrations.RunPython(preparar_catalogo, migrations.RunPython.noop),
    ]
