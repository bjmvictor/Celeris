from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlencode

from apps.atendimento.models import (
    ClasseItemPrescricao,
    DocumentoClinico,
    ItemPrescricao,
    Prescricao,
    PrescricaoItem,
    SolicitacaoExame,
    ViaAplicacaoPrescricao,
)


@dataclass(frozen=True)
class ResultadoRegistroPrescricao:
    prescricao: Prescricao | None
    solicitacoes_exame: tuple[SolicitacaoExame, ...]


def contexto_acao_prescricao(
    request,
    atendimento,
    tipo,
    documento=None,
    classes_permitidas=None,
    itens_menu=(),
):
    """Build the shared prescription/exam action context without controller imports."""
    empresa = atendimento.cd_empresa
    classes = list(
        ClasseItemPrescricao.objects.filter(
            cd_empresa=empresa,
            tp_classe=tipo,
            sn_ativo=True,
        ).order_by("nr_ordem", "ds_classe")
    )
    classes_configuradas = {
        str(valor).strip().upper()
        for valor in (classes_permitidas or request.GET.get("classes", "").split(","))
        if str(valor).strip()
    }
    if classes_configuradas:
        classes = [
            classe
            for classe in classes
            if str(classe.pk) in classes_configuradas or classe.sg_classe.upper() in classes_configuradas
        ]
    itens = (
        ItemPrescricao.objects.filter(
            cd_empresa=empresa,
            cd_classe__in=classes,
            sn_ativo=True,
        )
        .select_related("cd_classe", "cd_produto", "cd_via_padrao")
        .prefetch_related("documentos_exigidos__cd_modelo_documento")
        .order_by("cd_classe__nr_ordem", "nm_item")
    )
    itens_por_classe = {classe.pk: [] for classe in classes}
    itens_menu_por_modelo = {
        item.cd_modelo_documento_id: item
        for item in itens_menu
        if item.tp_item == "DOCUMENTO" and item.cd_modelo_documento_id
    }
    retorno_pep = _return_to_seguro(request)
    rota_prontuario = "pep_prontuario_standalone" if retorno_pep.startswith("/PEP/") else "atendimento:pep-prontuario-paciente"
    for item in itens:
        item.documentos_exigidos_lista = []
        for vinculo in item.documentos_exigidos.all():
            if not vinculo.sn_ativo or not vinculo.sn_obrigatorio:
                continue
            modelo = vinculo.cd_modelo_documento
            item_menu = itens_menu_por_modelo.get(modelo.pk)
            finalizado = DocumentoClinico.objects.filter(
                cd_atendimento=atendimento,
                cd_modelo_documento=modelo,
                ds_status__in=("FECHADO", "FINALIZADO", "ASSINADO"),
            ).exists()
            url_documento = ""
            if item_menu:
                url_documento = (
                    f"{reverse(rota_prontuario, args=[atendimento.cd_paciente_id])}?"
                    f"{urlencode({'modo': 'atendimento', 'atendimento': atendimento.pk, 'item': item_menu.pk, 'return_to': retorno_pep})}"
                )
            item.documentos_exigidos_lista.append({
                "nome": modelo.nm_modelo,
                "url": url_documento,
                "finalizado": finalizado,
            })
        itens_por_classe[item.cd_classe_id].append(item)
    for classe in classes:
        classe.itens_disponiveis = itens_por_classe.get(classe.pk, [])
    itens_salvos = []
    if documento and isinstance(documento.ds_dados_formulario, dict):
        dados_salvos = documento.ds_dados_formulario.get("itens", [])
        if isinstance(dados_salvos, list):
            itens_salvos = dados_salvos
    rota_salvar = "atendimento:prescrever" if tipo == "MEDICAMENTO" else "atendimento:solicitar-exame"
    return {
        "atendimento": atendimento,
        "classes": classes,
        "vias": ViaAplicacaoPrescricao.objects.filter(
            cd_empresa=empresa,
            sn_ativo=True,
        ).order_by("nr_ordem", "ds_via"),
        "tipo_prescricao": tipo,
        "return_to": _return_to_seguro(request),
        "prescricao_documento": documento,
        "prescricao_itens_salvos": itens_salvos,
        "prescricao_form_action": reverse(rota_salvar, args=[atendimento.pk]),
    }


def _return_to_seguro(request):
    candidate = request.POST.get("return_to") or request.GET.get("return_to", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return ""


def _documentos_obrigatorios_pendentes(atendimento, item: ItemPrescricao) -> list[str]:
    pendentes = []
    for vinculo in item.documentos_exigidos.select_related("cd_modelo_documento").filter(
        sn_ativo=True,
        sn_obrigatorio=True,
    ):
        finalizado = DocumentoClinico.objects.filter(
            cd_atendimento=atendimento,
            cd_modelo_documento=vinculo.cd_modelo_documento,
            ds_status__in=("FECHADO", "FINALIZADO", "ASSINADO"),
        ).exists()
        if not finalizado:
            pendentes.append(vinculo.cd_modelo_documento.nm_modelo)
    return pendentes


@transaction.atomic
def registrar_itens_prescricao(
    *,
    empresa,
    atendimento,
    usuario,
    itens: list[dict],
    tipo: str,
    documento: DocumentoClinico | None = None,
) -> ResultadoRegistroPrescricao:
    if tipo not in {"MEDICAMENTO", "EXAME"}:
        raise ValidationError("Tipo de prescrição inválido.")
    if documento and (
        documento.cd_empresa_id != empresa.pk
        or documento.cd_atendimento_id != atendimento.pk
        or documento.ds_status not in {"ABERTO", "RASCUNHO"}
    ):
        raise ValidationError("O documento informado não está disponível para edição.")
    ids = [int(item.get("item_id")) for item in itens if str(item.get("item_id", "")).isdigit()]
    cadastrados = {
        item.pk: item
        for item in ItemPrescricao.objects.select_for_update()
        .select_related("cd_classe", "cd_via_padrao")
        .prefetch_related("documentos_exigidos__cd_modelo_documento")
        .filter(cd_empresa=empresa, pk__in=ids, sn_ativo=True, cd_classe__tp_classe=tipo)
    }
    if len(cadastrados) != len(set(ids)) or not cadastrados:
        raise ValidationError("Selecione ao menos um item de prescrição válido.")
    erros = []
    for item in cadastrados.values():
        documentos = _documentos_obrigatorios_pendentes(atendimento, item)
        if documentos:
            erros.append(f"{item.nm_item}: {', '.join(documentos)}")
    if erros:
        raise ValidationError("Preencha e finalize os documentos obrigatórios: " + "; ".join(erros))

    if tipo == "EXAME":
        if documento:
            SolicitacaoExame.objects.select_for_update().filter(
                cd_empresa=empresa,
                cd_documento_clinico=documento,
                ds_status="SOLICITADO",
            ).delete()
        solicitacoes = []
        for dados in itens:
            item = cadastrados[int(dados["item_id"])]
            solicitacoes.append(
                SolicitacaoExame.objects.create(
                    cd_empresa=empresa,
                    cd_atendimento=atendimento,
                    cd_documento_clinico=documento,
                    ds_exame=item.nm_item,
                    ds_justificativa=str(dados.get("observacao") or "").strip(),
                    ds_prioridade=str(dados.get("prioridade") or "ROTINA"),
                    cd_usuario_criacao=usuario,
                    cd_usuario_atualizacao=usuario,
                )
            )
        if documento:
            documento.ds_conteudo = "\n\n".join(
                f"Exame: {solicitacao.ds_exame}\nPrioridade: {solicitacao.get_ds_prioridade_display()}\nJustificativa: {solicitacao.ds_justificativa or '-'}"
                for solicitacao in solicitacoes
            )
            documento.ds_dados_formulario = {"tipo": tipo, "itens": itens}
            documento.ds_status = "RASCUNHO"
            documento.cd_usuario_responsavel = usuario
            documento.cd_usuario_atualizacao = usuario
            documento.save(update_fields=[
                "ds_conteudo",
                "ds_dados_formulario",
                "ds_status",
                "cd_usuario_responsavel",
                "cd_usuario_atualizacao",
                "dh_atualizacao",
            ])
        return ResultadoRegistroPrescricao(None, tuple(solicitacoes))

    linhas = []
    for ordem, dados in enumerate(itens, 1):
        item = cadastrados[int(dados["item_id"])]
        via_id = dados.get("via_id")
        via = None
        if str(via_id or "").isdigit():
            via = ViaAplicacaoPrescricao.objects.filter(
                cd_empresa=empresa,
                pk=int(via_id),
                sn_ativo=True,
            ).first()
        posologia = str(dados.get("posologia") or item.ds_posologia_padrao or "").strip()
        if item.sn_exige_posologia and not posologia:
            raise ValidationError(f"Informe a posologia de {item.nm_item}.")
        linhas.append((item, via or item.cd_via_padrao, dados, posologia, ordem))
    resumo = "\n".join(
        f"{item.nm_item} — {posologia or 'conforme orientação'}"
        for item, _via, _dados, posologia, _ordem in linhas
    )
    prescricao = None
    if documento:
        prescricao = Prescricao.objects.select_for_update().filter(
            cd_empresa=empresa,
            cd_documento_clinico=documento,
        ).first()
    if prescricao:
        prescricao.ds_prescricao = resumo
        prescricao.ds_orientacoes = ""
        prescricao.sn_ativa = True
        prescricao.cd_usuario_atualizacao = usuario
        prescricao.save(update_fields=[
            "ds_prescricao",
            "ds_orientacoes",
            "sn_ativa",
            "cd_usuario_atualizacao",
            "dh_atualizacao",
        ])
        prescricao.itens.all().delete()
    else:
        prescricao = Prescricao.objects.create(
            cd_empresa=empresa,
            cd_atendimento=atendimento,
            cd_documento_clinico=documento,
            ds_prescricao=resumo,
            ds_orientacoes="",
            cd_usuario_criacao=usuario,
            cd_usuario_atualizacao=usuario,
        )
    PrescricaoItem.objects.bulk_create(
        [
            PrescricaoItem(
                cd_empresa=empresa,
                cd_prescricao=prescricao,
                cd_item_prescricao=item,
                cd_via_aplicacao=via,
                ds_dose=str(dados.get("dose") or item.ds_dose_padrao or "").strip(),
                ds_frequencia=str(dados.get("frequencia") or item.ds_frequencia_padrao or "").strip(),
                ds_duracao=str(dados.get("duracao") or item.ds_duracao_padrao or "").strip(),
                ds_posologia=posologia,
                ds_observacao=str(dados.get("observacao") or "").strip(),
                nr_ordem=ordem * 10,
                cd_usuario_criacao=usuario,
                cd_usuario_atualizacao=usuario,
            )
            for item, via, dados, posologia, ordem in linhas
        ]
    )
    if documento:
        documento.ds_conteudo = "\n".join(
            f"{linha.cd_item_prescricao.nm_item} — {linha.ds_posologia or 'conforme orientação'}"
            for linha in prescricao.itens.select_related("cd_item_prescricao").order_by("nr_ordem", "pk")
        )
        documento.ds_dados_formulario = {"tipo": tipo, "itens": itens}
        documento.ds_status = "RASCUNHO"
        documento.cd_usuario_responsavel = usuario
        documento.cd_usuario_atualizacao = usuario
        documento.save(update_fields=[
            "ds_conteudo",
            "ds_dados_formulario",
            "ds_status",
            "cd_usuario_responsavel",
            "cd_usuario_atualizacao",
            "dh_atualizacao",
        ])
    return ResultadoRegistroPrescricao(prescricao, ())
