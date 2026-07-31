from __future__ import annotations

from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .models import ChamadaPainel, MaquinaChamada, PainelChamada


LAYOUT_CHOICES = (("classico", "Clássico"), ("compacto", "Compacto"), ("destaque", "Destaque"))
SIZE_CHOICES = (("pequeno", "Pequeno"), ("medio", "Médio"), ("grande", "Grande"))
COLOR_CHOICES = (("azul", "Azul"), ("verde", "Verde"), ("roxo", "Roxo"), ("alto-contraste", "Alto contraste"))


def painel_chamada_publico(request: HttpRequest) -> HttpResponse:
    """Renderiza e configura o painel associado à máquina identificada."""
    legacy_panel = None
    machine_name = (
        request.headers.get("X-Celeris-Machine")
        or request.GET.get("maquina")
        or request.COOKIES.get("celeris_maquina_chamada")
        or ""
    ).strip().upper()
    legacy_panel_id = request.GET.get("painel")
    if legacy_panel_id and not machine_name:
        legacy_panel = PainelChamada.objects.filter(pk=legacy_panel_id, sn_ativo=True).first()
        machine_name = legacy_panel.nm_maquina.upper() if legacy_panel else ""

    machines = MaquinaChamada.objects.select_related("cd_empresa", "cd_setor").filter(
        nm_maquina__iexact=machine_name,
        tp_maquina="PAINEL",
        sn_ativo=True,
    )
    if request.session.get("cd_empresa"):
        machines = machines.filter(cd_empresa_id=request.session["cd_empresa"])
    machine = machines.first() if machine_name else None
    painel = legacy_panel
    if machine:
        painel = (
            PainelChamada.objects.prefetch_related("setores")
            .filter(cd_empresa=machine.cd_empresa, nm_maquina__iexact=machine.nm_maquina)
            .first()
        )

    if request.method == "POST" and machine:
        layouts = {value for value, _label in LAYOUT_CHOICES}
        sizes = {value for value, _label in SIZE_CHOICES}
        colors = {value for value, _label in COLOR_CHOICES}
        with transaction.atomic():
            painel, _created = PainelChamada.objects.update_or_create(
                cd_empresa=machine.cd_empresa,
                nm_maquina=machine.nm_maquina,
                defaults={
                    "nm_painel": machine.nm_sala or machine.nm_maquina,
                    "tp_painel": "PAINEL",
                    "ds_local_exibicao": machine.nm_sala,
                    "ds_layout": request.POST.get("layout") if request.POST.get("layout") in layouts else "classico",
                    "ds_tamanho": request.POST.get("tamanho") if request.POST.get("tamanho") in sizes else "medio",
                    "ds_cor": request.POST.get("cor") if request.POST.get("cor") in colors else "azul",
                    "sn_ativo": True,
                    "cd_usuario_atualizacao": request.user if request.user.is_authenticated else None,
                },
            )
            if machine.cd_setor_id:
                painel.setores.set([machine.cd_setor])
        response = redirect(f"{request.path}?maquina={machine.nm_maquina}")
        response.set_cookie("celeris_maquina_chamada", machine.nm_maquina, max_age=31_536_000, samesite="Lax")
        return response

    chamadas = ChamadaPainel.objects.none()
    if painel:
        sector_ids = list(painel.setores.values_list("pk", flat=True))
        if not sector_ids and machine and machine.cd_setor_id:
            sector_ids = [machine.cd_setor_id]
        chamadas = (
            ChamadaPainel.objects.select_related("cd_atendimento__cd_paciente", "cd_senha_atendimento", "cd_setor")
            .filter(cd_empresa=painel.cd_empresa, cd_setor_id__in=sector_ids, ds_status="CHAMADO")
            .order_by("-dh_chamada")[:8]
        )
    response = render(
        request,
        "atendimento/painel_chamada_publico.html",
        {
            "painel": painel,
            "maquina": machine,
            "chamadas": chamadas,
            "layout_choices": LAYOUT_CHOICES,
            "size_choices": SIZE_CHOICES,
            "color_choices": COLOR_CHOICES,
            "show_config": bool(machine and (not painel or request.GET.get("configurar") == "1")),
        },
    )
    if machine:
        response.set_cookie("celeris_maquina_chamada", machine.nm_maquina, max_age=31_536_000, samesite="Lax")
    return response
