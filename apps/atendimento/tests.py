from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa, User, UsuarioEmpresa
from apps.core.models import Cep, TabelaAuxiliarGlobal, ValorAuxiliarGlobal

from .forms import PrestadorForm
from .models import AgendaProfissional, Agendamento, Atendimento, EvolucaoAtendimento, Paciente, Prescricao, Prestador


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
        self.assertEqual(atendimento.ds_status, "ALTA")

        self.client.post(reverse("atendimento:finalizar-atendimento", args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "FINALIZADO")

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

    def test_consulta_de_prestadores_exibe_resultado_editar_e_retorno(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:profissionais"),
            {"nm_prestador": "MÉDICO TESTE"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1 registro(s) encontrado(s).")
        self.assertContains(response, "Editar")
        self.assertContains(response, reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))

        return_url = f"{reverse('atendimento:profissionais')}?nm_prestador=MÉDICO"
        edit_response = self.client.get(
            reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]),
            {"return_to": return_url},
        )
        self.assertEqual(edit_response.context["prestador"], self.prestador)
        self.assertEqual(edit_response.context["current_return_url"], return_url)

    def test_consulta_de_prestadores_sem_resultados_exibe_mensagem(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:profissionais"),
            {"nm_prestador": "INEXISTENTE"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum registro encontrado.")

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

    def test_consulta_sem_filtros_retorna_prestadores_ativos(self):
        Prestador.objects.create(
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
        self.assertEqual(self.client.session["consulta_prestadores"], [self.prestador.cd_prestador])

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
        self.assertRedirects(first_response, reverse("atendimento:cadastro-profissional", args=[matching.pk]))
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

        first = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[0].pk]))
        middle = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[1].pk]))
        last = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[2].pk]))
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
        self.assertContains(provider_response, "data-screen-overlay-link", count=3)
        self.assertContains(patient_response, "data-screen-overlay-link", count=2)
        overlay_response = self.client.get(reverse("core:global_ceps"), {"overlay": "1"})
        self.assertTrue(overlay_response.context["current_overlay_mode"])

    def test_telas_de_especialidade_e_convenio_abrem(self):
        self.login_as(self.ti_user)
        for route in ("atendimento:especialidades", "atendimento:convenios"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
