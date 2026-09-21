from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.shortcuts import render as django_render
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, Papel, User, UsuarioEmpresa

from .models import FaixaResultadoPesquisa, OpcaoRespostaPesquisa, PerguntaPesquisa, Pesquisa, RespostaPesquisa
from .views import configuracao, resultados


class PesquisaPublicaTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=9901, nm_empresa="Empresa Pesquisa", sn_ativo=True)
        self.pesquisa = Pesquisa.objects.create(
            cd_empresa=self.empresa,
            nm_pesquisa="Satisfação do atendimento",
            tp_calculo="MEDIA",
            sn_anonima=True,
            sn_publica=True,
        )
        self.pergunta = PerguntaPesquisa.objects.create(
            cd_pesquisa=self.pesquisa,
            ds_pergunta="Como foi o atendimento?",
            nr_peso=2,
            nr_ordem=1,
        )
        self.otima = OpcaoRespostaPesquisa.objects.create(
            cd_pergunta_pesquisa=self.pergunta,
            ds_resposta="Ótimo",
            nr_valor=5,
            nr_ordem=1,
        )
        FaixaResultadoPesquisa.objects.create(
            cd_pesquisa=self.pesquisa,
            nm_resultado="Excelente",
            nr_minimo=4,
            nr_maximo=5,
            ds_mensagem="Obrigado pela avaliação.",
        )

    def test_resposta_anonima_calcula_nota_e_mensagem(self):
        url = reverse("pesquisas:responder", args=[self.pesquisa.cd_token_publico])
        response = self.client.get(url)
        self.assertContains(response, "Como foi o atendimento?")

        response = self.client.post(url, {f"pergunta_{self.pergunta.pk}": self.otima.pk})
        resposta = RespostaPesquisa.objects.get()
        self.assertRedirects(response, reverse("pesquisas:concluida", args=[resposta.pk]))
        self.assertIsNone(resposta.cd_usuario)
        self.assertEqual(resposta.nr_resultado, Decimal("5.000"))
        self.assertEqual(resposta.cd_faixa_resultado.nm_resultado, "Excelente")

    def test_pesquisa_identificada_exige_login(self):
        self.pesquisa.sn_anonima = False
        self.pesquisa.save(update_fields=["sn_anonima"])
        response = self.client.get(reverse("pesquisas:responder", args=[self.pesquisa.cd_token_publico]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class PesquisaConfiguracaoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=9902, nm_empresa="Empresa Config", sn_ativo=True)
        self.user = User.objects.create_superuser("admin-pesquisa", "admin@example.com", "senha-forte")
        UsuarioEmpresa.objects.create(usuario=self.user, empresa=self.empresa, sn_ativo=True)
        self.client.force_login(self.user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_salva_pesquisa_dinamica(self):
        response = self.client.post(reverse("pesquisas:configuracao"), {
            "nm_pesquisa": "Pesquisa personalizada",
            "tp_pesquisa": "OUTRA",
            "ds_descricao": "Fluxo criado pelo usuário.",
            "sn_anonima": "on",
            "sn_publica": "on",
            "sn_ativo": "on",
        })
        pesquisa = Pesquisa.objects.get(nm_pesquisa="Pesquisa personalizada")
        self.assertRedirects(response, f"{reverse('pesquisas:configuracao')}?pesquisa={pesquisa.pk}")
        self.assertEqual(pesquisa.cd_empresa, self.empresa)


class PesquisasTenantContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa A", "sn_ativo": True},
        )
        self.empresa_b = Empresa.objects.create(cd_empresa=8171, nm_empresa="Empresa B", sn_ativo=True)
        grupo, _ = Group.objects.get_or_create(name="TI")
        Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
        self.usuario_a = User.objects.create_user("pesquisa-tenant-a", password="senha-forte")
        self.usuario_b = User.objects.create_user("pesquisa-tenant-b", password="senha-forte")
        self.usuario_a.groups.add(grupo)
        self.usuario_b.groups.add(grupo)
        UsuarioEmpresa.objects.create(usuario=self.usuario_a, empresa=self.empresa_a, sn_ativo=True)
        self.vinculo_b = UsuarioEmpresa.objects.create(
            usuario=self.usuario_b,
            empresa=self.empresa_b,
            sn_ativo=True,
        )
        self.pesquisa_a = Pesquisa.objects.create(cd_empresa=self.empresa_a, nm_pesquisa="Pesquisa A")
        self.pesquisa_b = Pesquisa.objects.create(cd_empresa=self.empresa_b, nm_pesquisa="Pesquisa B")

    def request(self, path, *, usuario, session, data=None, query=None):
        request = self.factory.post(path, data or {}) if data is not None else self.factory.get(path, query or {})
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session.update(session)
        request.session.save()
        request.user = usuario
        request._messages = FallbackStorage(request)
        return request

    def assert_tenant_invalido(self, *, usuario, session):
        request = self.request(reverse("pesquisas:resultados"), usuario=usuario, session=session)

        response = resultados(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertIsNone(request.session.get("cd_empresa"))

    def test_usuario_da_empresa_b_sem_sessao_nao_recebe_pesquisas_da_empresa_1(self):
        self.assert_tenant_invalido(usuario=self.usuario_b, session={})

    def test_usuario_da_empresa_b_sem_vinculo_na_empresa_1_falha_fechado(self):
        self.assert_tenant_invalido(
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_a.pk},
        )

    def test_vinculo_inativo_e_empresa_inativa_falham_fechado(self):
        self.vinculo_b.sn_ativo = False
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

        self.vinculo_b.sn_ativo = True
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.empresa_b.sn_ativo = False
        self.empresa_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

    def test_empresa_1_so_e_lida_quando_explicitamente_autorizada(self):
        request = self.request(
            reverse("pesquisas:resultados"),
            usuario=self.usuario_a,
            session={"cd_empresa": self.empresa_a.pk},
        )

        with patch("apps.pesquisas.views.render", wraps=django_render) as renderizada:
            response = resultados(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(renderizada.call_args.args[2]["pesquisas"]), [self.pesquisa_a])

    def test_leitura_e_escrita_usam_apenas_empresa_autorizada(self):
        leitura = self.request(
            reverse("pesquisas:resultados"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )
        with patch("apps.pesquisas.views.render", wraps=django_render) as renderizada:
            response = resultados(leitura)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(renderizada.call_args.args[2]["pesquisas"]), [self.pesquisa_b])

        escrita = self.request(
            reverse("pesquisas:configuracao"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            data={
                "nm_pesquisa": "Pesquisa criada por B",
                "tp_pesquisa": "OUTRA",
                "ds_descricao": "",
                "sn_anonima": "on",
                "sn_publica": "on",
                "sn_ativo": "on",
            },
        )
        response = configuracao(escrita)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Pesquisa.objects.filter(cd_empresa=self.empresa_b, nm_pesquisa="Pesquisa criada por B").exists()
        )
        self.assertFalse(
            Pesquisa.objects.filter(cd_empresa=self.empresa_a, nm_pesquisa="Pesquisa criada por B").exists()
        )
