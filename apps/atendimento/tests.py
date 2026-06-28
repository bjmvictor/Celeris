from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa, User, UsuarioEmpresa
from apps.core.models import Cep, TabelaAuxiliarGlobal, ValorAuxiliarGlobal

from .forms import PrestadorForm
from .models import AgendaProfissional, Agendamento, Atendimento, AtendimentoFluxo, Convenio, DocumentoClinico, EvolucaoAtendimento, Paciente, Prescricao, Prestador


class FluxoHomologacaoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=99, nm_empresa="Homologação", sn_ativo=True)
        self.recepcionista = self.create_user("RECEPTESTE", "Recepcionista")
        self.enfermeiro = self.create_user("ENFTESTE", "Enfermeiro")
        self.medico_user = self.create_user("MEDTESTE", "Médico")
        self.ti_user = self.create_user("TITESTE", "TI")
        self.paciente = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="PACIENTE HOMOLOGAÇÃO",
            nr_cpf="529.982.247-25",
            dt_nascimento="1990-01-01",
        )
        self.prestador = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="MÉDICO TESTE",
            nm_guerra="MÉDICO TESTE",
            tp_prestador="MEDICO",
            ds_conselho="CRM",
            nr_conselho="123",
            ds_especialidade="CLINICA_GERAL",
            ds_especialidades=["CLINICA_GERAL"],
            sn_permite_agenda=True,
            sn_permite_atendimento=True,
            sn_permite_prescricao=True,
            sn_permite_classificacao=True,
        )
        self.agenda = AgendaProfissional.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            ds_agenda="TESTE",
            nr_dia_semana=timezone.localdate().weekday(),
            hr_inicio="08:00",
            hr_fim="18:00",
        )
        self.agendamento = Agendamento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_agenda_profissional=self.agenda,
            dh_agendamento=timezone.now() + timedelta(hours=1),
            ds_status="AGENDADO",
            ds_especialidade="CLINICA_GERAL",
            ds_profissional=self.prestador.nm_prestador,
        )
        self.client = Client(HTTP_HOST="localhost")

    def create_user(self, username, role):
        user = User.objects.create_user(username=username, password="123456", is_active=True)
        user.groups.add(Group.objects.get_or_create(name=role)[0])
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        return user

    def login_as(self, user):
        self.client.force_login(user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.cd_empresa
        session.save()

    def test_fluxo_assistencial_completo(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:recepcionar-agendamento", args=[self.agendamento.pk]))
        self.assertEqual(response.status_code, 302)
        atendimento = Atendimento.objects.get(cd_agendamento=self.agendamento)
        self.assertEqual(atendimento.ds_status, "AGUARDANDO_CLASSIFICACAO")

        self.login_as(self.enfermeiro)
        response = self.client.post(
            reverse("atendimento:pre-atendimento", args=[self.agendamento.pk]),
            {
                "nr_prioridade": 3,
                "ds_queixa_principal": "Dor de cabeça",
                "ds_sintomas": "Náusea",
                "ds_cor_prioridade": "AMARELO",
                "cd_prestador_responsavel": self.prestador.pk,
                "nr_pressao_arterial": "120x80",
            },
        )
        self.assertEqual(response.status_code, 302)
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "AGUARDANDO_CONSULTA")

        self.login_as(self.medico_user)
        self.client.get(reverse("atendimento:abrir-consulta", args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "EM_ATENDIMENTO")

        response = self.client.post(
            reverse("atendimento:ficha-atendimento", args=[atendimento.pk]),
            {
                "cd_prestador": self.prestador.pk,
                "ds_origem": "AGENDADO",
                "ds_tipo_atendimento": "CONSULTA",
                "ds_especialidade": "CLINICA_GERAL",
                "ds_unidade_setor": "AMBULATÓRIO",
                "ds_anamnese": "Paciente consciente.",
                "ds_hipotese_diagnostica": "Cefaleia",
                "ds_diagnostico": "Cefaleia tensional",
                "ds_conduta": "Medicação e repouso.",
                "ds_destino": "DOMICÍLIO",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.post(
            reverse("atendimento:prescrever", args=[atendimento.pk]),
            {"ds_prescricao": "Analgésico", "ds_orientacoes": "Tomar após alimentação."},
        )
        self.assertEqual(Prescricao.objects.filter(cd_atendimento=atendimento).count(), 1)

        self.client.post(
            reverse("atendimento:evoluir", args=[atendimento.pk]),
            {"ds_evolucao": "Paciente apresenta melhora clínica."},
        )
        self.assertEqual(EvolucaoAtendimento.objects.filter(cd_atendimento=atendimento).count(), 1)

        self.client.post(reverse("atendimento:conceder-alta", args=[atendimento.pk]), {"ds_destino": "DOMICÍLIO"})
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "ALTA_MEDICA")

        self.client.post(reverse("atendimento:finalizar-atendimento", args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "FINALIZADO")
        self.assertTrue(AtendimentoFluxo.objects.filter(cd_atendimento=atendimento, ds_status_novo="FINALIZADO").exists())

    def test_recepcao_nao_duplica_atendimento_do_mesmo_agendamento(self):
        self.login_as(self.recepcionista)
        self.client.get(reverse("atendimento:recepcionar-agendamento", args=[self.agendamento.pk]))
        self.client.get(reverse("atendimento:recepcionar-agendamento", args=[self.agendamento.pk]))
        self.assertEqual(Atendimento.objects.filter(cd_agendamento=self.agendamento).count(), 1)

    def test_dados_de_outra_empresa_nao_entram_na_recepcao(self):
        outra_empresa = Empresa.objects.create(cd_empresa=100, nm_empresa="Outra empresa", sn_ativo=True)
        outro_paciente = Paciente.objects.create(cd_empresa=outra_empresa, nm_paciente="PACIENTE OUTRA EMPRESA")
        outro_agendamento = Agendamento.objects.create(
            cd_empresa=outra_empresa,
            cd_paciente=outro_paciente,
            dh_agendamento=timezone.now(),
            ds_status="AGENDADO",
        )
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:recepcao"))
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertNotContains(response, outro_paciente.nm_paciente)
        response = self.client.get(reverse("atendimento:recepcionar-agendamento", args=[outro_agendamento.pk]))
        self.assertEqual(response.status_code, 404)

    def test_pep_nao_lista_paciente_apenas_agendado(self):
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"))
        self.assertNotContains(response, self.paciente.nm_paciente)

    def test_pep_exibe_filtros_por_engrenagem_e_lista_atendimentos_sem_alta(self):
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="AGUARDANDO_CONSULTA",
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"))
        self.assertContains(response, "⚙")
        self.assertContains(response, "Todos os setores permitidos")
        self.assertContains(response, "Atendimentos sem alta")
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertContains(response, "Abrir ficha")

    def test_pep_todos_pacientes_consulta_prontuario_e_atendimentos(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="FINALIZADO",
            ds_diagnostico="Cefaleia",
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"), {"aba": "todos", "q": "PACIENTE"})
        self.assertContains(response, "Prontuário")
        self.assertContains(response, self.paciente.nm_paciente)

        detail = self.client.get(reverse("atendimento:pep"), {"aba": "todos", "paciente": self.paciente.pk, "atendimento": atendimento.pk})
        self.assertContains(detail, f"Atendimento {atendimento.pk}")
        self.assertContains(detail, "Cefaleia")

    def test_agendamentos_operacionais_exibe_calendario_e_comprovante(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:agendamentos-operacionais"))
        self.assertContains(response, "calendar-day")
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertContains(response, "Comprovante")

        comprovante = self.client.get(reverse("atendimento:comprovante-agendamento", args=[self.agendamento.pk]))
        self.assertContains(comprovante, f"Protocolo {self.agendamento.pk}")
        self.assertContains(comprovante, "Gerado automaticamente pelo Celeris")

    def test_selecionar_agenda_confirma_apenas_apos_escolher_horario(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]))
        self.assertContains(response, "calendar-day")
        self.assertNotContains(response, "Confirmar agendamento")
        horario = response.context["horarios"][0]
        selected = self.client.get(
            reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]),
            {
                "data": horario["dh_agendamento"].date().isoformat(),
                "agenda": horario["agenda"].pk,
                "horario": horario["dh_agendamento"].isoformat(),
            },
        )
        self.assertContains(selected, "Confirmar agendamento")

    def test_pep_pesquisa_por_atendimento_e_geral(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="AGUARDANDO_CONSULTA",
        )
        self.login_as(self.medico_user)
        por_codigo = self.client.get(reverse("atendimento:pep"), {"nr_atendimento": atendimento.pk, "q_atendimento": "IGNORAR"})
        self.assertContains(por_codigo, self.paciente.nm_paciente)
        self.assertEqual(por_codigo.context["busca_atendimento"], "")

        por_nome = self.client.get(reverse("atendimento:pep"), {"q_atendimento": "PACIENTE"})
        self.assertContains(por_nome, self.paciente.nm_paciente)

    def test_documento_clinico_rascunho_e_copia(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        self.login_as(self.medico_user)
        self.client.post(
            reverse("atendimento:prescrever", args=[atendimento.pk]),
            {"ds_prescricao": "Dipirona", "ds_orientacoes": "Se dor."},
        )
        documento = DocumentoClinico.objects.get(cd_atendimento=atendimento, tp_documento="PRESCRICAO")
        self.assertEqual(documento.ds_status, "RASCUNHO")
        impressao = self.client.get(reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]))
        self.assertContains(impressao, "draft")

        copia = self.client.get(reverse("atendimento:copiar-documento-clinico", args=[documento.pk]))
        self.assertEqual(copia.status_code, 302)
        self.assertEqual(DocumentoClinico.objects.filter(cd_atendimento=atendimento).count(), 2)

    def test_cadastro_prestador_com_multiespecialidade(self):
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR TESTE",
                "nm_guerra": "PRESTADOR TESTE",
                "dt_nascimento": "1980-01-01",
                "nr_cpf": "529.982.247-25",
                "tp_prestador": "MEDICO",
                "nr_conselho": "12345",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CLINICA_GERAL",
                "tp_vinculo": "CLT",
                "sn_permite_agenda": "on",
                "sn_permite_atendimento": "on",
                "sn_permite_prescricao": "on",
                "sn_ativo": "True",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        provider = form.save(commit=False)
        self.assertEqual(provider.ds_especialidades, ["CLINICA_GERAL"])
        self.assertEqual(provider.ds_especialidade, "CLINICA_GERAL")
        self.assertEqual(provider.ds_conselho, "CRM")
        self.assertTrue(provider.sn_permite_agenda)
        self.assertTrue(provider.sn_permite_atendimento)
        self.assertTrue(provider.sn_permite_prescricao)

    def test_menu_de_prestadores_abre_cadastro_integrado(self):
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:profissionais"))
        self.assertRedirects(response, reverse("atendimento:cadastro-profissional-novo"))

    def test_consulta_integrada_de_prestadores_habilita_navegacao_de_resultados(self):
        self.login_as(self.ti_user)
        second_provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="MÉDICO TESTE DOIS",
            nm_guerra="MÉDICO DOIS",
            dt_nascimento="1980-01-01",
            nr_cpf="111.444.777-35",
            tp_prestador="MEDICO",
        )
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "MÉDICO TESTE"},
        )
        self.assertRedirects(
            response,
            f"{reverse('atendimento:cadastro-profissional', args=[self.prestador.pk])}?origem=consulta",
        )
        result_response = self.client.get(response.url)
        self.assertEqual(result_response.context["prestador"], self.prestador)
        self.assertContains(result_response, reverse("atendimento:cadastro-profissional", args=[second_provider.pk]))

    def test_abertura_direta_de_prestador_carrega_apenas_um_registro(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]),
        )
        self.assertEqual(response.context["prestador"], self.prestador)
        self.assertEqual(response.context["current_previous_url"], "")
        self.assertEqual(response.context["current_next_url"], "")

    def test_consulta_de_prestadores_sem_resultados_mantem_tela_integrada(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "INEXISTENTE"},
        )
        self.assertRedirects(response, reverse("atendimento:cadastro-profissional-novo"))

    def test_consulta_de_prestadores_sem_filtros_retorna_ativos_e_inativos(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR INATIVO",
            nm_guerra="INATIVO",
            dt_nascimento="1980-01-01",
            nr_cpf="123.456.789-09",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        result_ids = self.client.session["consulta_prestadores"]
        self.assertIn(self.prestador.pk, result_ids)
        self.assertIn(inactive.pk, result_ids)

    def test_consulta_de_prestadores_status_so_filtra_quando_informado(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR STATUS INATIVO",
            nm_guerra="STATUS INATIVO",
            dt_nascimento="1980-01-01",
            nr_cpf="123.456.789-09",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "sn_ativo": "False"},
        )
        self.assertEqual(self.client.session["consulta_prestadores"], [inactive.pk])

    def test_endereco_comercial_pode_acompanhar_residencial(self):
        provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR COM ENDERECO",
            nm_guerra="PRESTADOR ENDERECO",
            nr_cep="01001-000",
            sg_estado="SP",
            ds_cidade="SAO PAULO",
            tp_logradouro="RUA",
            ds_endereco="PRACA DA SE",
            nr_endereco="100",
            ds_complemento="SALA 1",
            ds_bairro="SE",
            sn_mesmo_endereco=True,
        )
        self.assertEqual(provider.nr_cep_comercial, provider.nr_cep)
        self.assertEqual(provider.sg_estado_comercial, provider.sg_estado)
        self.assertEqual(provider.ds_cidade_comercial, provider.ds_cidade)
        self.assertEqual(provider.ds_endereco_comercial, provider.ds_endereco)

    def test_especialidade_principal_deve_estar_na_lista(self):
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR TESTE",
                "nm_guerra": "PRESTADOR TESTE",
                "dt_nascimento": "1980-01-01",
                "tp_prestador": "MEDICO",
                "nr_conselho": "12345",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CARDIOLOGIA",
                "sn_ativo": "True",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("ds_especialidade_principal", form.errors)

    def test_cadastro_paciente_abre_sem_campos_de_prestador(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        self.assertEqual(response.status_code, 200)

    def test_prestador_e_gravado_na_tela_unificada(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:cadastro-profissional-novo"),
            {
                "nm_prestador": "MARIA DA SILVA",
                "nm_guerra": "MARIA SILVA",
                "dt_nascimento": "1985-05-20",
                "nr_cpf": "111.444.777-35",
                "tp_prestador": "MEDICO",
                "nr_conselho": "998877",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CLINICA_GERAL",
            },
        )
        self.assertEqual(response.status_code, 302)
        provider = Prestador.objects.get(nr_conselho="998877")
        self.assertTrue(provider.cd_prestador)

    def test_consulta_sem_filtros_retorna_todos_os_prestadores(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR INATIVO",
            nm_guerra="PRESTADOR INATIVO",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session["consulta_prestadores"],
            [self.prestador.cd_prestador, inactive.cd_prestador],
        )

    def test_paciente_e_prestador_referenciam_cep_por_codigo(self):
        cep = Cep.objects.create(nr_cep="01001000", sg_estado="SP", ds_cidade="São Paulo")
        self.paciente.cd_cep = cep
        self.paciente.save()
        self.prestador.cd_cep = cep
        self.prestador.save()
        self.assertEqual(self.paciente.cd_cep_id, cep.cd_cep)
        self.assertEqual(self.prestador.cd_cep_id, cep.cd_cep)

    def test_desativacao_nao_exclui_paciente_ou_prestador(self):
        self.login_as(self.ti_user)
        self.client.post(reverse("atendimento:alternar-status-paciente", args=[self.paciente.pk]))
        self.client.post(reverse("atendimento:alternar-status-prestador", args=[self.prestador.pk]))
        self.paciente.refresh_from_db()
        self.prestador.refresh_from_db()
        self.assertFalse(self.paciente.sn_ativo)
        self.assertFalse(self.prestador.sn_ativo)
        self.assertTrue(Paciente.objects.filter(pk=self.paciente.pk).exists())
        self.assertTrue(Prestador.objects.filter(pk=self.prestador.pk).exists())

    def test_tipo_sem_conselho_apenas_alerta_e_nao_bloqueia(self):
        table = TabelaAuxiliarGlobal.objects.get(ds_tabela="tipo_prestador")
        ValorAuxiliarGlobal.objects.create(
            cd_tabela_auxiliar_global=table,
            cd_valor="ADMINISTRATIVO",
            ds_valor="ADMINISTRATIVO",
        )
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR ADMINISTRATIVO",
                "nm_guerra": "PRESTADOR ADMINISTRATIVO",
                "dt_nascimento": "1990-01-01",
                "nr_cpf": "111.444.777-35",
                "tp_prestador": "ADMINISTRATIVO",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["ds_conselho"], "")

    def test_filtro_prestador_nao_reutiliza_resultado_anterior(self):
        matching = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="BENJAMIN VIEIRA",
            nm_guerra="BENJAMIN VIEIRA",
            dt_nascimento="1985-01-01",
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        first_response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "BENJ"},
        )
        self.assertRedirects(
            first_response,
            f"{reverse('atendimento:cadastro-profissional', args=[matching.pk])}?origem=consulta",
        )
        second_response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "W"},
        )
        self.assertRedirects(second_response, reverse("atendimento:cadastro-profissional-novo"))
        self.assertEqual(self.client.session["consulta_prestadores"], [])

    def test_filtros_paciente_individuais_e_combinados(self):
        parda = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="ANA PARDA",
            dt_nascimento="1995-03-10",
            ds_cor_raca="PARDA",
            tp_sexo="F",
            nr_celular="(31) 9 1111-1111",
            ds_bairro="CENTRO",
            sn_ativo=True,
        )
        Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="BRUNO BRANCO",
            dt_nascimento="1992-02-02",
            ds_cor_raca="BRANCA",
            tp_sexo="M",
            nr_celular="(31) 9 2222-2222",
            ds_bairro="SAVASSI",
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        cases = (
            ({"ds_cor_raca": "PARDA"}, [parda.pk]),
            ({"tp_sexo": "F"}, [parda.pk]),
            ({"ds_bairro": "CENTRO"}, [parda.pk]),
            ({"ds_cor_raca": "PARDA", "tp_sexo": "F"}, [parda.pk]),
            ({"ds_cor_raca": "PARDA", "tp_sexo": "M"}, []),
        )
        for filters, expected_ids in cases:
            with self.subTest(filters=filters):
                response = self.client.get(
                    reverse("atendimento:cadastro-paciente-novo"),
                    {"consultar": "1", **filters},
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.client.session["consulta_pacientes"], expected_ids)

    def test_consulta_de_pacientes_sem_filtros_retorna_ativos_e_inativos(self):
        inactive = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="PACIENTE INATIVO",
            dt_nascimento="1990-01-01",
            nr_cpf="111.444.777-35",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-paciente-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        result_ids = self.client.session["consulta_pacientes"]
        self.assertIn(self.paciente.pk, result_ids)
        self.assertIn(inactive.pk, result_ids)

    def test_cadastros_reutilizam_a_mesma_chave_de_guia(self):
        self.login_as(self.ti_user)
        new_provider = self.client.get(reverse("atendimento:cadastro-profissional-novo"))
        saved_provider = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        new_patient = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        saved_patient = self.client.get(reverse("atendimento:cadastro-paciente", args=[self.paciente.pk]))
        self.assertEqual(new_provider.context["current_tab_key"], saved_provider.context["current_tab_key"])
        self.assertEqual(new_patient.context["current_tab_key"], saved_patient.context["current_tab_key"])

    def test_erro_conselho_e_renderizado_no_campo(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:cadastro-profissional-novo"),
            {
                "nm_prestador": "MEDICO SEM NUMERO",
                "nm_guerra": "MEDICO NUMERO",
                "dt_nascimento": "1980-01-01",
                "tp_prestador": "MEDICO",
                "sg_conselho": "SP",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe o número do conselho")
        self.assertContains(response, "data-form-errors=")
        self.assertContains(response, "nr_conselho")

    def test_cpf_prestador_obrigatorio_invalido_duplicado_e_valido(self):
        base_data = {
            "nm_prestador": "PRESTADOR CPF",
            "nm_guerra": "PRESTADOR",
            "dt_nascimento": "1988-01-01",
            "tp_prestador": "MEDICO",
            "nr_conselho": "554433",
            "sg_conselho": "SP",
        }
        missing = PrestadorForm(data=base_data)
        self.assertFalse(missing.is_valid())
        self.assertIn("nr_cpf", missing.errors)

        invalid = PrestadorForm(data={**base_data, "nr_cpf": "111.111.111-11"})
        self.assertFalse(invalid.is_valid())
        self.assertIn("nr_cpf", invalid.errors)

        Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="CPF EXISTENTE",
            nm_guerra="CPF EXISTENTE",
            dt_nascimento="1980-01-01",
            nr_cpf="529.982.247-25",
        )
        duplicate = PrestadorForm(data={**base_data, "nr_cpf": "529.982.247-25"})
        self.assertFalse(duplicate.is_valid())
        self.assertIn("nr_cpf", duplicate.errors)

        valid = PrestadorForm(data={**base_data, "nr_cpf": "111.444.777-35"})
        self.assertTrue(valid.is_valid(), valid.errors)

    def test_filtros_prestador_por_cpf_tipo_conselho_e_especialidade(self):
        provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="FILTRO PRESTADOR",
            nm_guerra="FILTRO",
            dt_nascimento="1981-01-01",
            nr_cpf="111.444.777-35",
            tp_prestador="MEDICO",
            ds_conselho="CRM",
            nr_conselho="FILTER123",
            ds_especialidade="CLINICA_GERAL",
            ds_especialidades=["CLINICA_GERAL"],
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        cases = (
            {"nr_cpf": "111.444.777-35"},
            {"tp_prestador": "MEDICO", "nr_conselho": "FILTER123"},
            {"ds_conselho": "CRM"},
            {"ds_especialidades": "CLINICA_GERAL"},
        )
        for filters in cases:
            with self.subTest(filters=filters):
                response = self.client.get(
                    reverse("atendimento:cadastro-profissional-novo"),
                    {"consultar": "1", **filters},
                )
                self.assertEqual(response.status_code, 302)
                self.assertIn(provider.pk, self.client.session["consulta_prestadores"])

    def test_navegacao_habilita_apenas_direcoes_disponiveis(self):
        providers = [
            Prestador.objects.create(
                cd_empresa=self.empresa,
                nm_prestador=f"NAVEGACAO {index}",
                nm_guerra=f"NAVEGACAO {index}",
                dt_nascimento="1980-01-01",
                nr_cpf=cpf,
                sn_ativo=True,
            )
            for index, cpf in enumerate(("111.444.777-35", "529.982.247-25", "123.456.789-09"), start=1)
        ]
        self.login_as(self.ti_user)
        session = self.client.session
        session["consulta_prestadores"] = [provider.pk for provider in providers]
        session.save()

        first = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[0].pk]), {"origem": "consulta"})
        middle = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[1].pk]), {"origem": "consulta"})
        last = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[2].pk]), {"origem": "consulta"})
        self.assertFalse(first.context["current_first_url"])
        self.assertFalse(first.context["current_previous_url"])
        self.assertTrue(first.context["current_next_url"])
        self.assertTrue(first.context["current_last_url"])
        self.assertTrue(middle.context["current_first_url"])
        self.assertTrue(middle.context["current_previous_url"])
        self.assertTrue(middle.context["current_next_url"])
        self.assertTrue(middle.context["current_last_url"])
        self.assertTrue(last.context["current_first_url"])
        self.assertTrue(last.context["current_previous_url"])
        self.assertFalse(last.context["current_next_url"])
        self.assertFalse(last.context["current_last_url"])

    def test_botao_status_alterna_rotulo(self):
        self.login_as(self.ti_user)
        active = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        self.assertEqual(active.context["current_toggle_active_label"], "Desativar")
        self.client.post(reverse("atendimento:alternar-status-prestador", args=[self.prestador.pk]))
        inactive = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        self.assertEqual(inactive.context["current_toggle_active_label"], "Ativar")

    def test_links_auxiliares_abrem_em_overlay(self):
        self.login_as(self.ti_user)
        provider_response = self.client.get(reverse("atendimento:cadastro-profissional-novo"))
        patient_response = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        self.assertContains(provider_response, "data-screen-overlay-link", count=2)
        self.assertContains(patient_response, "data-screen-overlay-link", count=1)
        self.assertNotContains(provider_response, "Especialidades <a")
        self.assertNotContains(patient_response, "Convênio <a")
        self.assertContains(patient_response, "Nenhum convênio cadastrado.")
        overlay_response = self.client.get(reverse("core:global_ceps"), {"overlay": "1"})
        self.assertTrue(overlay_response.context["current_overlay_mode"])

    def test_cadastro_paciente_agendamento_substitui_guia_e_volta_para_agendar(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:cadastro-paciente-agendamento"))
        self.assertEqual(response.context["current_tab_key"], reverse("atendimento:agendar"))
        self.assertEqual(response.context["current_close_mode"], "back")
        self.assertEqual(response.context["current_close_url"], reverse("atendimento:agendar"))
        self.assertEqual(response.context["current_tab_root_title"], "Cadastro de paciente")

    def test_telas_de_especialidade_e_convenio_abrem(self):
        self.login_as(self.ti_user)
        for route in ("atendimento:especialidades", "atendimento:convenios"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)

    def test_convenios_consulta_em_branco_lista_todos(self):
        self.login_as(self.ti_user)
        Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="SUL AMERICA", sn_ativo=True)
        Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="BRADESCO SAUDE", sn_ativo=True)

        response = self.client.get(reverse("atendimento:convenios"), {"consultar": "1"})

        self.assertContains(response, "SUL AMERICA")
        self.assertContains(response, "BRADESCO SAUDE")
        self.assertNotContains(response, "Nenhum dado encontrado.")

    def test_convenios_salvar_mantem_registros_exibidos(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:convenios"),
            {"new_name": ["SUL AMERICA"], "new_active": ["true"]},
        )
        self.assertRedirects(response, f"{reverse('atendimento:convenios')}?consultar=1")
        list_response = self.client.get(reverse("atendimento:convenios"), {"consultar": "1"})
        self.assertContains(list_response, "SUL AMERICA")
