from datetime import date, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Empresa, Papel, Setor, SetorUsuario, User, UsuarioEmpresa
from apps.atendimento.models import (
    Atendimento,
    AtendimentoFluxo,
    AgendaProfissional,
    ClasseSenhaAtendimento,
    Convenio,
    CorClassificacaoRisco,
    EscalaClinica,
    FluxoClassificacao,
    GrupoFluxoClassificacao,
    ItemMenuAssistencial,
    MaquinaChamada,
    ModeloDocumento,
    Paciente,
    PreAtendimento,
    PerguntaClassificacao,
    PerfilAssistencial,
    PerfilAssistencialTipo,
    PerfilAssistencialVersao,
    PainelChamada,
    Prescricao,
    Prestador,
    PrestadorTipo,
    SenhaAtendimento,
    TipoSenhaAtendimento,
)
from apps.pesquisas.models import (
    FaixaResultadoPesquisa,
    OpcaoRespostaPesquisa,
    PerguntaPesquisa,
    Pesquisa,
)


DEMO_COMPANY_CODE = 9000
DEMO_COMPANY_NAME = "Hospital Horizonte Demo"
DEFAULT_PASSWORD = "123456"


class Command(BaseCommand):
    help = "Popula uma empresa fictícia com dados realistas para teste e homologação."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa-codigo",
            type=int,
            default=DEMO_COMPANY_CODE,
            help=f"Código da empresa fictícia (padrão: {DEMO_COMPANY_CODE}).",
        )
        parser.add_argument(
            "--senha-padrao",
            default=DEFAULT_PASSWORD,
            help="Senha inicial dos usuários demo criados.",
        )
        parser.add_argument(
            "--permitir-fora-debug",
            action="store_true",
            help="Confirma conscientemente a execução quando DEBUG=False.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["permitir_fora_debug"]:
            raise CommandError(
                "O comando cria dados fictícios e está bloqueado com DEBUG=False. "
                "Em um ambiente de homologação, execute novamente com --permitir-fora-debug."
            )
        company_code = options["empresa_codigo"]
        if company_code <= 0:
            raise CommandError("--empresa-codigo deve ser um número inteiro positivo.")
        password = options["senha_padrao"]
        if len(password) < 8:
            raise CommandError("--senha-padrao deve possuir ao menos 8 caracteres.")

        self._assert_company_slot_is_safe(company_code)
        with transaction.atomic():
            company = self._create_company(company_code)
            sectors = self._create_sectors(company)
            plans = self._create_health_plans(company)
            providers = self._create_providers(company)
            roles = self._create_roles()
            users = self._create_users(company, sectors, providers, roles, password)
            patients = self._create_patients(company, plans, users["ADMINDEMO"])
            self._create_panel_and_schedules(company, sectors, plans, providers, users)
            self._create_classification_content(company, users)
            self._create_pep_content(company, providers, users)
            self._create_survey(company)
            queue_count, visits_count = self._create_care_scenario(
                company, sectors, plans, providers, patients, users
            )
            self._create_sample_prescription(company, providers, users)

        self.stdout.write(self.style.SUCCESS("Dados fictícios de homologação populados com sucesso."))
        self.stdout.write(f"Empresa: {company.cd_empresa} - {company.nm_empresa}")
        self.stdout.write(
            f"Registros: {len(sectors)} setores, {len(plans)} convênios, "
            f"{len(providers)} prestadores, {len(roles)} papéis, {len(users)} usuários, "
            f"{len(patients)} pacientes, {queue_count} senhas e {visits_count} atendimentos."
        )
        self.stdout.write("Acessos demo (todos usam a senha informada em --senha-padrao):")
        self.stdout.write("  ADMINDEMO, RECEPCAODEMO, ENFERMAGEMDEMO, MEDICODEMO, AUDITORDEMO")
        self.stdout.write(self.style.WARNING("Todos os nomes e contatos gerados são fictícios."))

    @staticmethod
    def _assert_company_slot_is_safe(company_code):
        company = Empresa.objects.filter(pk=company_code).first()
        if company and company.nm_empresa != DEMO_COMPANY_NAME:
            raise CommandError(
                f"A empresa {company_code} já existe com o nome {company.nm_empresa!r}. "
                "Escolha outro código com --empresa-codigo; nenhum dado foi alterado."
            )

    @staticmethod
    def _create_company(company_code):
        company, _ = Empresa.objects.update_or_create(
            cd_empresa=company_code,
            defaults={
                "nm_empresa": DEMO_COMPANY_NAME,
                "nr_cnpj": "00.000.000/0001-00",
                "nr_cnes": "0000000",
                "ds_razao_social": "Horizonte Serviços de Saúde Fictícios Ltda.",
                "ds_nome_fantasia": "Hospital Horizonte Demo",
                "ds_email": "contato@hospital-horizonte.example.com",
                "nr_telefone": "(11) 4000-9000",
                "ds_endereco": "Avenida dos Testes",
                "nr_endereco": "900",
                "ds_bairro": "Jardim Demonstração",
                "ds_cidade": "São Paulo",
                "sg_estado": "SP",
                "nr_cep": "00000-000",
                "sn_ativo": True,
            },
        )
        return company

    @staticmethod
    def _create_sectors(company):
        definitions = (
            ("Recepção Central", Setor.TipoSetor.ATENDIMENTO, "Entrada e cadastro de pacientes"),
            ("Classificação de Risco", Setor.TipoSetor.ATENDIMENTO, "Triagem assistencial"),
            ("Consultórios", Setor.TipoSetor.ATENDIMENTO, "Atendimento ambulatorial"),
            ("Observação", Setor.TipoSetor.ATENDIMENTO, "Observação clínica"),
            ("Administração", Setor.TipoSetor.EMPRESA, "Gestão administrativa"),
            ("Tecnologia da Informação", Setor.TipoSetor.EMPRESA, "Suporte e sistemas"),
        )
        result = {}
        for name, sector_type, description in definitions:
            sector, _ = Setor.objects.update_or_create(
                cd_empresa=company,
                nm_setor=name,
                tp_setor=sector_type,
                defaults={"ds_observacao": description, "sn_ativo": True},
            )
            result[name] = sector
        return result

    @staticmethod
    def _create_health_plans(company):
        result = {}
        for name in ("Particular", "Saúde Plena Demo", "Bem-Estar Empresarial"):
            plan, _ = Convenio.objects.update_or_create(
                cd_empresa=company,
                nm_convenio=name,
                defaults={"sn_ativo": True},
            )
            result[name] = plan
        return result

    @staticmethod
    def _create_providers(company):
        definitions = (
            ("Dra. Helena Martins Demo", "Helena Martins", "MEDICO", "CRM", "990001", "CLINICA_MEDICA", True, False),
            ("Dr. Rafael Nogueira Demo", "Rafael Nogueira", "MEDICO", "CRM", "990002", "PEDIATRIA", True, False),
            ("Dra. Camila Freitas Demo", "Camila Freitas", "MEDICO", "CRM", "990003", "ORTOPEDIA", True, False),
            ("Enf. Beatriz Lima Demo", "Beatriz Lima", "ENFERMEIRO", "COREN", "990004", "ENFERMAGEM", False, True),
            ("Enf. Gustavo Ribeiro Demo", "Gustavo Ribeiro", "ENFERMEIRO", "COREN", "990005", "ENFERMAGEM", False, True),
            ("Téc. Larissa Almeida Demo", "Larissa Almeida", "TECNICO_ENFERMAGEM", "COREN", "990006", "ENFERMAGEM", False, False),
            ("Psic. Marina Costa Demo", "Marina Costa", "PSICOLOGO", "CRP", "990007", "PSICOLOGIA", True, False),
            ("Fisio. André Rocha Demo", "André Rocha", "FISIOTERAPEUTA", "CREFITO", "990008", "FISIOTERAPIA", True, False),
        )
        result = {}
        for index, (name, short_name, provider_type, council, number, specialty, attends, classifies) in enumerate(definitions, 1):
            provider, _ = Prestador.objects.update_or_create(
                cd_empresa=company,
                nr_conselho=number,
                defaults={
                    "nm_prestador": name,
                    "nm_guerra": short_name,
                    "dt_nascimento": date(1975 + index, (index % 12) + 1, min(index + 5, 28)),
                    "tp_prestador": provider_type,
                    "ds_conselho": council,
                    "sg_conselho": "SP",
                    "ds_especialidade": specialty,
                    "ds_especialidades": [specialty],
                    "sn_permite_agenda": attends,
                    "sn_permite_atendimento": attends,
                    "sn_permite_prescricao": provider_type == "MEDICO",
                    "sn_permite_classificacao": classifies,
                    "nr_celular": f"(11) 99000-{index:04d}",
                    "ds_email": f"prestador{index}@hospital-horizonte.example.com",
                    "ds_cidade": "São Paulo",
                    "sg_estado": "SP",
                    "ds_endereco": "Rua dos Profissionais",
                    "nr_endereco": str(100 + index),
                    "ds_bairro": "Centro Demo",
                    "sn_ativo": True,
                },
            )
            PrestadorTipo.objects.update_or_create(
                cd_empresa=company,
                cd_prestador=provider,
                cd_tipo_prestador=provider_type,
                defaults={"sn_principal": True, "sn_ativo": True},
            )
            result[provider_type if provider_type not in result else f"{provider_type}_{index}"] = provider
        return result

    @staticmethod
    def _create_roles():
        descriptions = {
            "TI": "Administração técnica do sistema",
            "Recepcionista": "Cadastro, agenda e recepção de pacientes",
            "Enfermeiro": "Classificação de risco e registros assistenciais",
            "Médico": "Consulta e prontuário clínico",
            "Auditor": "Consulta gerencial e auditoria",
        }
        result = {}
        for name, description in descriptions.items():
            group, _ = Group.objects.get_or_create(name=name)
            Papel.objects.update_or_create(
                grupo=group,
                defaults={"ds_descricao": description, "sn_ativo": True},
            )
            result[name] = group
        return result

    @staticmethod
    def _create_users(company, sectors, providers, roles, password):
        definitions = (
            ("ADMINDEMO", "Alex Oliveira Demo", "admin@hospital-horizonte.example.com", "ADMINISTRADOR", None, "TI", "Tecnologia da Informação", True),
            ("RECEPCAODEMO", "Juliana Mendes Demo", "recepcao@hospital-horizonte.example.com", "USUARIO", None, "Recepcionista", "Recepção Central", False),
            ("ENFERMAGEMDEMO", "Beatriz Lima Demo", "enfermagem@hospital-horizonte.example.com", "USUARIO", "ENFERMEIRO", "Enfermeiro", "Classificação de Risco", True),
            ("MEDICODEMO", "Helena Martins Demo", "medico@hospital-horizonte.example.com", "USUARIO", "MEDICO", "Médico", "Consultórios", False),
            ("AUDITORDEMO", "Paulo Cardoso Demo", "auditoria@hospital-horizonte.example.com", "AUDITOR", None, "Auditor", "Administração", False),
        )
        result = {}
        for username, full_name, email, user_type, provider_key, role_name, sector_name, coordinator in definitions:
            user, created = User.objects.get_or_create(username=username)
            user.full_name = full_name
            user.email = email
            user.tp_usuario = user_type
            user.cd_prestador = providers.get(provider_key) if provider_key else None
            user.is_active = True
            user.is_staff = user_type == "ADMINISTRADOR"
            user.is_coordinator = coordinator
            user.can_register_patient = role_name in {"TI", "Recepcionista"}
            user.can_change_patient = role_name in {"TI", "Recepcionista"}
            user.can_create_users = role_name == "TI"
            user.can_deactivate_users = role_name == "TI"
            user.can_manage_auxiliary_tables = role_name == "TI"
            user.can_configure_system = role_name == "TI"
            if created or not user.has_usable_password():
                user.set_password(password)
            user.save()
            user.groups.set([roles[role_name]])
            UsuarioEmpresa.objects.update_or_create(
                usuario=user,
                empresa=company,
                defaults={"sn_padrao": True, "sn_ativo": True},
            )
            SetorUsuario.objects.get_or_create(cd_setor=sectors[sector_name], cd_usuario=user)
            result[username] = user
        return result

    @staticmethod
    def _create_patients(company, plans, creator):
        first_names = ("Ana", "Bruno", "Carolina", "Daniel", "Elisa", "Felipe", "Gabriela", "Henrique", "Isabela", "João", "Karen", "Lucas", "Mariana", "Nicolas", "Olívia", "Pedro", "Renata", "Samuel", "Talita", "Vinícius", "Yasmin", "Caio", "Débora", "Eduardo")
        last_names = ("Silva Demo", "Santos Demo", "Oliveira Demo", "Souza Demo", "Pereira Demo", "Costa Demo")
        plan_list = list(plans.values())
        result = []
        for index, first_name in enumerate(first_names, 1):
            name = f"{first_name} {last_names[(index - 1) % len(last_names)]}"
            plan = plan_list[index % len(plan_list)]
            patient, _ = Paciente.objects.update_or_create(
                cd_empresa=company,
                ds_email=f"paciente{index:02d}@example.com",
                defaults={
                    "nm_paciente": name,
                    "dt_nascimento": date(1952 + (index * 2), (index % 12) + 1, min(index, 28)),
                    "tp_sexo": "FEMININO" if index % 2 else "MASCULINO",
                    "ds_cor_raca": ("BRANCA", "PARDA", "PRETA")[index % 3],
                    "tp_estado_civil": ("SOLTEIRO", "CASADO", "DIVORCIADO")[index % 3],
                    "cd_convenio": plan,
                    "nm_convenio": plan.nm_convenio,
                    "nr_convenio": f"DEMO-{index:06d}",
                    "nr_celular": f"(11) 98000-{index:04d}",
                    "nm_mae": f"Responsável {first_name} Demo",
                    "ds_nacionalidade": "Brasileira",
                    "ds_naturalidade": "São Paulo",
                    "ds_endereco": "Rua dos Pacientes",
                    "nr_endereco": str(200 + index),
                    "ds_bairro": ("Centro Demo", "Vila Exemplo", "Jardim Teste")[index % 3],
                    "ds_cidade": "São Paulo",
                    "sg_estado": "SP",
                    "nr_cep": "00000-000",
                    "ds_observacao": "Cadastro exclusivamente fictício para homologação.",
                    "sn_ativo": True,
                    "cd_usuario_criacao": creator,
                    "cd_usuario_atualizacao": creator,
                },
            )
            result.append(patient)
        return result

    @staticmethod
    def _create_panel_and_schedules(company, sectors, plans, providers, users):
        machine, _ = MaquinaChamada.objects.update_or_create(
            cd_empresa=company,
            nm_maquina="PAINEL-DEMO-01",
            defaults={
                "tp_maquina": "PAINEL",
                "nm_sala": "Recepção e consultórios",
                "tp_sala": "SALA",
                "sn_ativo": True,
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )
        panel, _ = PainelChamada.objects.update_or_create(
            cd_empresa=company,
            nm_maquina=machine.nm_maquina,
            defaults={
                "nm_painel": "Painel Assistencial Demo",
                "ds_descricao": "Painel fictício para chamadas da classificação e do PEP.",
                "tp_painel": "PAINEL",
                "ds_local_exibicao": "Recepção principal",
                "ds_mensagem_padrao": "Aguarde sua chamada",
                "ds_configuracao": {"chamar_paciente": True, "mostrar_nome": True, "mostrar_senha": True},
                "sn_ativo": True,
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )
        panel.setores.set(
            [sectors["Classificação de Risco"], sectors["Consultórios"], sectors["Observação"]]
        )

        start = timezone.localdate() - timedelta(days=30)
        end = timezone.localdate() + timedelta(days=120)
        for index, provider in enumerate(
            (providers["MEDICO"], providers["MEDICO_2"], providers["MEDICO_3"]),
            1,
        ):
            schedule, _ = AgendaProfissional.objects.update_or_create(
                cd_empresa=company,
                cd_prestador=provider,
                ds_agenda=f"Agenda Demo {provider.nm_guerra}",
                defaults={
                    "cd_setor_atendimento": sectors["Consultórios"],
                    "tp_escala": "AMBULATORIAL",
                    "tp_horario": "HORA_MARCADA",
                    "ds_tipo_agendamento": "CONSULTA",
                    "ds_especialidade": provider.ds_especialidade,
                    "dt_inicio": start,
                    "dt_fim": end,
                    "nr_dia_semana": index - 1,
                    "ds_dias_semana": [index - 1, index + 1],
                    "hr_inicio": time(8, 0),
                    "hr_fim": time(17, 0),
                    "nr_tempo_atendimento": 30,
                    "qt_horarios_dia": 16,
                    "qt_encaixes": 2,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )
            schedule.convenios.set(plans.values())

    @staticmethod
    def _create_classification_content(company, users):
        colors = {}
        for code, name, hexadecimal, priority in (
            ("VERMELHO", "Emergência", "#dc2626", 1),
            ("LARANJA", "Muito urgente", "#f97316", 2),
            ("AMARELO", "Urgente", "#eab308", 3),
            ("VERDE", "Pouco urgente", "#22c55e", 4),
            ("AZUL", "Não urgente", "#2563eb", 5),
        ):
            colors[code], _ = CorClassificacaoRisco.objects.update_or_create(
                cd_empresa=company,
                cd_cor=code,
                defaults={
                    "nm_cor": name,
                    "ds_cor_hex": hexadecimal,
                    "nr_prioridade": priority,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )

        flow_groups = (
            (
                "Cardiorrespiratório",
                "Sintomas relacionados aos sistemas cardíaco e respiratório.",
                (
                    ("Dor torácica", "LARANJA", "Avaliar início, irradiação, intensidade e sinais associados."),
                    ("Falta de ar", "LARANJA", "Verificar saturação, frequência respiratória e esforço ventilatório."),
                    ("Palpitações", "AMARELO", "Investigar duração, recorrência, dor e sinais de instabilidade."),
                ),
            ),
            (
                "Neurológico",
                "Alterações neurológicas e do nível de consciência.",
                (
                    ("Rebaixamento do nível de consciência", "VERMELHO", "Avaliação imediata de consciência, glicemia e sinais vitais."),
                    ("Convulsão", "LARANJA", "Identificar duração, recorrência e recuperação pós-crise."),
                    ("Cefaleia", "AMARELO", "Pesquisar início súbito, déficit focal, febre e intensidade."),
                ),
            ),
            (
                "Gastrointestinal",
                "Queixas digestivas e abdominais.",
                (
                    ("Dor abdominal", "AMARELO", "Avaliar localização, intensidade, defesa e sintomas associados."),
                    ("Náuseas e vômitos", "VERDE", "Avaliar frequência, hidratação e presença de sangue."),
                    ("Diarreia", "VERDE", "Investigar duração, frequência e sinais de desidratação."),
                ),
            ),
            (
                "Condições gerais",
                "Sintomas gerais e situações de menor complexidade aparente.",
                (
                    ("Febre", "VERDE", "Aferir temperatura e pesquisar sinais de gravidade."),
                    ("Dor leve", "AZUL", "Caracterizar local, duração e fatores de melhora ou piora."),
                    ("Mal-estar geral", "VERDE", "Avaliar sinais vitais e sintomas associados."),
                ),
            ),
        )
        for group_order, (group_name, description, flows) in enumerate(flow_groups, 1):
            group, _ = GrupoFluxoClassificacao.objects.update_or_create(
                cd_empresa=company,
                nm_grupo=group_name,
                defaults={
                    "ds_descricao": description,
                    "nr_ordem": group_order * 10,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )
            for flow_order, (flow_name, color_code, guidance) in enumerate(flows, 1):
                FluxoClassificacao.objects.update_or_create(
                    cd_empresa=company,
                    cd_grupo=group,
                    nm_fluxo=flow_name,
                    defaults={
                        "nm_grupo": group.nm_grupo,
                        "ds_orientacao": guidance,
                        "cd_cor_recomendada": colors[color_code],
                        "ds_configuracao": {"origem": "POPULATE_DEMO"},
                        "nr_ordem": flow_order * 10,
                        "sn_ativo": True,
                        "cd_usuario_criacao": users["ADMINDEMO"],
                        "cd_usuario_atualizacao": users["ADMINDEMO"],
                    },
                )

        for order, (question, response_type, required) in enumerate(
            (
                ("Possui alergia conhecida?", "SIM_NAO", True),
                ("Fez uso de medicamento nas últimas 24 horas?", "SIM_NAO", False),
                ("Há quanto tempo os sintomas começaram?", "TEXTO", True),
                ("Qual a intensidade da dor de 0 a 10?", "NUMERO", False),
            ),
            1,
        ):
            PerguntaClassificacao.objects.update_or_create(
                cd_empresa=company,
                nm_pergunta=question,
                defaults={
                    "tp_resposta": response_type,
                    "nr_ordem": order * 10,
                    "sn_padrao": True,
                    "sn_editavel": True,
                    "sn_obrigatoria": required,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )
        EscalaClinica.objects.update_or_create(
            cd_empresa=company,
            nm_escala="Régua de dor Demo",
            nr_versao=1,
            defaults={
                "ds_descricao": "Escala numérica fictícia para homologação da classificação.",
                "tp_calculo": "SOMA",
                "ds_perguntas": [
                    {
                        "chave": "dor",
                        "texto": "Intensidade da dor",
                        "opcoes": [
                            {"valor": str(value), "descricao": str(value), "pontos": value}
                            for value in range(11)
                        ],
                    }
                ],
                "ds_faixas_resultado": [
                    {"minimo": 0, "maximo": 3, "descricao": "Leve", "cor": "#22c55e"},
                    {"minimo": 4, "maximo": 6, "descricao": "Moderada", "cor": "#eab308"},
                    {"minimo": 7, "maximo": 10, "descricao": "Intensa", "cor": "#dc2626"},
                ],
                "sn_ativo": True,
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )

    @staticmethod
    def _create_pep_content(company, providers, users):
        provider_types = sorted(
            {
                provider.tp_prestador
                for provider in providers.values()
                if provider.tp_prestador
            }
        )
        profile, _ = PerfilAssistencial.objects.update_or_create(
            cd_empresa=company,
            nm_perfil="Perfil Assistencial Multiprofissional Demo",
            defaults={
                "ds_descricao": "Menu simples para homologação do prontuário eletrônico.",
                "tipos_prestador": provider_types,
                "sn_ativo": True,
                "sn_sigiloso": False,
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )
        for provider_type in provider_types:
            PerfilAssistencialTipo.objects.update_or_create(
                cd_empresa=company,
                cd_tipo_prestador=provider_type,
                defaults={
                    "cd_perfil_assistencial": profile,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )
        version, _ = PerfilAssistencialVersao.objects.update_or_create(
            cd_perfil_assistencial=profile,
            nr_versao=1,
            defaults={
                "cd_empresa": company,
                "ds_status": "PUBLICADO",
                "ds_descricao_versao": "Versão de homologação criada pelo populate.",
                "dh_publicacao": timezone.now(),
                "cd_usuario_publicacao": users["ADMINDEMO"],
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )
        templates = {}
        for name, document_type, body in (
            ("Evolução clínica Demo", "EVOLUCAO", "<h2>Evolução clínica</h2><p>Paciente: {{ paciente.nome }}</p><p>Registro: {{ documento.conteudo }}</p>"),
            ("Resumo de alta Demo", "RESUMO_ALTA", "<h2>Resumo de alta</h2><p>Paciente: {{ paciente.nome }}</p><p>Conduta e orientações: {{ documento.conteudo }}</p>"),
        ):
            templates[document_type], _ = ModeloDocumento.objects.update_or_create(
                cd_empresa=company,
                tp_documento=document_type,
                nm_modelo=name,
                nr_versao=1,
                defaults={
                    "tp_elemento": "DOCUMENTO",
                    "ds_html_tela": body,
                    "ds_html_impressao": body,
                    "sn_versao_atual": True,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )
        root, _ = ItemMenuAssistencial.objects.update_or_create(
            cd_perfil_assistencial=profile,
            cd_item_tecnico="DEMO_CUIDADO",
            defaults={
                "cd_empresa": company,
                "cd_versao_perfil": version,
                "nm_item": "Cuidado assistencial",
                "ds_icone": "clipboard-plus",
                "nr_ordem": 10,
                "tp_item": "GRUPO",
                "sn_ativo": True,
                "cd_usuario_criacao": users["ADMINDEMO"],
                "cd_usuario_atualizacao": users["ADMINDEMO"],
            },
        )
        items = (
            ("DEMO_SINAIS", "Sinais vitais", "ACAO", "SINAIS_VITAIS", None),
            ("DEMO_EVOLUIR", "Evoluir", "ACAO", "EVOLUIR", None),
            ("DEMO_PRESCREVER", "Prescrição", "ACAO", "PRESCREVER", None),
            ("DEMO_EXAMES", "Solicitar exames", "ACAO", "EXAMES", None),
            ("DEMO_ALTA", "Alta médica", "ACAO", "ALTA_MEDICA", None),
            ("DEMO_DOC_EVOLUCAO", "Documento de evolução", "DOCUMENTO", "", templates["EVOLUCAO"]),
            ("DEMO_DOC_ALTA", "Resumo de alta", "DOCUMENTO", "", templates["RESUMO_ALTA"]),
        )
        for order, (key, name, item_type, action, document) in enumerate(items, 1):
            ItemMenuAssistencial.objects.update_or_create(
                cd_perfil_assistencial=profile,
                cd_item_tecnico=key,
                defaults={
                    "cd_empresa": company,
                    "cd_item_pai": root,
                    "cd_modelo_documento": document,
                    "cd_versao_perfil": version,
                    "nm_item": name,
                    "nr_ordem": order * 10,
                    "tp_item": item_type,
                    "ds_acao": action,
                    "sn_ativo": True,
                    "cd_usuario_criacao": users["ADMINDEMO"],
                    "cd_usuario_atualizacao": users["ADMINDEMO"],
                },
            )

    @staticmethod
    def _create_survey(company):
        survey, _ = Pesquisa.objects.update_or_create(
            cd_empresa=company,
            nm_pesquisa="Experiência do paciente Demo",
            defaults={
                "ds_descricao": "Pesquisa fictícia sobre a experiência durante o atendimento.",
                "tp_pesquisa": "SATISFACAO",
                "tp_calculo": "MEDIA",
                "sn_anonima": True,
                "sn_publica": True,
                "sn_ativo": True,
                "dh_inicio": timezone.now() - timedelta(days=30),
                "dh_fim": timezone.now() + timedelta(days=180),
            },
        )
        question, _ = PerguntaPesquisa.objects.update_or_create(
            cd_pesquisa=survey,
            ds_pergunta="Como você avalia o atendimento recebido?",
            defaults={
                "tp_resposta": "UNICA",
                "nr_peso": Decimal("1"),
                "nr_ordem": 10,
                "sn_obrigatoria": True,
                "sn_ativo": True,
            },
        )
        for order, (answer, value) in enumerate(
            (("Muito ruim", 1), ("Ruim", 2), ("Regular", 3), ("Bom", 4), ("Excelente", 5)),
            1,
        ):
            OpcaoRespostaPesquisa.objects.update_or_create(
                cd_pergunta_pesquisa=question,
                ds_resposta=answer,
                defaults={"nr_valor": Decimal(value), "nr_ordem": order, "sn_ativo": True},
            )
        PerguntaPesquisa.objects.update_or_create(
            cd_pesquisa=survey,
            ds_pergunta="O que poderíamos melhorar?",
            defaults={"tp_resposta": "TEXTO", "nr_ordem": 20, "sn_obrigatoria": False, "sn_ativo": True},
        )
        FaixaResultadoPesquisa.objects.update_or_create(
            cd_pesquisa=survey,
            nm_resultado="Experiência positiva",
            defaults={
                "nr_minimo": Decimal("4"),
                "nr_maximo": Decimal("5"),
                "ds_mensagem": "Obrigado por avaliar nosso atendimento demo.",
                "ds_cor": "#22c55e",
                "nr_ordem": 10,
                "sn_ativo": True,
            },
        )

    @staticmethod
    def _create_sample_prescription(company, providers, users):
        visit = Atendimento.objects.filter(cd_empresa=company, ds_status="EM_ATENDIMENTO").first()
        if not visit:
            return
        Prescricao.objects.update_or_create(
            cd_empresa=company,
            cd_atendimento=visit,
            ds_prescricao="Paracetamol 500 mg — uso exclusivamente fictício para homologação.",
            defaults={
                "ds_orientacoes": "Não representa orientação médica real.",
                "sn_ativa": True,
                "cd_usuario_criacao": users["MEDICODEMO"],
                "cd_usuario_atualizacao": users["MEDICODEMO"],
            },
        )

    def _create_care_scenario(self, company, sectors, plans, providers, patients, users):
        now = timezone.now()
        today = timezone.localdate()
        triage_provider = providers["ENFERMEIRO"]
        doctor = providers["MEDICO"]
        particular = plans["Particular"]

        colors = {}
        for code, name, color, priority in (
            ("VERMELHO", "Emergência", "#dc2626", 1),
            ("LARANJA", "Muito urgente", "#f97316", 2),
            ("AMARELO", "Urgente", "#eab308", 3),
            ("VERDE", "Pouco urgente", "#22c55e", 4),
            ("AZUL", "Não urgente", "#2563eb", 5),
        ):
            colors[code], _ = CorClassificacaoRisco.objects.update_or_create(
                cd_empresa=company,
                cd_cor=code,
                defaults={"nm_cor": name, "ds_cor_hex": color, "nr_prioridade": priority, "sn_ativo": True},
            )
        ticket_type, _ = TipoSenhaAtendimento.objects.update_or_create(
            cd_empresa=company,
            sg_tipo_senha="CE",
            defaults={
                "cd_setor_atendimento": sectors["Classificação de Risco"],
                "nm_tipo_senha": "Consulta espontânea",
                "ds_protocolo": "Classificação clínica demo",
                "nr_tempo_minimo": 30,
                "nr_prioridade": 3,
                "sn_ativo": True,
            },
        )
        ticket_class, _ = ClasseSenhaAtendimento.objects.update_or_create(
            cd_tipo_senha=ticket_type,
            sg_classe_senha="G",
            defaults={
                "cd_empresa": company,
                "nm_classe_senha": "Geral",
                "nr_prioridade": 3,
                "cd_cor_classificacao": colors["AMARELO"],
                "sn_ativo": True,
            },
        )

        queue_definitions = (
            (patients[0], "CE001", "AGUARDANDO", "VERDE", 4, 42),
            (patients[1], "CE002", "AGUARDANDO", "AMARELO", 3, 26),
            (patients[2], "CE003", "CHAMADA", "LARANJA", 2, 18),
            (patients[3], "CE004", "EM_CLASSIFICACAO", "AMARELO", 3, 12),
            (patients[4], "CE005", "CLASSIFICADA", "VERDE", 4, 55),
            (patients[5], "CE006", "RECEPCIONADA", "AZUL", 5, 75),
        )
        for number, (patient, label, status, color_code, priority, minutes_ago) in enumerate(queue_definitions, 1):
            created_at = now - timedelta(minutes=minutes_ago)
            ticket, _ = SenhaAtendimento.objects.update_or_create(
                cd_empresa=company,
                dt_senha=today,
                ds_senha=label,
                defaults={
                    "cd_tipo_senha": ticket_type,
                    "cd_classe_senha": ticket_class,
                    "cd_paciente": patient,
                    "nm_pre_cadastro": patient.nm_paciente,
                    "dt_nascimento_pre_cadastro": patient.dt_nascimento,
                    "tp_sexo_pre_cadastro": patient.tp_sexo,
                    "cd_cor_classificacao": colors[color_code] if status in {"CLASSIFICADA", "RECEPCIONADA"} else None,
                    "nr_senha": number,
                    "nr_prioridade": priority,
                    "nr_tempo_limite": 30,
                    "ds_status": status,
                    "dh_chamada": created_at + timedelta(minutes=5) if status in {"CHAMADA", "EM_CLASSIFICACAO", "CLASSIFICADA", "RECEPCIONADA"} else None,
                    "dh_classificacao": created_at + timedelta(minutes=14) if status in {"CLASSIFICADA", "RECEPCIONADA"} else None,
                    "dh_recepcao": created_at + timedelta(minutes=20) if status == "RECEPCIONADA" else None,
                    "dh_criacao": created_at,
                    "cd_usuario_criacao": users["RECEPCAODEMO"],
                    "cd_usuario_atualizacao": users["ENFERMAGEMDEMO"],
                },
            )
            if status in {"EM_CLASSIFICACAO", "CLASSIFICADA", "RECEPCIONADA"}:
                finished = status in {"CLASSIFICADA", "RECEPCIONADA"}
                pre, _ = PreAtendimento.objects.update_or_create(
                    cd_pre_atendimento=ticket.cd_pre_atendimento_id,
                    defaults={
                        "cd_empresa": company,
                        "cd_paciente": patient,
                        "dh_inicio": created_at + timedelta(minutes=6),
                        "nr_prioridade": priority,
                        "ds_queixa_principal": ("Dor abdominal", "Cefaleia", "Mal-estar geral")[number % 3],
                        "ds_sintomas": "Sintomas fictícios usados para validar a classificação.",
                        "ds_cor_prioridade": color_code,
                        "cd_prestador_responsavel": triage_provider,
                        "nr_pressao_arterial": "120/80",
                        "nr_frequencia_cardiaca": 72 + number,
                        "nr_frequencia_respiratoria": 18,
                        "nr_saturacao": 98,
                        "nr_temperatura": Decimal("36.7"),
                        "nr_peso": Decimal("70.00"),
                        "nr_altura": Decimal("1.70"),
                        "dh_fim": created_at + timedelta(minutes=14) if finished else None,
                        "cd_usuario_criacao": users["ENFERMAGEMDEMO"],
                        "cd_usuario_atualizacao": users["ENFERMAGEMDEMO"],
                    },
                )
                ticket.cd_pre_atendimento = pre
                ticket.save(update_fields=["cd_pre_atendimento"])

        visit_statuses = (
            "AGUARDANDO_CLASSIFICACAO",
            "EM_CLASSIFICACAO",
            "AGUARDANDO_CONSULTA",
            "EM_ATENDIMENTO",
            "EM_OBSERVACAO",
            "FINALIZADO",
            "ALTA_MEDICA",
            "CANCELADO",
        )
        for index, status in enumerate(visit_statuses, 1):
            started = now - timedelta(days=index % 4, hours=index)
            finished = status in {"FINALIZADO", "ALTA_MEDICA", "CANCELADO"}
            visit, _ = Atendimento.objects.update_or_create(
                cd_empresa=company,
                nr_senha_chamada=f"HOMO-{index:03d}",
                defaults={
                    "cd_paciente": patients[index + 5],
                    "cd_prestador": doctor if status not in {"AGUARDANDO_CLASSIFICACAO", "EM_CLASSIFICACAO", "CANCELADO"} else None,
                    "cd_convenio": patients[index + 5].cd_convenio or particular,
                    "ds_status": status,
                    "ds_origem": "DEMANDA_ESPONTANEA" if index % 2 else "AGENDADO",
                    "ds_tipo_atendimento": "Consulta ambulatorial",
                    "ds_especialidade": "Clínica médica",
                    "ds_plano": (patients[index + 5].cd_convenio or particular).nm_convenio,
                    "ds_unidade_setor": sectors["Consultórios"].nm_setor,
                    "cd_setor_atual": sectors["Observação"] if status == "EM_OBSERVACAO" else sectors["Consultórios"],
                    "ds_queixa_principal": "Queixa fictícia para validação do fluxo assistencial.",
                    "ds_anamnese": "Histórico clínico inteiramente fictício.",
                    "ds_hipotese_diagnostica": "Hipótese diagnóstica demo" if finished else "",
                    "ds_conduta": "Orientações e acompanhamento ambulatorial." if finished else "",
                    "ds_destino": "Residência" if finished else "",
                    "ds_motivo_cancelamento": "Cancelamento fictício solicitado pelo paciente." if status == "CANCELADO" else "",
                    "dh_inicio": started,
                    "dh_recepcao": started,
                    "dh_inicio_atendimento": started + timedelta(minutes=35) if status in {"EM_ATENDIMENTO", "EM_OBSERVACAO", "FINALIZADO", "ALTA_MEDICA"} else None,
                    "dh_fim_atendimento": started + timedelta(hours=1) if finished and status != "CANCELADO" else None,
                    "dh_fim": started + timedelta(hours=1) if finished else None,
                    "dh_cancelamento": started + timedelta(minutes=10) if status == "CANCELADO" else None,
                    "cd_usuario_cancelamento": users["RECEPCAODEMO"] if status == "CANCELADO" else None,
                    "cd_usuario_criacao": users["RECEPCAODEMO"],
                    "cd_usuario_atualizacao": users["MEDICODEMO"],
                    "sn_ativo": status != "CANCELADO",
                },
            )
            AtendimentoFluxo.objects.update_or_create(
                cd_atendimento=visit,
                ds_origem="POPULATE_DEMO",
                defaults={
                    "cd_empresa": company,
                    "ds_status_anterior": "RECEPCIONADO",
                    "ds_status_novo": status,
                    "cd_setor": visit.cd_setor_atual,
                    "cd_prestador": visit.cd_prestador,
                    "cd_usuario": users["RECEPCAODEMO"],
                    "dh_evento": started,
                    "ds_observacao": "Evento fictício criado pelo comando populate.",
                },
            )
        return len(queue_definitions), len(visit_statuses)
