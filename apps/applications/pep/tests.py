from django.http import Http404
from django.test import TestCase

from apps.accounts.models import Empresa, User
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
    atendimentos_do_paciente,
    buscar_pacientes,
    contexto_basico_prontuario,
    resolver_paciente,
)


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
