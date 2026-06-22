from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, User, UsuarioEmpresa

from .models import Cep, TipoPrestadorConselho, ValorAuxiliarGlobal


class GlobalIntegrationTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=199, nm_empresa="Integração", sn_ativo=True)
        self.user = User.objects.create_user(username="TIGLOBAL", password="123456", is_active=True)
        self.user.groups.add(Group.objects.get_or_create(name="TI")[0])
        UsuarioEmpresa.objects.create(usuario=self.user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.cd_empresa
        session.save()

    def test_importa_cidade_por_csv(self):
        upload = SimpleUploadedFile(
            "cidades.csv",
            "codigo;descricao;uf\n3550308;São Paulo;SP\n".encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("core:global_integrations"),
            {"table_name": "cidade", "file": upload},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ValorAuxiliarGlobal.objects.filter(
                cd_tabela_auxiliar_global__ds_tabela="cidade",
                cd_valor="3550308",
                ds_grupo="SP",
            ).exists()
        )

    def test_importa_cep_em_tabela_propria(self):
        upload = SimpleUploadedFile(
            "ceps.csv",
            "cep;descricao;uf;cidade;bairro;tipo_logradouro\n01001000;Praça da Sé;SP;São Paulo;Sé;Praça\n".encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("core:global_integrations"),
            {"table_name": "cep", "file": upload},
        )
        self.assertEqual(response.status_code, 200)
        cep = Cep.objects.get(nr_cep="01001000")
        self.assertEqual(cep.ds_bairro, "Sé")
        self.assertEqual(cep.sg_estado, "SP")

    def test_cadastro_cep_redireciona_para_lista_consultada(self):
        response = self.client.post(
            reverse("core:global_ceps"),
            {
                "new_postal_code": ["30140071"],
                "new_state": ["MG"],
                "new_city_code": ["3106200"],
                "new_city": ["Belo Horizonte"],
                "new_street_type": ["AVENIDA"],
                "new_street": ["Afonso Pena"],
                "new_district": ["Centro"],
                "new_active": ["true"],
            },
        )
        self.assertRedirects(response, f"{reverse('core:global_ceps')}?consultar=1")
        cep = Cep.objects.get(nr_cep="30140071")
        self.assertLess(cep.cd_cep, 10)
        list_response = self.client.get(reverse("core:global_ceps"), {"consultar": "1"})
        self.assertContains(list_response, "30140071")

    def test_vinculo_prestador_conselho_salva_e_reaparece(self):
        response = self.client.post(
            reverse("core:tipo_prestador_conselho"),
            {
                "new_type": ["MEDICO"],
                "new_council": ["CRM"],
                "new_active": ["true"],
            },
        )
        self.assertRedirects(response, f"{reverse('core:tipo_prestador_conselho')}?consultar=1")
        self.assertTrue(TipoPrestadorConselho.objects.filter(tp_prestador="MEDICO", ds_conselho="CRM").exists())
        list_response = self.client.get(reverse("core:tipo_prestador_conselho"), {"consultar": "1"})
        self.assertContains(list_response, "CRM")


class FrontendInteractionContractTests(SimpleTestCase):
    def test_dropdown_possui_um_unico_handler_de_abertura_por_mouse(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertEqual(javascript.count('document.addEventListener("mousedown", function (event) {'), 1)
        click_handler = javascript.split('document.addEventListener("click", function (event) {\n    const select = event.target.closest(".content select")', 1)[1].split("});", 1)[0]
        self.assertNotIn("openFloatingSelect(select)", click_handler)

    def test_dropdown_mantem_contratos_de_teclado(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        for key in ('event.key === "Tab"', 'event.key === "Enter"', 'event.key === "Escape"', 'event.key === "ArrowDown"', 'event.key === "ArrowUp"'):
            with self.subTest(key=key):
                self.assertIn(key, javascript)

    def test_overlay_preserva_tela_de_origem_no_dom(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        layout = (settings.BASE_DIR / "templates" / "base" / "layout.html").read_text(encoding="utf-8")
        self.assertIn("[data-screen-overlay-link]", javascript)
        self.assertIn("data-screen-overlay", layout)
        self.assertIn("data-overlay-frame", layout)

    def test_nome_guerra_autocomplete_e_desabilitado_na_consulta(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('document.body.classList.contains("screen-query-mode")', javascript)
        self.assertIn("!providerForm.dataset.providerId", javascript)
        self.assertIn('warNameField.value = nameParts[0] || ""', javascript)

    def test_autocomplete_nativo_e_desativado_globalmente(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('form.setAttribute("autocomplete", "off")', javascript)
        self.assertIn('field.setAttribute("autocomplete", "off")', javascript)

    def test_validacao_rola_ate_campo_invalido(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('scrollIntoView({ behavior: "smooth", block: "center" })', javascript)

    def test_menu_compacto_e_identidade_de_itens(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn(".sidebar-collapsed .nav-icon", stylesheet)
        self.assertIn("background: transparent", stylesheet)
        self.assertIn("transform: rotate(45deg)", stylesheet)

    def test_multisselecao_possui_reset_generico_e_teclado(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        user_template = (settings.BASE_DIR / "templates" / "accounts" / "usuario_form.html").read_text(encoding="utf-8")
        self.assertIn("celeris:reset-multiselects", javascript)
        self.assertIn('event.key !== "Enter"', javascript)
        self.assertEqual(user_template.count("data-assignment-manager"), 2)
        self.assertIn("Empresas vinculadas", user_template)

    def test_dropdown_recolhido_respeita_largura_do_conteudo(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("width: fit-content", stylesheet)
        self.assertIn("max-width: 100%", stylesheet)
        self.assertIn(".specialty-add-row[hidden]", stylesheet)

    def test_barra_de_status_exibe_label_de_negocio(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('status.textContent = businessLabel.trim()', javascript)
        self.assertNotIn("`${normalizedTable}.${normalizedField}`", javascript)
