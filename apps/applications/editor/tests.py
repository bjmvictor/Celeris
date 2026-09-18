import hashlib
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.accounts.models import Empresa, User
from apps.atendimento.models import (
    Atendimento,
    DocumentoClinico,
    EventoDocumentoClinico,
    ItemMenuAssistencial,
    ModeloDocumento,
    Paciente,
    PerfilAssistencial,
    PerfilAssistencialVersao,
)
from apps.applications.editor import locking
from apps.applications.editor.services import criar_documento_clinico
from apps.core.locks import ResultadoTrava


class DocumentoLockingTests(SimpleTestCase):
    def setUp(self):
        self.empresa = object()
        self.usuario = SimpleNamespace(pk=7)
        self.documento = SimpleNamespace(
            pk=42,
            cd_empresa=self.empresa,
            ds_titulo="",
            tp_documento="EVOLUCAO",
        )

    def test_titulo_equivale_ao_formato_legado(self):
        self.assertEqual(locking.titulo_trava_documento(self.documento), "Documento 42 - EVOLUCAO")

    @patch("apps.applications.editor.locking.adquirir_trava_edicao")
    def test_aquisicao_mantem_recurso_titulo_guia_e_resultado_de_conflito(self, adquirir):
        conflito = ResultadoTrava(False, mensagem="Em edicao por outro usuario.")
        adquirir.return_value = conflito

        resultado = locking.adquirir_lock_documento(self.documento, self.usuario, "guia-1")

        self.assertIs(resultado, conflito)
        adquirir.assert_called_once_with(
            self.empresa,
            self.usuario,
            "documento_clinico",
            42,
            "Documento 42 - EVOLUCAO",
            identificador_guia="guia-1",
        )

    @patch("apps.applications.editor.locking.consultar_trava_ativa")
    @patch("apps.applications.editor.locking.usuario_tem_trava_ou_livre")
    def test_consulta_e_ownership_delegam_o_mesmo_documento(self, ownership, consultar):
        trava = object()
        permitido = ResultadoTrava(True, trava)
        consultar.return_value = trava
        ownership.return_value = permitido

        self.assertIs(locking.consultar_lock_documento(self.documento), trava)
        self.assertIs(locking.usuario_tem_lock_documento_ou_livre(self.documento, self.usuario), permitido)
        consultar.assert_called_once_with(self.empresa, "documento_clinico", 42)
        ownership.assert_called_once_with(self.empresa, self.usuario, "documento_clinico", 42)

    @patch("apps.applications.editor.locking.liberar_trava_edicao")
    def test_liberacao_preserva_motivo_e_forcar(self, liberar):
        liberar.return_value = 1

        self.assertEqual(locking.liberar_lock_documento(self.documento, self.usuario, "Saida.", True), 1)

        liberar.assert_called_once_with(
            self.empresa,
            self.usuario,
            "documento_clinico",
            42,
            motivo="Saida.",
            forcar=True,
        )


class CriarDocumentoClinicoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=8140, nm_empresa="Editor", sn_ativo=True)
        self.usuario = User.objects.create_user("editor-documento", password="senha-forte")
        self.paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="Paciente Editor")
        self.atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_status="EM_ATENDIMENTO",
        )
        self.perfil = PerfilAssistencial.objects.create(
            cd_empresa=self.empresa,
            nm_perfil="Perfil Editor",
        )
        self.versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=self.perfil,
            nr_versao=1,
            ds_status="PUBLICADO",
        )
        self.modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Evolução",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
        )
        self.item = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=self.perfil,
            cd_versao_perfil=self.versao,
            cd_modelo_documento=self.modelo,
            nm_item="Evoluir",
            tp_item="DOCUMENTO",
        )

    def test_criacao_sem_metadados_preserva_compatibilidade_aberta(self):
        documento = criar_documento_clinico(
            self.atendimento, "EVOLUCAO", "Evolução", "conteúdo", self.usuario
        )

        self.assertIsNone(documento.cd_modelo_documento)
        self.assertIsNone(documento.cd_item_menu_assistencial)
        self.assertIsNone(documento.cd_versao_perfil)
        self.assertEqual(documento.cd_usuario_responsavel, self.usuario)
        self.assertIsNotNone(documento.dh_emissao)
        self.assertEqual(documento.ds_status, "ABERTO")
        self.assertEqual(documento.ds_hash_conteudo, "")
        self.assertIsNone(documento.dh_finalizacao)
        self.assertIsNone(documento.dh_assinatura)
        self.assertTrue(
            EventoDocumentoClinico.objects.filter(
                cd_documento_clinico=documento,
                tp_evento="CRIADO",
            ).exists()
        )

    def test_criacao_persiste_metadados_iniciais_completos(self):
        emissao = timezone.make_aware(datetime(2026, 9, 17, 10, 30))

        documento = criar_documento_clinico(
            self.atendimento,
            self.modelo.tp_documento,
            self.modelo.nm_modelo,
            "",
            self.usuario,
            modelo=self.modelo,
            item_menu_assistencial=self.item,
            versao_perfil=self.versao,
            usuario_responsavel=self.usuario,
            dh_emissao=emissao,
        )

        self.assertEqual(documento.cd_modelo_documento, self.modelo)
        self.assertEqual(documento.cd_item_menu_assistencial, self.item)
        self.assertEqual(documento.cd_versao_perfil, self.versao)
        self.assertEqual(documento.cd_usuario_responsavel, self.usuario)
        self.assertEqual(documento.dh_emissao, emissao)
        self.assertTrue(
            EventoDocumentoClinico.objects.filter(
                cd_documento_clinico=documento,
                tp_evento="CRIADO",
            ).exists()
        )

    def test_documento_fechado_preserva_hash_utf8_timestamps_e_evento(self):
        conteudo = "Evolução: pressão 120/80"

        documento = criar_documento_clinico(
            self.atendimento,
            "EVOLUCAO",
            "Evolução",
            conteudo,
            self.usuario,
            status="FINALIZADO",
        )

        self.assertEqual(documento.ds_status, "FECHADO")
        self.assertEqual(documento.ds_hash_conteudo, hashlib.sha256(conteudo.encode("utf-8")).hexdigest())
        self.assertIsNotNone(documento.dh_finalizacao)
        self.assertIsNotNone(documento.dh_assinatura)
        self.assertTrue(
            EventoDocumentoClinico.objects.filter(
                cd_documento_clinico=documento,
                tp_evento="FECHADO",
            ).exists()
        )

    def test_falha_no_evento_reverte_documento_completo(self):
        with patch(
            "apps.applications.editor.services.EventoDocumentoClinico.objects.create",
            side_effect=RuntimeError("falha de auditoria"),
        ):
            with self.assertRaisesRegex(RuntimeError, "falha de auditoria"):
                criar_documento_clinico(
                    self.atendimento,
                    self.modelo.tp_documento,
                    self.modelo.nm_modelo,
                    "",
                    self.usuario,
                    modelo=self.modelo,
                    item_menu_assistencial=self.item,
                    versao_perfil=self.versao,
                    usuario_responsavel=self.usuario,
                    dh_emissao=timezone.now(),
                )

        self.assertFalse(DocumentoClinico.objects.filter(cd_atendimento=self.atendimento).exists())
