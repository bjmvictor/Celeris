import importlib
import json

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.apps import apps as django_apps
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, Setor, User, UsuarioEmpresa
from apps.accounts.access import user_access_keys
from apps.atendimento.forms import PacienteForm
from apps.atendimento.models import Convenio

from .models import (
    Cep,
    Cidade,
    ConfiguracaoCampoFormulario,
    IconeSistema,
    Module,
    Plano,
    Procedimento,
    ScreenDefinition,
    Sexo,
    TipoAtendimento,
    TipoPrestadorConselho,
)
from .catalogos import modelo_catalogo


class InitialConfigurationCommandTests(TestCase):
    def test_comando_valida_e_aplica_arquivos_toml_de_forma_idempotente(self):
        with TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "empresas.toml").write_text(
                'habilitado = true\n[[registros]]\ncodigo = 731\nnome = "Empresa Inicial"\nativo = true\n',
                encoding="utf-8",
            )
            (directory / "setores.toml").write_text(
                'habilitado = true\n[[registros]]\nempresa_codigo = 731\nnome = "Recepção"\ntipo = "EMPRESA"\nativo = true\n',
                encoding="utf-8",
            )
            (directory / "convenios.toml").write_text(
                'habilitado = true\n[[registros]]\nempresa_codigo = 731\nnome = "Particular"\nativo = true\n',
                encoding="utf-8",
            )
            catalog_path = directory / "catalogo_tipo_atendimento.toml"
            catalog_path.write_text(
                'habilitado = true\ntabela = "tipo_atendimento"\ndescricao = "Tipos de atendimento"\n'
                '[[registros]]\ncodigo = "CONSULTA_INICIAL"\ndescricao = "Consulta inicial"\nativo = true\n',
                encoding="utf-8",
            )

            validation_output = StringIO()
            call_command(
                "aplicar_configuracao_inicial",
                diretorio=str(directory),
                validar=True,
                stdout=validation_output,
            )
            self.assertIn("Configuração válida", validation_output.getvalue())
            self.assertFalse(Empresa.objects.filter(pk=731).exists())

            call_command("aplicar_configuracao_inicial", diretorio=str(directory), stdout=StringIO())
            call_command("aplicar_configuracao_inicial", diretorio=str(directory), stdout=StringIO())

            company = Empresa.objects.get(pk=731)
            self.assertEqual(company.nm_empresa, "Empresa Inicial")
            self.assertEqual(Setor.objects.filter(cd_empresa=company, nm_setor="Recepção").count(), 1)
            self.assertEqual(Convenio.objects.filter(cd_empresa=company, nm_convenio="Particular").count(), 1)
            self.assertEqual(
                TipoAtendimento.objects.filter(cd_valor="CONSULTA_INICIAL").count(),
                1,
            )


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

    def test_catalogo_tematico_persiste_sem_indice_de_compatibilidade(self):
        valor = Cidade.objects.create(
            cd_valor="TESTE_2610006",
            ds_valor="Palmares",
            ds_grupo="PE",
        )
        valor.ds_valor = "Palmares - PE"
        valor.save()
        valor.refresh_from_db()
        self.assertEqual(valor.ds_valor, "Palmares - PE")

    def test_configuracao_de_formulario_lista_e_aplica_obrigatoriedade(self):
        route = reverse("core:configurar_formularios")
        initial = self.client.get(route)
        self.assertContains(initial, 'data-start-query="true"')
        self.assertContains(initial, 'data-consultable="true"', count=2)

        response = self.client.get(route, {"consultar": "1", "formulario": "cadastro_paciente"})
        self.assertContains(response, "Cadastro de paciente")
        self.assertContains(response, "nm_paciente")
        self.assertContains(response, "nr_cpf")
        self.assertContains(response, "<td>Nome</td>", html=True)

        saved = self.client.post(
            route,
            {
                "formulario": "cadastro_paciente",
                "nome_campo": "CPF",
                "campos_resultado": ["cadastro_paciente::nr_cpf"],
                "campos_obrigatorios": ["cadastro_paciente::nr_cpf"],
            },
        )
        self.assertRedirects(
            saved,
            f"{route}?consultar=1&formulario=cadastro_paciente&nome_campo=CPF",
        )
        configuracao = ConfiguracaoCampoFormulario.objects.get(
            cd_empresa=self.empresa,
            cd_formulario="cadastro_paciente",
            cd_campo="nr_cpf",
        )
        self.assertTrue(configuracao.sn_obrigatorio)
        self.assertEqual(configuracao.cd_usuario_criacao, self.user)
        formulario = PacienteForm(empresa=self.empresa)
        self.assertTrue(formulario.fields["nr_cpf"].required)
        self.assertTrue(formulario.fields["nm_paciente"].required)

    def test_arvore_de_navegacao_reordena_itens_do_mesmo_grupo(self):
        module = Module.objects.create(code="TESTE_MENU", title="Teste menu", order=990)
        group = ScreenDefinition.objects.create(
            module=module,
            title="Grupo",
            slug="teste-menu-grupo",
            screen_type=ScreenDefinition.TYPE_GROUP,
        )
        first = ScreenDefinition.objects.create(
            module=module,
            parent=group,
            title="Primeiro",
            slug="teste-menu-primeiro",
            access_key="teste-menu-primeiro",
            order=10,
        )
        second = ScreenDefinition.objects.create(
            module=module,
            parent=group,
            title="Segundo",
            slug="teste-menu-segundo",
            access_key="teste-menu-segundo",
            order=20,
        )
        response = self.client.post(
            reverse("core:system_navigation_reorder"),
            {"node": second.pk, "parent": group.pk, "order": [second.pk, first.pk]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(group.children.order_by("order").values_list("pk", flat=True)),
            [second.pk, first.pk],
        )

    def test_salvar_modulo_preserva_ordem_reorganizada_dos_itens(self):
        module = Module.objects.create(code="TESTE_ORDEM", title="Teste ordem", order=991)
        first = ScreenDefinition.objects.create(
            module=module,
            title="Primeiro",
            slug="teste-ordem-primeiro",
            access_key="teste-ordem-primeiro",
            order=10,
        )
        second = ScreenDefinition.objects.create(
            module=module,
            title="Segundo",
            slug="teste-ordem-segundo",
            access_key="teste-ordem-segundo",
            order=20,
        )

        response = self.client.post(
            reverse("core:system_screens"),
            {
                "module_id": module.pk,
                "code": module.code,
                "title": "Teste ordem atualizado",
                "icon": "",
                "order": module.order,
                "active": "True",
                "navigation_order_changed": json.dumps({"": [second.pk, first.pk]}),
            },
        )

        self.assertEqual(response.status_code, 302)
        module.refresh_from_db()
        self.assertEqual(module.title, "Teste ordem atualizado")
        self.assertEqual(
            list(module.screens.order_by("order").values_list("pk", flat=True)),
            [second.pk, first.pk],
        )

    def test_configuracao_usa_rotulos_visiveis_do_cadastro_de_prestador(self):
        response = self.client.get(
            reverse("core:configurar_formularios"),
            {"consultar": "1", "formulario": "cadastro_prestador"},
        )
        self.assertContains(response, "<td>Nome</td>", html=True)
        self.assertContains(response, "<td>Nome de guerra</td>", html=True)
        self.assertNotContains(response, "<td>Nm prestador</td>", html=True)

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
            Cidade.objects.filter(
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
                "new_nr_cep": ["30140071"],
                "new_sg_estado": ["MG"],
                "new_cd_cidade": ["3106200"],
                "new_ds_cidade": ["Belo Horizonte"],
                "new_tp_logradouro": ["AVENIDA"],
                "new_ds_logradouro": ["Afonso Pena"],
                "new_ds_bairro": ["Centro"],
                "new_sn_ativo": ["true"],
            },
        )
        self.assertRedirects(response, f"{reverse('core:global_ceps')}?consultar=1")
        cep = Cep.objects.get(nr_cep="30140071")
        self.assertGreater(cep.cd_cep, 0)
        list_response = self.client.get(reverse("core:global_ceps"), {"q": "30140071"})
        self.assertContains(list_response, "30140071")

    def test_consulta_cep_por_uf_nao_retorna_todos(self):
        Cep.objects.create(nr_cep="50000000", sg_estado="PE", ds_cidade="Recife", ds_logradouro="Rua PE")
        Cep.objects.create(nr_cep="01001000", sg_estado="SP", ds_cidade="São Paulo", ds_logradouro="Rua SP")
        response = self.client.get(reverse("core:global_ceps"), {"q": "PE"})
        self.assertContains(response, "50000000")
        self.assertNotContains(response, "01001000")

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

    def test_planos_e_procedimentos_usam_tabelas_auxiliares_persistentes(self):
        for slug, table_name, description in (
            ("cadastros-planos", "plano", "PLANO TESTE"),
            ("cadastros-procedimentos", "procedimento", "PROCEDIMENTO TESTE"),
        ):
            modelo_catalogo(table_name).objects.create(
                cd_valor="TESTE",
                ds_valor=description,
            )
            with self.subTest(slug=slug):
                response = self.client.get(
                    reverse("core:dynamic_screen", args=[slug]),
                    {"q": "TESTE"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, description)

    def test_auxiliar_consulta_sem_filtro_por_codigo_descricao_e_sem_resultado(self):
        Especialidade = modelo_catalogo("especialidade")
        value = Especialidade.objects.create(
            cd_valor="CARDIO",
            ds_valor="Cardiologia",
        )
        route = reverse("core:global_auxiliar", args=["especialidade"])
        cases = (
            ({"q": str(value.pk)}, "Cardiologia"),
            ({"q": "CARDIO"}, "Cardiologia"),
            ({"q": "Cardiologia"}, "Cardiologia"),
        )
        response = self.client.get(route, {"consultar": "1"})
        displayed = min(Especialidade.objects.count(), 20)
        self.assertContains(response, f"{displayed} exibido(s)")
        for params, expected in cases:
            with self.subTest(params=params):
                response = self.client.get(route, params)
                self.assertContains(response, expected)
        empty_response = self.client.get(route, {"q": "INEXISTENTE"})
        self.assertContains(empty_response, "0 encontrado(s)")

    def test_exclusao_de_auxiliar_remove_registro(self):
        total_anterior = Plano.objects.count()
        value = Plano.objects.create(
            cd_valor="LOGICO",
            ds_valor="Plano Lógico",
            sn_ativo=True,
        )
        response = self.client.post(
            reverse("core:global_auxiliar", args=["plano"]),
            {
                f"delete_{value.pk}": "1",
                f"description_{value.pk}": value.ds_valor,
                f"group_{value.pk}": "",
                f"active_{value.pk}": "true",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Plano.objects.filter(pk=value.pk).exists())
        refreshed = self.client.get(
            reverse("core:global_auxiliar", args=["plano"]),
            {"consultar": "1"},
        )
        self.assertContains(refreshed, f"{total_anterior} encontrado(s)")
        self.assertNotContains(refreshed, "Plano Lógico")


class FrontendInteractionContractTests(SimpleTestCase):
    def test_class_confirma_exclusao_e_exibe_origem_do_campo(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        class_layout = (settings.BASE_DIR / "templates" / "base" / "class_layout.html").read_text(encoding="utf-8")
        fila = (settings.BASE_DIR / "templates" / "atendimento" / "_fila_classificacao_demanda.html").read_text(encoding="utf-8")
        self.assertIn("setupFormConfirmations", javascript)
        self.assertIn('form[data-confirm]', javascript)
        self.assertIn("data-confirm=", fila)
        self.assertIn("data-field-status", class_layout)

    def test_arvore_de_itens_exibe_conectores_e_reabre_secao_ancorada(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        template = (settings.BASE_DIR / "templates" / "core" / "system_screens.html").read_text(encoding="utf-8")
        self.assertIn(".navigation-tree-children::before", stylesheet)
        self.assertIn(".navigation-tree-branch", stylesheet)
        self.assertIn("border-left: 1px solid var(--line)", stylesheet)
        self.assertIn("border-top: 1px solid var(--line)", stylesheet)
        self.assertIn('id="module-items"', template)
        self.assertIn("const anchoredSection = window.location.hash", javascript)
        self.assertIn('anchoredSection.scrollIntoView({ block: "start" })', javascript)

    def test_dropdown_possui_um_unico_handler_de_abertura_por_mouse(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertEqual(javascript.count('document.addEventListener("pointerdown", function (event) {'), 1)
        click_handler = javascript.split(
            'document.addEventListener("click", function (event) {\n'
            '    const select = event.target.closest(".content select, .pep-standalone-main select")',
            1,
        )[1].split('document.addEventListener("submit"', 1)[0]
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
        self.assertIn('`${nameParts[0]} ${nameParts.at(-1)}`', javascript)
        self.assertIn("window.setTimeout", javascript)

    def test_autocomplete_nativo_e_desativado_globalmente(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('form.setAttribute("autocomplete", "off")', javascript)
        self.assertIn('field.setAttribute("autocomplete", `section-${section}-${fieldIndex} new-password`)', javascript)
        self.assertIn('field.setAttribute("aria-autocomplete", "none")', javascript)
        self.assertIn('field.setAttribute("data-lpignore", "true")', javascript)
        self.assertIn("shouldPreserveNativeAutocomplete", javascript)

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
        self.assertEqual(user_template.count("data-assignment-manager"), 3)
        self.assertIn("Empresas vinculadas", user_template)
        self.assertIn("Setores vinculados", user_template)

    def test_dropdown_recolhido_respeita_largura_do_conteudo(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("width: fit-content", stylesheet)
        self.assertIn("max-width: 100%", stylesheet)
        self.assertIn(".specialty-add-row[hidden]", stylesheet)

    def test_barra_de_status_exibe_label_de_negocio(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn('owner.tagName !== "FORM"', javascript)
        self.assertIn('owner.method?.toLowerCase() !== "get"', javascript)
        self.assertIn("fieldColumnAliases", javascript)
        self.assertIn('replace(/^new_/, "").replace(/_\\d+$/, "")', javascript)
        self.assertIn("`${normalizeFieldName(tableName)}.${normalizeFieldName(fieldName)}`", javascript)
        self.assertIn("businessLabel.trim()", javascript)

    def test_editor_suporta_opcoes_estruturadas_e_multiplos_campos(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "document-editor.js").read_text(encoding="utf-8")
        template = (settings.BASE_DIR / "templates" / "atendimento" / "modelos_documento.html").read_text(encoding="utf-8")
        self.assertIn("splitStructuredOptions", javascript)
        self.assertIn('field.type === "multiple-fields"', javascript)
        self.assertIn("data-source-value-field", javascript)
        self.assertIn('value="multiple-fields"', template)
        self.assertNotIn('value="query">Consulta do sistema', template)

    def test_tabela_vazia_inicia_com_linha_de_digitacao_e_lixeira_condicional(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("setupInitialEditableRows", javascript)
        self.assertIn("addEditableTableRow(form, false)", javascript)
        initial_rows = javascript.split("function setupInitialEditableRows()", 1)[1].split("function removeEditableTableRow", 1)[0]
        self.assertIn("hasLoadedRows", initial_rows)
        self.assertIn("if (hasLoadedRows) return", initial_rows)
        self.assertIn("hasSelectedPersistedRow", javascript)
        self.assertIn("hasLoadedRecord", javascript)
        self.assertIn("getSelectedRowActiveField", javascript)

    def test_consulta_de_tabela_libera_codigo_como_filtro(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        query_mode = javascript.split("function setQueryMode(enabled)", 1)[1].split("function clearFormFields", 1)[0]
        self.assertIn('field.removeAttribute("readonly")', query_mode)
        self.assertNotIn('field.closest("[data-editable-table]")', query_mode)

    def test_layout_nao_exibe_mensagem_superior_de_quantidade(self):
        layout = (settings.BASE_DIR / "templates" / "base" / "layout.html").read_text(encoding="utf-8")
        self.assertNotIn("current_query_message", layout)
        self.assertNotIn("query-result-message", layout)

    def test_pos_salvar_limpa_formulario_antes_da_consulta(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        startup = javascript.split('sessionStorage.getItem("celeris-open-query-after-save")', 1)[1]
        self.assertIn("clearFormFields(getPrimaryForm())", startup)
        self.assertIn("setQueryMode(true)", startup)

    def test_limpar_formulario_get_recarrega_tela_sem_resultados(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        clear_screen = javascript.split("function clearScreenData()", 1)[1].split("const savedTheme", 1)[0]
        self.assertIn('form.method?.toLowerCase() === "get"', clear_screen)
        self.assertIn("window.location.href = window.location.pathname", clear_screen)

    def test_novo_pela_barra_de_acoes_envia_retorno_da_tela_atual(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        new_action = javascript.split("const newAction = event.target.closest", 1)[1].split("const continueAction", 1)[0]
        self.assertIn('url.searchParams.set("return_to"', new_action)
        self.assertIn("window.location.pathname", new_action)

    def test_consulta_tabela_editavel_inclui_dropdown_com_valor(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        table_query = javascript.split("const queryValue = Array.from", 1)[1].split("window.location.href", 1)[0]
        self.assertIn('querySelectorAll("input:not([type=\'hidden\']), textarea, select")', table_query)
        self.assertIn("field.value.trim()", table_query)
        self.assertIn("clearCurrentFormState(form)", table_query)

    def test_toolbar_condiciona_senha_status_e_exclusao(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("hasLoadedRecord", javascript)
        self.assertIn("hasSelectedPersistedRow", javascript)
        self.assertIn("rowActiveField", javascript)
        self.assertIn("changePasswordButton.disabled = !document.body.dataset.passwordUrl || !hasLoadedRecord()", javascript)
        self.assertIn('toggleActiveButton.title === "Ativar" ?"check" : "ban"', javascript)

    def test_secoes_recolhidas_usam_layout_horizontal_exclusivo(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        provider_template = (settings.BASE_DIR / "templates" / "atendimento" / "cadastro_profissional.html").read_text(encoding="utf-8")
        self.assertIn("display: flex", stylesheet)
        self.assertIn(".form-section[open]", stylesheet)
        self.assertIn("setupFormSectionAccordion", javascript)
        self.assertEqual(provider_template.count('class="card form-section" data-provider-section="1" open'), 1)
        self.assertNotIn('data-provider-section="2" open', provider_template)

    def test_ordenacao_possui_indicadores_visuais(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("setupSortableTables", javascript)
        self.assertIn('currentOrdering.startsWith("-") ?"▼" : "▲"', javascript)
        self.assertIn(".sort-indicator", stylesheet)

    def test_edicao_inline_nao_adiciona_botao_editar_e_enter_navega(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertNotIn("setupEditableTableActions", javascript)
        self.assertNotIn("data-edit-row", javascript)
        self.assertIn('form[data-editable-table] input, form[data-editable-table] select', javascript)
        self.assertIn("focusEditableTableNextField(event.target", javascript)
        editable_enter = javascript.split('event.key === "Enter" && event.target.matches("form[data-editable-table]', 1)[1].split("return;", 1)[0]
        self.assertNotIn("submitPrimaryForm", editable_enter)

    def test_tabela_editavel_abre_consulta_com_uma_linha_de_filtro(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("resetEditableTableRows(form, false)", javascript)
        query_open = javascript.split('if (form.matches("[data-editable-table]")) {', 1)[1].split("setQueryMode(true)", 1)[0]
        self.assertIn("resetEditableTableRows(form, false)", query_open)

    def test_tabelas_editaveis_nao_abrem_em_modo_consulta_automaticamente(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        start_mode = javascript.split("function shouldStartInQueryMode()", 1)[1].split("renderTabs();", 1)[0]
        self.assertIn('document.body.dataset.startQuery === "true"', start_mode)
        self.assertIn('!document.querySelector(".content form[data-editable-table]")', start_mode)
        startup = javascript.rsplit("if (shouldStartInQueryMode()", 1)[1]
        self.assertIn("setQueryMode(true)", startup)

    def test_previa_da_nova_linha_de_icones_fica_centralizada(self):
        template = (settings.BASE_DIR / "templates" / "core" / "system_icons.html").read_text(encoding="utf-8")
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        new_row = template.split("<template data-table-new-row>", 1)[1]
        self.assertIn('<td class="td-icon"><span class="call-icon-preview', new_row)
        icon_cell = stylesheet.split(".td-icon {", 1)[1].split("}", 1)[0]
        self.assertIn("text-align: center", icon_cell)
        self.assertIn("vertical-align: middle", icon_cell)

    def test_estado_de_tabela_e_isolado_por_pagina_sem_criar_linhas_para_outros_ids(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        state_key = javascript.split("function getCurrentFormStateKey", 1)[1].split("function getFormStateFields", 1)[0]
        self.assertIn('form.matches("[data-editable-table]")', state_key)
        self.assertIn("`${window.location.pathname}${window.location.search}`", state_key)
        restore = javascript.split("function restoreCurrentFormState", 1)[1].split("function storeCurrentListPosition", 1)[0]
        self.assertIn("templateFieldNames", restore)
        self.assertIn("if (!templateFieldNames.has(field.name)) return counts", restore)

    def test_sanitizacao_svg_preserva_geometria_exibida_na_previa(self):
        from apps.atendimento.views import _sanitize_call_icon_svg
        from apps.core.views import _sanitize_system_icon_svg

        source = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" class="lucide lucide-calendar-days">'
            '<rect x="3" y="3" width="18" height="18" rx="2"/>'
            '<path d="M3 9h18"/></svg>'
        )
        for sanitize in (_sanitize_system_icon_svg, _sanitize_call_icon_svg):
            sanitized = sanitize(source)
            self.assertIn('<rect x="3" y="3" width="18" height="18" rx="2"></rect>', sanitized)
            self.assertIn('class="lucide lucide-calendar-days"', sanitized)

        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        preview_sanitizer = javascript.split("const allowedAttributes = new Set([", 1)[1].split("]);", 1)[0]
        self.assertIn('"width", "height"', preview_sanitizer)
        self.assertIn('"stroke-dasharray"', preview_sanitizer)

    def test_css_clinico_remove_importacoes_urls_e_propriedades_perigosas(self):
        from apps.atendimento.views import _css_documento_seguro

        sanitized = str(
            _css_documento_seguro(
                '@import url("https://exemplo.test/import.css");'
                '.seguro{color:#123456;background:url("https://exemplo.test/pixel");'
                'position:fixed;behavior:url(script.htc)}'
                '@page{margin:10mm}'
            )
        )
        self.assertNotIn("@import", sanitized)
        self.assertNotIn("url(", sanitized)
        self.assertNotIn("behavior", sanitized)
        self.assertIn("color:#123456", sanitized)
        self.assertIn("position:fixed", sanitized)
        self.assertIn("@page", sanitized)

    def test_scrollbar_tem_cores_do_tema(self):
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("scrollbar-color: var(--primary)", stylesheet)
        self.assertIn("*::-webkit-scrollbar-thumb", stylesheet)
        self.assertIn("linear-gradient(135deg, var(--primary), var(--primary-dark))", stylesheet)

    def test_tabelas_possuem_resize_manual_de_colunas(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("setupResizableTables", javascript)
        self.assertIn("column-resize-handle", javascript)
        self.assertIn("if (index >= headers.length - 1) return", javascript)
        self.assertIn("colgroup", javascript)
        self.assertIn("cursor: col-resize", stylesheet)
        self.assertIn("td:last-child", stylesheet)

    def test_ceps_e_cidades_usam_dropdowns_auxiliares(self):
        cep_template = (settings.BASE_DIR / "templates" / "core" / "global_ceps.html").read_text(encoding="utf-8")
        auxiliary_template = (settings.BASE_DIR / "templates" / "core" / "global_auxiliary_values.html").read_text(encoding="utf-8")
        self.assertIn('name="sg_estado_', cep_template)
        self.assertIn('name="cd_cidade_', cep_template)
        self.assertIn('data-cep-state-select', cep_template)
        self.assertIn('data-option-label-target="ds_cidade_', cep_template)
        self.assertIn('name="ds_cidade_', cep_template)
        self.assertIn('type="hidden"', cep_template)
        self.assertIn('tabela.ds_tabela == "cidade"', auxiliary_template)
        self.assertIn('name="group_', auxiliary_template)

    def test_pager_de_tabela_e_compacto_e_controlado_por_js(self):
        pager_template = (settings.BASE_DIR / "templates" / "components" / "table_pager.html").read_text(encoding="utf-8")
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("data-table-pager", pager_template)
        self.assertIn('data-nav-icon="arrow-left"', pager_template)
        self.assertIn('data-nav-icon="arrow-right"', pager_template)
        self.assertIn("table-pager-actions", pager_template)
        self.assertIn("min-height: var(--actionbar-height, 44px)", stylesheet)
        self.assertIn("updateTablePagerVisibility", javascript)
        self.assertIn(".content:has(form.table-card[data-editable-table])", stylesheet)

    def test_interface_preserva_scroll_e_esconde_acoes_inuteis(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("tableTop", javascript)
        self.assertIn("tableCard.scrollTop", javascript)
        self.assertIn("changePasswordButton.hidden", javascript)
        self.assertIn("toggleActiveButton.hidden", javascript)

    def test_topo_notificacoes_login_e_sessao(self):
        layout = (settings.BASE_DIR / "templates" / "base" / "layout.html").read_text(encoding="utf-8")
        login = (settings.BASE_DIR / "templates" / "accounts" / "login.html").read_text(encoding="utf-8")
        settings_file = (settings.BASE_DIR / "celeris" / "settings.py").read_text(encoding="utf-8")
        self.assertIn("data-notifications-clear", layout)
        self.assertIn("current_user_short_name", layout)
        self.assertIn("celeris-theme-user", login)
        self.assertIn("SESSION_COOKIE_AGE = 900", settings_file)

    def test_guias_usam_nome_curto_e_toolbar_mantem_caminho(self):
        context_processor = (settings.BASE_DIR / "apps" / "core" / "context_processors.py").read_text(encoding="utf-8")
        layout = (settings.BASE_DIR / "templates" / "base" / "layout.html").read_text(encoding="utf-8")
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("def _short_tab_title", context_processor)
        self.assertIn('data-tab-root-title="{{ current_tab_root_title }}"', layout)
        self.assertIn("document.body.dataset.tabRootTitle || document.body.dataset.tabTitle", javascript)

    def test_guias_persistem_url_com_query_e_campos_digitados(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        stylesheet = (settings.BASE_DIR / "static" / "css" / "celeris.css").read_text(encoding="utf-8")
        self.assertIn("`${window.location.pathname}${window.location.search}`", javascript)
        self.assertIn("celeris-form-state", javascript)
        self.assertIn("persistCurrentFormState", javascript)
        self.assertIn("restoreCurrentFormState", javascript)
        self.assertIn("max-width: 240px", stylesheet)

    def test_menu_lateral_ordena_telas_antes_de_submenus(self):
        context_processor = (settings.BASE_DIR / "apps" / "core" / "context_processors.py").read_text(encoding="utf-8")
        self.assertIn('.order_by("module__order", "module__title", "order", "title")', context_processor)
        self.assertNotIn('bool(item[1].get("children"))', context_processor)

class CatalogosIniciaisMigrationTests(TestCase):
    def test_remove_dados_artificiais_e_preserva_catalogos_essenciais(self):
        valor_teste = Sexo.objects.create(
            cd_valor="TESTE_999",
            ds_valor="SEXO TESTE 999",
            sn_ativo=True,
        )
        cep_teste = Cep.objects.create(
            nr_cep="01999999",
            sg_estado="SP",
            cd_cidade="SAO_PAULO",
            ds_cidade="SÃO PAULO",
            tp_logradouro="RUA",
            ds_logradouro="RUA TESTE 999",
            ds_bairro="BAIRRO TESTE 999",
            sn_ativo=True,
        )

        valor_teste.delete()
        cep_teste.delete()

        self.assertFalse(Sexo.objects.filter(pk=valor_teste.pk).exists())
        self.assertFalse(Cep.objects.filter(pk=cep_teste.pk).exists())
        self.assertTrue(Sexo.objects.filter(cd_valor="N").exists())
        self.assertEqual(Sexo.objects.get(cd_valor="N").ds_valor, "NÃO INFORMADO")
        self.assertFalse(User.objects.filter(username__in=["RECEPCAO", "ENFERMAGEM", "MEDICO"]).exists())

    def test_mescla_grupos_legados_sem_perder_filhos(self):
        module = Module.objects.create(code="TESTE_DUPLICIDADE", title="Teste", order=999)
        canonical = ScreenDefinition.objects.create(
            module=module,
            title="Tabelas",
            slug="teste-duplicidade-tabelas",
            screen_type=ScreenDefinition.TYPE_GROUP,
            order=10,
        )
        duplicate = ScreenDefinition.objects.create(
            module=module,
            title="TABELAS",
            slug="teste-duplicidade-tabelas-duplicada",
            screen_type=ScreenDefinition.TYPE_GROUP,
            order=20,
        )
        child = ScreenDefinition.objects.create(
            module=module,
            parent=duplicate,
            parent_label=duplicate.title,
            title="Item atual",
            slug="teste-duplicidade-item-atual",
            access_key="teste-duplicidade-item-atual",
        )
        legacy = ScreenDefinition.objects.create(
            module=module,
            parent_label="tAbElAs",
            title="Item legado",
            slug="teste-duplicidade-item-legado",
            access_key="teste-duplicidade-item-legado",
        )

        migration = importlib.import_module("apps.core.operacoes_migracao.operacao_0037")
        migration.mesclar_grupos_navegacao(django_apps, None)

        duplicate.refresh_from_db()
        child.refresh_from_db()
        legacy.refresh_from_db()
        self.assertFalse(duplicate.active)
        self.assertEqual(child.parent_id, canonical.pk)
        self.assertEqual(legacy.parent_id, canonical.pk)


class NavigationIntegrationTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=198, nm_empresa="Navegação", sn_ativo=True)
        self.user = User.objects.create_user(username="TINAVEGACAO", password="123456", is_active=True)
        self.user.groups.add(Group.objects.get_or_create(name="TI")[0])
        UsuarioEmpresa.objects.create(usuario=self.user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.cd_empresa
        session.save()

    def test_configuracao_de_modulos_e_telas_carrega(self):
        response = self.client.get(reverse("core:system_screens"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Módulos e Telas")
        self.assertContains(response, 'data-start-query="true"')
        self.assertContains(response, "1. Módulo")
        self.assertContains(response, "2. Itens")
        self.assertFalse(response.context["current_can_remove"])

    def test_menu_e_carregado_do_banco_mesmo_sem_grupos(self):
        from apps.core.context_processors import _database_navigation_menu

        module = Module.objects.create(
            code="MODULO_SOMENTE_BANCO",
            title="Módulo somente banco",
            order=905,
        )
        ScreenDefinition.objects.create(
            module=module,
            title="Tela raiz",
            slug="tela-raiz-somente-banco",
            access_key="teste:tela-raiz-somente-banco",
        )

        database_menu = _database_navigation_menu()
        configured_module = next(item for item in database_menu if item["code"] == module.code)
        self.assertEqual([item["label"] for item in configured_module["items"]], ["Tela raiz"])

    def test_modulos_estruturais_permite_apenas_atualizar_ordem(self):
        module = Module.objects.get(code="GLOBAL")
        self.assertTrue(module.is_system)
        nova_ordem = module.order + 7

        save_response = self.client.post(
            reverse("core:system_screens"),
            {
                "module_id": module.pk,
                "code": module.code,
                "title": "Global alterado",
                "icon": module.icon,
                "order": nova_ordem,
                "active": "True",
            },
        )
        self.assertEqual(save_response.status_code, 302)
        module.refresh_from_db()
        self.assertEqual(module.title, "Global")
        self.assertEqual(module.order, nova_ordem)
        self.assertEqual(
            self.client.post(
                reverse("core:system_module_toggle_active", args=[module.pk])
            ).status_code,
            403,
        )

        screen = module.screens.filter(active=True).first()
        self.assertIsNotNone(screen)
        self.assertEqual(
            self.client.post(
                reverse("core:system_navigation_reorder"),
                {"node": screen.pk, "parent": "", "order": [screen.pk]},
            ).status_code,
            200,
        )

        loaded = self.client.get(reverse("core:system_screens"), {"module": module.pk})
        self.assertContains(loaded, "Estrutural")
        self.assertTrue(loaded.context["current_can_save"])

    def test_configuracao_de_modulos_consulta_cria_e_desativa(self):
        module = Module.objects.create(
            code="MODULO_TESTE_CONFIG",
            title="Módulo de teste configurável",
            icon="grid",
            order=910,
            active=True,
        )
        query_response = self.client.get(
            reverse("core:system_screens"),
            {"consultar": "1", "title": "teste configurável"},
        )
        self.assertRedirects(
            query_response,
            f"{reverse('core:system_screens')}?module={module.pk}&origem=consulta",
            fetch_redirect_response=False,
        )
        loaded = self.client.get(query_response.url)
        self.assertContains(loaded, 'value="Módulo de teste configurável"')
        self.assertContains(loaded, "Item 1 de 1")

        create_response = self.client.post(
            reverse("core:system_screens"),
            {
                "code": "NOVO_MODULO_CONFIG",
                "title": "Novo módulo",
                "icon": "boxes",
                "order": 920,
                "active": "True",
            },
        )
        created = Module.objects.get(code="NOVO_MODULO_CONFIG")
        self.assertRedirects(
            create_response,
            f"{reverse('core:system_screens')}?module={created.pk}",
            fetch_redirect_response=False,
        )

        toggle_response = self.client.post(reverse("core:system_module_toggle_active", args=[created.pk]))
        self.assertRedirects(
            toggle_response,
            f"{reverse('core:system_screens')}?module={created.pk}",
            fetch_redirect_response=False,
        )
        created.refresh_from_db()
        self.assertFalse(created.active)

    def test_salvar_modulo_preserva_indices_e_navegacao_da_consulta(self):
        modules = [
            Module.objects.create(
                code=f"MODULO_FLUXO_{index}",
                title=f"Fluxo persistido {index}",
                icon="grid",
                order=930 + index,
            )
            for index in range(1, 4)
        ]
        query_response = self.client.get(
            reverse("core:system_screens"),
            {"consultar": "1", "title": "Fluxo persistido"},
        )
        self.assertEqual(query_response.status_code, 302)

        current = modules[1]
        edit_url = (
            f"{reverse('core:system_screens')}?module={current.pk}&origem=consulta"
        )
        save_response = self.client.post(
            edit_url,
            {
                "module_id": current.pk,
                "code": current.code,
                "title": "Fluxo persistido 2 atualizado",
                "icon": current.icon,
                "order": current.order,
                "active": "True",
            },
        )
        self.assertRedirects(
            save_response,
            edit_url,
            fetch_redirect_response=False,
        )

        loaded = self.client.get(save_response.url)
        self.assertEqual(loaded.context["current_record_status"], "Item 2 de 3")
        self.assertTrue(loaded.context["current_first_url"])
        self.assertTrue(loaded.context["current_previous_url"])
        self.assertTrue(loaded.context["current_next_url"])
        self.assertTrue(loaded.context["current_last_url"])

    def test_nome_do_modulo_preserva_caixa_acentos_e_caracteres_especiais(self):
        response = self.client.post(
            reverse("core:system_screens"),
            {
                "code": "MODULO_NOME_LIVRE",
                "title": "Módulo Ágil: caixa Mista & especial!",
                "icon": "grid",
                "order": 925,
                "active": "True",
            },
        )
        self.assertEqual(response.status_code, 302)
        module = Module.objects.get(code="MODULO_NOME_LIVRE")
        self.assertEqual(module.title, "Módulo Ágil: caixa Mista & especial!")

    def test_catalogo_de_icones_alimenta_seletor_com_previa_e_nome(self):
        icon = IconeSistema.objects.create(
            cd_icone="icone-personalizado",
            nm_icone="Ícone personalizado",
            ds_svg='<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>',
        )
        table_response = self.client.get(reverse("core:system_icons"), {"consultar": "1"})
        self.assertEqual(table_response.status_code, 200)
        self.assertContains(table_response, 'data-table="icone_sistema"')
        self.assertContains(table_response, icon.nm_icone)

        form_response = self.client.get(reverse("core:system_screens"), {"novo": "1"})
        self.assertContains(form_response, 'data-system-icon-preview')
        self.assertContains(form_response, 'data-icon-key="icone-personalizado"')
        self.assertContains(form_response, "Ícone personalizado")

    def test_configuracao_de_item_abre_subtela_com_roles_multiplos(self):
        module = Module.objects.create(code="MODULO_SUBTELA", title="Módulo subtela", icon="grid", order=927)
        Group.objects.get_or_create(name="Recepcionista")
        response = self.client.get(reverse("core:system_screen_new"), {"module": module.pk})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["current_can_query"])
        self.assertEqual(response.context["current_close_mode"], "back")
        self.assertEqual(response.context["current_tab_key"], reverse("core:system_screens"))
        self.assertEqual(
            response.context["current_close_url"],
            f"{reverse('core:system_screens')}?module={module.pk}#module-items",
        )
        self.assertContains(response, 'data-nav-icon="corner-up-left"')
        self.assertContains(response, 'data-subscreen-toolbar="true"')
        self.assertContains(response, 'type="checkbox" name="roles" value="TI"')
        self.assertContains(response, 'type="checkbox" name="roles" value="Recepcionista"')

        saved = self.client.post(
            reverse("core:system_screen_new"),
            {
                "module": module.pk,
                "parent": "",
                "title": "Tela com roles",
                "slug": "tela-com-roles-teste",
                "navigation_url": "",
                "access_key": "",
                "icon": "grid",
                "roles": ["TI", "Recepcionista"],
                "screen_type": ScreenDefinition.TYPE_FORM,
                "parent_label": "",
                "table_name": "",
                "description": "",
                "allow_query": "on",
                "allow_insert": "on",
                "allow_update": "on",
                "active": "on",
                "order": 10,
            },
        )
        self.assertEqual(saved.status_code, 302)
        self.assertEqual(
            ScreenDefinition.objects.get(slug="tela-com-roles-teste").roles,
            ["TI", "Recepcionista"],
        )

    def test_arvore_usa_marcadores_para_itens_sem_icone(self):
        module = Module.objects.create(code="MODULO_MARCADORES", title="Marcadores", order=930)
        group = ScreenDefinition.objects.create(
            module=module,
            title="Grupo sem ícone",
            slug="grupo-sem-icone-teste",
            screen_type=ScreenDefinition.TYPE_GROUP,
        )
        ScreenDefinition.objects.create(
            module=module,
            parent=group,
            title="Tela sem ícone",
            slug="tela-sem-icone-teste",
        )
        response = self.client.get(reverse("core:system_screens"), {"module": module.pk})
        self.assertContains(response, "navigation-tree-marker is-group")
        self.assertContains(response, "navigation-tree-marker is-screen")

    def test_menu_lateral_nao_repete_grupos_equivalentes(self):
        response = self.client.get(reverse("core:home"))
        modules = response.context["modules_menu"]
        self.assertFalse(any(module["code"] == "CADASTROS" for module in modules))
        atendimento = next(module for module in modules if module["code"] == "ATENDIMENTO")
        cadastros = next(item for item in atendimento["items"] if item["label"] == "Cadastros")
        ti = next(module for module in modules if module["code"] == "TI")
        self.assertFalse(any(item["label"].casefold() == "tabelas" for item in cadastros["children"]))
        self.assertEqual(
            [item["label"] for item in cadastros["children"]],
            ["Pacientes", "Prestadores", "Convênios", "Planos", "Procedimentos", "Salas e Recursos"],
        )
        self.assertFalse(
            any(item["label"].casefold().startswith("gerenciamento de usu") for item in ti["items"])
        )
        self.assertEqual(
            sum(item["label"].casefold() == "usuários e acessos" for item in ti["items"]),
            1,
        )
        global_module = next(module for module in modules if module["code"] == "GLOBAL")
        system_config = next(item for item in global_module["items"] if item["label"] == "Configuração do Sistema")
        modules_and_screens = next(item for item in system_config["children"] if item["label"] == "Módulos e Telas")
        icons_screen = ScreenDefinition.objects.get(access_key="core:system_icons")
        self.assertTrue(icons_screen.papeis.filter(papel__grupo__user=self.user).exists())
        self.assertIn("core:system_icons", user_access_keys(self.user))
        self.assertEqual(
            [item["label"] for item in modules_and_screens["children"]],
            ["Configurar", "Ícones"],
            system_config,
        )
