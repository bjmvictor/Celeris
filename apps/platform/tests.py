from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, User, UsuarioEmpresa

from .form_registry import form_registry
from .registry import registry
from .seeding import seed_registry
from .tenancy import TenantContextError, current_tenant, empresa_atual


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
        self.usuario_empresa_b = User.objects.create_user("tenant-b", password="senha-forte")
        UsuarioEmpresa.objects.create(
            usuario=self.usuario_empresa_b,
            empresa=self.empresa_selecionada,
            sn_ativo=True,
        )
        self.usuario_empresa_um = User.objects.create_user("tenant-um", password="senha-forte")
        UsuarioEmpresa.objects.create(
            usuario=self.usuario_empresa_um,
            empresa=self.empresa_padrao,
            sn_ativo=True,
        )

    def request(self, session=None, query=None, usuario=None):
        request = self.factory.get("/PEP/", query or {})
        request.session = session or {}
        request.user = self.usuario_empresa_b if usuario is None else usuario
        return request

    def test_resolve_empresa_ativa_da_sessao_como_instancia_empresa(self):
        empresa = empresa_atual(self.request({"cd_empresa": str(self.empresa_selecionada.cd_empresa)}))

        self.assertIsInstance(empresa, Empresa)
        self.assertEqual(empresa, self.empresa_selecionada)

    def test_empresa_um_funciona_quando_explicitamente_selecionada_e_autorizada(self):
        self.assertEqual(
            empresa_atual(self.request({"cd_empresa": 1}, usuario=self.usuario_empresa_um)),
            self.empresa_padrao,
        )

    def test_sessao_sem_empresa_falha_fechado(self):
        with self.assertRaisesRegex(TenantContextError, "Contexto de empresa") as erro:
            empresa_atual(self.request())

        self.assertEqual(erro.exception.reason, "missing_company")

    def test_nao_aceita_empresa_por_get_ou_post(self):
        empresa = empresa_atual(
            self.request({"cd_empresa": self.empresa_selecionada.cd_empresa}, {"cd_empresa": 1})
        )
        request_post = self.factory.post("/PEP/", {"cd_empresa": 1})
        request_post.session = {"cd_empresa": self.empresa_selecionada.cd_empresa}
        request_post.user = self.usuario_empresa_b

        self.assertEqual(empresa, self.empresa_selecionada)
        self.assertEqual(empresa_atual(request_post), self.empresa_selecionada)

    def test_empresa_inexistente_ou_inativa_falha_fechado(self):
        with self.assertRaises(TenantContextError) as inexistente:
            empresa_atual(self.request({"cd_empresa": 999999}))
        self.assertEqual(inexistente.exception.reason, "company_not_found")

        with self.assertRaises(TenantContextError) as inativa:
            empresa_atual(self.request({"cd_empresa": self.empresa_inativa.cd_empresa}))
        self.assertEqual(inativa.exception.reason, "company_inactive")

    def test_vinculo_ausente_ou_inativo_falha_fechado(self):
        with self.assertRaises(TenantContextError) as ausente:
            empresa_atual(self.request({"cd_empresa": self.empresa_padrao.cd_empresa}))
        self.assertEqual(ausente.exception.reason, "membership_invalid")

        usuario_vinculo_inativo = User.objects.create_user("tenant-inativo", password="senha-forte")
        UsuarioEmpresa.objects.create(
            usuario=usuario_vinculo_inativo,
            empresa=self.empresa_padrao,
            sn_ativo=False,
        )
        with self.assertRaises(TenantContextError) as inativo:
            empresa_atual(self.request({"cd_empresa": 1}, usuario=usuario_vinculo_inativo))
        self.assertEqual(inativo.exception.reason, "membership_invalid")

    def test_usuario_anonimo_falha_fechado(self):
        with self.assertRaises(TenantContextError) as erro:
            empresa_atual(self.request({"cd_empresa": self.empresa_selecionada.cd_empresa}, usuario=AnonymousUser()))
        self.assertEqual(erro.exception.reason, "anonymous_user")
