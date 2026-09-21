from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.shortcuts import render as django_render
from django.test import RequestFactory, TestCase
from django.urls import reverse
from unittest.mock import patch

from apps.accounts.models import Empresa, Papel, User, UsuarioEmpresa

from .models import Estoque, MovimentoEstoque, Produto, UnidadeProduto
from .views import movimentacoes, unidades


class TabelasEstoqueTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=8801, nm_empresa="Empresa Estoque", sn_ativo=True)
        self.usuario = User.objects.create_user("almoxarife-teste", password="senha-forte")
        self.usuario.groups.add(Group.objects.get_or_create(name="Almoxarifado")[0])
        UsuarioEmpresa.objects.create(usuario=self.usuario, empresa=self.empresa, sn_ativo=True)
        self.client.force_login(self.usuario)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_unidades_usam_tabela_editavel_e_salvamento_atomico(self):
        pagina = self.client.get(reverse("estoque:unidades"))
        self.assertContains(pagina, 'data-editable-table')
        self.assertNotContains(pagina, 'class="provider-form"')
        resposta = self.client.post(
            reverse("estoque:unidades"),
            {
                "new_ds_sigla": "AMP",
                "new_ds_descricao": "Ampola",
                "new_qt_fator_conversao": "1.000",
                "new_sn_ativo": "true",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(
            UnidadeProduto.objects.filter(
                cd_empresa=self.empresa,
                ds_sigla="AMP",
                ds_descricao="Ampola",
            ).exists()
        )

    def test_estoque_permanece_cadastro_mestre_com_regras_operacionais(self):
        pagina = self.client.get(reverse("estoque:estoques"))
        self.assertContains(pagina, 'class="provider-form stock-form"')
        self.assertContains(pagina, "Permite saída para paciente")
        self.assertContains(pagina, "Controla lote e validade")
        resposta = self.client.post(
            reverse("estoque:estoques"),
            {
                "ds_codigo": "FARM",
                "nm_estoque": "Farmácia central",
                "sn_saida_setor": "on",
                "sn_saida_paciente": "on",
                "sn_saida_gasto_sala": "on",
                "sn_transferencia": "on",
                "sn_controla_lote_validade": "on",
                "sn_ativo": "on",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        estoque = Estoque.objects.get(cd_empresa=self.empresa, ds_codigo="FARM")
        self.assertTrue(estoque.sn_saida_paciente)
        self.assertFalse(estoque.sn_saida_fornecedor)


class EstoqueTenantContextTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa A", "sn_ativo": True},
        )
        self.empresa_b = Empresa.objects.create(cd_empresa=8161, nm_empresa="Empresa B", sn_ativo=True)
        grupo, _ = Group.objects.get_or_create(name="Almoxarifado")
        Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
        self.usuario_a = User.objects.create_user("estoque-tenant-a", password="senha-forte")
        self.usuario_b = User.objects.create_user("estoque-tenant-b", password="senha-forte")
        self.usuario_a.groups.add(grupo)
        self.usuario_b.groups.add(grupo)
        UsuarioEmpresa.objects.create(usuario=self.usuario_a, empresa=self.empresa_a, sn_ativo=True)
        self.vinculo_b = UsuarioEmpresa.objects.create(
            usuario=self.usuario_b,
            empresa=self.empresa_b,
            sn_ativo=True,
        )
        self.unidade_a = UnidadeProduto.objects.create(
            cd_empresa=self.empresa_a,
            ds_sigla="UA",
            ds_descricao="Unidade A",
        )
        self.unidade_b = UnidadeProduto.objects.create(
            cd_empresa=self.empresa_b,
            ds_sigla="UB",
            ds_descricao="Unidade B",
        )
        self.produto_a = Produto.objects.create(cd_empresa=self.empresa_a, nm_produto="Produto A")
        self.produto_b = Produto.objects.create(cd_empresa=self.empresa_b, nm_produto="Produto B")

    def request(self, path, *, usuario, session, data=None, query=None):
        request = self.factory.post(path, data or {}) if data is not None else self.factory.get(path, query or {})
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session.update(session)
        request.session.save()
        request.user = usuario
        request._messages = FallbackStorage(request)
        return request

    def assert_tenant_invalido(self, *, view, usuario, session, data=None, args=()):
        request = self.request(reverse("estoque:unidades"), usuario=usuario, session=session, data=data)

        response = view(request, *args)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertIsNone(request.session.get("cd_empresa"))

    def test_usuario_da_empresa_b_sem_sessao_nao_le_dados_da_empresa_1(self):
        self.assert_tenant_invalido(view=unidades, usuario=self.usuario_b, session={})

    def test_usuario_da_empresa_b_sem_vinculo_na_empresa_1_falha_fechado(self):
        self.assert_tenant_invalido(
            view=unidades,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_a.pk},
        )

    def test_vinculo_inativo_e_empresa_inativa_falham_fechado(self):
        self.vinculo_b.sn_ativo = False
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            view=unidades,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

        self.vinculo_b.sn_ativo = True
        self.vinculo_b.save(update_fields=["sn_ativo"])
        self.empresa_b.sn_ativo = False
        self.empresa_b.save(update_fields=["sn_ativo"])
        self.assert_tenant_invalido(
            view=unidades,
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
        )

    def test_empresa_1_so_e_lida_quando_explicitamente_autorizada(self):
        request = self.request(
            reverse("estoque:unidades"),
            usuario=self.usuario_a,
            session={"cd_empresa": self.empresa_a.pk},
            query={"consultar": "1"},
        )

        with patch("apps.estoque.views.render", wraps=django_render) as renderizada:
            response = unidades(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [linha["pk"] for linha in renderizada.call_args.args[2]["linhas"]],
            [self.unidade_a.pk],
        )

    def test_leitura_e_escrita_de_movimento_usam_apenas_empresa_autorizada(self):
        leitura = self.request(
            reverse("estoque:unidades"),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            query={"consultar": "1"},
        )
        with patch("apps.estoque.views.render", wraps=django_render) as renderizada:
            response = unidades(leitura)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [linha["pk"] for linha in renderizada.call_args.args[2]["linhas"]],
            [self.unidade_b.pk],
        )

        escrita = self.request(
            reverse("estoque:movimentacoes_tipo", args=["entrada"]),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            data={
                "tp_movimento": MovimentoEstoque.Tipo.ENTRADA,
                "tp_destino": "",
                "cd_estoque_origem": "",
                "cd_estoque_destino": "",
                "cd_setor": "",
                "cd_atendimento": "",
                "ds_motivo": "Entrada B",
                "ds_observacao": "",
                "ds_status": MovimentoEstoque.Status.ABERTO,
                "itens-TOTAL_FORMS": "1",
                "itens-INITIAL_FORMS": "0",
                "itens-MIN_NUM_FORMS": "0",
                "itens-MAX_NUM_FORMS": "1000",
                "itens-0-cd_produto": str(self.produto_b.pk),
                "itens-0-qt_movimento": "1.000",
                "itens-0-ds_lote": "",
                "itens-0-dt_validade": "",
            },
        )
        response = movimentacoes(escrita, "entrada")

        self.assertEqual(response.status_code, 302)
        movimento = MovimentoEstoque.objects.get(ds_motivo="Entrada B")
        self.assertEqual(movimento.cd_empresa, self.empresa_b)
        self.assertEqual(movimento.itens.get().cd_produto, self.produto_b)

    def test_movimento_rejeita_produto_de_outra_empresa(self):
        request = self.request(
            reverse("estoque:movimentacoes_tipo", args=["entrada"]),
            usuario=self.usuario_b,
            session={"cd_empresa": self.empresa_b.pk},
            data={
                "tp_movimento": MovimentoEstoque.Tipo.ENTRADA,
                "tp_destino": "",
                "cd_estoque_origem": "",
                "cd_estoque_destino": "",
                "cd_setor": "",
                "cd_atendimento": "",
                "ds_motivo": "Entrada cruzada",
                "ds_observacao": "",
                "ds_status": MovimentoEstoque.Status.ABERTO,
                "itens-TOTAL_FORMS": "1",
                "itens-INITIAL_FORMS": "0",
                "itens-MIN_NUM_FORMS": "0",
                "itens-MAX_NUM_FORMS": "1000",
                "itens-0-cd_produto": str(self.produto_a.pk),
                "itens-0-qt_movimento": "1.000",
                "itens-0-ds_lote": "",
                "itens-0-dt_validade": "",
            },
        )

        response = movimentacoes(request, "entrada")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MovimentoEstoque.objects.filter(ds_motivo="Entrada cruzada").exists())
