"""Editor-owned document rendering services over legacy model storage."""
import hashlib

from django.db import transaction
from django.utils import timezone

from apps.atendimento.models import DocumentoClinico, EventoDocumentoClinico


@transaction.atomic
def criar_documento_clinico(
    atendimento,
    tipo,
    titulo,
    conteudo,
    user,
    status="ABERTO",
    origem=None,
    modelo=None,
    campos_bloqueados=None,
    dados_formulario=None,
    item_menu_assistencial=None,
    versao_perfil=None,
    usuario_responsavel=None,
    dh_emissao=None,
):
    """Persist a clinical document and its initial audit event atomically."""
    status_final = {
        "RASCUNHO": "ABERTO",
        "FINALIZADO": "FECHADO",
        "ASSINADO": "FECHADO",
    }.get(status, status)
    dados_documento = {
        "cd_empresa": atendimento.cd_empresa,
        "cd_atendimento": atendimento,
        "cd_modelo_documento": modelo,
        "cd_documento_origem": origem,
        "cd_item_menu_assistencial": item_menu_assistencial,
        "cd_versao_perfil": versao_perfil,
        "tp_documento": tipo,
        "ds_titulo": titulo,
        "ds_conteudo": conteudo,
        "ds_dados_formulario": dados_formulario or {},
        "ds_status": status_final,
        "dh_finalizacao": timezone.now() if status_final == "FECHADO" else None,
        "dh_assinatura": timezone.now() if status_final == "FECHADO" else None,
        "cd_usuario_emissor": user,
        "cd_usuario_responsavel": usuario_responsavel or user,
        "ds_hash_conteudo": hashlib.sha256((conteudo or "").encode("utf-8")).hexdigest() if status_final == "FECHADO" else "",
        "cd_usuario_criacao": user,
        "cd_usuario_atualizacao": user,
        "ds_campos_bloqueados": {
            "paciente.codigo": atendimento.cd_paciente_id,
            "paciente.nome": (atendimento.cd_paciente.nm_social or "").strip() or atendimento.cd_paciente.nm_paciente,
            "atendimento.codigo": atendimento.pk,
            "empresa.nome": atendimento.cd_empresa.nm_empresa,
            "usuario.nome": user.display_name() if hasattr(user, "display_name") else user.get_username(),
            **(campos_bloqueados or {}),
        },
    }
    if dh_emissao is not None:
        dados_documento["dh_emissao"] = dh_emissao
    documento = DocumentoClinico.objects.create(**dados_documento)
    EventoDocumentoClinico.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_documento_clinico=documento,
        cd_usuario=user,
        tp_evento="FECHADO" if status_final == "FECHADO" else "CRIADO",
    )
    return documento


def modelos_para_tela(empresa, chaves_tela, tipos=None):
    from apps.atendimento.views import _modelos_documento_por_tela

    return _modelos_documento_por_tela(empresa, chaves_tela, tipos)


def renderizar_documento(documento, modo_impressao=True):
    from apps.atendimento.views import _renderizar_documento

    return _renderizar_documento(documento, modo_impressao)


def resposta_pdf_documento(request, documento, empresa, apresentacao=None):
    from apps.atendimento.views import _resposta_pdf_documento

    return _resposta_pdf_documento(request, documento, empresa, apresentacao)
