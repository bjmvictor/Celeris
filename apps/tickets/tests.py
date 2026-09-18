from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, Papel, User, UsuarioEmpresa

from .models import MotivoServicoSuporte, OficinaSuporte, Ticket, UsuarioOficinaSuporte
from .views import imprimir_chamado, solicitar, ticket_list


class TicketsTenantContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa A", "sn_ativo": True},
        )
        self.empresa_b = Empresa.objects.create(cd_empresa=8151, nm_empresa="Empresa B", sn_ativo=True)
        grupo, _ = Group.objects.get_or_create(name="Suporte")
        Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
        self.usuario_a = User.objects.create_user("tickets-tenant-a", password="senha-forte")
        self.usuario_b = User.objects.create_user("tickets-tenant-b", password="senha-forte")
        self.usuario_a.groups.add(grupo)
        self.usuario_b.groups.add(grupo)
        UsuarioEmpresa.objects.create(usuario=self.usuario_a, empresa=self.empresa_a, sn_ativo=True)
        self.vinculo_b = UsuarioEmpresa.objects.create(
            usuario=self.usuario_b,
            empresa=self.empresa_b,
            sn_ativo=True,
        )
        self.oficina_b = OficinaSuporte.objects.create(cd_empresa=self.empresa_b, nm_oficina="Oficina B")
        UsuarioOficinaSuporte.objects.create(
            cd_empresa=self.empresa_b,
            cd_usuario=self.usuario_b,
            cd_oficina=self.oficina_b,
            sn_solicita=True,
        )
        self.motivo_b = MotivoServicoSuporte.objects.create(
            cd_empresa=self.empresa_b,
            cd_oficina=self.oficina_b,
            nm_motivo="Motivo B",
        )
        self.ticket_a = self.criar_ticket(self.empresa_a, self.usuario_a, "Ticket A")
        self.ticket_b = self.criar_ticket(self.empresa_b, self.usuario_b, "Ticket B")

    def criar_ticket(self, empresa, usuario, titulo):
        return Ticket.objects.create(
            cd_empresa=empresa,
            module="Suporte",
            title=titulo,
            requester=usuario,
        )

    def request(self, path, *, usuario, session, data=None):
        request = self.factory.post(path, data or {}) if data is not None else self.factory.get(path)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session.update(session)
        request.session.save()
        request.user = usuario
        request._messages = FallbackStorage(request)
        return request

    def assert_tenant_invalido(self, *, view, usuario, session, data=None, args=()):
        request = self.request(reverse("tickets:list"), usuario=usuario, session=session, data=data)

        response = view(request, *args)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertIsNone(request.session.get("cd_empresa"))

    def test_usuario_da_empresa_b_sem_sessao_nao_le_tickets_da_empresa_1(self):
        self.assert_tenant_invalido(view=ticket_list, usuario=self.usuario_b, session={})

    def test_usuario_da_empresa_b_sem_vinculo_na_empresa_1_falha_fechado(self):
        self.assert_tenant_invalido(
            view=ticket_list,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_a.pk},
        )

    def test_vinculo_inativo_e_empresa_inativa_falham_fechado(self):
        self.vinculo_b.sn_ativo = False
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            view=ticket_list,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

        self.vinculo_b.sn_ativo = True
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.empresa_b.sn_ativo = False
        self.empresa_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            view=ticket_list,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

    def test_empresa_1_so_e_lida_quando_explicitamente_autorizada(self):
        request = self.request(
            reverse("tickets:list"),
            usuario=self.usuario_a,
            session={"cd_empresa": self.empresa_a.pk},
        )

        response = ticket_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket_a.title)
        self.assertNotContains(response, self.ticket_b.title)

    def test_leitura_e_escrita_usam_apenas_empresa_autorizada_da_sessao(self):
        leitura = self.request(
            reverse("tickets:list"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )
        response = ticket_list(leitura)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ticket_b.title)
        self.assertNotContains(response, self.ticket_a.title)

        escrita = self.request(
            reverse("tickets:solicitar"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            data={
                "title": "Novo ticket B",
                "description": "Descrição B",
                "cd_oficina": self.oficina_b.pk,
                "cd_motivo": self.motivo_b.pk,
            },
        )
        response = solicitar(escrita)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Ticket.objects.filter(cd_empresa=self.empresa_b, title="Novo ticket B").exists())
        self.assertEqual(Ticket.objects.filter(cd_empresa=self.empresa_a).count(), 1)

    def test_escrita_sem_tenant_nao_cria_ticket(self):
        self.assert_tenant_invalido(
            view=solicitar,
            usuario=self.usuario_b,
            session={},
            data={
                "title": "Não deve ser criado",
                "description": "Sem tenant",
                "cd_oficina": self.oficina_b.pk,
                "cd_motivo": self.motivo_b.pk,
            },
        )
        self.assertFalse(Ticket.objects.filter(title="Não deve ser criado").exists())

    def test_impressao_nao_localiza_ticket_de_outra_empresa(self):
        request = self.request(
            reverse("tickets:imprimir_chamado", args=[self.ticket_a.pk]),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

        with self.assertRaises(Http404):
            imprimir_chamado(request, self.ticket_a.pk)
