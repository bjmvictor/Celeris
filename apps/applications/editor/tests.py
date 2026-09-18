import hashlib
from datetime import datetime, timedelta
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
from apps.applications.editor.selectors import (
    documentos_do_prontuario,
    modelos_documentais_vigentes_por_tipo,
)
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


class EditorDocumentSelectorsTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=8141, nm_empresa="Editor selectors", sn_ativo=True)
        self.outra_empresa = Empresa.objects.create(cd_empresa=8142, nm_empresa="Outra empresa", sn_ativo=True)
        self.usuario = User.objects.create_user("editor-selector", password="senha-forte")
        self.paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="Paciente selector")
        self.atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_status="EM_ATENDIMENTO",
        )
        self.modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Evolução da empresa",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
        )

    def test_modelos_vigentes_preservam_preferencia_por_empresa(self):
        ModeloDocumento.objects.create(
            nm_modelo="Evolução global",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
            nr_versao=9,
        )
        ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Inativo",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
            nr_versao=99,
            sn_ativo=False,
        )

        modelos = modelos_documentais_vigentes_por_tipo(
            self.empresa,
            ("EVOLUCAO", "EDITOR_TEST_MISSING"),
        )

        self.assertEqual(modelos["EVOLUCAO"], self.modelo)
        self.assertNotIn("EDITOR_TEST_MISSING", modelos)

    def test_historico_preserva_tenant_familia_ordenacao_e_eventos_prefetched(self):
        emissao_antiga = timezone.make_aware(datetime(2026, 9, 1, 8, 0))
        emissao_recente = timezone.make_aware(datetime(2026, 9, 2, 8, 0))
        antigo = criar_documento_clinico(
            self.atendimento,
            "EVOLUCAO",
            "Antigo",
            "",
            self.usuario,
            modelo=self.modelo,
            dh_emissao=emissao_antiga,
        )
        recente = criar_documento_clinico(
            self.atendimento,
            "EVOLUCAO",
            "Recente",
            "",
            self.usuario,
            modelo=self.modelo,
            dh_emissao=emissao_recente,
        )
        criar_documento_clinico(
            self.atendimento,
            "EVOLUCAO",
            "Abandonado",
            "",
            self.usuario,
            modelo=self.modelo,
            status="ABANDONADO",
            dh_emissao=timezone.make_aware(datetime(2026, 9, 3, 8, 0)),
        )
        EventoDocumentoClinico.objects.create(
            cd_empresa=self.empresa,
            cd_documento_clinico=recente,
            cd_usuario=self.usuario,
            tp_evento="ATUALIZADO",
            dh_evento=timezone.now() + timedelta(minutes=1),
        )
        outro_modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Outro modelo",
            tp_documento="RECEITUARIO",
            tp_elemento="DOCUMENTO",
        )
        criar_documento_clinico(
            self.atendimento,
            "RECEITUARIO",
            "Fora da família",
            "",
            self.usuario,
            modelo=outro_modelo,
        )

        documentos = list(documentos_do_prontuario(self.empresa, self.paciente, [self.modelo.pk]))

        self.assertEqual([documento.pk for documento in documentos], [recente.pk, antigo.pk])
        documento_recente = documentos[0]
        self.assertIn("eventos", documento_recente._prefetched_objects_cache)
        self.assertEqual([evento.tp_evento for evento in documento_recente.eventos.all()][0], "ATUALIZADO")

    def test_historico_isola_empresa_e_retorna_vazio_sem_modelos(self):
        paciente_outra = Paciente.objects.create(
            cd_empresa=self.outra_empresa,
            nm_paciente="Paciente de outra empresa",
        )
        atendimento_outra = Atendimento.objects.create(
            cd_empresa=self.outra_empresa,
            cd_paciente=paciente_outra,
            ds_status="EM_ATENDIMENTO",
        )
        modelo_outra = ModeloDocumento.objects.create(
            cd_empresa=self.outra_empresa,
            nm_modelo="Evolução outra empresa",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
        )
        documento_outra = criar_documento_clinico(
            atendimento_outra,
            "EVOLUCAO",
            "Outra empresa",
            "",
            self.usuario,
            modelo=modelo_outra,
        )

        self.assertEqual(
            list(documentos_do_prontuario(self.empresa, self.paciente, [self.modelo.pk])),
            [],
        )
        self.assertEqual(
            list(documentos_do_prontuario(self.outra_empresa, self.paciente, [modelo_outra.pk])),
            [],
        )
        self.assertNotIn(
            documento_outra,
            documentos_do_prontuario(self.empresa, self.paciente, [self.modelo.pk]),
        )
