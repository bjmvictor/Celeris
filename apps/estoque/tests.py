from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, User

from .models import Estoque, UnidadeProduto


class TabelasEstoqueTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=8801, nm_empresa="Empresa Estoque", sn_ativo=True)
        self.usuario = User.objects.create_user("almoxarife-teste", password="senha-forte")
        self.usuario.groups.add(Group.objects.get_or_create(name="Almoxarifado")[0])
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
