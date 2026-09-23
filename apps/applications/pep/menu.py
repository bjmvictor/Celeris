"""PEP workspace menu composition over legacy clinical-menu storage."""

import copy

from django.db.models import Q

from apps.atendimento.services.perfis_assistenciais import perfis_assistenciais_usuario


def itens_menu_assistencial_mesclados(usuario, empresa):
    """Return the legacy PEP menu items merged across the user's profiles."""
    perfis = list(perfis_assistenciais_usuario(usuario, empresa))
    if not perfis:
        return perfis, []
    itens = []
    for perfil in perfis:
        versao = (
            perfil.versoes.filter(ds_status="RASCUNHO").first()
            or perfil.versoes.filter(ds_status="PUBLICADO").first()
        )
        queryset = perfil.itens.select_related(
            "cd_modelo_documento",
            "cd_item_pai",
            "cd_versao_perfil",
            "cd_perfil_assistencial",
        ).filter(sn_ativo=True)
        if versao:
            queryset = queryset.filter(Q(cd_versao_perfil=versao) | Q(cd_versao_perfil__isnull=True))
        itens.extend(queryset)

    mesclados = {}
    id_para_chave = {}
    for item in sorted(itens, key=lambda value: (value.nr_ordem, value.pk)):
        chave = item.cd_item_tecnico or f"{item.tp_item}:{item.nm_item.strip().upper()}"
        id_para_chave[item.pk] = chave
        if chave not in mesclados:
            mesclados[chave] = copy.copy(item)
            mesclados[chave].perfis_origem = [item.cd_perfil_assistencial]
            continue
        atual = mesclados[chave]
        if item.cd_perfil_assistencial.sn_sigiloso and not atual.cd_perfil_assistencial.sn_sigiloso:
            perfis_origem = atual.perfis_origem
            anterior = atual
            atual = copy.copy(item)
            atual.perfis_origem = perfis_origem
            atual.sn_privado = anterior.sn_privado
            atual.sn_imprimivel = anterior.sn_imprimivel
            atual.sn_permite_criar = anterior.sn_permite_criar
            atual.sn_permite_abandonar = anterior.sn_permite_abandonar
            atual.sn_permite_cancelar = anterior.sn_permite_cancelar
            atual.sn_somente_historico = anterior.sn_somente_historico
            mesclados[chave] = atual
        atual.sn_privado = atual.sn_privado or item.sn_privado
        atual.sn_imprimivel = atual.sn_imprimivel and item.sn_imprimivel
        atual.sn_permite_criar = atual.sn_permite_criar and item.sn_permite_criar
        atual.sn_permite_abandonar = atual.sn_permite_abandonar and item.sn_permite_abandonar
        atual.sn_permite_cancelar = atual.sn_permite_cancelar and item.sn_permite_cancelar
        atual.sn_somente_historico = atual.sn_somente_historico or item.sn_somente_historico
        atual.nr_ordem = min(atual.nr_ordem, item.nr_ordem)
        atual.perfis_origem.append(item.cd_perfil_assistencial)

    resultado = list(mesclados.values())
    for item in resultado:
        item.chave_mesclagem = item.cd_item_tecnico or f"{item.tp_item}:{item.nm_item.strip().upper()}"
        item.chave_pai_mesclagem = id_para_chave.get(item.cd_item_pai_id)
        item.filhos_renderizados = []
    return perfis, sorted(resultado, key=lambda value: (value.nr_ordem, value.pk))
