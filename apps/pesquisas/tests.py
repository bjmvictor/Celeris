from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, User

from .models import FaixaResultadoPesquisa, OpcaoRespostaPesquisa, PerguntaPesquisa, Pesquisa, RespostaPesquisa


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
