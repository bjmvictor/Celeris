"""Editor-owned document rendering services over legacy model storage."""


def modelos_para_tela(empresa, chaves_tela, tipos=None):
    from apps.atendimento.views import _modelos_documento_por_tela

    return _modelos_documento_por_tela(empresa, chaves_tela, tipos)


def renderizar_documento(documento, modo_impressao=True):
    from apps.atendimento.views import _renderizar_documento

    return _renderizar_documento(documento, modo_impressao)


def resposta_pdf_documento(request, documento, empresa, apresentacao=None):
    from apps.atendimento.views import _resposta_pdf_documento

    return _resposta_pdf_documento(request, documento, empresa, apresentacao)
