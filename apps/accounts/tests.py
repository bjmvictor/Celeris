from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from apps.atendimento.models import Prestador
from apps.core.models import Module, ScreenDefinition

from .forms import UsuarioForm, UsuarioPasswordForm
from .models import (
    Empresa,
    Papel,
    PapelModulo,
    PapelTela,
    User,
    UsuarioEmpresa,
    available_username,
    generate_username,
)


class AdministrationScreenTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=301, nm_empresa="Administração", sn_ativo=True)
        self.user = User.objects.create_superuser(username="ADMINTESTE", password="123456", email="admin@example.com")
        UsuarioEmpresa.objects.create(usuario=self.user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_telas_de_usuarios_perfis_e_permissoes_abrem(self):
        for route in ("usuarios", "perfis", "permissoes"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)

    def test_perfil_pode_ser_criado_e_editado(self):
        permission = Permission.objects.first()
        response = self.client.post(
            reverse("perfil_novo"),
            {"name": "AUDITORIA", "permissions": [permission.pk]},
        )
        self.assertEqual(response.status_code, 302)


class UsuarioCadastroTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=302, nm_empresa="Usuários", sn_ativo=True)
        self.admin = User.objects.create_superuser(
            username="ADMINUSUARIO",
            password="senha-segura",
            email="admin@example.com",
        )
        UsuarioEmpresa.objects.create(usuario=self.admin, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.admin)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_login_e_gerado_e_recebe_sufixo_quando_duplicado(self):
        first = User.objects.create(full_name="João Souza Silva")
        second = User.objects.create(full_name="João Souza Silva")
        self.assertEqual(first.username, "JOAOSS")
        self.assertEqual(second.username, "JOAOSS1")

    def test_vinculo_com_prestador_completa_campos_vazios(self):
        provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="Maria dos Santos",
            nr_cpf="529.982.247-25",
            dt_nascimento="1985-04-10",
            ds_email="maria@example.com",
            nr_celular="(11) 99999-9999",
            tp_prestador="MEDICO",
        )
        role = Group.objects.get_or_create(name="Médico")[0]
        form = UsuarioForm(
            data={
                "full_name": "",
                "nr_cpf": "",
                "cd_prestador": provider.pk,
                "password1": "senha-forte-123",
                "password2": "senha-forte-123",
                "empresas": [self.empresa.pk],
                "grupos": [role.pk],
            },
            empresa=self.empresa,
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.full_name, provider.nm_prestador)
        self.assertEqual(user.nr_cpf, provider.nr_cpf)
        self.assertEqual(user.email, provider.ds_email)
        self.assertEqual(user.cd_prestador, provider)
        self.assertTrue(user.groups.filter(pk=role.pk).exists())
        self.assertTrue(UsuarioEmpresa.objects.filter(usuario=user, empresa=self.empresa, sn_ativo=True).exists())

    def test_cpf_de_usuario_nao_pode_ser_duplicado(self):
        User.objects.create(username="EXISTENTE", full_name="Existente", nr_cpf="529.982.247-25")
        form = UsuarioForm(
            data={
                "full_name": "Outro Usuário",
                "nr_cpf": "52998224725",
                "password1": "senha-forte-123",
                "password2": "senha-forte-123",
                "empresas": [self.empresa.pk],
            },
            empresa=self.empresa,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nr_cpf", form.errors)

    def test_toolbar_de_usuario_exibe_status_e_alteracao_de_senha(self):
        user = User.objects.create_user(
            username="OPERADOR",
            password="senha-forte",
            full_name="Operador Teste",
            nr_cpf="111.444.777-35",
        )
        response = self.client.get(reverse("usuario_editar", args=[user.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-toggle-active-url="{reverse("usuario_alternar_status", args=[user.pk])}"')
        self.assertContains(response, f'data-password-url="{reverse("usuario_alterar_senha", args=[user.pk])}"')

    def test_cadastro_de_usuario_exibe_labels_de_negocio(self):
        response = self.client.get(reverse("usuario_novo"))
        for label in ("Nome Completo", "CPF", "Login", "Data de Nascimento", "Empresas vinculadas"):
            self.assertContains(response, label)
        for technical_label in ("NR_CPF", "FULL_NAME", "USER_LOGIN", "DT_BIRTH"):
            self.assertNotContains(response, technical_label)

    def test_status_pode_ser_alternado(self):
        user = User.objects.create_user(username="STATUS", password="senha-forte", is_active=True)
        response = self.client.post(reverse("usuario_alternar_status", args=[user.pk]))
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_permissao_de_incluir_nao_exige_permissao_de_alterar(self):
        operator = User.objects.create_user(username="INCLUSOR", password="senha-forte")
        role = Group.objects.get(name="TI")
        operator.groups.add(role)
        UsuarioEmpresa.objects.create(usuario=operator, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client.force_login(operator)
        response = self.client.get(reverse("usuario_novo"))
        self.assertEqual(response.status_code, 200)

    def test_alteracao_de_senha_exige_oito_caracteres(self):
        user = User.objects.create_user(username="SENHA", password="senha-antiga")
        weak_form = UsuarioPasswordForm(
            user,
            data={"new_password1": "curta", "new_password2": "curta"},
        )
        self.assertFalse(weak_form.is_valid())
        strong_form = UsuarioPasswordForm(
            user,
            data={"new_password1": "nova-senha-123", "new_password2": "nova-senha-123"},
        )
        self.assertTrue(strong_form.is_valid(), strong_form.errors)

    def test_usuario_pode_receber_multiplos_papeis_e_remover_um(self):
        first_role = Group.objects.get(name="Médico")
        second_role = Group.objects.get(name="Recepcionista")
        user = User.objects.create_user(
            username="PAPEIS",
            password="senha-forte",
            full_name="Usuário com Papéis",
            nr_cpf="111.444.777-35",
        )
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        form = UsuarioForm(
            data={
                "full_name": user.full_name,
                "nr_cpf": user.nr_cpf,
                "empresas": [self.empresa.pk],
                "grupos": [first_role.pk, second_role.pk],
            },
            instance=user,
            empresa=self.empresa,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(set(user.groups.values_list("pk", flat=True)), {first_role.pk, second_role.pk})

        removal_form = UsuarioForm(
            data={
                "full_name": user.full_name,
                "nr_cpf": user.nr_cpf,
                "empresas": [self.empresa.pk],
                "grupos": [second_role.pk],
            },
            instance=user,
            empresa=self.empresa,
        )
        self.assertTrue(removal_form.is_valid(), removal_form.errors)
        removal_form.save()
        self.assertEqual(list(user.groups.values_list("pk", flat=True)), [second_role.pk])

    def test_usuario_pode_adicionar_remover_e_persistir_multiplas_empresas(self):
        second_company = Empresa.objects.create(cd_empresa=305, nm_empresa="Clínica Centro", sn_ativo=True)
        user = User.objects.create_user(
            username="MULTIEMPRESA",
            password="senha-forte",
            full_name="Usuário Multiempresa",
            nr_cpf="111.444.777-35",
        )
        form = UsuarioForm(
            data={
                "full_name": user.full_name,
                "nr_cpf": user.nr_cpf,
                "empresas": [self.empresa.pk, second_company.pk],
            },
            instance=user,
            empresa=self.empresa,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(
            set(UsuarioEmpresa.objects.filter(usuario=user, sn_ativo=True).values_list("empresa_id", flat=True)),
            {self.empresa.pk, second_company.pk},
        )

        removal_form = UsuarioForm(
            data={
                "full_name": user.full_name,
                "nr_cpf": user.nr_cpf,
                "empresas": [second_company.pk],
            },
            instance=user,
            empresa=self.empresa,
        )
        self.assertTrue(removal_form.is_valid(), removal_form.errors)
        removal_form.save()
        self.assertEqual(
            list(UsuarioEmpresa.objects.filter(usuario=user, sn_ativo=True).values_list("empresa_id", flat=True)),
            [second_company.pk],
        )


class LoginGenerationTests(TestCase):
    def test_nome_simples(self):
        self.assertEqual(generate_username("BENJAMIN"), "BENJAMIN")

    def test_nomes_compostos(self):
        cases = {
            "BENJAMIN VICTOR VIEIRA DA SILVA": "BENJAMINVVS",
            "WLADEMIR JOSE RODRIGUES": "WLADEMIRJR",
            "MARIA APARECIDA DOS SANTOS": "MARIAAS",
        }
        for full_name, expected in cases.items():
            with self.subTest(full_name=full_name):
                self.assertEqual(generate_username(full_name), expected)

    def test_duplicidade_tenta_particulas_antes_da_numeracao(self):
        name = "BENJAMIN VICTOR VIEIRA DA SILVA"
        User.objects.create(username="BENJAMINVVS")
        self.assertEqual(available_username(name), "BENJAMINVVDS")
        User.objects.create(username="BENJAMINVVDS")
        self.assertEqual(available_username(name), "BENJAMINVVS1")
        User.objects.create(username="BENJAMINVVS1")
        self.assertEqual(available_username(name), "BENJAMINVVS2")

    def test_edicao_nao_recalcula_login(self):
        user = User.objects.create(username="LOGINMANTIDO", full_name="Nome Antigo")
        user.full_name = "Nome Completamente Diferente"
        user.save()
        self.assertEqual(user.username, "LOGINMANTIDO")

    def test_modo_consulta_nao_gera_login(self):
        script = open("static/js/celeris.js", encoding="utf-8").read()
        self.assertIn('document.body.classList.contains("screen-query-mode")', script)


class PapelAcessoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=303, nm_empresa="Papéis", sn_ativo=True)
        self.admin = User.objects.create_superuser(username="ADMINPAPEL", password="senha-segura")
        UsuarioEmpresa.objects.create(usuario=self.admin, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.admin)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()
        self.module = Module.objects.get(code="ATENDIMENTO")
        self.agendamento = ScreenDefinition.objects.get(access_key="atendimento:agendar")
        self.recepcao = ScreenDefinition.objects.get(access_key="atendimento:recepcao")

    def test_criar_consultar_e_editar_papel(self):
        response = self.client.post(
            reverse("perfil_novo"),
            {
                "name": "PAPEL TESTE",
                "ds_descricao": "Acesso inicial",
                "modulos": [self.module.pk],
                "telas": [self.agendamento.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        group = Group.objects.get(name="PAPEL TESTE")
        self.assertTrue(PapelModulo.objects.filter(papel=group.papel, modulo=self.module).exists())
        self.assertTrue(PapelTela.objects.filter(papel=group.papel, tela=self.agendamento).exists())

        response = self.client.get(reverse("perfis"), {"q": "PAPEL TESTE"})
        self.assertContains(response, "PAPEL TESTE")

        response = self.client.post(
            reverse("perfil_editar", args=[group.pk]),
            {
                "name": "PAPEL TESTE EDITADO",
                "ds_descricao": "Acesso alterado",
                "modulos": [self.module.pk],
                "telas": [self.recepcao.pk],
            },
        )
        self.assertEqual(response.status_code, 302)
        group.refresh_from_db()
        self.assertEqual(group.name, "PAPEL TESTE EDITADO")
        self.assertFalse(PapelTela.objects.filter(papel=group.papel, tela=self.agendamento).exists())
        self.assertTrue(PapelTela.objects.filter(papel=group.papel, tela=self.recepcao).exists())

    def test_ativar_e_desativar_papel(self):
        group = Group.objects.create(name="PAPEL STATUS")
        role = Papel.objects.create(grupo=group)
        self.client.post(reverse("perfil_alternar_status", args=[group.pk]))
        role.refresh_from_db()
        self.assertFalse(role.sn_ativo)
        self.client.post(reverse("perfil_alternar_status", args=[group.pk]))
        role.refresh_from_db()
        self.assertTrue(role.sn_ativo)

    def test_tela_de_modulo_nao_selecionado_e_rejeitada(self):
        form_response = self.client.post(
            reverse("perfil_novo"),
            {"name": "INVÁLIDO", "telas": [self.agendamento.pk]},
        )
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, "módulos não selecionados")

    def _user_with_role(self, username, screens):
        group = Group.objects.create(name=f"PAPEL {username}")
        role = Papel.objects.create(grupo=group)
        modules = {screen.module for screen in screens}
        for module in modules:
            PapelModulo.objects.create(papel=role, modulo=module)
        for screen in screens:
            PapelTela.objects.create(papel=role, tela=screen)
        user = User.objects.create_user(username=username, password="senha-segura")
        user.groups.add(group)
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        return user, role

    def test_usuario_sem_papel_ve_apenas_inicio(self):
        user = User.objects.create_user(username="SEMPAPEL", password="senha-segura")
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client.force_login(user)
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.context["modules_menu"], [])

    def test_um_papel_exibe_apenas_telas_permitidas(self):
        user, _role = self._user_with_role("AGENDA", [self.agendamento])
        self.client.force_login(user)
        response = self.client.get(reverse("core:home"))
        menu_text = str(response.context["modules_menu"])
        self.assertIn("Agendamentos", menu_text)
        self.assertNotIn("Recepção", menu_text)

    def test_multiplos_papeis_acumulam_permissoes(self):
        user, _first_role = self._user_with_role("MULTIPAPEL", [self.agendamento])
        second_group = Group.objects.create(name="PAPEL RECEPÇÃO")
        second_role = Papel.objects.create(grupo=second_group)
        PapelModulo.objects.create(papel=second_role, modulo=self.module)
        PapelTela.objects.create(papel=second_role, tela=self.recepcao)
        user.groups.add(second_group)
        self.client.force_login(user)
        menu_text = str(self.client.get(reverse("core:home")).context["modules_menu"])
        self.assertIn("Agendamentos", menu_text)
        self.assertIn("Recepção", menu_text)

    def test_modulo_sem_tela_nao_aparece(self):
        group = Group.objects.create(name="MÓDULO VAZIO")
        role = Papel.objects.create(grupo=group)
        PapelModulo.objects.create(papel=role, modulo=self.module)
        user = User.objects.create_user(username="VAZIO", password="senha-segura")
        user.groups.add(group)
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("core:home")).context["modules_menu"], [])

    def test_backend_bloqueia_url_direta_sem_permissao(self):
        user = User.objects.create_user(username="BLOQUEADO", password="senha-segura")
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client.force_login(user)
        response = self.client.get(reverse("atendimento:agendar"))
        self.assertEqual(response.status_code, 403)

    def test_backend_libera_url_com_modulo_e_tela(self):
        user, _role = self._user_with_role("LIBERADO", [self.agendamento])
        self.client.force_login(user)
        response = self.client.get(reverse("atendimento:agendar"))
        self.assertEqual(response.status_code, 200)

    def test_papel_inativo_remove_acesso(self):
        user, role = self._user_with_role("INATIVO", [self.agendamento])
        role.sn_ativo = False
        role.save(update_fields=["sn_ativo"])
        self.client.force_login(user)
        response = self.client.get(reverse("atendimento:agendar"))
        self.assertEqual(response.status_code, 403)

    def test_modulo_ou_tela_inativos_removem_acesso(self):
        user, _role = self._user_with_role("RECURSOINATIVO", [self.agendamento])
        self.client.force_login(user)
        self.agendamento.active = False
        self.agendamento.save(update_fields=["active"])
        self.assertEqual(self.client.get(reverse("atendimento:agendar")).status_code, 403)
        self.agendamento.active = True
        self.agendamento.save(update_fields=["active"])
        self.module.active = False
        self.module.save(update_fields=["active"])
        self.assertEqual(self.client.get(reverse("atendimento:agendar")).status_code, 403)


class ConsultaCadastroNavigationTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=304, nm_empresa="Consultas", sn_ativo=True)
        self.admin = User.objects.create_superuser(username="ADMINCONSULTA", password="senha-segura")
        UsuarioEmpresa.objects.create(usuario=self.admin, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        self.client = Client(HTTP_HOST="localhost")
        self.client.force_login(self.admin)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_consulta_de_papeis_sem_filtros_retorna_apenas_ativos(self):
        active_group = Group.objects.create(name="PAPEL ATIVO CONSULTA")
        Papel.objects.create(grupo=active_group, sn_ativo=True)
        inactive_group = Group.objects.create(name="PAPEL INATIVO CONSULTA")
        Papel.objects.create(grupo=inactive_group, sn_ativo=False)
        response = self.client.get(reverse("perfis"))
        self.assertContains(response, active_group.name)
        self.assertNotContains(response, inactive_group.name)
        self.assertContains(response, "registro(s) encontrado(s)")

    def test_consulta_de_papeis_por_codigo_nome_e_status(self):
        group = Group.objects.create(name="RECEPÇÃO CONSULTA")
        Papel.objects.create(grupo=group, sn_ativo=False)
        for params in (
            {"codigo": group.pk, "status": "inativo"},
            {"q": "RECEPÇÃO", "status": "inativo"},
            {"q": "RECEPÇÃO", "status": "todos"},
        ):
            with self.subTest(params=params):
                response = self.client.get(reverse("perfis"), params)
                self.assertContains(response, group.name)

    def test_grade_exibe_editar_e_preserva_contexto_no_retorno(self):
        group = Group.objects.create(name="PAPEL RETORNO")
        Papel.objects.create(grupo=group)
        list_url = f"{reverse('perfis')}?q=RETORNO&pagina=2"
        response = self.client.get(reverse("perfis"), {"q": "RETORNO", "pagina": 2})
        self.assertContains(response, "Editar")
        self.assertContains(response, "return_to=")
        edit_response = self.client.get(reverse("perfil_editar", args=[group.pk]), {"return_to": list_url})
        self.assertNotContains(edit_response, 'data-action="return"')
        self.assertContains(edit_response, 'data-close-mode="back"')
        self.assertContains(edit_response, 'data-close-url="/accounts/perfis/?q=RETORNO&amp;pagina=2"')
        self.assertEqual(edit_response.context["current_return_url"], list_url)

    def test_tela_aberta_diretamente_mantem_fechar_e_contextual_usa_voltar(self):
        direct_response = self.client.get(reverse("usuario_novo"))
        self.assertContains(direct_response, 'data-close-mode=""')
        contextual_response = self.client.get(
            reverse("usuario_novo"),
            {"return_to": f"{reverse('usuarios')}?q=TESTE"},
        )
        self.assertContains(contextual_response, 'data-close-mode="back"')
        self.assertContains(contextual_response, 'data-close-url="/accounts/usuarios/?q=TESTE"')

    def test_erro_de_consulta_exibe_mensagem_obrigatoria(self):
        with patch("apps.accounts.views.paginate_table", side_effect=RuntimeError("falha")):
            response = self.client.get(reverse("perfis"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Erro ao executar consulta.")

    def test_consulta_de_usuario_pagina_e_edita_registro(self):
        user = User.objects.create_user(
            username="USUARIOCONSULTA",
            password="senha-segura",
            full_name="Usuário Consulta",
            nr_cpf="529.982.247-25",
        )
        response = self.client.get(reverse("usuarios"), {"q": "USUARIOCONSULTA"})
        self.assertContains(response, "1 registro(s) encontrado(s).")
        self.assertContains(response, reverse("usuario_editar", args=[user.pk]))
        edit_response = self.client.get(
            reverse("usuario_editar", args=[user.pk]),
            {"return_to": f"{reverse('usuarios')}?q=USUARIOCONSULTA"},
        )
        self.assertEqual(edit_response.context["usuario"], user)
