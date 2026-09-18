from django.http import Http404
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa

from .form_registry import form_registry
from .registry import registry
from .seeding import seed_registry
from .tenancy import current_tenant, empresa_atual


class ApplicationRegistryTests(SimpleTestCase):
    def test_discovers_independent_application_manifests(self):
        manifests = {manifest.code: manifest for manifest in registry.manifests()}
        self.assertEqual(set(manifests), {"CLASSIFICACAO", "EDITOR", "PAINEL", "PEP", "TOTEM"})
        self.assertEqual(manifests["PEP"].url_prefix, "PEP/")
        self.assertIn("atendimento.criado", manifests["PEP"].events)

    def test_legacy_public_routes_remain_reversible(self):
        self.assertEqual(reverse("pep_standalone"), "/PEP/")
        self.assertEqual(reverse("class_senhas"), "/class/senhas/")
        self.assertEqual(reverse("painel_chamada_standalone"), "/painel/")
        self.assertEqual(reverse("totem_standalone"), "/totem/")

    def test_tenant_context_uses_existing_session_contract(self):
        request = self.client.request().wsgi_request
        request.session["cd_empresa"] = 42
        self.assertEqual(current_tenant(request).empresa_id, 42)

    def test_atendimento_registers_its_configurable_forms(self):
        definitions = {definition.code: definition for definition in form_registry.definitions()}
        self.assertEqual(
            set(definitions),
            {
                "cadastro_paciente",
                "cadastro_prestador",
                "cadastro_atendimento",
                "responsavel_atendimento",
                "cadastro_escala",
                "cadastro_painel_chamada",
                "pre_atendimento",
            },
        )
        self.assertEqual(definitions["cadastro_paciente"].form_class, "apps.atendimento.forms.PacienteForm")

    def test_registered_demo_seed_providers_have_a_resolvable_order(self):
        providers = seed_registry.providers()
        self.assertEqual([provider.code for provider in providers], ["atendimento.demo_legacy"])

    def test_demo_seed_context_only_shares_scalar_values(self):
        from .seeding import DemoSeedContext

        context = DemoSeedContext(1, "senha-teste", False, None, None)
        context.set("empresa.demo", 1)
        self.assertEqual(context.get("empresa.demo"), 1)
        with self.assertRaises(TypeError):
            context.set("empresa.model", object())


class EmpresaAtualTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_padrao, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa padrão", "sn_ativo": True},
        )
        self.empresa_selecionada = Empresa.objects.create(
            cd_empresa=9201,
            nm_empresa="Empresa selecionada",
            sn_ativo=True,
        )
        self.empresa_inativa = Empresa.objects.create(
            cd_empresa=9202,
            nm_empresa="Empresa inativa",
            sn_ativo=False,
        )

    def request(self, session=None, query=None):
        request = self.factory.get("/PEP/", query or {})
        request.session = session or {}
        return request

    def test_resolve_empresa_ativa_da_sessao_como_instancia_empresa(self):
        empresa = empresa_atual(self.request({"cd_empresa": str(self.empresa_selecionada.cd_empresa)}))

        self.assertIsInstance(empresa, Empresa)
        self.assertEqual(empresa, self.empresa_selecionada)

    def test_usa_empresa_padrao_sem_empresa_na_sessao(self):
        self.assertEqual(empresa_atual(self.request()), self.empresa_padrao)

    def test_nao_aceita_empresa_por_get_ou_post(self):
        empresa = empresa_atual(
            self.request({"cd_empresa": self.empresa_selecionada.cd_empresa}, {"cd_empresa": 1})
        )
        request_post = self.factory.post("/PEP/", {"cd_empresa": 1})
        request_post.session = {"cd_empresa": self.empresa_selecionada.cd_empresa}

        self.assertEqual(empresa, self.empresa_selecionada)
        self.assertEqual(empresa_atual(request_post), self.empresa_selecionada)

    def test_empresa_inexistente_ou_inativa_retorna_404(self):
        with self.assertRaises(Http404):
            empresa_atual(self.request({"cd_empresa": 999999}))
        with self.assertRaises(Http404):
            empresa_atual(self.request({"cd_empresa": self.empresa_inativa.cd_empresa}))
