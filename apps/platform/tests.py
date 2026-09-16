from django.test import SimpleTestCase
from django.urls import reverse

from .form_registry import form_registry
from .registry import registry
from .seeding import seed_registry
from .tenancy import current_tenant


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
