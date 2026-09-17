"""Read-only document-model lineage and version selection."""

from apps.atendimento.models import ModeloDocumento


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
