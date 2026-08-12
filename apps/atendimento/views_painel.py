from __future__ import annotations

from datetime import timedelta
import mimetypes
from pathlib import Path
from uuid import uuid4

from django.db import transaction
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa
from apps.core.catalogos import catalogo_queryset

from .models import AgendaProfissional, Atendimento, ChamadaPainel, CorClassificacaoRisco, MaquinaChamada, PainelChamada, Prestador, SenhaAtendimento


LAYOUT_CHOICES = (("classico", "Clássico"), ("compacto", "Compacto"), ("destaque", "Destaque"))
SIZE_CHOICES = (("pequeno", "Pequeno"), ("medio", "Médio"), ("grande", "Grande"))
COLOR_CHOICES = (("azul", "Azul"), ("verde", "Verde"), ("roxo", "Roxo"), ("alto-contraste", "Alto contraste"))
DEFAULT_CONFIG = {
    "especialidades": [],
    "tipos_atendimento": [],
    "cores_classificacao": [],
    "chamar_paciente": True,
    "habilitar_midia": False,
    "mostrar_nome": True,
    "mostrar_senha": True,
    "abreviar_nome": False,
    "mostrar_especialidade": True,
    "mostrar_fila": False,
    "mostrar_direcao": True,
    "som_chamada": True,
    "voz_chamada": True,
    "ler_nome": True,
    "ler_senha": False,
    "tela_cheia": False,
    "mostrar_ultimas": True,
    "quantidade_ultimas": 5,
    "repeticoes": 1,
}


def _booleano_post(request: HttpRequest, nome: str) -> bool:
    return request.POST.get(nome) == "1"


def _numero_post(request: HttpRequest, nome: str, padrao: int, minimo: int, maximo: int) -> int:
    try:
        valor = int(request.POST.get(nome) or padrao)
    except (TypeError, ValueError):
        valor = padrao
    return min(max(valor, minimo), maximo)


def _configuracao_painel(painel: PainelChamada | None) -> dict:
    configuracao = DEFAULT_CONFIG.copy()
    if painel and isinstance(painel.ds_configuracao, dict):
        configuracao.update(painel.ds_configuracao)
    return configuracao


def _rotulos_auxiliares(tabela: str) -> dict[str, str]:
    return dict(catalogo_queryset(tabela, ativos=True).values_list("cd_valor", "ds_valor"))


def _catalogo_empresa(empresa: Empresa) -> dict[str, list[dict[str, str]]]:
    rotulos_especialidades = _rotulos_auxiliares("especialidade")
    codigos_especialidades = set()
    for codigos, principal in Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True).values_list(
        "ds_especialidades", "ds_especialidade"
    ):
        codigos_especialidades.update(codigo for codigo in (codigos or []) if codigo)
        if principal:
            codigos_especialidades.add(principal)
    codigos_especialidades.update(
        valor
        for valor in Atendimento.objects.filter(cd_empresa=empresa)
        .exclude(ds_especialidade="")
        .values_list("ds_especialidade", flat=True)
        .distinct()
        if valor
    )

    tipos = set(
        valor
        for valor in Atendimento.objects.filter(cd_empresa=empresa)
        .exclude(ds_tipo_atendimento="")
        .values_list("ds_tipo_atendimento", flat=True)
        .distinct()
        if valor
    )
    tipos.update(
        valor
        for valor in AgendaProfissional.objects.filter(cd_empresa=empresa, sn_ativo=True)
        .exclude(ds_tipo_agendamento="")
        .values_list("ds_tipo_agendamento", flat=True)
        .distinct()
        if valor
    )
    rotulos_tipos = _rotulos_auxiliares("tipo_atendimento")
    cores = CorClassificacaoRisco.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by(
        "nr_prioridade", "nm_cor"
    )
    return {
        "especialidades": [
            {"valor": codigo, "rotulo": rotulos_especialidades.get(codigo, codigo.replace("_", " ").title())}
            for codigo in sorted(codigos_especialidades, key=lambda item: rotulos_especialidades.get(item, item))
        ],
        "tipos_atendimento": [
            {"valor": valor, "rotulo": rotulos_tipos.get(valor, valor.replace("_", " ").title())}
            for valor in sorted(tipos, key=lambda item: rotulos_tipos.get(item, item))
        ],
        "cores_classificacao": [
            {"valor": cor.cd_cor, "rotulo": cor.nm_cor}
            for cor in cores
        ],
    }


def paineis_compativeis_atendimento(atendimento: Atendimento, setor_id: int | None = None):
    """Retorna somente painéis ativos cuja configuração aceita o atendimento."""
    paineis = PainelChamada.objects.filter(cd_empresa=atendimento.cd_empresa, sn_ativo=True).prefetch_related("setores")
    cor_classificacao = ""
    if atendimento.cd_pre_atendimento_id and atendimento.cd_pre_atendimento:
        cor_classificacao = (atendimento.cd_pre_atendimento.ds_cor_prioridade or "").upper()
    compativeis = []
    for painel in paineis:
        configuracao = _configuracao_painel(painel)
        if not configuracao.get("chamar_paciente", True):
            continue
        setores = {setor.pk for setor in painel.setores.all()}
        if setores and setor_id not in setores:
            continue
        especialidades = configuracao.get("especialidades") or []
        if especialidades and atendimento.ds_especialidade not in especialidades:
            continue
        tipos = configuracao.get("tipos_atendimento") or []
        if tipos and atendimento.ds_tipo_atendimento not in tipos:
            continue
        cores = {str(cor).upper() for cor in configuracao.get("cores_classificacao") or []}
        if cores and cor_classificacao not in cores:
            continue
        compativeis.append(painel)
    return compativeis


def paineis_compativeis_agendamento(agendamento: Agendamento):
    paineis = PainelChamada.objects.filter(cd_empresa=agendamento.cd_empresa, sn_ativo=True).prefetch_related("setores")
    compativeis = []
    for painel in paineis:
        configuracao = _configuracao_painel(painel)
        if not configuracao.get("chamar_paciente", True):
            continue
        especialidades = configuracao.get("especialidades") or []
        if especialidades and agendamento.ds_especialidade not in especialidades:
            continue
        tipos = configuracao.get("tipos_atendimento") or []
        if tipos and agendamento.ds_tipo_atendimento not in tipos:
            continue
        compativeis.append(painel)
    return compativeis


def paineis_compativeis_senha(senha: SenhaAtendimento):
    paineis = PainelChamada.objects.filter(cd_empresa=senha.cd_empresa, sn_ativo=True).prefetch_related("setores")
    setor_id = senha.cd_tipo_senha.cd_setor_atendimento_id
    cor = ""
    if senha.cd_cor_classificacao_id:
        cor = senha.cd_cor_classificacao.cd_cor.upper()
    elif senha.cd_classe_senha.cd_cor_classificacao_id:
        cor = senha.cd_classe_senha.cd_cor_classificacao.cd_cor.upper()
    compativeis = []
    for painel in paineis:
        configuracao = _configuracao_painel(painel)
        if not configuracao.get("chamar_paciente", True):
            continue
        setores = {setor.pk for setor in painel.setores.all()}
        if setores and setor_id not in setores:
            continue
        cores = {str(item).upper() for item in configuracao.get("cores_classificacao") or []}
        if cores and cor not in cores:
            continue
        compativeis.append(painel)
    return compativeis


def _tipo_midia(painel: PainelChamada | None) -> tuple[str, str]:
    if not painel:
        return "", ""
    origem = (
        reverse("painel_chamada_midia", args=[painel.pk])
        if painel.ds_midia_arquivo
        else painel.ds_midia_url
    )
    extensao = Path(origem.split("?", 1)[0]).suffix.lower()
    if extensao in {".mp4", ".webm", ".ogg", ".mov"}:
        return "video", origem
    if extensao in {".mp3", ".wav", ".aac", ".m4a"}:
        return "audio", origem
    return ("imagem", origem) if origem else ("", "")


def midia_painel_publica(request: HttpRequest, cd_painel: int) -> FileResponse:
    """Entrega a mídia configurada sem depender do servidor de arquivos do DEBUG."""
    painel = get_object_or_404(PainelChamada, pk=cd_painel, sn_ativo=True)
    arquivo = painel.ds_midia_arquivo
    if not arquivo:
        raise Http404("Mídia não configurada.")
    try:
        stream = arquivo.open("rb")
    except (FileNotFoundError, OSError, ValueError) as error:
        raise Http404("Arquivo de mídia não encontrado.") from error
    content_type = mimetypes.guess_type(arquivo.name)[0] or "application/octet-stream"
    response = FileResponse(stream, content_type=content_type)
    response["Content-Disposition"] = f'inline; filename="{Path(arquivo.name).name}"'
    response["Cache-Control"] = "public, max-age=3600"
    return response


def _dados_chamada(chamada: ChamadaPainel) -> dict[str, str | int]:
    atendimento = chamada.cd_atendimento
    senha_atendimento = chamada.cd_senha_atendimento
    agendamento = chamada.cd_agendamento
    paciente = (
        atendimento.cd_paciente
        if atendimento
        else (
            agendamento.cd_paciente
            if agendamento
            else (senha_atendimento.cd_paciente if senha_atendimento else None)
        )
    )
    nome = "Paciente de teste"
    senha = "TESTE 001"
    especialidade = ""
    if paciente:
        nome = paciente.nm_social or paciente.nm_paciente
    if atendimento:
        senha = atendimento.nr_senha_chamada or str(atendimento.pk)
        especialidade = atendimento.ds_especialidade
    elif agendamento:
        senha = str(agendamento.pk)
        especialidade = agendamento.ds_especialidade
    elif senha_atendimento:
        senha = senha_atendimento.ds_senha
    setor = chamada.cd_setor.nm_setor if chamada.cd_setor_id else ""
    destino = chamada.ds_local or setor
    return {
        "id": chamada.pk,
        "nome": nome,
        "senha": senha,
        "especialidade": especialidade,
        "destino": destino,
        "hora": timezone.localtime(chamada.dh_chamada).strftime("%H:%M"),
    }


def painel_chamada_publico(request: HttpRequest) -> HttpResponse:
    """Exibe e configura o painel associado ao navegador ou à máquina identificada."""
    legacy_panel = None
    machine_name = (
        request.headers.get("X-Celeris-Machine")
        or request.GET.get("maquina")
        or request.COOKIES.get("celeris_maquina_chamada")
        or ""
    ).strip().upper()
    if not machine_name:
        machine_name = f"PAINEL-{uuid4().hex[:8].upper()}"

    legacy_panel_id = request.GET.get("painel")
    if legacy_panel_id:
        legacy_panel = PainelChamada.objects.filter(pk=legacy_panel_id, sn_ativo=True).first()
        if legacy_panel:
            machine_name = legacy_panel.nm_maquina.upper()

    machines = MaquinaChamada.objects.select_related("cd_empresa", "cd_setor").filter(
        nm_maquina__iexact=machine_name,
        tp_maquina="PAINEL",
        sn_ativo=True,
    )
    if request.session.get("cd_empresa"):
        machines = machines.filter(cd_empresa_id=request.session["cd_empresa"])
    machine = machines.first()
    painel = legacy_panel
    if machine:
        painel = (
            PainelChamada.objects.prefetch_related("setores")
            .filter(cd_empresa=machine.cd_empresa, nm_maquina__iexact=machine.nm_maquina)
            .first()
        )

    empresas = Empresa.objects.filter(sn_ativo=True).order_by("nm_empresa")
    configuracao = _configuracao_painel(painel)
    erro_configuracao = ""
    if request.method == "POST":
        empresa = empresas.filter(pk=request.POST.get("empresa")).first()
        if not empresa:
            erro_configuracao = "Selecione uma empresa válida."
        else:
            layouts = {value for value, _label in LAYOUT_CHOICES}
            sizes = {value for value, _label in SIZE_CHOICES}
            colors = {value for value, _label in COLOR_CHOICES}
            catalogo_empresa = _catalogo_empresa(empresa)
            valores_permitidos = {
                chave: {item["valor"] for item in catalogo_empresa[chave]}
                for chave in ("especialidades", "tipos_atendimento", "cores_classificacao")
            }
            configuracao = {
                "especialidades": [
                    valor for valor in request.POST.getlist("especialidades") if valor in valores_permitidos["especialidades"]
                ],
                "tipos_atendimento": [
                    valor for valor in request.POST.getlist("tipos_atendimento") if valor in valores_permitidos["tipos_atendimento"]
                ],
                "cores_classificacao": [
                    valor for valor in request.POST.getlist("cores_classificacao") if valor in valores_permitidos["cores_classificacao"]
                ],
                "chamar_paciente": _booleano_post(request, "chamar_paciente"),
                "habilitar_midia": _booleano_post(request, "habilitar_midia"),
                "mostrar_nome": _booleano_post(request, "mostrar_nome"),
                "mostrar_senha": _booleano_post(request, "mostrar_senha"),
                "abreviar_nome": _booleano_post(request, "abreviar_nome"),
                "mostrar_especialidade": _booleano_post(request, "mostrar_especialidade"),
                "mostrar_fila": _booleano_post(request, "mostrar_fila"),
                "mostrar_direcao": _booleano_post(request, "mostrar_direcao"),
                "som_chamada": _booleano_post(request, "som_chamada"),
                "voz_chamada": _booleano_post(request, "voz_chamada"),
                "ler_nome": _booleano_post(request, "ler_nome"),
                "ler_senha": _booleano_post(request, "ler_senha"),
                "tela_cheia": _booleano_post(request, "tela_cheia"),
                "mostrar_ultimas": _booleano_post(request, "mostrar_ultimas"),
                "quantidade_ultimas": _numero_post(request, "quantidade_ultimas", 5, 1, 20),
                "repeticoes": _numero_post(request, "repeticoes", 1, 1, 5),
            }
            with transaction.atomic():
                if not machine:
                    machine = MaquinaChamada.objects.filter(
                        cd_empresa=empresa,
                        nm_maquina__iexact=machine_name,
                    ).first()
                if machine:
                    machine.cd_empresa = empresa
                    machine.tp_maquina = "PAINEL"
                    machine.sn_ativo = True
                    machine.save(update_fields=("cd_empresa", "tp_maquina", "sn_ativo", "dh_atualizacao"))
                else:
                    machine = MaquinaChamada.objects.create(
                        cd_empresa=empresa,
                        nm_maquina=machine_name,
                        tp_maquina="PAINEL",
                        nm_sala="Painel",
                        tp_sala="SALA",
                        sn_ativo=True,
                        cd_usuario_criacao=request.user if request.user.is_authenticated else None,
                        cd_usuario_atualizacao=request.user if request.user.is_authenticated else None,
                    )
                painel, _created = PainelChamada.objects.update_or_create(
                    cd_empresa=empresa,
                    nm_maquina=machine_name,
                    defaults={
                        "nm_painel": request.POST.get("nome_painel", "").strip() or machine.nm_sala or machine_name,
                        "tp_painel": "PAINEL",
                        "ds_local_exibicao": machine.nm_sala,
                        "ds_layout": request.POST.get("layout") if request.POST.get("layout") in layouts else "classico",
                        "ds_tamanho": request.POST.get("tamanho") if request.POST.get("tamanho") in sizes else "medio",
                        "ds_cor": request.POST.get("cor") if request.POST.get("cor") in colors else "azul",
                        "nr_tempo_exibicao": _numero_post(request, "tempo_exibicao", 10, 3, 60),
                        "sn_voz": configuracao["voz_chamada"],
                        "ds_midia_url": request.POST.get("midia_url", "").strip(),
                        "ds_configuracao": configuracao,
                        "sn_ativo": True,
                        "cd_usuario_atualizacao": request.user if request.user.is_authenticated else None,
                    },
                )
                arquivo = request.FILES.get("midia_arquivo")
                if arquivo:
                    painel.ds_midia_arquivo = arquivo
                    painel.save(update_fields=("ds_midia_arquivo", "dh_atualizacao"))
                if machine.cd_setor_id:
                    painel.setores.set([machine.cd_setor])
                if _booleano_post(request, "debug"):
                    ChamadaPainel.objects.create(
                        cd_empresa=empresa,
                        cd_painel_chamada=painel,
                        cd_setor=machine.cd_setor,
                        ds_local="Teste de configuração",
                        cd_usuario_criacao=request.user if request.user.is_authenticated else None,
                        cd_usuario_atualizacao=request.user if request.user.is_authenticated else None,
                    )
            response = redirect(f"{request.path}?maquina={machine_name}")
            response.set_cookie("celeris_maquina_chamada", machine_name, max_age=31_536_000, samesite="Lax")
            return response

    empresa_selecionada = painel.cd_empresa if painel else (machine.cd_empresa if machine else empresas.first())
    catalogos_empresas = {str(empresa.pk): _catalogo_empresa(empresa) for empresa in empresas}
    catalogo_atual = catalogos_empresas.get(str(empresa_selecionada.pk), {}) if empresa_selecionada else {}
    chamada_atual = None
    historico_chamadas = []
    if painel:
        sector_ids = list(painel.setores.values_list("pk", flat=True))
        if not sector_ids and machine and machine.cd_setor_id:
            sector_ids = [machine.cd_setor_id]
        chamadas = ChamadaPainel.objects.select_related(
            "cd_atendimento__cd_paciente",
            "cd_atendimento__cd_pre_atendimento",
            "cd_agendamento__cd_paciente",
            "cd_senha_atendimento",
            "cd_setor",
        ).filter(cd_empresa=painel.cd_empresa, cd_painel_chamada=painel).exclude(ds_status="CANCELADO")
        if sector_ids:
            chamadas = chamadas.filter(cd_setor_id__in=sector_ids)
        chamadas = list(chamadas.order_by("-dh_chamada")[: configuracao["quantidade_ultimas"] + 1])
        if chamadas:
            candidata = chamadas[0]
            duracao = max(painel.nr_tempo_exibicao, 3)
            if candidata.ds_status == "CHAMADO" and candidata.dh_chamada >= timezone.now() - timedelta(seconds=duracao):
                chamada_atual = candidata
                chamadas = chamadas[1:]
        if configuracao["mostrar_ultimas"]:
            historico_chamadas = chamadas[: configuracao["quantidade_ultimas"]]

    media_kind, media_source = _tipo_midia(painel)
    chamada_atual_dados = _dados_chamada(chamada_atual) if chamada_atual else None
    historico_chamadas_dados = [_dados_chamada(chamada) for chamada in historico_chamadas]
    estado_painel = {
        "chamada": chamada_atual_dados,
        "historico": historico_chamadas_dados,
        "midia": media_source,
    }
    if request.GET.get("estado") == "1":
        return JsonResponse(estado_painel)
    show_config = bool(not painel or request.GET.get("configurar") == "1" or erro_configuracao)
    response = render(
        request,
        "atendimento/painel_chamada_publico.html",
        {
            "painel": painel,
            "maquina": machine,
            "machine_name": machine_name,
            "empresas": empresas,
            "chamada_atual": chamada_atual_dados,
            "historico_chamadas": historico_chamadas_dados,
            "config": configuracao,
            "empresa_selecionada": empresa_selecionada,
            "catalogo_atual": catalogo_atual,
            "catalogos_empresas": catalogos_empresas,
            "layout_choices": LAYOUT_CHOICES,
            "size_choices": SIZE_CHOICES,
            "color_choices": COLOR_CHOICES,
            "show_config": show_config,
            "erro_configuracao": erro_configuracao,
            "media_kind": media_kind,
            "media_source": media_source,
            "estado_painel": estado_painel,
        },
    )
    response.set_cookie("celeris_maquina_chamada", machine_name, max_age=31_536_000, samesite="Lax")
    return response
