from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, Papel, User, UsuarioEmpresa
from apps.atendimento.models import ClasseSenhaAtendimento, SenhaAtendimento, TipoSenhaAtendimento

from .views import gerar_senha_totem


class TotemTenantContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa A", "sn_ativo": True},
        )
        self.empresa_b = Empresa.objects.create(cd_empresa=8141, nm_empresa="Empresa B", sn_ativo=True)
        grupo, _ = Group.objects.get_or_create(name="Recepcionista")
        Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
        self.usuario_a = User.objects.create_user("totem-tenant-a", password="senha-forte")
        self.usuario_b = User.objects.create_user("totem-tenant-b", password="senha-forte")
        self.usuario_a.groups.add(grupo)
        self.usuario_b.groups.add(grupo)
        UsuarioEmpresa.objects.create(usuario=self.usuario_a, empresa=self.empresa_a, sn_ativo=True)
        UsuarioEmpresa.objects.create(usuario=self.usuario_b, empresa=self.empresa_b, sn_ativo=True)
        self.classe_b = self.criar_classe(self.empresa_b, "B", "B")

    def criar_classe(self, empresa, sigla_tipo, sigla_classe):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=empresa,
            nm_tipo_senha=f"Tipo {sigla_tipo}",
            sg_tipo_senha=sigla_tipo,
        )
        return ClasseSenhaAtendimento.objects.create(
            cd_empresa=empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha=f"Classe {sigla_classe}",
            sg_classe_senha=sigla_classe,
        )

    def request(self, path, *, usuario, session, data=None):
        request = self.factory.post(path, data or {}) if data is not None else self.factory.get(path)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session.update(session)
        request.session.save()
        request.user = usuario
        request._messages = FallbackStorage(request)
        return request

    def assert_tenant_invalido(self, *, usuario, session):
        request = self.request(reverse("totem_standalone"), usuario=usuario, session=session)

        response = gerar_senha_totem(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertIsNone(request.session.get("cd_empresa"))
        self.assertFalse(SenhaAtendimento.objects.exists())

    def test_usuario_da_empresa_b_sem_sessao_nao_recebe_fallback_da_empresa_1(self):
        self.assert_tenant_invalido(usuario=self.usuario_b, session={})

    def test_usuario_da_empresa_b_nao_vinculado_a_empresa_1_e_invalidado(self):
        self.assert_tenant_invalido(usuario=self.usuario_b, session={"cd_empresa": self.empresa_a.pk})

    def test_usuario_anonimo_e_redirecionado_antes_de_resolver_empresa(self):
        request = self.request(reverse("totem_standalone"), usuario=AnonymousUser(), session={})

        response = gerar_senha_totem(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertFalse(SenhaAtendimento.objects.exists())

    def test_empresa_1_somente_e_usada_quando_esta_explicita_e_autorizada(self):
        request = self.request(
            reverse("totem_standalone"),
            usuario=self.usuario_a,
            session={"cd_empresa": self.empresa_a.pk},
        )

        response = gerar_senha_totem(request)

        self.assertEqual(response.status_code, 200)

    def test_geracao_usa_apenas_a_empresa_atual_autorizada(self):
        request = self.request(
            reverse("totem_standalone"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            data={"classe": self.classe_b.pk},
        )

        response = gerar_senha_totem(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(SenhaAtendimento.objects.filter(cd_empresa=self.empresa_b).exists())
        self.assertFalse(SenhaAtendimento.objects.filter(cd_empresa=self.empresa_a).exists())
