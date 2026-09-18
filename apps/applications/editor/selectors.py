"""Read-only document-model lineage, version selection and history queries."""

from django.db.models import Prefetch, Q

from apps.atendimento.models import DocumentoClinico, EventoDocumentoClinico, ModeloDocumento


def ids_familia_modelo_documento(modelo):
    """Return the legacy document-model lineage, starting at its root."""
    raiz = modelo
    while raiz.cd_versao_anterior_id:
        raiz = raiz.cd_versao_anterior
    candidatos = list(
        ModeloDocumento.objects.filter(cd_empresa=modelo.cd_empresa)
        .only("pk", "cd_versao_anterior_id")
    )
    filhos = {}
    for candidato in candidatos:
        filhos.setdefault(candidato.cd_versao_anterior_id, []).append(candidato.pk)
    encontrados = []
    pendentes = [raiz.pk]
    while pendentes:
        atual = pendentes.pop()
        if atual in encontrados:
            continue
        encontrados.append(atual)
        pendentes.extend(filhos.get(atual, []))
    return encontrados


def versao_atual_modelo_documento(modelo):
    if not modelo:
        return None
    if modelo.sn_versao_atual and modelo.sn_ativo:
        return modelo
    atual = (
        ModeloDocumento.objects.filter(
            pk__in=ids_familia_modelo_documento(modelo),
            sn_versao_atual=True,
            sn_ativo=True,
        )
        .order_by("-nr_versao", "-pk")
        .first()
    )
    return atual or modelo


def modelos_documentais_vigentes_por_tipo(empresa, tipos_documento):
    """Return the current active model for each requested document type."""
    modelos = {}
    for modelo in (
        ModeloDocumento.objects.filter(
            Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
            tp_documento__in=tipos_documento,
            tp_elemento="DOCUMENTO",
            sn_versao_atual=True,
            sn_ativo=True,
        )
        .order_by("tp_documento", "-cd_empresa_id", "-nr_versao", "pk")
    ):
        modelos.setdefault(modelo.tp_documento, modelo)
    return modelos


def documentos_do_prontuario(empresa, paciente, modelos_documento_ids):
    """Return a patient's active document history with ordered audit events."""
    return (
        DocumentoClinico.objects.filter(
            cd_empresa=empresa,
            cd_atendimento__cd_paciente=paciente,
            cd_modelo_documento_id__in=modelos_documento_ids,
        )
        .exclude(ds_status="ABANDONADO")
        .select_related(
            "cd_atendimento",
            "cd_usuario_responsavel",
            "cd_usuario_cancelamento",
        )
        .prefetch_related(
            Prefetch(
                "eventos",
                queryset=EventoDocumentoClinico.objects.select_related("cd_usuario").order_by("-dh_evento"),
            )
        )
        .order_by("-dh_emissao")
    )
