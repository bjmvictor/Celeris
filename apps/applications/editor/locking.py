"""Document-specific lock orchestration over the legacy generic lock service."""

from apps.core.locks import (
    adquirir_trava_edicao,
    consultar_trava_ativa,
    liberar_trava_edicao,
    usuario_tem_trava_ou_livre,
)


RECURSO_DOCUMENTO_CLINICO = "documento_clinico"


def titulo_trava_documento(documento):
    return f"Documento {documento.pk} - {documento.ds_titulo or documento.tp_documento}"


def adquirir_lock_documento(documento, usuario, identificador_guia=""):
    return adquirir_trava_edicao(
        documento.cd_empresa,
        usuario,
        RECURSO_DOCUMENTO_CLINICO,
        documento.pk,
        titulo_trava_documento(documento),
        identificador_guia=identificador_guia,
    )


def consultar_lock_documento(documento):
    return consultar_trava_ativa(documento.cd_empresa, RECURSO_DOCUMENTO_CLINICO, documento.pk)


def usuario_tem_lock_documento_ou_livre(documento, usuario):
    return usuario_tem_trava_ou_livre(documento.cd_empresa, usuario, RECURSO_DOCUMENTO_CLINICO, documento.pk)


def liberar_lock_documento(documento, usuario, motivo="Liberada pelo usu\u00e1rio.", forcar=False):
    return liberar_trava_edicao(
        documento.cd_empresa,
        usuario,
        RECURSO_DOCUMENTO_CLINICO,
        documento.pk,
        motivo=motivo,
        forcar=forcar,
    )
