"""Real PEP workspace controllers over legacy clinical model storage."""

from datetime import datetime
import unicodedata
from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.atendimento.services.prescricoes import contexto_acao_prescricao
from apps.applications.editor.locking import adquirir_lock_documento, consultar_lock_documento
from apps.applications.editor.permissions import usuario_pode_operar_documento, usuario_pode_visualizar_documento
from apps.applications.editor.selectors import (
    documentos_do_prontuario,
    ids_familia_modelo_documento,
    modelos_documentais_vigentes_por_tipo,
    versao_atual_modelo_documento,
)
from apps.applications.editor.services import criar_documento_clinico, renderizar_documento
from apps.applications.pep.menu import itens_menu_assistencial_mesclados
from apps.applications.pep.selectors import (
    atendimentos_base_da_fila_pep,
    atendimentos_da_aba_todos_pep,
    atendimentos_do_paciente,
    buscar_pacientes,
    codigos_especialidades_pep,
    contexto_basico_prontuario,
    contexto_setores_pep,
    filtrar_fila_pep,
    resolver_paciente,
    resolver_atendimento_da_aba_todos_pep,
)
from apps.core.catalogos import catalogo_queryset
from apps.core.locks import nome_usuario_trava
from apps.core.permissions import role_required
from apps.core.services.certificados_digitais import ErroCertificadoDigital, certificado_ativo_para
from apps.platform.tenancy import TenantContextError, empresa_atual


def _marcar_ramo_menu_assistencial(itens, item_selecionado):
    selecionado_id = getattr(item_selecionado, "pk", None)

    def marcar(item):
        filhos = list(getattr(item, "filhos_renderizados", []) or [])
        ativo = item.pk == selecionado_id
        for filho in filhos:
            ativo = marcar(filho) or ativo
        item.tem_item_ativo = ativo
        return ativo

    for item in itens:
        marcar(item)


def _preparar_arvore_menu_assistencial(itens, grupo_atual=None):
    grupo_atual_id = getattr(grupo_atual, "pk", None)

    def preparar(item):
        filhos = list(getattr(item, "filhos_renderizados", []) or [])
        for filho in filhos:
            preparar(filho)
        item.tem_subgrupo_renderizado = any(getattr(filho, "tp_item", "") == "GRUPO" for filho in filhos)
        item.eh_grupo_atual = bool(grupo_atual_id and item.pk == grupo_atual_id)
        primeira_tela = next((filho for filho in filhos if getattr(filho, "tp_item", "") != "GRUPO"), None)
        if not primeira_tela:
            primeira_tela = next((getattr(filho, "primeira_tela_renderizada", None) for filho in filhos if getattr(filho, "primeira_tela_renderizada", None)), None)
        item.primeira_tela_renderizada = primeira_tela
        item.url_abrir_grupo = getattr(primeira_tela, "url_renderizada", "") or getattr(item, "url_inicio_renderizada", "") or getattr(item, "url_renderizada", "#")

    for item in itens:
        preparar(item)


def _safe_return_url(request):
    candidate = request.POST.get("return_to") or request.GET.get("return_to", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return ""


def _idade(data_nascimento):
    if not data_nascimento:
        return ""
    hoje = timezone.localdate()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))


def _validar_prestador_pep_standalone(request):
    if getattr(request.user, "cd_prestador_id", None):
        return True
    messages.error(request, "O PEP exige um prestador vinculado ao usuário.")
    return False


def _redirecionar_tenant_pep_invalido(request):
    if request.user.is_authenticated:
        from apps.atendimento.public import limpar_rascunhos_do_usuario

        limpar_rascunhos_do_usuario(request.user)
    logout(request)
    messages.error(request, "Sua sessão de empresa não é mais válida. Entre novamente.")
    return redirect(f"{reverse('login')}?{urlencode({'next': request.get_full_path()})}")


def _proteger_contexto_tenant_pep(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except TenantContextError:
            return _redirecionar_tenant_pep_invalido(request)

    return wrapped


def _view_sem_decoradores(view):
    while getattr(view, "__wrapped__", None):
        view = view.__wrapped__
    return view


@login_required
@role_required("TI", "Médico", "Enfermeiro")
@_proteger_contexto_tenant_pep
def pep(request):
    empresa = empresa_atual(request)
    pep_standalone = getattr(request, "pep_standalone", False)
    request.current_tab_title = "Atendimento > PEP"
    request.current_tab_root_title = "PEP"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    busca_unificada = request.GET.get("q_pep", "").strip().replace("%", "")
    grupos_status_pep = {
        "EM_ATENDIMENTO": {
            "titulo": "Em atendimento",
            "icone": "stethoscope",
            "status": ("EM_ATENDIMENTO",),
        },
        "AGUARDANDO": {
            "titulo": "Aguardando",
            "icone": "clock",
            "status": ("RECEPCIONADO", "ABERTO", "AGUARDANDO_CLASSIFICACAO", "EM_CLASSIFICACAO", "AGUARDANDO_CONSULTA", "AGUARDANDO_EXAMES"),
        },
        "REAVALIACAO": {
            "titulo": "Reavaliação",
            "icone": "refresh-cw",
            "status": ("RETORNO_EXAMES",),
        },
        "OBSERVACAO": {
            "titulo": "Observação",
            "icone": "eye",
            "status": ("EM_OBSERVACAO",),
        },
        "ALTA": {
            "titulo": "Alta",
            "icone": "badge-check",
            "status": ("ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "FINALIZADO"),
        },
    }
    status_pep_selecionados = [
        valor for valor in request.GET.getlist("status_pep") if valor in grupos_status_pep
    ]
    aba = request.GET.get("aba", "atendimentos")
    setor_ids = [value for value in request.GET.getlist("setores") if value.isdigit()]
    usar_todos_setores = request.GET.get("todos_setores", "1") == "1" and not setor_ids
    usuario_eh_ti, setores, setores_filtrados = contexto_setores_pep(
        empresa,
        request.user,
        setor_ids,
        usar_todos_setores,
    )
    prestador_logado = getattr(request.user, "cd_prestador", None)
    codigos_especialidades_permitidas = codigos_especialidades_pep(
        empresa,
        prestador_logado,
        usuario_eh_ti,
    )
    nomes_especialidades = {
        str(item.cd_valor).strip().upper(): item.ds_valor
        for item in catalogo_queryset("especialidade", ativos=True)
    }
    especialidades_permitidas = []
    descricoes_adicionadas = set()
    for codigo in codigos_especialidades_permitidas:
        descricao = (
            nomes_especialidades.get(codigo)
            or {"CLINICA_GERAL": "Clínica Geral"}.get(codigo)
            or codigo.replace("_", " ").title()
        )
        chave_descricao = unicodedata.normalize("NFKD", descricao).encode("ascii", "ignore").decode().strip().casefold()
        if chave_descricao in descricoes_adicionadas:
            continue
        descricoes_adicionadas.add(chave_descricao)
        especialidades_permitidas.append({"codigo": codigo, "descricao": descricao})
    especialidades_selecionadas = [
        str(codigo).strip().upper()
        for codigo in request.GET.getlist("especialidades_atendimento")
        if str(codigo).strip().upper() in codigos_especialidades_permitidas
    ]
    atendimentos_base = atendimentos_base_da_fila_pep(
        empresa,
        setores,
        setores_filtrados,
        prestador_logado,
        usuario_eh_ti,
        codigos_especialidades_permitidas,
        especialidades_selecionadas,
    )
    indicadores_status_pep = []
    for chave, configuracao in grupos_status_pep.items():
        indicadores_status_pep.append({
            "chave": chave,
            "titulo": configuracao["titulo"],
            "icone": configuracao["icone"],
            "total": atendimentos_base.filter(ds_status__in=configuracao["status"]).count(),
            "selecionado": chave in status_pep_selecionados,
        })
    if status_pep_selecionados:
        status_filtrados = {
            status
            for chave in status_pep_selecionados
            for status in grupos_status_pep[chave]["status"]
        }
    else:
        status_filtrados = {
            status
            for chave, configuracao in grupos_status_pep.items()
            if chave != "ALTA"
            for status in configuracao["status"]
        }
    busca_atendimento = busca_unificada or request.GET.get("q_atendimento", "").strip().replace("%", "")
    nr_atendimento = request.GET.get("nr_atendimento", "").strip()
    if nr_atendimento.isdigit():
        busca_atendimento = ""
    atendimentos_setor = filtrar_fila_pep(
        atendimentos_base,
        status_filtrados,
        busca=busca_atendimento,
        nr_atendimento=nr_atendimento,
    )

    atendimentos_lista = list(atendimentos_setor[:80])
    for atendimento_lista in atendimentos_lista:
        alertas = []
        dados_classificacao = (
            getattr(atendimento_lista.cd_pre_atendimento, "ds_dados_classificacao", None) or {}
        )
        if dados_classificacao.get("alergias") or dados_classificacao.get("alergias_itens"):
            alertas.append({"icone": "shield", "classe": "allergy", "titulo": "Alergia registrada"})
        prescricoes = list(atendimento_lista.prescricoes.all())
        if any(prescricao.sn_ativa for prescricao in prescricoes):
            alertas.append({"icone": "pill", "classe": "pending", "titulo": "Medicação pendente"})
        if any(not prescricao.sn_ativa for prescricao in prescricoes):
            alertas.append({"icone": "badge-check", "classe": "done", "titulo": "Medicação realizada"})
        solicitacoes = list(atendimento_lista.solicitacoes_exames.all())
        if any(solicitacao.ds_status not in {"LIBERADO", "CANCELADO"} for solicitacao in solicitacoes):
            alertas.append({"icone": "flask", "classe": "pending", "titulo": "Exame pendente"})
        if any(solicitacao.ds_status == "LIBERADO" for solicitacao in solicitacoes):
            alertas.append({"icone": "circle-check-big", "classe": "done", "titulo": "Exame realizado"})
        if atendimento_lista.cd_paciente.ds_observacao:
            alertas.append({"icone": "message-square-warning", "classe": "warning", "titulo": "Observação clínica"})
        atendimento_lista.alertas_pep = alertas

    pacientes_geral = ()
    paciente_selecionado = None
    atendimentos_paciente = ()
    atendimento_selecionado = None
    busca = busca_unificada or request.GET.get("q", "").strip().replace("%", "")
    nr_atendimento_geral = request.GET.get("nr_atendimento_geral", "").strip()
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    paciente_id = request.GET.get("paciente")
    atendimento_id = request.GET.get("atendimento")
    if aba == "todos":
        if nr_atendimento_geral.isdigit():
            busca = ""
            data_inicio = ""
            data_fim = ""
        pacientes_geral = buscar_pacientes(
            empresa,
            busca=busca,
            nr_atendimento=nr_atendimento_geral,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        if paciente_id:
            paciente_selecionado = resolver_paciente(empresa, paciente_id)
            atendimentos_paciente = atendimentos_da_aba_todos_pep(empresa, paciente_selecionado)
        if atendimento_id:
            atendimento_selecionado = resolver_atendimento_da_aba_todos_pep(empresa, atendimento_id)
            paciente_selecionado = atendimento_selecionado.cd_paciente
            atendimentos_paciente = atendimentos_do_paciente(empresa, paciente_selecionado)
    return render(
        request,
        "atendimento/pep.html",
        {
            "pep_standalone": pep_standalone,
            "pep_base_template": "base/pep_layout.html" if pep_standalone else "base/layout.html",
            "pep_list_url": reverse("pep_standalone") if pep_standalone else reverse("atendimento:pep"),
            "setores": setores,
            "setores_filtrados": setores_filtrados,
            "setor_ids": [str(value) for value in setores_filtrados.values_list("pk", flat=True)],
            "setor_chamada_padrao": setores_filtrados.first(),
            "usar_todos_setores": usar_todos_setores,
            "especialidades_permitidas": especialidades_permitidas,
            "especialidades_selecionadas": especialidades_selecionadas,
            "busca_unificada": busca_unificada,
            "indicadores_status_pep": indicadores_status_pep,
            "status_pep_selecionados": status_pep_selecionados,
            "tem_filtros_ativos": bool(status_pep_selecionados or not usar_todos_setores or especialidades_selecionadas),
            "atendimentos": atendimentos_lista,
            "aba": aba,
            "busca_atendimento": busca_atendimento,
            "nr_atendimento": nr_atendimento,
            "busca": busca,
            "nr_atendimento_geral": nr_atendimento_geral,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "pacientes_geral": pacientes_geral,
            "paciente_selecionado": paciente_selecionado,
            "atendimentos_paciente": atendimentos_paciente,
            "atendimento_selecionado": atendimento_selecionado,
            "agora": timezone.now(),
        },
    )


@login_required
@role_required("TI", "Médico", "Enfermeiro")
@_proteger_contexto_tenant_pep
def pep_prontuario_paciente(request, cd_paciente):
    from apps.applications.pep.selectors import (
        atendimentos_do_paciente,
        contexto_basico_prontuario,
        resolver_paciente,
    )

    empresa = empresa_atual(request)
    pep_standalone = getattr(request, "pep_standalone", False)
    pep_list_route = "pep_standalone" if pep_standalone else "atendimento:pep"
    pep_patient_route = "pep_prontuario_standalone" if pep_standalone else "atendimento:pep-prontuario-paciente"
    paciente = resolver_paciente(empresa, cd_paciente)
    somente_consulta = request.GET.get("modo") == "consulta"
    atendimentos = atendimentos_do_paciente(empresa, paciente)
    atendimento_id = request.GET.get("atendimento", "").strip()
    atendimento_selecionado, ultimos_sinais_vitais, historico_sinais_vitais = contexto_basico_prontuario(
        empresa, paciente, atendimentos, atendimento_id
    )
    return_to = _safe_return_url(request) or f"{reverse(pep_list_route)}?aba=todos"
    request.current_return_url = return_to
    request.current_tab_title = "Atendimento > PEP > Prontuário"
    request.current_tab_root_title = "PEP"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    grupos = set(request.user.groups.values_list("name", flat=True))
    can_clinical_actions = request.user.is_superuser or bool(grupos.intersection({"TI", "Médico", "Médico"}))
    perfis_assistenciais, itens_assistenciais = itens_menu_assistencial_mesclados(request.user, empresa)
    menu_assistencial_raizes = []
    if atendimento_selecionado:
        tipos_documentais_por_acao = {
            "ADMISSAO": "ADMISSAO_ANAMNESE",
            "EVOLUIR": "EVOLUCAO",
            "PRESCREVER": "PRESCRICAO",
            "EXAMES": "SOLICITACAO_EXAME",
            "RECEITUARIO": "RECEITUARIO",
            "AIH": "AIH",
        }
        modelos_por_tipo = modelos_documentais_vigentes_por_tipo(
            empresa,
            tipos_documentais_por_acao.values(),
        )
        modelos_documentais = {
            acao: modelos_por_tipo.get(tipo_documento)
            for acao, tipo_documento in tipos_documentais_por_acao.items()
        }
        mapa_acoes = {
            "SINAIS_VITAIS": f"{reverse('atendimento:ficha-atendimento', args=[atendimento_selecionado.pk])}#classificacao",
            "ADMISSAO": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "admissao"]),
            "EVOLUIR": reverse("atendimento:evoluir", args=[atendimento_selecionado.pk]),
            "PRESCREVER": reverse("atendimento:prescrever", args=[atendimento_selecionado.pk]),
            "EXAMES": reverse("atendimento:solicitar-exame", args=[atendimento_selecionado.pk]),
            "ALTA_MEDICA": reverse("atendimento:conceder-alta", args=[atendimento_selecionado.pk]),
            "RECEITUARIO": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "receituario"]),
            "AIH": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "aih"]),
            "DOCUMENTOS": f"{reverse('atendimento:ficha-atendimento', args=[atendimento_selecionado.pk])}#documentos",
        }
        for item in itens_assistenciais:
            modelo_documental = modelos_documentais.get(item.ds_acao)
            if modelo_documental:
                item.tp_item = "DOCUMENTO"
                item.cd_modelo_documento = modelo_documental
                item.cd_modelo_documento_id = modelo_documental.pk
            item.url_conteudo_renderizada = mapa_acoes.get(item.ds_acao, item.ds_url or "#")
            item.somente_consulta = somente_consulta and item.tp_item not in {"DOCUMENTO", "HISTORICO", "GRUPO"}
            if item.tp_item == "GRUPO":
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'grupo': item.pk, 'return_to': return_to})}"
                )
                item.url_inicio_renderizada = item.url_renderizada
            elif item.tp_item == "DOCUMENTO" and item.cd_modelo_documento_id:
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                )
            elif item.tp_item in {"ESCALA", "ANEXO", "HISTORICO", "LINK_EXTERNO"}:
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                )
            else:
                if item.ds_acao:
                    item.url_renderizada = (
                        f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                        f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                    )
                else:
                    item.url_renderizada = item.ds_url or "#"
        itens_por_chave = {item.chave_mesclagem: item for item in itens_assistenciais}
        for item in itens_assistenciais:
            pai = itens_por_chave.get(item.chave_pai_mesclagem)
            if pai:
                pai.filhos_renderizados.append(item)
            else:
                menu_assistencial_raizes.append(item)
    item_selecionado = None
    ultimo_documento_item = None
    documento_aberto_item = None
    apresentacao_documento_item = None
    documento_editavel_item = False
    documento_modo_impressao_item = False
    pode_assumir_documento_item = False
    pode_cancelar_documento_item = False
    pode_copiar_documento_item = False
    documento_bloqueio_item = ""
    prescricao_documento_contexto = None
    pep_documento_next_url = ""
    historico_documentos_item = ()
    item_id = (request.POST.get("item") or request.GET.get("item") or "").strip()
    if atendimento_selecionado and item_id.isdigit():
        item_selecionado = next(
            (
                item for item in itens_assistenciais
                if item.pk == int(item_id) and item.tp_item != "GRUPO"
            ),
            None,
        )
    pep_item_embed_url = ""
    if (
        item_selecionado
        and item_selecionado.tp_item != "DOCUMENTO"
        and item_selecionado.ds_acao in {"PRESCREVER", "EXAMES"}
    ):
        item_return_url = (
            f"{reverse(pep_patient_route, args=[paciente.pk])}?"
            f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item_selecionado.pk, 'return_to': return_to})}"
        )
        parametros_embed = {"embed": "1", "return_to": item_return_url}
        classes_prescricao = (item_selecionado.ds_configuracao or {}).get("classes_prescricao") or []
        if classes_prescricao:
            parametros_embed["classes"] = ",".join(str(valor) for valor in classes_prescricao)
        pep_item_embed_url = f"{item_selecionado.url_conteudo_renderizada}?{urlencode(parametros_embed)}"
    if item_selecionado and item_selecionado.tp_item == "DOCUMENTO" and item_selecionado.cd_modelo_documento_id:
        modelo_documento_item = versao_atual_modelo_documento(item_selecionado.cd_modelo_documento)
        if modelo_documento_item and modelo_documento_item.pk != item_selecionado.cd_modelo_documento_id:
            item_selecionado.cd_modelo_documento = modelo_documento_item
            item_selecionado.cd_modelo_documento_id = modelo_documento_item.pk
        modelos_familia_item = ids_familia_modelo_documento(modelo_documento_item) if modelo_documento_item else [item_selecionado.cd_modelo_documento_id]
        historico_documentos_item = documentos_do_prontuario(
            empresa,
            paciente,
            modelos_familia_item,
        )
        documento_id = (request.GET.get("documento") or "").strip()
        if documento_id.isdigit():
            ultimo_documento_item = historico_documentos_item.filter(pk=int(documento_id)).first()
        documento_aberto_item = historico_documentos_item.filter(ds_status__in=["ABERTO", "RASCUNHO"]).first()
        if not ultimo_documento_item:
            ultimo_documento_item = documento_aberto_item or historico_documentos_item.first()
        if request.method == "POST" and request.POST.get("acao") == "novo_documento":
            if somente_consulta:
                raise PermissionDenied("O prontuário foi aberto em modo de consulta.")
            if not item_selecionado.sn_permite_criar or item_selecionado.sn_somente_historico:
                raise PermissionDenied("Esta tela não permite criar documentos.")
            if not atendimento_selecionado or atendimento_selecionado.ds_status in {
                "FINALIZADO", "ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "CANCELADO",
            }:
                raise PermissionDenied("Não é possível criar documentos em um atendimento encerrado.")
            data_hora_texto = request.POST.get("dh_documento", "").strip()
            try:
                data_hora_documento = datetime.fromisoformat(data_hora_texto)
                if timezone.is_naive(data_hora_documento):
                    data_hora_documento = timezone.make_aware(data_hora_documento)
            except (TypeError, ValueError):
                messages.error(request, "Informe uma data e hora válida para o documento.")
            else:
                documento = criar_documento_clinico(
                    atendimento_selecionado,
                    modelo_documento_item.tp_documento,
                    modelo_documento_item.nm_modelo,
                    "",
                    request.user,
                    modelo=modelo_documento_item,
                    item_menu_assistencial=item_selecionado,
                    versao_perfil=item_selecionado.cd_versao_perfil,
                    usuario_responsavel=request.user,
                    dh_emissao=data_hora_documento,
                )
                params = urlencode({
                    "modo": "atendimento",
                    "atendimento": atendimento_selecionado.pk,
                    "item": item_selecionado.pk,
                    "documento": documento.pk,
                    "return_to": return_to,
                })
                return redirect(f"{reverse(pep_patient_route, args=[paciente.pk])}?{params}")
        if ultimo_documento_item:
            documento_editavel_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}
                and ultimo_documento_item.cd_usuario_responsavel_id in {None, request.user.pk}
            )
            pode_assumir_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}
                and ultimo_documento_item.cd_usuario_responsavel_id not in {None, request.user.pk}
                and usuario_pode_operar_documento(request.user, ultimo_documento_item)
            )
            pode_cancelar_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"FECHADO", "FINALIZADO", "ASSINADO"}
                and item_selecionado.sn_permite_cancelar
                and usuario_pode_operar_documento(request.user, ultimo_documento_item)
            )
            pode_copiar_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"FECHADO", "FINALIZADO", "ASSINADO", "CANCELADO"}
                and usuario_pode_visualizar_documento(request.user, ultimo_documento_item)
            )
            if ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}:
                if documento_editavel_item:
                    resultado_trava = adquirir_lock_documento(ultimo_documento_item, request.user)
                    if not resultado_trava.permitido:
                        documento_editavel_item = False
                        pode_assumir_documento_item = False
                        documento_bloqueio_item = (
                            f"{resultado_trava.mensagem} O documento ficará somente para consulta até a liberação."
                        )
                elif pode_assumir_documento_item:
                    trava_ativa = consultar_lock_documento(ultimo_documento_item)
                    if trava_ativa and trava_ativa.cd_usuario_id != request.user.pk:
                        pode_assumir_documento_item = False
                        documento_bloqueio_item = (
                            f"Este documento está em edição por {nome_usuario_trava(trava_ativa.cd_usuario)}. "
                            "Não é possível assumir enquanto a trava estiver ativa."
                        )
            documento_modo_impressao_item = not documento_editavel_item
            tipo_documento_item = getattr(ultimo_documento_item.cd_modelo_documento, "tp_documento", "")
            if documento_editavel_item and tipo_documento_item in {"PRESCRICAO", "SOLICITACAO_EXAME"}:
                tipo_prescricao_item = "MEDICAMENTO" if tipo_documento_item == "PRESCRICAO" else "EXAME"
                prescricao_documento_contexto = contexto_acao_prescricao(
                    request,
                    atendimento_selecionado,
                    tipo_prescricao_item,
                    ultimo_documento_item,
                    (item_selecionado.ds_configuracao or {}).get("classes_prescricao") or None,
                    itens_menu=itens_assistenciais,
                )
            else:
                apresentacao_documento_item = (
                    renderizar_documento(ultimo_documento_item, False)
                    if documento_editavel_item
                    else None
                )
            pep_documento_next_url = (
                f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item_selecionado.pk, 'documento': ultimo_documento_item.pk, 'return_to': return_to})}"
            )
    _marcar_ramo_menu_assistencial(menu_assistencial_raizes, item_selecionado)
    itens_por_id = {item.pk: item for item in itens_assistenciais}
    grupo_id = (request.GET.get("grupo") or "").strip()
    grupo_requisitado = itens_por_id.get(int(grupo_id)) if grupo_id.isdigit() else None
    if item_selecionado:
        grupo_telas = itens_por_id.get(item_selecionado.cd_item_pai_id)
        pep_telas_barra = [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO"
            and item.cd_item_pai_id == getattr(grupo_telas, "pk", None)
        ] if grupo_telas else [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO" and not item.cd_item_pai_id
        ]
        pep_grupo_tela_atual = grupo_telas
    else:
        pep_grupo_tela_atual = grupo_requisitado if getattr(grupo_requisitado, "tp_item", "") == "GRUPO" else None
        pep_telas_barra = [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO"
            and item.cd_item_pai_id == getattr(pep_grupo_tela_atual, "pk", None)
        ] if pep_grupo_tela_atual else []
        if pep_grupo_tela_atual:
            pep_grupo_tela_atual.tem_item_ativo = True
    _preparar_arvore_menu_assistencial(menu_assistencial_raizes, pep_grupo_tela_atual)
    historico_documentos_lista = list(historico_documentos_item[:30])
    travas_por_documento = {
        int(trava.ds_recurso_id): trava
        for trava in (
            consultar_lock_documento(documento)
            for documento in historico_documentos_lista
            if documento.ds_status in {"ABERTO", "RASCUNHO"}
        )
        if trava and str(trava.ds_recurso_id).isdigit()
    }
    for documento_historico in historico_documentos_lista:
        eventos_status = [
            evento for evento in documento_historico.eventos.all()
            if evento.tp_evento in {"ABANDONADO", "CANCELADO"}
        ]
        documento_historico.pep_evento_status = eventos_status[0] if eventos_status else None
        documento_historico.pep_status_inativo = documento_historico.ds_status in {"ABANDONADO", "CANCELADO"}
        trava_documento = travas_por_documento.get(documento_historico.pk)
        documento_historico.pep_travado_por_outro = bool(
            trava_documento and trava_documento.cd_usuario_id != request.user.pk
        )
        documento_historico.pep_trava_usuario = (
            nome_usuario_trava(trava_documento.cd_usuario)
            if documento_historico.pep_travado_por_outro
            else ""
        )
    certificado_documento_disponivel = False
    erro_certificado_documento = ""
    if documento_editavel_item and ultimo_documento_item:
        finalidade_documento = (
            getattr(ultimo_documento_item.cd_modelo_documento, "tp_finalidade_assinatura", "MEDICO")
            if ultimo_documento_item.cd_modelo_documento_id
            else "MEDICO"
        )
        try:
            certificado_documento_disponivel = bool(
                certificado_ativo_para(empresa, finalidade_documento, request.user)
            )
        except (ErroCertificadoDigital, ImproperlyConfigured) as exc:
            erro_certificado_documento = str(exc)
    if documento_bloqueio_item:
        messages.warning(request, documento_bloqueio_item)
    return render(
        request,
        "atendimento/pep_prontuario_paciente.html",
        {
            "pep_standalone": pep_standalone,
            "pep_base_template": "base/pep_layout.html" if pep_standalone else "base/layout.html",
            "pep_list_url": reverse(pep_list_route),
            "pep_patient_url": reverse(pep_patient_route, args=[paciente.pk]),
            "paciente": paciente,
            "idade": _idade(paciente.dt_nascimento),
            "atendimentos": atendimentos,
            "atendimento": atendimento_selecionado,
            "ultimos_sinais_vitais": ultimos_sinais_vitais,
            "historico_sinais_vitais": historico_sinais_vitais,
            "return_to": return_to,
            "can_clinical_actions": can_clinical_actions,
            "perfis_assistenciais": perfis_assistenciais,
            "menu_assistencial_raizes": menu_assistencial_raizes,
            "pep_telas_barra": pep_telas_barra,
            "pep_grupo_tela_atual": pep_grupo_tela_atual,
            "item_selecionado": item_selecionado,
            "pep_item_embed_url": pep_item_embed_url,
            "ultimo_documento_item": ultimo_documento_item,
            "documento_aberto_item": documento_aberto_item,
            "documento_editavel_item": documento_editavel_item,
            "documento_modo_impressao_item": documento_modo_impressao_item,
            "pode_assumir_documento_item": pode_assumir_documento_item,
            "pode_cancelar_documento_item": pode_cancelar_documento_item,
            "pode_copiar_documento_item": pode_copiar_documento_item,
            "documento_bloqueio_item": documento_bloqueio_item,
            "certificado_documento_disponivel": certificado_documento_disponivel,
            "erro_certificado_documento": erro_certificado_documento,
            "apresentacao_documento_item": apresentacao_documento_item,
            "prescricao_documento_contexto": prescricao_documento_contexto,
            "pep_documento_next_url": pep_documento_next_url,
            "historico_documentos_item": historico_documentos_lista,
            "agora_documento": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "atendimento_aberto": atendimento_selecionado and atendimento_selecionado.ds_status not in {
                "FINALIZADO", "ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "CANCELADO",
            },
            "somente_consulta": somente_consulta,
        },
    )


@login_required
@_proteger_contexto_tenant_pep
def pep_standalone(request):
    if not _validar_prestador_pep_standalone(request):
        return redirect("core:home")
    request.pep_standalone = True
    return _view_sem_decoradores(pep)(request)


@login_required
@_proteger_contexto_tenant_pep
def pep_prontuario_paciente_standalone(request, cd_paciente):
    if not _validar_prestador_pep_standalone(request):
        return redirect("core:home")
    request.pep_standalone = True
    return _view_sem_decoradores(pep_prontuario_paciente)(request, cd_paciente)
