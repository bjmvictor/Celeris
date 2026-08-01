import importlib

from django.apps import apps as django_apps
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Empresa, User, UsuarioEmpresa
from apps.atendimento.forms import PacienteForm

from .models import (
    Cep,
    ConfiguracaoCampoFormulario,
    Module,
    ScreenDefinition,
    TabelaAuxiliarGlobal,
    TipoPrestadorConselho,
    ValorAuxiliarGlobal,
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
            table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
                ds_tabela=table_name,
                defaults={"ds_descricao": description, "sn_ativo": True},
            )
            ValorAuxiliarGlobal.objects.create(
                cd_tabela_auxiliar_global=table,
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
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela="especialidade",
            defaults={"ds_descricao": "Especialidades", "sn_ativo": True},
        )
        value = ValorAuxiliarGlobal.objects.create(
            cd_tabela_auxiliar_global=table,
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
        self.assertContains(response, "20 exibido(s)")
        for params, expected in cases:
            with self.subTest(params=params):
                response = self.client.get(route, params)
                self.assertContains(response, expected)
        empty_response = self.client.get(route, {"q": "INEXISTENTE"})
        self.assertContains(empty_response, "0 encontrado(s)")

    def test_exclusao_de_auxiliar_remove_registro(self):
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela="plano",
            defaults={"ds_descricao": "Planos", "sn_ativo": True},
        )
        value = ValorAuxiliarGlobal.objects.create(
            cd_tabela_auxiliar_global=table,
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
        self.assertFalse(ValorAuxiliarGlobal.objects.filter(pk=value.pk).exists())
        refreshed = self.client.get(
            reverse("core:global_auxiliar", args=["plano"]),
            {"consultar": "1"},
        )
        self.assertContains(refreshed, "0 encontrado(s)")
        self.assertNotContains(refreshed, "Plano Lógico")


class FrontendInteractionContractTests(SimpleTestCase):
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
        self.assertIn('warNameField.value = nameParts[0] || ""', javascript)

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
        self.assertIn('owner?.tagName === "FORM"', javascript)
        self.assertIn('owner.method?.toLowerCase() !== "get"', javascript)
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
        tabela, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela="sexo",
            defaults={"ds_descricao": "Cadastro de teste", "sn_ativo": True},
        )
        valor_teste = ValorAuxiliarGlobal.objects.create(
            cd_tabela_auxiliar_global=tabela,
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

        migration = importlib.import_module("apps.core.operacoes_migracao.operacao_0036")
        migration.normalizar_catalogos(django_apps, None)

        self.assertFalse(ValorAuxiliarGlobal.objects.filter(pk=valor_teste.pk).exists())
        self.assertFalse(Cep.objects.filter(pk=cep_teste.pk).exists())
        tabela.refresh_from_db()
        self.assertEqual(tabela.ds_descricao, "Sexos")
        self.assertEqual(tabela.valores.get(cd_valor="N").ds_valor, "Não informado")
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
        cadastros = next(module for module in modules if module["code"] == "CADASTROS")
        ti = next(module for module in modules if module["code"] == "TI")
        self.assertEqual(
            sum(item["label"].casefold() == "tabelas" for item in cadastros["items"]),
            1,
        )
        self.assertFalse(
            any(item["label"].casefold().startswith("gerenciamento de usu") for item in ti["items"])
        )
        self.assertEqual(
            sum(item["label"].casefold() == "usuários e acessos" for item in ti["items"]),
            1,
        )
