from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.applications.editor import locking
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
