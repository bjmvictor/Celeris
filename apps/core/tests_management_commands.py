from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.accounts.models import Empresa, Papel, User
from apps.atendimento.models import (
    AgendaProfissional,
    Atendimento,
    CorClassificacaoRisco,
    EscalaClinica,
    FluxoClassificacao,
    GrupoFluxoClassificacao,
    ItemMenuAssistencial,
    MaquinaChamada,
    Paciente,
    PainelChamada,
    PerguntaClassificacao,
    PerfilAssistencial,
    PreAtendimento,
    Prescricao,
    Prestador,
    SenhaAtendimento,
)
from apps.pesquisas.models import Pesquisa
from apps.atendimento.views_painel import paineis_compativeis_atendimento


class PopulateCommandTests(TestCase):
    @override_settings(DEBUG=True)
    def test_populate_cria_cenario_completo_e_e_idempotente(self):
        output = StringIO()
        call_command("populate", stdout=output)

        company = Empresa.objects.get(pk=9000)
        self.assertEqual(company.nm_empresa, "Hospital Horizonte Demo")
        self.assertEqual(company.setores.count(), 6)
        self.assertEqual(Prestador.objects.filter(cd_empresa=company).count(), 8)
        self.assertEqual(Paciente.objects.filter(cd_empresa=company).count(), 24)
        self.assertEqual(User.objects.filter(username__endswith="DEMO").count(), 5)
        self.assertEqual(Papel.objects.filter(grupo__name__in=["TI", "Recepcionista", "Enfermeiro", "Médico", "Auditor"]).count(), 5)
        self.assertEqual(SenhaAtendimento.objects.filter(cd_empresa=company).count(), 6)
        self.assertEqual(PreAtendimento.objects.filter(cd_empresa=company).count(), 3)
        self.assertEqual(Atendimento.objects.filter(cd_empresa=company).count(), 8)
        self.assertEqual(PainelChamada.objects.filter(cd_empresa=company, sn_ativo=True).count(), 1)
        self.assertEqual(MaquinaChamada.objects.filter(cd_empresa=company, sn_ativo=True).count(), 1)
        self.assertEqual(AgendaProfissional.objects.filter(cd_empresa=company).count(), 3)
        self.assertEqual(PerguntaClassificacao.objects.filter(cd_empresa=company).count(), 4)
        self.assertEqual(CorClassificacaoRisco.objects.filter(cd_empresa=company).count(), 5)
        self.assertEqual(GrupoFluxoClassificacao.objects.filter(cd_empresa=company).count(), 4)
        self.assertEqual(FluxoClassificacao.objects.filter(cd_empresa=company).count(), 12)
        self.assertEqual(EscalaClinica.objects.filter(cd_empresa=company).count(), 1)
        self.assertEqual(PerfilAssistencial.objects.filter(cd_empresa=company).count(), 1)
        self.assertEqual(ItemMenuAssistencial.objects.filter(cd_empresa=company).count(), 8)
        self.assertEqual(Prescricao.objects.filter(cd_empresa=company).count(), 1)
        self.assertEqual(Pesquisa.objects.filter(cd_empresa=company).count(), 1)
        self.assertIn("ADMINDEMO", output.getvalue())

        call_command("populate", stdout=StringIO())
        self.assertEqual(Paciente.objects.filter(cd_empresa=company).count(), 24)
        self.assertEqual(SenhaAtendimento.objects.filter(cd_empresa=company).count(), 6)
        self.assertEqual(PreAtendimento.objects.filter(cd_empresa=company).count(), 3)
        self.assertEqual(Atendimento.objects.filter(cd_empresa=company).count(), 8)
        self.assertEqual(AgendaProfissional.objects.filter(cd_empresa=company).count(), 3)
        self.assertEqual(CorClassificacaoRisco.objects.filter(cd_empresa=company).count(), 5)
        self.assertEqual(GrupoFluxoClassificacao.objects.filter(cd_empresa=company).count(), 4)
        self.assertEqual(FluxoClassificacao.objects.filter(cd_empresa=company).count(), 12)
        self.assertEqual(ItemMenuAssistencial.objects.filter(cd_empresa=company).count(), 8)
        self.assertEqual(Pesquisa.objects.filter(cd_empresa=company).count(), 1)

    @override_settings(DEBUG=True)
    def test_produtos_ocultos_sem_permissao_e_retorno_do_class_preservado(self):
        call_command("populate", stdout=StringIO())
        company = Empresa.objects.get(pk=9000)

        self.client.force_login(User.objects.get(username="RECEPCAODEMO"))
        session = self.client.session
        session["cd_empresa"] = company.pk
        session.save()
        home = self.client.get("/")
        self.assertNotContains(home, "Celeris PEP")
        self.assertNotContains(home, "Celeris Class")
        denied = self.client.get("/class/")
        self.assertEqual(denied.status_code, 403)
        self.assertContains(denied, "error-page-card", status_code=403)

        self.client.force_login(User.objects.get(username="ENFERMAGEMDEMO"))
        session = self.client.session
        session["cd_empresa"] = company.pk
        session.save()
        ticket = SenhaAtendimento.objects.filter(cd_empresa=company, ds_status="AGUARDANDO").first()
        class_list = self.client.get("/class/", {"filtro": "nao_classificados"})
        self.assertContains(class_list, "Celeris Class")
        editor = self.client.get("/class/", {"filtro": "nao_classificados", "senha": ticket.pk})
        self.assertTrue(editor.context["class_close_url"].startswith("/class/?"))

    @override_settings(DEBUG=True)
    def test_fila_coloca_senha_vencida_mais_antiga_antes_da_prioridade_recente(self):
        call_command("populate", stdout=StringIO())
        company = Empresa.objects.get(pk=9000)
        self.client.force_login(User.objects.get(username="ENFERMAGEMDEMO"))
        session = self.client.session
        session["cd_empresa"] = company.pk
        session.save()

        response = self.client.get("/class/", {"filtro": "nao_classificados"})
        unclassified = [ticket for ticket in response.context["senhas"] if ticket.ds_status != "CLASSIFICADA"]
        self.assertEqual(unclassified[0].ds_senha, "CE001")
        self.assertTrue(unclassified[0].tempo_excedido)

    @override_settings(DEBUG=True)
    def test_painel_compara_codigos_e_rotulos_normalizados(self):
        call_command("populate", stdout=StringIO())
        company = Empresa.objects.get(pk=9000)
        panel = PainelChamada.objects.get(cd_empresa=company)
        panel.ds_configuracao = {
            "chamar_paciente": True,
            "especialidades": ["CLINICA_MEDICA"],
            "tipos_atendimento": ["CONSULTA_AMBULATORIAL"],
        }
        panel.save(update_fields=["ds_configuracao"])
        visit = Atendimento.objects.filter(
            cd_empresa=company,
            ds_tipo_atendimento="Consulta ambulatorial",
            cd_setor_atual__nm_setor="Consultórios",
        ).first()

        self.assertEqual(paineis_compativeis_atendimento(visit, visit.cd_setor_atual_id), [panel])

    @override_settings(DEBUG=True)
    def test_populate_nao_sobrescreve_empresa_real_no_mesmo_codigo(self):
        Empresa.objects.create(cd_empresa=9000, nm_empresa="Empresa real")

        with self.assertRaisesMessage(CommandError, "já existe"):
            call_command("populate", stdout=StringIO())

        self.assertEqual(Empresa.objects.get(pk=9000).nm_empresa, "Empresa real")

    @override_settings(DEBUG=False)
    def test_populate_exige_confirmacao_fora_de_debug(self):
        with self.assertRaisesMessage(CommandError, "--permitir-fora-debug"):
            call_command("populate", stdout=StringIO())
