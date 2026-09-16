"""Public document operations backed by the legacy Atendimento implementation.

Consumers must use this module instead of importing document models or private
view helpers directly. Model ownership remains unchanged during the migration.
"""
from .models import DocumentoClinico
from apps.applications.editor.services import (
    modelos_para_tela,
    renderizar_documento,
    resposta_pdf_documento,
)

