"""Totem application views backed by the existing shared clinical models."""
import random

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.atendimento.models import (
    ClasseSenhaAtendimento,
    RegraSubdivisaoSenha,
    SenhaAtendimento,
)
from apps.core.permissions import role_required
from apps.platform.tenancy import empresa_atual, proteger_contexto_tenant


@login_required
@role_required("TI", "Recepcionista")
@proteger_contexto_tenant
def gerar_senha_totem(request):
    """Generate a ticket for the selected Totem class or subdivision rule."""
    empresa = empresa_atual(request)
    request.current_tab_title = "Totem > Gerar senha"
    request.current_tab_root_title = "Gerar senha"
    request.current_module_title = "Totem"
    senha_gerada = None
    if request.method == "POST":
        regra = None
        if request.POST.get("regra", "").isdigit():
            regra = get_object_or_404(
                RegraSubdivisaoSenha.objects.select_related("cd_tipo_senha", "cd_classe_senha"),
                cd_empresa=empresa,
                sn_ativo=True,
                cd_tipo_senha__sn_ativo=True,
                cd_classe_senha__sn_ativo=True,
                pk=request.POST["regra"],
            )
            classe = regra.cd_classe_senha
            tipo = regra.cd_tipo_senha
            prioridade = regra.nr_prioridade
        else:
            classe = get_object_or_404(
                ClasseSenhaAtendimento.objects.select_related("cd_tipo_senha"),
                cd_empresa=empresa,
                sn_ativo=True,
                cd_tipo_senha__sn_ativo=True,
                pk=request.POST.get("classe"),
            )
            tipo = classe.cd_tipo_senha
            prioridade = classe.nr_prioridade
        hoje = timezone.localdate()
        sigla_subdivisao = regra.sg_regra if regra and regra.sg_regra else classe.sg_classe_senha
        prefixo = f"{tipo.sg_tipo_senha}{sigla_subdivisao}"
        with transaction.atomic():
            usados = set(
                SenhaAtendimento.objects.select_for_update()
                .filter(cd_empresa=empresa, dt_senha=hoje, ds_senha__startswith=prefixo)
                .values_list("nr_senha", flat=True)
            )
            disponiveis = [numero for numero in range(1, 100) if numero not in usados]
            numero = random.SystemRandom().choice(disponiveis) if disponiveis else max(usados, default=99) + 1
            senha_gerada = SenhaAtendimento.objects.create(
                cd_empresa=empresa,
                cd_tipo_senha=tipo,
                cd_classe_senha=classe,
                cd_cor_classificacao=classe.cd_cor_classificacao,
                nr_senha=numero,
                ds_senha=f"{prefixo} {numero:02d}",
                nr_prioridade=prioridade,
                nr_tempo_limite=regra.nr_tempo_limite if regra else tipo.nr_tempo_minimo,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
    classes = ClasseSenhaAtendimento.objects.select_related("cd_tipo_senha", "cd_icone_chamada").filter(
        cd_empresa=empresa,
        sn_ativo=True,
        cd_tipo_senha__sn_ativo=True,
        regras_subdivisao__isnull=True,
    )
    regras = RegraSubdivisaoSenha.objects.select_related(
        "cd_tipo_senha", "cd_classe_senha", "cd_icone_chamada", "cd_classe_senha__cd_icone_chamada"
    ).filter(
        cd_empresa=empresa,
        sn_ativo=True,
        cd_tipo_senha__sn_ativo=True,
        cd_classe_senha__sn_ativo=True,
    )
    historico = SenhaAtendimento.objects.filter(
        cd_empresa=empresa,
        dt_senha=timezone.localdate(),
    ).order_by("-dh_criacao")[:10]
    return render(
        request,
        "atendimento/gerar_senha_totem.html",
        {
            "classes": classes,
            "regras": regras,
            "historico": historico,
            "senha_gerada": senha_gerada,
            "empresa": empresa,
        },
    )
