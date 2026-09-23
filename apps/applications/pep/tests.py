from datetime import timedelta

from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa, Papel, Setor, User, UsuarioEmpresa
from apps.atendimento.models import (
    Atendimento,
    ItemMenuAssistencial,
    Paciente,
    PerfilAssistencial,
    PerfilAssistencialTipo,
    PerfilAssistencialVersao,
    Prestador,
    PrestadorTipo,
)

from .menu import itens_menu_assistencial_mesclados
from .selectors import (
    atendimentos_base_da_fila_pep,
    atendimentos_da_aba_todos_pep,
    atendimentos_do_paciente,
    buscar_pacientes,
    codigos_especialidades_pep,
    contexto_basico_prontuario,
    contexto_setores_pep,
    filtrar_fila_pep,
    resolver_atendimento_da_aba_todos_pep,
    resolver_paciente,
)
from .views import pep, pep_prontuario_paciente, pep_prontuario_paciente_standalone, pep_standalone


class PepSelectorsTenantTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(cd_empresa=8101, nm_empresa="PEP A", sn_ativo=True)
        self.empresa_b = Empresa.objects.create(cd_empresa=8102, nm_empresa="PEP B", sn_ativo=True)
        self.paciente_a = Paciente.objects.create(cd_empresa=self.empresa_a, nm_paciente="PACIENTE A")
        self.paciente_b = Paciente.objects.create(cd_empresa=self.empresa_b, nm_paciente="PACIENTE B")
        self.atendimento_a = Atendimento.objects.create(
            cd_empresa=self.empresa_a,
            cd_paciente=self.paciente_a,
            ds_status="EM_ATENDIMENTO",
        )

    def test_busca_e_contexto_nao_atravessam_empresas(self):
        encontrados = buscar_pacientes(self.empresa_a, busca="PACIENTE")
        self.assertEqual(list(encontrados), [self.paciente_a])
        with self.assertRaises(Http404):
            resolver_paciente(self.empresa_a, self.paciente_b.pk)

        atendimentos = atendimentos_do_paciente(self.empresa_a, self.paciente_a)
        atendimento, ultimos_sinais, historico_sinais = contexto_basico_prontuario(
            self.empresa_a, self.paciente_a, atendimentos, str(self.atendimento_a.pk)
        )
        self.assertEqual(atendimento, self.atendimento_a)
        self.assertIsNone(ultimos_sinais)
        self.assertEqual(list(historico_sinais), [])

    def test_atendimento_de_outro_paciente_nao_pode_ser_resolvido(self):
        with self.assertRaises(Http404):
            contexto_basico_prontuario(
                self.empresa_b,
                self.paciente_b,
                atendimentos_do_paciente(self.empresa_b, self.paciente_b),
                str(self.atendimento_a.pk),
            )


class PepOperationalSelectorsTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(cd_empresa=8120, nm_empresa="Operacional A", sn_ativo=True)
        self.empresa_b = Empresa.objects.create(cd_empresa=8121, nm_empresa="Operacional B", sn_ativo=True)
        self.usuario = User.objects.create_user("operacional-pep", password="senha-forte")
        self.setor_a = Setor.objects.create(
            cd_empresa=self.empresa_a,
            nm_setor="Clínica A",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        self.setor_b = Setor.objects.create(
            cd_empresa=self.empresa_a,
            nm_setor="Clínica B",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        self.setor_a.usuarios.add(self.usuario)
        self.paciente = Paciente.objects.create(cd_empresa=self.empresa_a, nm_paciente="Paciente fila")
        agora = timezone.now()
        self.atendimento_setor = Atendimento.objects.create(
            cd_empresa=self.empresa_a,
            cd_paciente=self.paciente,
            cd_setor_atual=self.setor_a,
            ds_status="EM_ATENDIMENTO",
            ds_especialidade="CLINICA_GERAL",
            dh_inicio=agora - timedelta(minutes=20),
        )
        self.atendimento_sem_setor = Atendimento.objects.create(
            cd_empresa=self.empresa_a,
            cd_paciente=self.paciente,
            ds_status="RECEPCIONADO",
            ds_especialidade="CLINICA_GERAL",
            dh_inicio=agora - timedelta(minutes=10),
        )
        self.atendimento_outro_setor = Atendimento.objects.create(
            cd_empresa=self.empresa_a,
            cd_paciente=self.paciente,
            cd_setor_atual=self.setor_b,
            ds_status="EM_ATENDIMENTO",
            ds_especialidade="CLINICA_GERAL",
        )
        paciente_b = Paciente.objects.create(cd_empresa=self.empresa_b, nm_paciente="Paciente externo")
        self.atendimento_outra_empresa = Atendimento.objects.create(
            cd_empresa=self.empresa_b,
            cd_paciente=paciente_b,
            ds_status="EM_ATENDIMENTO",
            ds_especialidade="CARDIOLOGIA",
        )

    def test_fila_preserva_empresa_setor_especialidade_estado_e_ordenacao(self):
        usuario_eh_ti, setores, setores_filtrados = contexto_setores_pep(
            self.empresa_a,
            self.usuario,
            [str(self.setor_a.pk)],
            False,
        )
        codigos = codigos_especialidades_pep(self.empresa_a, None, True)
        fila = atendimentos_base_da_fila_pep(
            self.empresa_a,
            setores,
            setores_filtrados,
            None,
            usuario_eh_ti,
            codigos,
            ["CLINICA_GERAL"],
        )
        filtrada = filtrar_fila_pep(fila, {"EM_ATENDIMENTO", "RECEPCIONADO"})

        self.assertFalse(usuario_eh_ti)
        self.assertEqual(list(setores), [self.setor_a])
        self.assertEqual(
            [atendimento.pk for atendimento in filtrada],
            [self.atendimento_setor.pk, self.atendimento_sem_setor.pk],
        )
        self.assertNotIn(self.atendimento_outra_empresa.pk, [atendimento.pk for atendimento in filtrada])

    def test_fila_por_numero_e_aba_todos_preservam_tenant_e_atendimento(self):
        grupo_ti = Group.objects.get_or_create(name="TI")[0]
        self.usuario.groups.add(grupo_ti)
        usuario_eh_ti, setores, setores_filtrados = contexto_setores_pep(
            self.empresa_a,
            self.usuario,
            [],
            True,
        )
        fila = atendimentos_base_da_fila_pep(
            self.empresa_a,
            setores,
            setores_filtrados,
            None,
            usuario_eh_ti,
            codigos_especialidades_pep(self.empresa_a, None, usuario_eh_ti),
            [],
        )

        self.assertEqual(
            list(filtrar_fila_pep(fila, {"EM_ATENDIMENTO"}, nr_atendimento=str(self.atendimento_setor.pk))),
            [self.atendimento_setor],
        )
        self.assertEqual(
            list(atendimentos_da_aba_todos_pep(self.empresa_a, self.paciente)),
            [self.atendimento_outro_setor, self.atendimento_sem_setor, self.atendimento_setor],
        )
        self.assertEqual(
            resolver_atendimento_da_aba_todos_pep(self.empresa_a, self.atendimento_setor.pk),
            self.atendimento_setor,
        )
        with self.assertRaises(Http404):
            resolver_atendimento_da_aba_todos_pep(self.empresa_a, self.atendimento_outra_empresa.pk)


class PepMenuTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(cd_empresa=8111, nm_empresa="Menu A", sn_ativo=True)
        self.empresa_b = Empresa.objects.create(cd_empresa=8112, nm_empresa="Menu B", sn_ativo=True)
        self.usuario = User.objects.create_user("menu-pep", password="senha-forte")
        self.prestador = Prestador.objects.create(
            cd_empresa=self.empresa_a,
            nm_prestador="Prestador menu",
            nm_guerra="Menu",
        )
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa_a,
            cd_prestador=self.prestador,
            cd_tipo_prestador="MEDICO",
            sn_principal=True,
        )
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa_a,
            cd_prestador=self.prestador,
            cd_tipo_prestador="AUDITOR",
        )
        self.usuario.cd_prestador = self.prestador
        self.usuario.save(update_fields=["cd_prestador"])

    def criar_perfil(self, empresa, nome, tipo, *, sigiloso=False):
        perfil = PerfilAssistencial.objects.create(
            cd_empresa=empresa,
            nm_perfil=nome,
            sn_sigiloso=sigiloso,
        )
        PerfilAssistencialTipo.objects.create(
            cd_empresa=empresa,
            cd_perfil_assistencial=perfil,
            cd_tipo_prestador=tipo,
        )
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="PUBLICADO",
        )
        return perfil, versao

    def test_mescla_itens_ativos_preserva_precedencia_flags_e_url(self):
        medico, versao_medico = self.criar_perfil(self.empresa_a, "Medico", "MEDICO")
        auditor, versao_auditor = self.criar_perfil(
            self.empresa_a, "Auditor", "AUDITOR", sigiloso=True
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa_a,
            cd_perfil_assistencial=medico,
            cd_versao_perfil=versao_medico,
            cd_item_tecnico="EVOLUIR",
            nm_item="Evoluir",
            tp_item="ACAO",
            ds_url="atendimento:evoluir",
            nr_ordem=10,
            sn_imprimivel=False,
            sn_permite_criar=False,
            sn_permite_abandonar=False,
            sn_permite_cancelar=True,
            sn_somente_historico=True,
        )
        segundo = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa_a,
            cd_perfil_assistencial=auditor,
            cd_versao_perfil=versao_auditor,
            cd_item_tecnico="EVOLUIR",
            nm_item="Evoluir auditor",
            tp_item="ACAO",
            ds_url="atendimento:evoluir-auditor",
            nr_ordem=20,
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa_a,
            cd_perfil_assistencial=medico,
            cd_versao_perfil=versao_medico,
            cd_item_tecnico="INATIVO",
            nm_item="Nao exibir",
            tp_item="ACAO",
            sn_ativo=False,
        )

        perfis, itens = itens_menu_assistencial_mesclados(self.usuario, self.empresa_a)

        self.assertEqual({perfil.pk for perfil in perfis}, {medico.pk, auditor.pk})
        self.assertEqual(len(itens), 1)
        item = itens[0]
        self.assertEqual(item.pk, segundo.pk)
        self.assertEqual(item.chave_mesclagem, "EVOLUIR")
        self.assertEqual(item.nr_ordem, segundo.nr_ordem)
        self.assertEqual(item.ds_url, "atendimento:evoluir-auditor")
        self.assertFalse(item.sn_imprimivel)
        self.assertFalse(item.sn_permite_criar)
        self.assertFalse(item.sn_permite_abandonar)
        self.assertFalse(item.sn_permite_cancelar)
        self.assertTrue(item.sn_somente_historico)
        self.assertEqual([perfil.pk for perfil in item.perfis_origem], [medico.pk, auditor.pk])

    def test_menu_nao_expoe_configuracao_de_outra_empresa(self):
        perfil_a, versao_a = self.criar_perfil(self.empresa_a, "Perfil A", "MEDICO")
        perfil_b, versao_b = self.criar_perfil(self.empresa_b, "Perfil B", "MEDICO")
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa_a,
            cd_perfil_assistencial=perfil_a,
            cd_versao_perfil=versao_a,
            cd_item_tecnico="EMPRESA_A",
            nm_item="Empresa A",
            tp_item="ANCORA",
            ds_url="#empresa-a",
            nr_ordem=2,
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa_b,
            cd_perfil_assistencial=perfil_b,
            cd_versao_perfil=versao_b,
            cd_item_tecnico="EMPRESA_B",
            nm_item="Empresa B",
            tp_item="ANCORA",
            ds_url="#empresa-b",
            nr_ordem=1,
        )

        perfis, itens = itens_menu_assistencial_mesclados(self.usuario, self.empresa_a)

        self.assertEqual([perfil.pk for perfil in perfis], [perfil_a.pk])
        self.assertEqual([(item.cd_item_tecnico, item.ds_url) for item in itens], [("EMPRESA_A", "#empresa-a")])


class PepStandaloneViewsTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=8130, nm_empresa="Standalone", sn_ativo=True)
        self.usuario = User.objects.create_user("pep-standalone", password="senha-forte")
        prestador = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="Prestador standalone",
            nm_guerra="Standalone",
        )
        self.usuario.cd_prestador = prestador
        self.usuario.save(update_fields=["cd_prestador"])
        UsuarioEmpresa.objects.create(usuario=self.usuario, empresa=self.empresa, sn_ativo=True)
        self.paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="Paciente standalone")
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=prestador,
            ds_status="EM_ATENDIMENTO",
        )
        self.client.force_login(self.usuario)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

    def test_entradas_standalone_preservam_workspace_e_prontuario(self):
        workspace = self.client.get(reverse("pep_standalone"))
        prontuario = self.client.get(reverse("pep_prontuario_standalone", args=[self.paciente.pk]))

        self.assertEqual(workspace.status_code, 200)
        self.assertEqual(prontuario.status_code, 200)
        self.assertTemplateUsed(workspace, "atendimento/pep.html")
        self.assertTemplateUsed(prontuario, "atendimento/pep_prontuario_paciente.html")

    def test_standalone_sem_prestador_mantem_redirect_legado(self):
        self.usuario.cd_prestador = None
        self.usuario.save(update_fields=["cd_prestador"])

        response = self.client.get(reverse("pep_standalone"))

        self.assertRedirects(response, reverse("core:home"))


class PepTenantInvalidationViewsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.empresa_a, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={"nm_empresa": "Empresa A", "sn_ativo": True},
        )
        self.empresa_b = Empresa.objects.create(cd_empresa=8131, nm_empresa="Empresa B", sn_ativo=True)
        prestador = Prestador.objects.create(
            cd_empresa=self.empresa_b,
            nm_prestador="Prestador B",
            nm_guerra="B",
        )
        self.usuario = User.objects.create_user(
            "pep-tenant-b",
            password="senha-forte",
            cd_prestador=prestador,
        )
        grupo, _ = Group.objects.get_or_create(name="Médico")
        Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
        self.usuario.groups.add(grupo)
        UsuarioEmpresa.objects.create(usuario=self.usuario, empresa=self.empresa_b, sn_ativo=True)
        self.paciente_a = Paciente.objects.create(cd_empresa=self.empresa_a, nm_paciente="Paciente A")

    def request(self, path, session):
        request = self.factory.get(path)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session.update(session)
        request.session.save()
        request.user = self.usuario
        request._messages = FallbackStorage(request)
        return request

    def assert_redireciona_para_login_por_tenant_invalido(self, view, path, *args, session):
        request = self.request(path, session)

        response = view(request, *args)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith(f"{reverse('login')}?next="))
        self.assertIsNone(request.session.get("cd_empresa"))

    def test_usuario_da_empresa_b_sem_tenant_nao_acessa_empresa_a_nas_quatro_entradas(self):
        entradas = (
            (pep, reverse("atendimento:pep"), ()),
            (pep_prontuario_paciente, reverse("atendimento:pep-prontuario-paciente", args=[self.paciente_a.pk]), (self.paciente_a.pk,)),
            (pep_standalone, reverse("pep_standalone"), ()),
            (
                pep_prontuario_paciente_standalone,
                reverse("pep_prontuario_standalone", args=[self.paciente_a.pk]),
                (self.paciente_a.pk,),
            ),
        )

        for view, path, args in entradas:
            with self.subTest(view=view.__name__):
                self.assert_redireciona_para_login_por_tenant_invalido(
                    view,
                    path,
                    *args,
                    session={},
                )

    def test_empresa_ativa_sem_vinculo_tambem_invalida_sessao(self):
        self.assert_redireciona_para_login_por_tenant_invalido(
            pep_standalone,
            reverse("pep_standalone"),
            session={"cd_empresa": self.empresa_a.pk},
        )
