from django.test import SimpleTestCase
from django.urls import reverse

from .registry import registry
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
