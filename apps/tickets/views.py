from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.accounts.models import Empresa
from apps.core.permissions import role_required
from apps.core.table_utils import paginate_table

from .forms import MotivoConclusaoSuporteForm, MotivoServicoSuporteForm, OficinaSuporteForm, PrioridadeSuporteForm, TicketAtendimentoForm, TicketForm, UsuarioOficinaSuporteForm
from .models import MotivoConclusaoSuporte, MotivoServicoSuporte, OficinaSuporte, PrioridadeSuporte, Ticket, TicketTransferenciaSuporte, UsuarioOficinaSuporte


User = get_user_model()


def _empresa_logada(request):
    return get_object_or_404(Empresa, cd_empresa=request.session.get("cd_empresa") or 1, sn_ativo=True)


def _toolbar_context(request, title, path=None):
    request.current_tab_title = path or title
    request.current_tab_root_title = title
    request.current_module_title = "Suporte"
    request.current_can_query = True


def _query_session_key(request, model):
    return f"consulta_{model._meta.app_label}_{model._meta.model_name}_{request.path.replace('/', '_')}"


def _apply_form_query(queryset, form_class, request, empresa):
    form = form_class(empresa=empresa)
    for name in form.fields:
        value = request.GET.get(name, "").strip()
        if not value:
            continue
        model_field = queryset.model._meta.get_field(name)
        if getattr(model_field, "remote_field", None):
            queryset = queryset.filter(**{name: value})
        elif model_field.get_internal_type() in {"BooleanField", "NullBooleanField"}:
            queryset = queryset.filter(**{name: value in {"true", "True", "on", "1"}})
        elif model_field.get_internal_type() in {"DateField", "DateTimeField"}:
            queryset = queryset.filter(**{name: value})
        elif model_field.get_internal_type() in {"IntegerField", "BigIntegerField", "AutoField", "BigAutoField", "PositiveIntegerField"} and value.isdigit():
            queryset = queryset.filter(**{name: int(value)})
        else:
            queryset = queryset.filter(**{f"{name}__icontains": value.replace("%", "")})
    return queryset


def _support_office_ids(request, empresa, *, permission):
    if request.user.is_superuser:
        return list(OficinaSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True).values_list("pk", flat=True))
    lookup = {
        "atende": {"sn_atende": True},
        "solicita": {"sn_solicita": True},
    }.get(permission, {})
    return list(
        UsuarioOficinaSuporte.objects.filter(
            cd_empresa=empresa,
            cd_usuario=request.user,
            sn_ativo=True,
            cd_oficina__sn_ativo=True,
            **lookup,
        ).values_list("cd_oficina_id", flat=True)
    )


def _support_users_by_office(empresa, *, attends=True):
    query = UsuarioOficinaSuporte.objects.select_related("cd_usuario", "cd_oficina").filter(
        cd_empresa=empresa,
        sn_ativo=True,
        cd_oficina__sn_ativo=True,
        cd_usuario__is_active=True,
    )
    if attends:
        query = query.filter(sn_atende=True)
    users_by_office = {}
    for link in query.order_by("cd_oficina__nm_oficina", "cd_usuario__first_name", "cd_usuario__last_name", "cd_usuario__username"):
        full_name = link.cd_usuario.get_full_name().strip()
        users_by_office.setdefault(str(link.cd_oficina_id), []).append(
            {"id": str(link.cd_usuario_id), "label": full_name or link.cd_usuario.username}
        )
    return users_by_office


def _usuario_pode_acessar_ticket(request, ticket, empresa):
    if request.user.is_superuser or ticket.requester_id == request.user.pk:
        return True
    office_ids = set(_support_office_ids(request, empresa, permission="atende"))
    office_ids.update(_support_office_ids(request, empresa, permission="solicita"))
    return bool(ticket.cd_oficina_id and ticket.cd_oficina_id in office_ids)


def _fmt_datetime(value):
    return timezone.localtime(value).strftime("%d/%m/%Y %H:%M") if value else ""


def _variaveis_chamado(ticket, request):
    solicitante = ticket.requester
    responsavel = ticket.assigned_to
    executores = ", ".join(
        user.get_full_name() or user.username
        for user in ticket.performers.all().order_by("username")
    )
    return {
        "chamado.codigo": ticket.pk,
        "chamado.titulo": ticket.title,
        "chamado.descricao": ticket.description,
        "chamado.modulo": ticket.module,
        "chamado.status": ticket.get_status_display(),
        "chamado.setor": getattr(ticket.cd_setor, "nm_setor", "") or ticket.sector,
        "chamado.prioridade": getattr(ticket.cd_prioridade, "nm_prioridade", "") or ticket.priority,
        "chamado.motivo": getattr(ticket.cd_motivo, "nm_motivo", "") or "",
        "chamado.oficina": getattr(ticket.cd_oficina, "nm_oficina", "") or "",
        "chamado.solicitante": solicitante.get_full_name() or solicitante.username if solicitante else "",
        "chamado.usuario_solicitante": solicitante.username if solicitante else "",
        "chamado.responsavel": responsavel.get_full_name() or responsavel.username if responsavel else "",
        "chamado.usuario_responsavel": responsavel.username if responsavel else "",
        "chamado.data_hora_solicitacao": _fmt_datetime(ticket.created_at),
        "chamado.data_hora_recebimento": _fmt_datetime(ticket.received_at),
        "chamado.data_hora_realizacao": _fmt_datetime(ticket.performed_at),
        "chamado.data_hora_conclusao": _fmt_datetime(ticket.closed_at),
        "chamado.motivo_conclusao": getattr(ticket.cd_motivo_conclusao, "nm_motivo", "") or "",
        "chamado.conclusao": ticket.conclusion,
        "chamado.observacao_conclusao": ticket.ds_observacao_conclusao,
        "chamado.executores": executores,
        "chamado.usuario_emissao": request.user.get_username(),
        "chamado.data_hora_emissao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
    }


def _parse_local_datetime(value):
    if not value:
        return None
    try:
        parsed = timezone.datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _prepare_navigation(request, instance, session_key):
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get(session_key, []) if query_context else []
    if query_context:
        request.current_new_url = f"{request.path}?origem=consulta&novo=1"
    if not instance and query_context and request.GET.get("novo") == "1":
        request.current_record_status = f"Item {len(result_ids) + 1} de {len(result_ids)}"
        if result_ids:
            request.current_first_url = f"{request.path}?id={result_ids[0]}&origem=consulta"
            request.current_previous_url = f"{request.path}?id={result_ids[-1]}&origem=consulta"
    if instance and instance.pk in result_ids:
        current_index = result_ids.index(instance.pk)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        if current_index > 0:
            request.current_first_url = f"{request.path}?id={result_ids[0]}&origem=consulta"
            request.current_previous_url = f"{request.path}?id={result_ids[current_index - 1]}&origem=consulta"
        if current_index < len(result_ids) - 1:
            request.current_next_url = f"{request.path}?id={result_ids[current_index + 1]}&origem=consulta"
            request.current_last_url = f"{request.path}?id={result_ids[-1]}&origem=consulta"


def _cadastro_simples(request, *, model, form_class, title, search_fields):
    empresa = _empresa_logada(request)
    _toolbar_context(request, title)
    queryset = model.objects.filter(cd_empresa=empresa)
    session_key = _query_session_key(request, model)
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        registros = _apply_form_query(queryset, form_class, request, empresa)
        result_ids = list(registros.order_by(model._meta.pk.name).values_list(model._meta.pk.name, flat=True)[:300])
        request.session[session_key] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum registro encontrado para os filtros informados.")
            return redirect(f"{request.path}?sem_resultados=1")
        return redirect(f"{request.path}?id={result_ids[0]}&origem=consulta")
    instance = None
    if request.GET.get("id"):
        instance = get_object_or_404(queryset, pk=request.GET["id"])
    if request.GET.get("sem_resultados") == "1":
        request.current_start_query = True
    _prepare_navigation(request, instance, session_key)
    form = form_class(request.POST or None, instance=instance, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"{title} salvo com sucesso.")
        return redirect(f"{request.path}?id={saved.pk}")
    return render(request, "tickets/cadastro_simples.html", {"title": title, "form": form, "instance": instance, "form_table": model._meta.model_name})


@login_required
def ticket_list(request):
    _toolbar_context(request, "Chamados", "Suporte > Chamados")
    tickets = Ticket.objects.filter(cd_empresa=_empresa_logada(request))[:100]
    return render(request, "core/table_page.html", {"title": "Chamados", "rows": tickets})


@login_required
@role_required("Suporte")
@transaction.atomic
def prioridades(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Prioridades", "Suporte > Tabelas > Prioridades")
    request.current_can_remove = True
    registros = PrioridadeSuporte.objects.filter(cd_empresa=empresa)
    q = request.GET.get("q", "").strip()
    if q:
        registros = registros.filter(nm_prioridade__icontains=q.replace("%", ""))
    registros = paginate_table(request, registros, {"cd_prioridade_suporte", "nm_prioridade", "nr_peso", "sn_ativo"}, "nr_peso")
    if request.method == "POST":
        for item in registros:
            if request.POST.get(f"delete_{item.pk}") == "1":
                item.sn_ativo = False
                item.save(update_fields=["sn_ativo", "updated_at"])
                continue
            if f"name_{item.pk}" not in request.POST:
                continue
            item.nm_prioridade = request.POST.get(f"name_{item.pk}", item.nm_prioridade).strip()
            item.nr_peso = int(request.POST.get(f"weight_{item.pk}") or item.nr_peso or 0)
            item.ds_cor = request.POST.get(f"color_{item.pk}", item.ds_cor).strip()
            item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
            item.save()
        for index, name in enumerate(request.POST.getlist("new_name")):
            name = name.strip()
            if not name:
                continue
            weights = request.POST.getlist("new_weight")
            colors = request.POST.getlist("new_color")
            active = request.POST.getlist("new_active")
            PrioridadeSuporte.objects.create(
                cd_empresa=empresa,
                nm_prioridade=name,
                nr_peso=int(weights[index] or 0) if index < len(weights) else 0,
                ds_cor=colors[index].strip() if index < len(colors) else "",
                sn_ativo=(active[index] == "true") if index < len(active) else True,
            )
        messages.success(request, "Prioridades salvas com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "tickets/tabela_prioridades.html", {"registros": registros})


@transaction.atomic
def _tabela_motivos_suporte(request, *, model, title, path, table_name, pk_sort):
    empresa = _empresa_logada(request)
    _toolbar_context(request, title, path)
    request.current_can_remove = True
    oficinas = OficinaSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_oficina")
    registros = model.objects.select_related("cd_oficina").filter(cd_empresa=empresa)
    q = request.GET.get("q", "").strip()
    if q:
        registros = registros.filter(Q(nm_motivo__icontains=q.replace("%", "")) | Q(cd_oficina__nm_oficina__icontains=q.replace("%", "")))
    registros = paginate_table(request, registros, {pk_sort, "nm_motivo", "cd_oficina__nm_oficina", "sn_ativo"}, "nm_motivo")
    if request.method == "POST":
        for item in registros:
            if request.POST.get(f"delete_{item.pk}") == "1":
                item.sn_ativo = False
                item.save(update_fields=["sn_ativo", "updated_at"])
                continue
            if f"name_{item.pk}" not in request.POST:
                continue
            item.nm_motivo = request.POST.get(f"name_{item.pk}", item.nm_motivo).strip()
            oficina_id = request.POST.get(f"office_{item.pk}") or None
            item.cd_oficina = oficinas.filter(pk=oficina_id).first() if oficina_id else None
            item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
            item.save()
        new_names = request.POST.getlist("new_name")
        new_offices = request.POST.getlist("new_office")
        new_active = request.POST.getlist("new_active")
        for index, name in enumerate(new_names):
            name = name.strip()
            if not name:
                continue
            oficina_id = new_offices[index] if index < len(new_offices) else ""
            model.objects.create(
                cd_empresa=empresa,
                cd_oficina=oficinas.filter(pk=oficina_id).first() if oficina_id else None,
                nm_motivo=name,
                sn_ativo=(new_active[index] == "true") if index < len(new_active) else True,
            )
        messages.success(request, f"{title} salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(
        request,
        "tickets/tabela_motivos.html",
        {"registros": registros, "oficinas": oficinas, "table_name": table_name, "pk_sort": pk_sort},
    )


@login_required
@role_required("Suporte")
def motivos_servico(request):
    return _tabela_motivos_suporte(
        request,
        model=MotivoServicoSuporte,
        title="Motivos de serviço",
        path="Suporte > Tabelas > Motivos de serviço",
        table_name="suporte_motivo_servico",
        pk_sort="cd_motivo_servico_suporte",
    )


@login_required
@role_required("Suporte")
def motivos_conclusao(request):
    return _tabela_motivos_suporte(
        request,
        model=MotivoConclusaoSuporte,
        title="Motivos de conclusão",
        path="Suporte > Tabelas > Motivos de conclusão",
        table_name="suporte_motivo_conclusao",
        pk_sort="cd_motivo_conclusao_suporte",
    )

@login_required
@role_required("Suporte")
@transaction.atomic
def oficinas(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Oficinas", "Suporte > Tabelas > Oficinas")
    request.current_can_remove = True
    registros = OficinaSuporte.objects.filter(cd_empresa=empresa)
    q = request.GET.get("q", "").strip()
    if q:
        registros = registros.filter(Q(nm_oficina__icontains=q.replace("%", "")) | Q(ds_descricao__icontains=q.replace("%", "")))
    registros = paginate_table(request, registros, {"cd_oficina_suporte", "nm_oficina", "ds_descricao", "sn_ativo"}, "nm_oficina")
    if request.method == "POST":
        for item in registros:
            if request.POST.get(f"delete_{item.pk}") == "1":
                item.sn_ativo = False
                item.save(update_fields=["sn_ativo", "updated_at"])
                continue
            if f"name_{item.pk}" not in request.POST:
                continue
            item.nm_oficina = request.POST.get(f"name_{item.pk}", item.nm_oficina).strip()
            item.ds_descricao = request.POST.get(f"description_{item.pk}", item.ds_descricao).strip()
            item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
            item.save()
        new_names = request.POST.getlist("new_name")
        new_descriptions = request.POST.getlist("new_description")
        new_active = request.POST.getlist("new_active")
        for index, name in enumerate(new_names):
            name = name.strip()
            if not name:
                continue
            OficinaSuporte.objects.create(
                cd_empresa=empresa,
                nm_oficina=name,
                ds_descricao=new_descriptions[index].strip() if index < len(new_descriptions) else "",
                sn_ativo=(new_active[index] == "true") if index < len(new_active) else True,
            )
        messages.success(request, "Oficinas salvas com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "tickets/tabela_oficinas.html", {"registros": registros})


@login_required
@role_required("Suporte")
@transaction.atomic
def solicitar(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Solicitar suporte", "Suporte > Solicitação > Solicitar")
    registros = Ticket.objects.filter(cd_empresa=empresa, requester=request.user).order_by("-created_at")
    session_key = _query_session_key(request, Ticket)
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        queryset = _apply_form_query(registros, TicketForm, request, empresa)
        codigo = request.GET.get("codigo", "").strip()
        if codigo.isdigit():
            queryset = queryset.filter(pk=int(codigo))
        result_ids = list(queryset.order_by("id").values_list("id", flat=True)[:300])
        request.session[session_key] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum chamado encontrado.")
            return redirect(f"{request.path}?sem_resultados=1")
        return redirect(f"{request.path}?id={result_ids[0]}&origem=consulta")
    instance = None
    if request.GET.get("id"):
        instance = get_object_or_404(registros, pk=request.GET["id"])
    if instance:
        request.current_print_url = (
            f'{reverse("tickets:imprimir_chamado", args=[instance.pk])}?tela=tickets:solicitar'
        )
    if request.GET.get("sem_resultados") == "1":
        request.current_start_query = True
    _prepare_navigation(request, instance, session_key)
    form = TicketForm(request.POST or None, instance=instance, empresa=empresa, usuario=request.user)
    if request.method == "POST" and form.is_valid():
        if form.no_support_offices:
            messages.error(request, "Seu usuário não possui oficina liberada para solicitar suporte.")
            return redirect(request.path)
        ticket = form.save(commit=False)
        ticket.cd_empresa = empresa
        ticket.module = "Suporte"
        ticket.requester = request.user
        if ticket.cd_setor:
            ticket.sector = ticket.cd_setor.nm_setor
        if ticket.cd_prioridade:
            ticket.priority = ticket.cd_prioridade.nm_prioridade
        ticket.save()
        form.save_m2m()
        messages.success(request, "Solicitação de suporte salva com sucesso.")
        return redirect(request.path + f"?id={ticket.pk}")
    motivos_por_oficina = {}
    for motivo in MotivoServicoSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_motivo"):
        motivos_por_oficina.setdefault(str(motivo.cd_oficina_id or ""), []).append(str(motivo.pk))
    return render(request, "tickets/solicitar.html", {
        "title": "Solicitar suporte",
        "form": form,
        "instance": instance,
        "form_table": "chamado",
        "motivos_por_oficina": motivos_por_oficina,
    })


@login_required
@role_required("Suporte")
@xframe_options_sameorigin
def imprimir_chamado(request, cd_ticket):
    from apps.atendimento.models import DocumentoClinico
    from apps.atendimento.views import (
        _modelos_documento_por_tela,
        _renderizar_documento,
        _resposta_pdf_documento,
    )

    empresa = _empresa_logada(request)
    ticket = get_object_or_404(
        Ticket.objects.select_related(
            "cd_empresa",
            "cd_setor",
            "cd_prioridade",
            "cd_motivo",
            "cd_oficina",
            "requester",
            "assigned_to",
            "cd_motivo_conclusao",
        ).prefetch_related("performers"),
        cd_empresa=empresa,
        pk=cd_ticket,
    )
    if not _usuario_pode_acessar_ticket(request, ticket, empresa):
        return HttpResponse("Usuário sem acesso a este chamado.", status=403, content_type="text/plain; charset=utf-8")
    chave_tela = request.GET.get("tela", "tickets:solicitar")
    if chave_tela not in {"tickets:solicitar", "tickets:atender"}:
        chave_tela = "tickets:solicitar"
    modelo = _modelos_documento_por_tela(
        empresa,
        chave_tela,
        {"COMPROVANTE_CHAMADO"},
    ).order_by("-cd_empresa_id", "nm_modelo").first()
    if not modelo:
        return HttpResponse(
            "Nenhum layout ativo do tipo Comprovante de chamado foi configurado no editor de documentos.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )
    agora = timezone.now()
    documento = DocumentoClinico(
        cd_documento_clinico=ticket.pk,
        cd_empresa=empresa,
        cd_atendimento=None,
        cd_modelo_documento=modelo,
        tp_documento=modelo.tp_documento,
        ds_titulo=modelo.nm_modelo,
        ds_status="FECHADO",
        ds_conteudo="",
        ds_dados_formulario={},
        dh_criacao=ticket.created_at or agora,
        dh_emissao=agora,
        cd_usuario_emissor=request.user,
        cd_usuario_criacao=ticket.requester or request.user,
    )
    documento._variaveis_adicionais = _variaveis_chamado(ticket, request)
    apresentacao = _renderizar_documento(documento, True)
    return _resposta_pdf_documento(request, documento, empresa, apresentacao)


@login_required
@role_required("Suporte")
@transaction.atomic
def atender(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Atender suporte", "Suporte > Solicitação > Atender")
    request.current_can_save = False
    request.current_can_remove = False
    request.current_start_query = not bool(request.GET)
    office_ids = _support_office_ids(request, empresa, permission="atende")
    registros = Ticket.objects.filter(cd_empresa=empresa).select_related("cd_oficina", "cd_motivo", "cd_prioridade", "requester", "assigned_to", "cd_setor")
    if not request.user.is_superuser:
        registros = registros.filter(cd_oficina_id__in=office_ids)
    oficinas = OficinaSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True)
    if not request.user.is_superuser:
        oficinas = oficinas.filter(pk__in=office_ids)
    oficinas = oficinas.order_by("nm_oficina")

    def redirect_to_current_filters():
        params = request.GET.copy()
        params["consultar"] = "1"
        query_string = params.urlencode()
        return redirect(f"{request.path}?{query_string}" if query_string else f"{request.path}?consultar=1")
    if request.method == "POST":
        ticket = get_object_or_404(registros, pk=request.POST.get("ticket_id"))
        action = request.POST.get("action")
        if action == "receber":
            if ticket.status != "open":
                messages.warning(request, "Apenas chamados solicitados podem ser recebidos.")
                return redirect_to_current_filters()
            ticket.status = "received"
            ticket.assigned_to = request.user
            ticket.received_at = timezone.now()
            ticket.save(update_fields=["status", "assigned_to", "received_at", "updated_at"])
            messages.success(request, "Chamado recebido.")
        elif action == "concluir":
            motivo = get_object_or_404(MotivoConclusaoSuporte, cd_empresa=empresa, pk=request.POST.get("motivo_conclusao"))
            if motivo.cd_oficina_id and motivo.cd_oficina_id != ticket.cd_oficina_id:
                messages.error(request, "O motivo de conclusão não pertence à oficina do chamado.")
                return redirect_to_current_filters()
            performed_at = _parse_local_datetime(request.POST.get("performed_at")) or timezone.now()
            user_ids = [value for value in request.POST.getlist("performers") if value]
            allowed_users = UsuarioOficinaSuporte.objects.filter(
                cd_empresa=empresa,
                cd_oficina=ticket.cd_oficina,
                sn_ativo=True,
                sn_atende=True,
                cd_usuario_id__in=user_ids,
            ).values_list("cd_usuario_id", flat=True)
            if not allowed_users:
                messages.error(request, "Selecione ao menos um usuário autorizado para atender esta oficina.")
                return redirect_to_current_filters()
            ticket.status = "done"
            ticket.assigned_to = ticket.assigned_to or request.user
            ticket.cd_motivo_conclusao = motivo
            ticket.conclusion = motivo.nm_motivo
            ticket.ds_observacao_conclusao = request.POST.get("observacao_conclusao", "").strip()
            ticket.performed_at = performed_at
            ticket.closed_at = performed_at
            ticket.save(update_fields=["status", "assigned_to", "cd_motivo_conclusao", "conclusion", "ds_observacao_conclusao", "performed_at", "closed_at", "updated_at"])
            ticket.performers.set(allowed_users)
            messages.success(request, "Chamado concluído.")
        elif action == "transferir":
            destino_id = request.POST.get("oficina_destino")
            if destino_id == "__not_done__":
                ticket.status = "not_done"
                ticket.assigned_to = ticket.assigned_to or request.user
                ticket.conclusion = request.POST.get("observacao", "").strip() or "Não realizado"
                ticket.closed_at = timezone.now()
                ticket.save(update_fields=["status", "assigned_to", "conclusion", "closed_at", "updated_at"])
                messages.success(request, "Chamado marcado como não concluído.")
                return redirect_to_current_filters()
            destino = get_object_or_404(oficinas, pk=destino_id)
            if ticket.cd_oficina_id == destino.pk:
                messages.warning(request, "O chamado já está nessa oficina.")
            else:
                TicketTransferenciaSuporte.objects.create(
                    cd_empresa=empresa,
                    cd_ticket=ticket,
                    cd_oficina_origem=ticket.cd_oficina,
                    cd_oficina_destino=destino,
                    cd_usuario=request.user,
                    ds_observacao=request.POST.get("observacao", "").strip(),
                )
                ticket.cd_oficina = destino
                ticket.status = "open"
                ticket.assigned_to = None
                ticket.received_at = None
                ticket.save(update_fields=["cd_oficina", "status", "assigned_to", "received_at", "updated_at"])
                messages.success(request, "Chamado transferido.")
        return redirect_to_current_filters()
    should_query = request.GET.get("consultar") == "1"
    tickets = registros.none()
    selected_users = [value for value in request.GET.getlist("usuario") if value]
    selected_offices = [value for value in request.GET.getlist("oficina") if value]
    selected_statuses = [value for value in request.GET.getlist("status") if value]
    sort_key = request.GET.get("ordenar", "").strip()
    sort_direction = request.GET.get("direcao", "asc").strip()
    sort_map = {
        "data": "created_at",
        "chamado": "title",
        "solicitante": "requester__username",
        "oficina": "cd_oficina__nm_oficina",
        "status": "status",
    }
    if should_query:
        tickets = registros
        q = request.GET.get("q", "").strip().replace("%", "")
        data = request.GET.get("data", "").strip()
        if q:
            tickets = tickets.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if selected_users:
            tickets = tickets.filter(Q(requester_id__in=selected_users) | Q(assigned_to_id__in=selected_users) | Q(performers__id__in=selected_users)).distinct()
        if data:
            tickets = tickets.filter(created_at__date=data)
        if selected_offices:
            tickets = tickets.filter(cd_oficina_id__in=selected_offices)
        if selected_statuses:
            tickets = tickets.filter(status__in=selected_statuses)
        if sort_key in sort_map:
            sort_field = sort_map[sort_key]
            if sort_direction == "desc":
                sort_field = f"-{sort_field}"
            tickets = tickets.order_by(sort_field, "pk")
        else:
            tickets = tickets.order_by("cd_prioridade__nr_peso", "created_at", "pk")
    paginator = Paginator(tickets, 20)
    page = paginator.get_page(request.GET.get("page") or 1)
    now = timezone.localtime()
    for ticket in page.object_list:
        created = timezone.localtime(ticket.created_at) if ticket.created_at else now
        age_days = (now.date() - created.date()).days
        if ticket.status == "received":
            ticket.support_row_class = "ticket-row-in-progress"
        elif age_days <= 0:
            ticket.support_row_class = "ticket-row-today"
        elif age_days == 1:
            ticket.support_row_class = "ticket-row-yesterday"
        elif created.year == now.year and created.month == now.month:
            ticket.support_row_class = "ticket-row-month"
        else:
            ticket.support_row_class = "ticket-row-old"
        responsible = ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else ""
        if ticket.status == "received":
            ticket.support_status_label = f"Em atendimento por {responsible or '-'}"
            ticket.support_status_class = "is-received"
            ticket.support_status_icon = "play"
        elif ticket.status == "open":
            ticket.support_status_label = "Solicitado"
            ticket.support_status_class = "is-open"
            ticket.support_status_icon = "clock"
        elif ticket.status == "done":
            ticket.support_status_label = f"Concluído por {responsible or '-'}"
            ticket.support_status_class = "is-done"
            ticket.support_status_icon = "circle-check-big"
        elif ticket.status == "not_done":
            ticket.support_status_label = "Não concluído"
            ticket.support_status_class = "is-not-done"
            ticket.support_status_icon = "x"
        else:
            ticket.support_status_label = ticket.get_status_display()
            ticket.support_status_class = "is-cancelled"
            ticket.support_status_icon = "ban"
    motivos = MotivoConclusaoSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_motivo")
    users = User.objects.filter(is_active=True).order_by("username")
    return render(request, "tickets/atender.html", {
        "title": "Atender suporte",
        "tickets": page,
        "oficinas": oficinas,
        "motivos": motivos,
        "usuarios": users,
        "users_by_office": _support_users_by_office(empresa),
        "status_choices": Ticket.STATUS,
        "selected_users": selected_users,
        "selected_offices": selected_offices,
        "selected_statuses": selected_statuses,
        "sort_key": sort_key,
        "sort_direction": sort_direction,
        "query_executed": should_query,
        "form_table": "chamado",
    })


@login_required
@role_required("TI")
@transaction.atomic
def usuario_oficina(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Usuário x oficina", "TI > Usuários e acessos > Acessos > Usuário x oficina")
    request.current_module_title = "TI"
    request.current_can_remove = True
    registros = UsuarioOficinaSuporte.objects.select_related("cd_usuario", "cd_oficina").filter(cd_empresa=empresa)
    q = request.GET.get("q", "").strip().replace("%", "")
    if q:
        registros = registros.filter(Q(cd_usuario__username__icontains=q) | Q(cd_usuario__first_name__icontains=q) | Q(cd_usuario__last_name__icontains=q) | Q(cd_oficina__nm_oficina__icontains=q))
    registros = paginate_table(request, registros, {"cd_usuario_oficina_suporte", "cd_usuario__username", "cd_oficina__nm_oficina", "sn_ativo", "sn_atende", "sn_solicita"}, "cd_usuario__username")
    usuarios = User.objects.filter(is_active=True).order_by("username")
    oficinas = OficinaSuporte.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_oficina")
    if request.method == "POST":
        for item in registros:
            if request.POST.get(f"delete_{item.pk}") == "1":
                item.delete()
                continue
            if f"user_{item.pk}" not in request.POST:
                continue
            user_id = request.POST.get(f"user_{item.pk}")
            office_id = request.POST.get(f"office_{item.pk}")
            if not user_id or not office_id:
                continue
            item.cd_usuario_id = user_id
            item.cd_oficina_id = office_id
            item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
            item.sn_atende = request.POST.get(f"attends_{item.pk}") == "true"
            item.sn_solicita = request.POST.get(f"requests_{item.pk}") == "true"
            item.save()
        new_users = request.POST.getlist("new_user")
        new_offices = request.POST.getlist("new_office")
        new_active = request.POST.getlist("new_active")
        new_attends = request.POST.getlist("new_attends")
        new_requests = request.POST.getlist("new_requests")
        for index, user_id in enumerate(new_users):
            office_id = new_offices[index] if index < len(new_offices) else ""
            if not user_id or not office_id:
                continue
            UsuarioOficinaSuporte.objects.update_or_create(
                cd_empresa=empresa,
                cd_usuario_id=user_id,
                cd_oficina_id=office_id,
                defaults={
                    "sn_ativo": (new_active[index] == "true") if index < len(new_active) else True,
                    "sn_atende": (new_attends[index] == "true") if index < len(new_attends) else True,
                    "sn_solicita": (new_requests[index] == "true") if index < len(new_requests) else True,
                },
            )
        messages.success(request, "Vínculos de usuário por oficina salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "tickets/usuario_oficina.html", {
        "registros": registros,
        "usuarios": usuarios,
        "oficinas": oficinas,
    })
