from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.forms import modelform_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import datetime, timedelta
import calendar
import logging
import re
import unicodedata
from urllib.parse import urlencode

from apps.accounts.models import Empresa, Setor
from apps.core.models import TabelaAuxiliarGlobal, ValorAuxiliarGlobal
from apps.core.permissions import role_required
from apps.core.table_utils import paginate_table

from .forms import AgendamentoForm, AtendimentoForm, EvolucaoAtendimentoForm, PacienteForm, PacienteSearchForm, PreAtendimentoForm, PrescricaoForm, PrestadorForm, ResultadoExameForm, SolicitacaoExameForm
from .models import Atendimento, AtendimentoFluxo, AtendimentoPrestador, AgendaProfissional, Agendamento, ChamadaPainel, Convenio, DocumentoClinico, EvolucaoAtendimento, HistoricoAlteracaoPaciente, ModeloDocumento, Paciente, PainelChamada, PainelChamadaSetor, PreAtendimento, Prescricao, Prestador, ResultadoExame, SolicitacaoExame


logger = logging.getLogger("celeris.atendimento")


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


def _parse_date(value, fallback=None):
    try:
        return datetime.fromisoformat(value).date() if value else fallback
    except ValueError:
        return fallback


def _feriados():
    valores = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="feriado",
        sn_ativo=True,
    )
    datas = set()
    for valor in valores:
        for raw in (valor.cd_valor, valor.ds_valor):
            texto = str(raw or "").strip()
            for formato in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    datas.add(datetime.strptime(texto[:10], formato).date())
                    break
                except ValueError:
                    continue
    return datas


def _dias_com_agenda(empresa, inicio, fim):
    agendas = AgendaProfissional.objects.filter(cd_empresa=empresa, sn_ativo=True)
    weekdays = set(agendas.values_list("nr_dia_semana", flat=True))
    dias = set()
    atual = inicio
    while atual <= fim:
        if atual.weekday() in weekdays:
            dias.add(atual)
        atual += timedelta(days=1)
    dias.update(
        Agendamento.objects.filter(cd_empresa=empresa, dh_agendamento__date__gte=inicio, dh_agendamento__date__lte=fim)
        .values_list("dh_agendamento__date", flat=True)
    )
    return dias


def _calendario_mensal(empresa, data_selecionada, data_final=None):
    primeiro = data_selecionada.replace(day=1)
    ultimo_dia = calendar.monthrange(primeiro.year, primeiro.month)[1]
    ultimo = primeiro.replace(day=ultimo_dia)
    feriados = _feriados()
    dias_com_agenda = _dias_com_agenda(empresa, primeiro, ultimo)
    semanas = []
    for semana in calendar.Calendar(firstweekday=6).monthdatescalendar(primeiro.year, primeiro.month):
        semanas.append([
            {
                "date": dia,
                "iso": dia.isoformat(),
                "day": dia.day,
                "in_month": dia.month == primeiro.month,
                "selected": dia == data_selecionada or (data_final and data_selecionada <= dia <= data_final),
                "holiday": dia in feriados,
                "has_schedule": dia in dias_com_agenda,
                "today": dia == timezone.localdate(),
            }
            for dia in semana
        ])
    anterior = (primeiro - timedelta(days=1)).replace(day=1)
    proximo = (ultimo + timedelta(days=1)).replace(day=1)
    return {
        "month": primeiro,
        "weeks": semanas,
        "previous": anterior,
        "next": proximo,
        "weekdays": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
    }


def _criar_documento_clinico(atendimento, tipo, titulo, conteudo, user, status="RASCUNHO", origem=None):
    return DocumentoClinico.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        cd_documento_origem=origem,
        tp_documento=tipo,
        ds_titulo=titulo,
        ds_conteudo=conteudo,
        ds_status=status,
        dh_finalizacao=timezone.now() if status in {"FINALIZADO", "ASSINADO"} else None,
        cd_usuario_emissor=user,
        cd_usuario_criacao=user,
        cd_usuario_atualizacao=user,
        ds_campos_bloqueados={
            "paciente.codigo": atendimento.cd_paciente_id,
            "paciente.nome": atendimento.cd_paciente.nm_paciente,
            "atendimento.codigo": atendimento.pk,
            "empresa.nome": atendimento.cd_empresa.nm_empresa,
            "usuario.nome": user.display_name() if hasattr(user, "display_name") else user.get_username(),
        },
    )


ModeloDocumentoForm = modelform_factory(
    ModeloDocumento,
    fields=("nm_modelo", "tp_documento", "ds_cabecalho", "ds_corpo", "ds_rodape", "ds_variaveis", "ds_campos_bloqueados", "sn_ativo"),
)


STATUS_TIMESTAMP_FIELDS = {
    "RECEPCIONADO": "dh_recepcao",
    "EM_CLASSIFICACAO": "dh_inicio_classificacao",
    "AGUARDANDO_CONSULTA": "dh_fim_classificacao",
    "EM_ATENDIMENTO": "dh_inicio_atendimento",
    "ALTA_MEDICA": "dh_alta_medica",
    "ALTA_HOSPITALAR": "dh_alta_hospitalar",
    "FINALIZADO": "dh_fim",
    "CANCELADO": "dh_cancelamento",
}


def _registrar_fluxo(atendimento, status_anterior, status_novo, user=None, *, setor=None, prestador=None, origem="", observacao=""):
    AtendimentoFluxo.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        ds_status_anterior=status_anterior or "",
        ds_status_novo=status_novo,
        cd_setor=setor or atendimento.cd_setor_atual,
        cd_prestador=prestador or atendimento.cd_prestador,
        cd_usuario=user,
        ds_origem=origem,
        ds_observacao=observacao,
    )


def _mudar_status_atendimento(atendimento, status_novo, user=None, *, setor=None, prestador=None, origem="", observacao="", save=True):
    status_anterior = atendimento.ds_status
    agora = timezone.now()
    atendimento.ds_status = status_novo
    if setor:
        atendimento.cd_setor_atual = setor
    timestamp_field = STATUS_TIMESTAMP_FIELDS.get(status_novo)
    if timestamp_field and not getattr(atendimento, timestamp_field):
        setattr(atendimento, timestamp_field, agora)
    if status_novo == "CANCELADO":
        atendimento.cd_usuario_cancelamento = user
        atendimento.sn_ativo = False
    if user:
        atendimento.cd_usuario_atualizacao = user
    if save:
        atendimento.save()
    if status_anterior != status_novo:
        _registrar_fluxo(
            atendimento,
            status_anterior,
            status_novo,
            user,
            setor=setor,
            prestador=prestador,
            origem=origem,
            observacao=observacao,
        )
    return atendimento


def _vincular_prestador_atendimento(atendimento, prestador, user=None, papel="MEDICO", principal=False):
    if not prestador:
        return
    AtendimentoPrestador.objects.update_or_create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        cd_prestador=prestador,
        tp_papel=papel,
        defaults={
            "sn_responsavel_principal": principal,
            "sn_ativo": True,
            "cd_usuario_atualizacao": user,
            "cd_usuario_criacao": user,
        },
    )


FORM_SCREENS = {
    "agendar",
    "atender-agendamento",
    "atendimento",
    "cadastro-paciente-agendamento",
    "cadastro-paciente-atendimento",
}


def _apply_audit(instance, user):
    if not instance.pk and hasattr(instance, "cd_usuario_criacao"):
        instance.cd_usuario_criacao = user
    if hasattr(instance, "cd_usuario_atualizacao"):
        instance.cd_usuario_atualizacao = user


def _query_text(request):
    return request.GET.get("q", "").strip().replace("%", "")


def _auxiliary_code(value):
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    return re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_")[:40]

SCREEN_TITLES = {
    "agendar": "Agendar",
    "atender-agendamento": "Atender",
    "consultar-agendamento": "Consultar",
    "agendas": "Agendas",
    "cadastro-paciente-agendamento": "Cadastro de paciente",
    "atendimento": "Atendimento",
    "consulta-atendimento": "Consulta de atendimento",
    "cadastro-paciente-atendimento": "Cadastro de paciente",
    "convenios-agendamento": "Convênios",
    "tipos-atendimento-agendamento": "Tipos de Atendimento",
    "especialidades-agendamento": "Especialidades",
    "convenios-atendimento": "Convênios",
    "tipos-atendimento-atendimento": "Tipos de Atendimento",
    "especialidades-atendimento": "Especialidades",
    "convenios": "Convênios",
    "tipos-atendimento": "Tipos de Atendimento",
    "especialidades": "Especialidades",
    "profissionais": "Prestadores",
    "salas": "Salas",
    "relatorio-agendamentos": "Relatório de Agendamentos",
    "relatorio-atendimentos": "Relatório de Atendimentos",
    "relatorio-produtividade": "Relatório de Produtividade",
}


@login_required
def screen(request, screen):
    roles_by_screen = {
        "agendas": {"Recepcionista"},
        "atender-agendamento": {"Enfermeiro"},
        "convenios": {"TI", "Recepcionista"},
        "especialidades": {"TI"},
        "escalas": {"TI"},
        "tipos-atendimento": {"TI"},
        "salas": {"TI"},
    }
    required_roles = roles_by_screen.get(screen)
    if required_roles and not (
        request.user.is_superuser
        or request.user.groups.filter(name__in=("TI", *required_roles)).exists()
    ):
        raise PermissionDenied
    title = SCREEN_TITLES.get(screen, "Atendimento")
    if screen in {"convenios-agendamento", "convenios-atendimento", "convenios"}:
        return _editable_convenios(request, title)
    if screen in {"profissionais"}:
        return profissionais(request)
    if screen in {"escalas"}:
        return _editable_escalas(request, title)
    if screen in {"agendas"}:
        return _agenda_dashboard(request)
    if screen in {"atender-agendamento"}:
        return _fila_atendimento(request)
    auxiliary_by_screen = {
        "tipos-atendimento-agendamento": "tipo_atendimento",
        "tipos-atendimento-atendimento": "tipo_atendimento",
        "tipos-atendimento": "tipo_atendimento",
        "especialidades-agendamento": "especialidade",
        "especialidades-atendimento": "especialidade",
        "especialidades": "especialidade",
        "salas": "sala",
    }
    if screen in auxiliary_by_screen:
        return _editable_auxiliary(request, auxiliary_by_screen[screen], title)
    template = "core/form_page.html" if screen in FORM_SCREENS else "core/table_page.html"
    return render(request, template, {"title": title, "rows": []})


def _editable_convenios(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
    empresa = _empresa_logada(request)
    registros = Convenio.objects.filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        filtro = Q(nm_convenio__icontains=query)
        if query.isdigit():
            filtro |= Q(cd_convenio=int(query))
        registros = registros.filter(filtro)
    registros = paginate_table(
        request,
        registros,
        {"cd_convenio", "nm_convenio", "sn_ativo"},
        "cd_convenio",
    )
    if request.method == "POST":
        for convenio in registros:
            if request.POST.get(f"delete_{convenio.pk}") == "1":
                convenio.sn_ativo = False
                _apply_audit(convenio, request.user)
                convenio.save(update_fields=["sn_ativo", "cd_usuario_atualizacao", "dh_atualizacao"])
                continue
            if f"name_{convenio.pk}" not in request.POST:
                continue
            convenio.nm_convenio = request.POST.get(f"name_{convenio.pk}", convenio.nm_convenio)
            convenio.sn_ativo = request.POST.get(f"active_{convenio.pk}") == "true"
            _apply_audit(convenio, request.user)
            convenio.save()
        for index, name in enumerate(request.POST.getlist("new_name")):
            name = name.strip()
            if not name:
                continue
            Convenio.objects.update_or_create(
                cd_empresa=empresa,
                nm_convenio=name,
                defaults={"sn_ativo": request.POST.getlist("new_active")[index] == "true" if index < len(request.POST.getlist("new_active")) else True},
            )
        messages.success(request, "Convênios salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "atendimento/editable_convenios.html", {"title": title, "registros": registros})


def _editable_prestadores(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = False
    empresa = _empresa_logada(request)
    registros = Prestador.objects.filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        filtro = Q(nm_prestador__icontains=query) | Q(ds_especialidade__icontains=query)
        if query.isdigit():
            filtro |= Q(cd_prestador=int(query))
        registros = registros.filter(filtro)
    if request.method == "POST":
        for prestador in registros:
            if f"name_{prestador.pk}" not in request.POST:
                continue
            prestador.nm_prestador = request.POST.get(f"name_{prestador.pk}", prestador.nm_prestador)
            prestador.ds_especialidade = request.POST.get(f"specialty_{prestador.pk}", prestador.ds_especialidade)
            prestador.sn_ativo = request.POST.get(f"active_{prestador.pk}") == "true"
            prestador.save()
        new_names = request.POST.getlist("new_name")
        new_specialties = request.POST.getlist("new_specialty")
        new_actives = request.POST.getlist("new_active")
        for index, name in enumerate(new_names):
            name = name.strip()
            if not name:
                continue
            Prestador.objects.create(
                cd_empresa=empresa,
                nm_prestador=name,
                ds_especialidade=new_specialties[index].strip() if index < len(new_specialties) else "",
                sn_ativo=(new_actives[index] if index < len(new_actives) else "true") == "true",
            )
        messages.success(request, "Prestadores salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "atendimento/editable_prestadores.html", {"title": title, "registros": registros})


@login_required
@role_required("TI")
def profissionais(request):
    return redirect("atendimento:cadastro-profissional-novo")


@login_required
@role_required("TI")
def cadastro_profissional(request, cd_prestador=None):
    request.current_tab_title = "Cadastros > Prestadores > Cadastro"
    request.current_tab_root_title = "Cadastro de prestador"
    request.current_module_title = "Cadastros"
    request.current_can_query = True
    request.current_return_url = _safe_return_url(request)
    empresa = _empresa_logada(request)
    if request.GET.get("consultar") == "1":
        logger.info(
            "Consulta de prestadores iniciada usuario=%s empresa=%s filtros=%s",
            request.user.pk,
            empresa.pk,
            request.GET.dict(),
        )
        registros = Prestador.objects.filter(cd_empresa=empresa)
        text_fields = (
            "nm_prestador", "nm_guerra", "nr_cpf", "nr_rg", "ds_orgao_emissor", "nm_mae", "nm_pai",
            "nr_cartao_sus", "ds_grau_instrucao", "tp_genero", "ds_nacionalidade",
            "ds_naturalidade", "ds_observacao", "tp_prestador", "ds_conselho", "nr_conselho",
            "sg_conselho", "tp_sexo", "ds_cor_raca", "tp_vinculo", "nr_telefone", "nr_celular", "nr_celular_2",
            "ds_email", "nr_cep", "sg_estado", "ds_cidade", "tp_logradouro",
            "ds_endereco", "nr_endereco", "ds_complemento", "ds_bairro",
            "nr_cep_comercial", "sg_estado_comercial", "ds_cidade_comercial",
            "tp_logradouro_comercial", "ds_endereco_comercial", "nr_endereco_comercial",
            "ds_complemento_comercial", "ds_bairro_comercial", "cd_banco", "nr_agencia",
            "nr_digito_agencia", "nm_agencia", "nr_conta", "nr_digito_conta", "tp_conta",
            "nm_favorecido", "nr_documento_favorecido", "ds_chave_pix", "ds_contato_principal",
        )
        provider_code = request.GET.get("cd_prestador", "").strip()
        has_filter = False
        if provider_code.isdigit():
            registros = registros.filter(cd_prestador=int(provider_code))
            has_filter = True
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
            has_filter = True
        expedition_date = request.GET.get("dt_expedicao", "")
        if expedition_date:
            registros = registros.filter(dt_expedicao=expedition_date)
            has_filter = True
        birth_date = request.GET.get("dt_nascimento", "")
        if birth_date:
            registros = registros.filter(dt_nascimento=birth_date)
            has_filter = True
        for field_name in ("cd_cep", "cd_cep_comercial"):
            value = request.GET.get(field_name, "")
            if value.isdigit():
                registros = registros.filter(**{f"{field_name}_id": int(value)})
                has_filter = True
        for field_name in text_fields:
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
                has_filter = True
        for field_name in (
            "sn_permite_agenda",
            "sn_permite_atendimento",
            "sn_permite_prescricao",
            "sn_permite_classificacao",
            "sn_mesmo_endereco",
        ):
            value = request.GET.get(field_name, "")
            if value in {"True", "False"}:
                registros = registros.filter(**{field_name: value == "True"})
                has_filter = True
        specialties = request.GET.getlist("ds_especialidades")
        if specialties:
            has_filter = True
        ordered_records = registros.order_by("cd_prestador")
        if specialties:
            specialty_set = set(specialties)
            result_ids = [
                provider.cd_prestador
                for provider in ordered_records
                if specialty_set.intersection(provider.ds_especialidades or [provider.ds_especialidade])
            ][:200]
        else:
            result_ids = list(ordered_records.values_list("cd_prestador", flat=True)[:200])
        request.session["consulta_prestadores"] = result_ids
        logger.info(
            "Consulta de prestadores concluida usuario=%s empresa=%s quantidade=%s",
            request.user.pk,
            empresa.pk,
            len(result_ids),
        )
        if not result_ids:
            messages.warning(request, "Nenhum prestador encontrado para os filtros informados.")
            return redirect(request.path)
        return redirect(
            f"{reverse('atendimento:cadastro-profissional', args=[result_ids[0]])}?origem=consulta"
        )
    prestador = get_object_or_404(Prestador, cd_empresa=empresa, cd_prestador=cd_prestador) if cd_prestador else None
    if prestador:
        request.current_toggle_active_url = reverse("atendimento:alternar-status-prestador", args=[prestador.pk])
        request.current_toggle_active_label = "Desativar" if prestador.sn_ativo else "Ativar"
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get("consulta_prestadores", []) if query_context else []
    if prestador and prestador.cd_prestador in result_ids:
        current_index = result_ids.index(prestador.cd_prestador)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        if current_index > 0:
            request.current_first_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[current_index - 1]])}?origem=consulta"
        if current_index < len(result_ids) - 1:
            request.current_next_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[current_index + 1]])}?origem=consulta"
            request.current_last_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[-1]])}?origem=consulta"
    form = PrestadorForm(request.POST or None, instance=prestador)
    if request.method == "POST":
        logger.info(
            "Gravacao de prestador iniciada usuario=%s empresa=%s prestador=%s campos=%s",
            request.user.pk,
            empresa.pk,
            cd_prestador or "novo",
            sorted(request.POST.keys()),
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    saved = form.save(commit=False)
                    saved.cd_empresa = empresa
                    _apply_audit(saved, request.user)
                    saved.save()
                    form.save_m2m()
                logger.info(
                    "Prestador gravado usuario=%s empresa=%s prestador=%s",
                    request.user.pk,
                    empresa.pk,
                    saved.cd_prestador,
                )
                messages.success(request, "Prestador salvo com sucesso.")
                edit_url = reverse("atendimento:cadastro-profissional", args=[saved.cd_prestador])
                if request.current_return_url:
                    edit_url = f"{edit_url}?{urlencode({'return_to': request.current_return_url})}"
                elif query_context:
                    edit_url = f"{edit_url}?origem=consulta"
                return redirect(edit_url)
            except Exception:
                logger.exception(
                    "Falha inesperada ao gravar prestador usuario=%s empresa=%s prestador=%s",
                    request.user.pk,
                    empresa.pk,
                    cd_prestador or "novo",
                )
                messages.error(request, "Não foi possível gravar o prestador. Consulte o log técnico.")
        else:
            logger.warning(
                "Prestador nao gravado por validacao usuario=%s empresa=%s prestador=%s erros=%s",
                request.user.pk,
                empresa.pk,
                cd_prestador or "novo",
                form.errors.as_json(),
            )
    return render(
        request,
        "atendimento/cadastro_profissional.html",
        {"form": form, "prestador": prestador, "return_to": request.current_return_url},
    )


@login_required
@role_required("TI")
def alternar_status_prestador(request, cd_prestador):
    if request.method != "POST":
        raise PermissionDenied
    empresa = _empresa_logada(request)
    provider = get_object_or_404(Prestador, cd_empresa=empresa, cd_prestador=cd_prestador)
    provider.sn_ativo = not provider.sn_ativo
    _apply_audit(provider, request.user)
    provider.save()
    messages.success(request, f"Prestador {'reativado' if provider.sn_ativo else 'desativado'} com sucesso.")
    return redirect("atendimento:cadastro-profissional", cd_prestador=provider.pk)


@login_required
@role_required("Enfermeiro")
def iniciar_pre_atendimento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    request.current_tab_title = "Atendimento > Pré-atendimento"
    request.current_tab_root_title = "Pré-atendimento"
    request.current_module_title = "Atendimento"
    pre_atendimento = getattr(agendamento, "pre_atendimento", None)
    form = PreAtendimentoForm(request.POST or None, instance=pre_atendimento, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_paciente = agendamento.cd_paciente
        saved.cd_agendamento = agendamento
        saved.dh_fim = timezone.now()
        _apply_audit(saved, request.user)
        saved.save()
        agendamento.ds_status = "RECEPCIONADO"
        agendamento.save(update_fields=["ds_status", "dh_atualizacao"])
        atendimento = Atendimento.objects.filter(cd_empresa=empresa, cd_agendamento=agendamento).first()
        if atendimento:
            atendimento.cd_pre_atendimento = saved
            atendimento.ds_queixa_principal = saved.ds_queixa_principal
            atendimento.save(update_fields=["cd_pre_atendimento", "ds_queixa_principal", "dh_atualizacao"])
            _mudar_status_atendimento(atendimento, "AGUARDANDO_CONSULTA", request.user, origem="pre_atendimento")
        messages.success(request, "Pré-atendimento concluído e paciente encaminhado por prioridade.")
        return redirect("atendimento:atender-agendamento")
    return render(
        request,
        "atendimento/pre_atendimento.html",
        {"form": form, "agendamento": agendamento, "paciente": agendamento.cd_paciente},
    )


@login_required
@role_required("Enfermeiro")
def iniciar_pre_atendimento_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_agendamento"),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    request.current_tab_title = "Atendimento > Pré-atendimento"
    request.current_tab_root_title = "Pré-atendimento"
    request.current_module_title = "Atendimento"
    form = PreAtendimentoForm(request.POST or None, instance=atendimento.cd_pre_atendimento, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_paciente = atendimento.cd_paciente
        saved.cd_agendamento = atendimento.cd_agendamento
        saved.dh_fim = timezone.now()
        _apply_audit(saved, request.user)
        saved.save()
        atendimento.cd_pre_atendimento = saved
        atendimento.ds_queixa_principal = saved.ds_queixa_principal
        atendimento.save(update_fields=["cd_pre_atendimento", "ds_queixa_principal", "dh_atualizacao"])
        _mudar_status_atendimento(atendimento, "AGUARDANDO_CONSULTA", request.user, origem="pre_atendimento")
        messages.success(request, "Pré-atendimento concluído e paciente encaminhado por prioridade.")
        return redirect("atendimento:fila-classificacao")
    return render(
        request,
        "atendimento/pre_atendimento.html",
        {"form": form, "agendamento": atendimento.cd_agendamento, "paciente": atendimento.cd_paciente, "atendimento": atendimento},
    )


@login_required
@role_required("Recepcionista", "Médico")
def iniciar_atendimento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    atendimento, created = Atendimento.objects.get_or_create(
        cd_empresa=empresa,
        cd_agendamento=agendamento,
        defaults={
            "cd_paciente": agendamento.cd_paciente,
            "cd_pre_atendimento": getattr(agendamento, "pre_atendimento", None),
            "cd_prestador": agendamento.cd_agenda_profissional.cd_prestador if agendamento.cd_agenda_profissional else None,
            "cd_convenio": agendamento.cd_paciente.cd_convenio,
            "ds_origem": "AGENDADO",
            "ds_tipo_atendimento": agendamento.ds_tipo_atendimento,
            "ds_especialidade": agendamento.ds_especialidade,
            "ds_plano": agendamento.ds_plano,
            "ds_status": "AGUARDANDO_CLASSIFICACAO",
            "cd_usuario_criacao": request.user,
            "cd_usuario_atualizacao": request.user,
        },
    )
    if created:
        _registrar_fluxo(atendimento, "", atendimento.ds_status, request.user, origem="iniciar_atendimento")
    _vincular_prestador_atendimento(atendimento, atendimento.cd_prestador, request.user, principal=True)
    agendamento.ds_status = "EM_ATENDIMENTO"
    agendamento.save(update_fields=["ds_status"])
    return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.cd_atendimento)


@login_required
@role_required("Recepcionista")
def recepcao(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Recepção"
    request.current_tab_root_title = "Recepção"
    request.current_module_title = "Atendimento"
    agendamentos = (
        Agendamento.objects.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador")
        .filter(cd_empresa=empresa, dh_agendamento__date=timezone.localdate())
        .exclude(ds_status__in=["CANCELADO", "FALTOU"])
        .order_by("dh_agendamento")
    )
    return render(request, "atendimento/recepcao.html", {"agendamentos": agendamentos})


@login_required
@role_required("Recepcionista")
def agendamentos_operacionais(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Agendamentos"
    request.current_tab_root_title = "Agendamentos"
    request.current_module_title = "Atendimento"
    hoje = timezone.localdate()
    data = request.GET.get("data") or hoje.isoformat()
    data_inicio = _parse_date(data, hoje)
    selecionar_intervalo = request.GET.get("intervalo") == "1"
    data_final = _parse_date(request.GET.get("data_fim"), data_inicio) if selecionar_intervalo else data_inicio
    mes = int(request.GET.get("mes") or data_inicio.month)
    ano = int(request.GET.get("ano") or data_inicio.year)
    data_calendario = data_inicio.replace(year=ano, month=mes, day=min(data_inicio.day, calendar.monthrange(ano, mes)[1]))
    termo = request.GET.get("q", "").strip().replace("%", "")
    todos = request.GET.get("todas_especialidades", "1") == "1" and not request.GET.getlist("especialidades")
    especialidades_selecionadas = [value for value in request.GET.getlist("especialidades") if value]
    registros = (
        Agendamento.objects.select_related(
            "cd_paciente",
            "cd_paciente__cd_convenio",
            "cd_agenda_profissional__cd_prestador",
            "atendimento",
        )
        .filter(cd_empresa=empresa, dh_agendamento__date__gte=data_inicio, dh_agendamento__date__lte=data_final)
        .order_by("dh_agendamento")
    )
    if not todos and especialidades_selecionadas:
        registros = registros.filter(ds_especialidade__in=especialidades_selecionadas)
    if termo:
        filtros = (
            Q(cd_paciente__nm_paciente__icontains=termo)
            | Q(cd_paciente__nr_cpf__icontains=termo)
            | Q(cd_paciente__nr_cartao_sus__icontains=termo)
            | Q(cd_paciente__nr_rg__icontains=termo)
            | Q(ds_profissional__icontains=termo)
            | Q(cd_agenda_profissional__cd_prestador__nm_prestador__icontains=termo)
            | Q(ds_especialidade__icontains=termo)
            | Q(cd_paciente__nm_mae__icontains=termo)
        )
        if termo.isdigit():
            filtros |= Q(cd_paciente_id=int(termo))
        if re.match(r"^\d{1,2}:\d{2}$", termo):
            filtros |= Q(dh_agendamento__time=datetime.strptime(termo, "%H:%M").time())
        registros = registros.filter(filtros)
    especialidades_qs = ValorAuxiliarGlobal.objects.filter(cd_tabela_auxiliar_global__ds_tabela="especialidade", sn_ativo=True).order_by("ds_valor")
    especialidades = [{"codigo": item.cd_valor, "descricao": item.ds_valor} for item in especialidades_qs]
    if not especialidades:
        especialidades = [
            {"codigo": value, "descricao": value}
            for value in Agendamento.objects.filter(cd_empresa=empresa)
            .exclude(ds_especialidade="")
            .order_by("ds_especialidade")
            .values_list("ds_especialidade", flat=True)
            .distinct()
        ]
    calendario = _calendario_mensal(empresa, data_calendario, data_final if selecionar_intervalo else None)
    return render(
        request,
        "atendimento/agendamentos_operacionais.html",
        {
            "registros": registros[:200],
            "data": data_inicio.isoformat(),
            "data_fim": data_final.isoformat(),
            "selecionar_intervalo": selecionar_intervalo,
            "termo": termo,
            "todos": todos,
            "especialidades": especialidades,
            "especialidades_selecionadas": especialidades_selecionadas,
            "calendario": calendario,
        },
    )


@login_required
@role_required("Recepcionista")
def recepcionar_agendamento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(Agendamento, cd_empresa=empresa, cd_agendamento=cd_agendamento)
    atendimento_existente = Atendimento.objects.filter(cd_empresa=empresa, cd_agendamento=agendamento).first()
    if atendimento_existente:
        messages.warning(request, "Este agendamento já possui atendimento gerado.")
        return redirect("atendimento:recepcao")
    agendamento.ds_status = "RECEPCIONADO"
    agendamento.cd_usuario_atualizacao = request.user
    agendamento.save(update_fields=["ds_status", "cd_usuario_atualizacao", "dh_atualizacao"])
    atendimento, created = Atendimento.objects.get_or_create(
        cd_empresa=empresa,
        cd_agendamento=agendamento,
        defaults={
            "cd_paciente": agendamento.cd_paciente,
            "cd_prestador": agendamento.cd_agenda_profissional.cd_prestador if agendamento.cd_agenda_profissional else None,
            "cd_convenio": agendamento.cd_paciente.cd_convenio,
            "ds_origem": "ENCAIXE" if agendamento.sn_encaixe else "AGENDADO",
            "ds_tipo_atendimento": agendamento.ds_tipo_atendimento,
            "ds_especialidade": agendamento.ds_especialidade,
            "ds_plano": agendamento.ds_plano,
            "ds_status": "AGUARDANDO_CLASSIFICACAO",
            "cd_usuario_criacao": request.user,
            "cd_usuario_atualizacao": request.user,
        },
    )
    if created:
        _mudar_status_atendimento(atendimento, "AGUARDANDO_CLASSIFICACAO", request.user, origem="recepcao")
    _vincular_prestador_atendimento(atendimento, atendimento.cd_prestador, request.user, principal=True)
    messages.success(request, "Paciente recepcionado e encaminhado para classificação.")
    return redirect("atendimento:atender-agendamento")


@login_required
@role_required("Médico")
def ficha_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related(
            "cd_paciente",
            "cd_agendamento",
            "cd_pre_atendimento",
            "cd_prestador",
        ),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    request.current_tab_title = "Atendimento > Ficha de atendimento"
    request.current_tab_root_title = f"Atendimento {atendimento.cd_atendimento}"
    request.current_module_title = "Atendimento"
    request.current_return_url = _safe_return_url(request)
    status_final = request.POST.get("status_final") or "FINALIZADO"
    form = AtendimentoForm(request.POST or None, instance=atendimento, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_usuario_atualizacao = request.user
        saved.save()
        _vincular_prestador_atendimento(saved, saved.cd_prestador, request.user, principal=True)
        if saved.cd_agendamento:
            saved.cd_agendamento.ds_status = "EM_ATENDIMENTO"
            saved.cd_agendamento.cd_usuario_atualizacao = request.user
            saved.cd_agendamento.save(update_fields=["ds_status", "cd_usuario_atualizacao", "dh_atualizacao"])
        messages.success(request, "Consulta salva. Continue com prescrição, evolução ou alta.")
        if request.POST.get("finalizar") == "1":
            _mudar_status_atendimento(saved, status_final, request.user, origem="ficha_atendimento")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=saved.cd_atendimento)
    historico = Atendimento.objects.filter(cd_empresa=empresa, cd_paciente=atendimento.cd_paciente).exclude(pk=atendimento.pk)[:10]
    grupos = set(request.user.groups.values_list("name", flat=True))
    clinical_permissions = {
        "medico": request.user.is_superuser or bool(grupos.intersection({"TI", "Médico", "MÃ©dico"})),
        "enfermeiro": request.user.is_superuser or bool(grupos.intersection({"TI", "Enfermeiro"})),
        "laboratorio": request.user.is_superuser or bool(grupos.intersection({"TI", "Laboratório", "Laboratorio"})),
    }
    return render(
        request,
        "atendimento/ficha_atendimento.html",
        {
            "form": form,
            "atendimento": atendimento,
            "paciente": atendimento.cd_paciente,
            "idade": _idade(atendimento.cd_paciente.dt_nascimento),
            "historico": historico,
            "documentos": atendimento.documentos.all(),
            "clinical_permissions": clinical_permissions,
        },
    )


@login_required
@role_required("Médico")
def solicitar_exame(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    form = SolicitacaoExameForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "SOLICITACAO_EXAME",
            f"Solicitação de exame {saved.cd_solicitacao_exame}",
            f"Exame: {saved.ds_exame}\nPrioridade: {saved.get_ds_prioridade_display()}\nJustificativa: {saved.ds_justificativa}",
            request.user,
        )
        _mudar_status_atendimento(atendimento, "AGUARDANDO_EXAMES", request.user, origem="solicitacao_exame")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/solicitar_exame.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("TI")
def resultado_exame(request, cd_solicitacao):
    empresa = _empresa_logada(request)
    solicitacao = get_object_or_404(SolicitacaoExame, cd_empresa=empresa, cd_solicitacao_exame=cd_solicitacao)
    resultado = getattr(solicitacao, "resultado", None)
    form = ResultadoExameForm(request.POST or None, request.FILES or None, instance=resultado)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_solicitacao_exame = solicitacao
        if saved.sn_liberado:
            saved.dh_liberacao = timezone.now()
            solicitacao.ds_status = "LIBERADO"
            solicitacao.save(update_fields=["ds_status", "dh_atualizacao"])
        _apply_audit(saved, request.user)
        saved.save()
        if saved.sn_liberado:
            _mudar_status_atendimento(solicitacao.cd_atendimento, "RETORNO_EXAMES", request.user, origem="resultado_exame")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=solicitacao.cd_atendimento_id)
    return render(request, "atendimento/resultado_exame.html", {"form": form, "solicitacao": solicitacao})


@login_required
@role_required("Médico")
def prescrever(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    form = PrescricaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "PRESCRICAO",
            f"Prescrição {saved.cd_prescricao}",
            f"{saved.ds_prescricao}\n\nOrientações: {saved.ds_orientacoes}",
            request.user,
        )
        messages.success(request, "Prescrição registrada.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/prescricao.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("Médico")
def evoluir(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    if not atendimento.cd_prestador:
        messages.error(request, "Informe o prestador na consulta antes de evoluir.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    form = EvolucaoAtendimentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        saved.cd_prestador = atendimento.cd_prestador
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "EVOLUCAO",
            f"Evolução {saved.cd_evolucao_atendimento}",
            saved.ds_evolucao,
            request.user,
        )
        messages.success(request, "Evolução registrada.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/evolucao.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("Médico")
def conceder_alta(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    if request.method == "POST":
        atendimento.ds_destino = request.POST.get("ds_destino", "").strip()
        if not atendimento.cd_prestador or not atendimento.ds_conduta or not (atendimento.ds_diagnostico or atendimento.ds_hipotese_diagnostica) or not atendimento.ds_destino:
            messages.error(request, "Informe profissional, diagnóstico ou hipótese, conduta e destino antes da alta.")
            return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
        _criar_documento_clinico(
            atendimento,
            "RESUMO_ALTA",
            f"Resumo de alta {atendimento.pk}",
            f"Diagnóstico/Hipótese: {atendimento.ds_diagnostico or atendimento.ds_hipotese_diagnostica}\nConduta: {atendimento.ds_conduta}\nDestino: {atendimento.ds_destino}",
            request.user,
        )
        _mudar_status_atendimento(atendimento, "ALTA_MEDICA", request.user, origem="alta_medica")
        messages.success(request, "Alta concedida. Finalize o atendimento para concluir o fluxo.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/alta.html", {"atendimento": atendimento})


@login_required
@role_required("Médico")
def finalizar_atendimento(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    if request.method != "POST":
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    if atendimento.ds_status not in {"ALTA", "ALTA_MEDICA"}:
        messages.error(request, "Conceda a alta antes de finalizar o atendimento.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    _mudar_status_atendimento(atendimento, "FINALIZADO", request.user, origem="finalizar_atendimento")
    if atendimento.cd_agendamento:
        atendimento.cd_agendamento.ds_status = "FINALIZADO"
        atendimento.cd_agendamento.save(update_fields=["ds_status", "dh_atualizacao"])
    messages.success(request, "Atendimento finalizado com sucesso.")
    return redirect("atendimento:atendimentos")


@login_required
def imprimir_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_pre_atendimento", "cd_agendamento"),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    return render(request, "atendimento/imprimir_atendimento.html", {"atendimento": atendimento, "empresa": empresa})


@login_required
@role_required("TI")
def modelos_documento(request, cd_modelo=None):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Modelos de documentos"
    request.current_tab_root_title = "Modelos de documentos"
    request.current_module_title = "Atendimento"
    modelo = ModeloDocumento.objects.filter(cd_empresa=empresa, pk=cd_modelo).first() if cd_modelo else None
    form = ModeloDocumentoForm(request.POST or None, instance=modelo)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        _apply_audit(saved, request.user)
        saved.save()
        messages.success(request, "Modelo de documento salvo com sucesso.")
        return redirect("atendimento:modelos-documento")
    modelos = ModeloDocumento.objects.filter(cd_empresa=empresa).order_by("tp_documento", "nm_modelo")
    return render(request, "atendimento/modelos_documento.html", {"form": form, "modelos": modelos, "modelo": modelo})


@login_required
@role_required("TI", "Médico", "MÃ©dico", "Enfermeiro")
def imprimir_documento_clinico(request, cd_documento):
    empresa = _empresa_logada(request)
    documento = get_object_or_404(
        DocumentoClinico.objects.select_related("cd_atendimento__cd_paciente", "cd_atendimento__cd_prestador", "cd_usuario_emissor"),
        cd_empresa=empresa,
        cd_documento_clinico=cd_documento,
    )
    return render(request, "atendimento/documento_clinico.html", {"documento": documento, "atendimento": documento.cd_atendimento, "empresa": empresa})


@login_required
@role_required("TI", "Médico", "MÃ©dico")
def copiar_documento_clinico(request, cd_documento):
    empresa = _empresa_logada(request)
    origem = get_object_or_404(DocumentoClinico, cd_empresa=empresa, cd_documento_clinico=cd_documento)
    copia = _criar_documento_clinico(
        origem.cd_atendimento,
        origem.tp_documento,
        f"Cópia de {origem.ds_titulo}",
        origem.ds_conteudo,
        request.user,
        origem=origem,
    )
    messages.success(request, "Documento copiado como rascunho.")
    return redirect("atendimento:imprimir-documento-clinico", cd_documento=copia.pk)


def _editable_auxiliary(request, table_name, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
    tabela, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela=table_name,
        defaults={"ds_descricao": title, "sn_ativo": True},
    )
    query = _query_text(request)
    if request.method == "POST":
        for valor in tabela.valores.all():
            if request.POST.get(f"delete_{valor.pk}") == "1":
                valor.sn_ativo = False
                valor.save(update_fields=["sn_ativo", "updated_at"])
                continue
            if f"description_{valor.pk}" not in request.POST:
                continue
            valor.ds_valor = request.POST.get(f"description_{valor.pk}", valor.ds_valor)
            valor.sn_ativo = request.POST.get(f"active_{valor.pk}") == "true"
            valor.save()
        new_descriptions = request.POST.getlist("new_description")
        new_actives = request.POST.getlist("new_active")
        created = 0
        for index, description in enumerate(new_descriptions):
            description = description.strip()
            if not description:
                continue
            code = _auxiliary_code(description)
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": (new_actives[index] if index < len(new_actives) else "true") == "true"},
            )
            created += 1
        if new_descriptions and not created and not any(
            request.POST.get(f"description_{valor.pk}", "").strip()
            for valor in tabela.valores.all()
        ):
            messages.error(request, "Informe a descrição obrigatória antes de salvar.")
        else:
            messages.success(request, f"{title} salvo com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    valores = tabela.valores.all()
    if query:
        value_filter = Q(cd_valor__icontains=query) | Q(ds_valor__icontains=query)
        if query.isdigit():
            value_filter |= Q(cd_valor_auxiliar_global=int(query))
        valores = valores.filter(value_filter)
    valores = paginate_table(
        request,
        valores,
        {"cd_valor_auxiliar_global", "cd_valor", "ds_valor", "sn_ativo"},
        "cd_valor_auxiliar_global",
    )
    return render(request, "atendimento/editable_auxiliary.html", {"title": title, "tabela": tabela, "valores": valores})


def _editable_escalas(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
    empresa = _empresa_logada(request)
    registros = AgendaProfissional.objects.select_related("cd_prestador").filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        registros = registros.filter(Q(ds_agenda__icontains=query) | Q(cd_prestador__nm_prestador__icontains=query) | Q(cd_prestador__ds_especialidade__icontains=query))
    registros = paginate_table(
        request,
        registros,
        {
            "cd_agenda_profissional",
            "cd_prestador__nm_prestador",
            "ds_agenda",
            "nr_dia_semana",
            "hr_inicio",
            "hr_fim",
            "nr_tempo_atendimento",
            "nr_intervalo",
            "sn_ativo",
        },
        "cd_agenda_profissional",
    )
    prestadores = Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_agenda=True)
    if request.method == "POST":
        for escala in registros:
            if request.POST.get(f"delete_{escala.pk}") == "1":
                escala.delete()
                continue
            if f"name_{escala.pk}" not in request.POST:
                continue
            escala.cd_prestador_id = request.POST.get(f"provider_{escala.pk}") or escala.cd_prestador_id
            escala.ds_agenda = request.POST.get(f"name_{escala.pk}", escala.ds_agenda)
            escala.nr_dia_semana = request.POST.get(f"weekday_{escala.pk}", escala.nr_dia_semana)
            escala.hr_inicio = request.POST.get(f"start_{escala.pk}", escala.hr_inicio)
            escala.hr_fim = request.POST.get(f"end_{escala.pk}", escala.hr_fim)
            escala.nr_tempo_atendimento = request.POST.get(f"duration_{escala.pk}", escala.nr_tempo_atendimento)
            escala.nr_intervalo = request.POST.get(f"interval_{escala.pk}", escala.nr_intervalo)
            escala.sn_ativo = request.POST.get(f"active_{escala.pk}") == "true"
            _apply_audit(escala, request.user)
            escala.save()
        new_providers = request.POST.getlist("new_provider")
        for index, provider_id in enumerate(new_providers):
            if not provider_id:
                continue
            escala = AgendaProfissional(
                cd_empresa=empresa,
                cd_prestador_id=provider_id,
                ds_agenda=request.POST.getlist("new_name")[index].strip() if index < len(request.POST.getlist("new_name")) else "ESCALA",
                nr_dia_semana=request.POST.getlist("new_weekday")[index] if index < len(request.POST.getlist("new_weekday")) else 0,
                hr_inicio=request.POST.getlist("new_start")[index] if index < len(request.POST.getlist("new_start")) else "08:00",
                hr_fim=request.POST.getlist("new_end")[index] if index < len(request.POST.getlist("new_end")) else "12:00",
                nr_tempo_atendimento=request.POST.getlist("new_duration")[index] if index < len(request.POST.getlist("new_duration")) else 30,
                nr_intervalo=request.POST.getlist("new_interval")[index] if index < len(request.POST.getlist("new_interval")) else 0,
                sn_ativo=(request.POST.getlist("new_active")[index] if index < len(request.POST.getlist("new_active")) else "true") == "true",
            )
            _apply_audit(escala, request.user)
            escala.save()
        messages.success(request, "Escalas salvas com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(
        request,
        "atendimento/editable_escalas.html",
        {"title": title, "registros": registros, "prestadores": prestadores, "dias_semana": AgendaProfissional.DIAS_SEMANA},
    )


def _agenda_dashboard(request):
    request.current_tab_title = "Agendas"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = False
    empresa = _empresa_logada(request)
    hoje = timezone.localdate()
    agendamentos_hoje = Agendamento.objects.filter(cd_empresa=empresa, dh_agendamento__date=hoje)
    total_agendado = agendamentos_hoje.count()
    total_confirmado = agendamentos_hoje.filter(sn_confirmado=True).count()
    especialidade_totais = {}
    for item in agendamentos_hoje.values("ds_especialidade"):
        chave = item["ds_especialidade"] or "Não informada"
        especialidade_totais[chave] = especialidade_totais.get(chave, 0) + 1
    return render(
        request,
        "atendimento/agendas_dashboard.html",
        {
            "total_agendado": total_agendado,
            "total_confirmado": total_confirmado,
            "total_pendente": max(total_agendado - total_confirmado, 0),
            "especialidade_totais": especialidade_totais.items(),
            "horarios": _horarios_disponiveis(empresa),
            "agendamentos": agendamentos_hoje.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador"),
        },
    )


def _fila_atendimento(request):
    request.current_tab_title = "Atendimento > Fila de atendimento"
    request.current_tab_root_title = "Atender"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    fila = (
        Agendamento.objects.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador", "pre_atendimento")
        .filter(
            cd_empresa=empresa,
            ds_status__in=["AGENDADO", "AGUARDANDO_PRE_ATENDIMENTO", "AGUARDANDO_ATENDIMENTO"],
        )
        .order_by("pre_atendimento__nr_prioridade", "dh_agendamento", "dh_criacao")
    )
    return render(request, "atendimento/fila_atendimento.html", {"fila": fila})


@login_required
@role_required("Recepcionista", "Enfermeiro", "Médico")
def atendimentos(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Atendimentos"
    request.current_tab_root_title = "Atendimentos"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_prestador").filter(cd_empresa=empresa).order_by("-dh_inicio")[:100]
    return render(request, "atendimento/atendimentos.html", {"registros": registros})


@login_required
@role_required("TI", "Médico", "Enfermeiro")
def pep(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > PEP"
    request.current_tab_root_title = "PEP"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    setores = Setor.objects.filter(cd_empresa=empresa, tp_setor=Setor.TipoSetor.ATENDIMENTO, sn_ativo=True)
    if not request.user.groups.filter(name="TI").exists():
        setores = setores.filter(usuarios=request.user)
    setores = setores.distinct().order_by("nm_setor")
    aba = request.GET.get("aba", "atendimentos")
    setor_ids = [value for value in request.GET.getlist("setores") if value.isdigit()]
    usar_todos_setores = request.GET.get("todos_setores", "1") == "1" and not setor_ids
    setores_filtrados = setores if usar_todos_setores else setores.filter(pk__in=setor_ids)
    atendimentos_setor = (
        Atendimento.objects.select_related("cd_paciente", "cd_paciente__cd_convenio", "cd_convenio", "cd_prestador", "cd_pre_atendimento", "cd_setor_atual")
        .prefetch_related("solicitacoes_exames", "prescricoes")
        .filter(cd_empresa=empresa, sn_ativo=True)
        .filter(ds_status__in=["AGUARDANDO_CONSULTA", "EM_ATENDIMENTO", "AGUARDANDO_EXAMES", "RETORNO_EXAMES", "EM_OBSERVACAO"])
        .order_by("cd_pre_atendimento__nr_prioridade", "dh_inicio")
    )
    if setores_filtrados.exists():
        atendimentos_setor = atendimentos_setor.filter(Q(cd_setor_atual__in=setores_filtrados) | Q(cd_setor_atual__isnull=True))
    elif setores.exists():
        atendimentos_setor = atendimentos_setor.none()
    if getattr(request.user, "cd_prestador_id", None) and not request.user.groups.filter(name="TI").exists():
        atendimentos_setor = atendimentos_setor.filter(Q(cd_prestador=request.user.cd_prestador) | Q(cd_prestador__isnull=True))
    busca_atendimento = request.GET.get("q_atendimento", "").strip().replace("%", "")
    nr_atendimento = request.GET.get("nr_atendimento", "").strip()
    if nr_atendimento.isdigit():
        atendimentos_setor = atendimentos_setor.filter(cd_atendimento=int(nr_atendimento))
        busca_atendimento = ""
    elif busca_atendimento:
        filtros_atendimento = (
            Q(cd_paciente__nm_paciente__icontains=busca_atendimento)
            | Q(cd_paciente__nr_cpf__icontains=busca_atendimento)
            | Q(cd_paciente__nr_cartao_sus__icontains=busca_atendimento)
            | Q(cd_paciente__nr_rg__icontains=busca_atendimento)
        )
        if busca_atendimento.isdigit():
            filtros_atendimento |= Q(cd_paciente_id=int(busca_atendimento))
        atendimentos_setor = atendimentos_setor.filter(filtros_atendimento)

    pacientes_geral = Paciente.objects.none()
    paciente_selecionado = None
    atendimentos_paciente = Atendimento.objects.none()
    atendimento_selecionado = None
    busca = request.GET.get("q", "").strip().replace("%", "")
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    paciente_id = request.GET.get("paciente")
    atendimento_id = request.GET.get("atendimento")
    if aba == "todos":
        pacientes_geral = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if busca:
            filtros = (
                Q(nm_paciente__icontains=busca)
                | Q(nr_cpf__icontains=busca)
                | Q(nr_cartao_sus__icontains=busca)
                | Q(nr_rg__icontains=busca)
                | Q(atendimento__cd_atendimento__icontains=busca)
            )
            if busca.isdigit():
                filtros |= Q(cd_paciente=int(busca))
            pacientes_geral = pacientes_geral.filter(filtros)
        elif not data_inicio and not data_fim:
            pacientes_geral = pacientes_geral.none()
        if data_inicio:
            pacientes_geral = pacientes_geral.filter(atendimento__dh_inicio__date__gte=data_inicio)
        if data_fim:
            pacientes_geral = pacientes_geral.filter(atendimento__dh_inicio__date__lte=data_fim)
        pacientes_geral = pacientes_geral.distinct().order_by("nm_paciente")[:50]
        if paciente_id:
            paciente_selecionado = get_object_or_404(Paciente, cd_empresa=empresa, pk=paciente_id)
            atendimentos_paciente = (
                Atendimento.objects.select_related("cd_prestador", "cd_pre_atendimento", "cd_convenio")
                .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes")
                .filter(cd_empresa=empresa, cd_paciente=paciente_selecionado)
                .order_by("-dh_inicio")
            )
        if atendimento_id:
            atendimento_selecionado = get_object_or_404(
                Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_pre_atendimento", "cd_convenio")
                .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes"),
                cd_empresa=empresa,
                pk=atendimento_id,
            )
            paciente_selecionado = atendimento_selecionado.cd_paciente
            atendimentos_paciente = Atendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente_selecionado).order_by("-dh_inicio")
    return render(
        request,
        "atendimento/pep.html",
        {
            "setores": setores,
            "setores_filtrados": setores_filtrados,
            "setor_ids": [str(value) for value in setores_filtrados.values_list("pk", flat=True)],
            "setor_chamada_padrao": setores_filtrados.first(),
            "usar_todos_setores": usar_todos_setores,
            "atendimentos": atendimentos_setor[:80],
            "aba": aba,
            "busca_atendimento": busca_atendimento,
            "nr_atendimento": nr_atendimento,
            "busca": busca,
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
def pep_chamar(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    setor = get_object_or_404(Setor, cd_empresa=empresa, pk=request.POST.get("setor"))
    ChamadaPainel.objects.create(
        cd_empresa=empresa,
        cd_atendimento=atendimento,
        cd_setor=setor,
        ds_local=f"{setor.nm_setor}",
        cd_usuario_criacao=request.user,
        cd_usuario_atualizacao=request.user,
    )
    messages.success(request, "Paciente enviado para o painel de chamada.")
    return redirect(f"{reverse('atendimento:pep')}?aba=atendimentos&todos_setores=0&setores={setor.pk}")


@login_required
@role_required("TI")
def paineis_chamada(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Painéis de chamada"
    request.current_tab_root_title = "Painéis de chamada"
    request.current_module_title = "Atendimento"
    setores = Setor.objects.filter(cd_empresa=empresa, tp_setor=Setor.TipoSetor.ATENDIMENTO, sn_ativo=True).order_by("nm_setor")
    if request.method == "POST":
        painel_id = request.POST.get("painel")
        painel = PainelChamada.objects.filter(cd_empresa=empresa, pk=painel_id).first() if painel_id else PainelChamada(cd_empresa=empresa)
        painel.nm_painel = request.POST.get("nm_painel", "").strip()
        painel.ds_descricao = request.POST.get("ds_descricao", "").strip()
        painel.nm_maquina = request.POST.get("nm_maquina", "").strip()
        painel.tp_painel = request.POST.get("tp_painel") or "PAINEL"
        painel.nr_referencia = request.POST.get("nr_referencia", "").strip()
        painel.ds_local_exibicao = request.POST.get("ds_local_exibicao", "").strip()
        painel.ds_mensagem_padrao = request.POST.get("ds_mensagem_padrao", "").strip()
        painel.nr_tempo_exibicao = int(request.POST.get("nr_tempo_exibicao") or 10)
        painel.ds_layout = request.POST.get("ds_layout", "padrao").strip() or "padrao"
        painel.ds_tamanho = request.POST.get("ds_tamanho", "medio").strip() or "medio"
        painel.ds_cor = request.POST.get("ds_cor", "azul").strip() or "azul"
        painel.ds_prioridade_visual = request.POST.get("ds_prioridade_visual", "normal").strip() or "normal"
        painel.sn_voz = request.POST.get("sn_voz") == "on"
        painel.ds_midia_url = request.POST.get("ds_midia_url", "").strip()
        painel.ds_observacao = request.POST.get("ds_observacao", "").strip()
        painel.sn_ativo = request.POST.get("sn_ativo") == "on"
        if painel.nm_painel and painel.nm_maquina:
            painel.cd_usuario_atualizacao = request.user
            if not painel.pk:
                painel.cd_usuario_criacao = request.user
            painel.save()
            painel.setores.set(setores.filter(pk__in=request.POST.getlist("setores")))
            messages.success(request, "Painel de chamada salvo com sucesso.")
            return redirect("atendimento:paineis-chamada")
        messages.error(request, "Informe nome do painel e nome da máquina.")
    paineis = PainelChamada.objects.prefetch_related("setores").filter(cd_empresa=empresa).order_by("nm_painel")
    return render(request, "atendimento/paineis_chamada.html", {"paineis": paineis, "setores": setores, "tipos": PainelChamada.TIPOS})


def painel_chamada_publico(request):
    painel = None
    painel_id = request.GET.get("painel") or request.COOKIES.get("celeris_painel_chamada")
    if painel_id:
        painel = PainelChamada.objects.prefetch_related("setores").filter(pk=painel_id, sn_ativo=True).first()
    paineis = PainelChamada.objects.filter(sn_ativo=True).order_by("nm_painel")
    chamadas = ChamadaPainel.objects.none()
    if painel:
        chamadas = (
            ChamadaPainel.objects.select_related("cd_atendimento__cd_paciente", "cd_setor")
            .filter(cd_setor__in=painel.setores.all(), ds_status="CHAMADO")
            .order_by("-dh_chamada")[:8]
        )
    response = render(request, "atendimento/painel_chamada_publico.html", {"painel": painel, "paineis": paineis, "chamadas": chamadas})
    if painel:
        response.set_cookie("celeris_painel_chamada", str(painel.pk), max_age=60 * 60 * 24 * 365)
    return response


@login_required
@role_required("Enfermeiro")
def fila_classificacao(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Classificação de Risco"
    request.current_tab_root_title = "Classificação de Risco"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_agendamento").filter(
        cd_empresa=empresa,
        ds_status="AGUARDANDO_CLASSIFICACAO",
    ).order_by("dh_inicio")
    return render(request, "atendimento/fila_classificacao.html", {"registros": registros})


@login_required
@role_required("Médico")
def fila_medica(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Consultas Médicas"
    request.current_tab_root_title = "Consultas Médicas"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_pre_atendimento", "cd_prestador").filter(
        cd_empresa=empresa,
        ds_status__in=["AGUARDANDO_CONSULTA", "EM_ATENDIMENTO", "ALTA"],
    ).order_by("cd_pre_atendimento__nr_prioridade", "dh_inicio")
    return render(request, "atendimento/fila_medica.html", {"registros": registros})


@login_required
@role_required("Médico")
def abrir_consulta(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    if atendimento.ds_status == "AGUARDANDO_CONSULTA":
        _mudar_status_atendimento(atendimento, "EM_ATENDIMENTO", request.user, origem="consulta_medica")
        _vincular_prestador_atendimento(atendimento, atendimento.cd_prestador, request.user, principal=True)
    return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)


@login_required
def gerar_agenda(request):
    request.current_tab_title = "Atendimento > Agendamento > Gerar agenda"
    request.current_tab_root_title = "Gerar agenda"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    empresa = _empresa_logada(request)
    data_inicio = request.GET.get("data_inicio") or timezone.localdate().isoformat()
    data_fim = request.GET.get("data_fim") or (timezone.localdate() + timedelta(days=7)).isoformat()
    try:
        inicio = datetime.fromisoformat(data_inicio).date()
        fim = datetime.fromisoformat(data_fim).date()
    except ValueError:
        inicio = timezone.localdate()
        fim = inicio + timedelta(days=7)
    dias = max((fim - inicio).days + 1, 1)
    horarios = [
        horario
        for horario in _horarios_disponiveis(empresa, dias=dias)
        if inicio <= horario["dh_agendamento"].date() <= fim
    ]
    if request.method == "POST":
        messages.success(request, "Agenda gerada a partir das escalas cadastradas.")
        return redirect("atendimento:agendas")
    return render(
        request,
        "atendimento/gerar_agenda.html",
        {"data_inicio": inicio, "data_fim": fim, "horarios": horarios},
    )

def _empresa_logada(request):
    cd_empresa = request.session.get("cd_empresa") or 1
    return get_object_or_404(Empresa, cd_empresa=cd_empresa, sn_ativo=True)


@login_required
@role_required("Recepcionista")
def agendar_consultar_paciente(request):
    request.current_tab_title = "Atendimento > Agendamento > Agendar"
    request.current_module_title = "Atendimento"
    request.current_start_query = not bool(request.GET)
    empresa = _empresa_logada(request)
    form = PacienteSearchForm(request.GET or None)
    pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True).none()
    if request.GET and form.is_valid():
        cd_paciente = form.cleaned_data.get("cd_paciente")
        termo = form.cleaned_data.get("termo") or ""
        nr_cpf = form.cleaned_data.get("nr_cpf") or ""
        nr_cartao_sus = form.cleaned_data.get("nr_cartao_sus") or ""
        dt_nascimento = form.cleaned_data.get("dt_nascimento")
        nm_mae = form.cleaned_data.get("nm_mae") or ""
        pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if cd_paciente:
            pacientes = pacientes.filter(cd_paciente=cd_paciente)
        if termo:
            termo_like = termo.replace("%", "")
            pacientes = pacientes.filter(
                Q(nm_paciente__icontains=termo_like)
                | Q(nm_social__icontains=termo_like)
                | Q(nm_mae__icontains=termo_like)
                | Q(nr_celular__icontains=termo_like)
            )
        if nr_cpf:
            pacientes = pacientes.filter(nr_cpf__icontains=nr_cpf.replace("%", ""))
        if nr_cartao_sus:
            pacientes = pacientes.filter(nr_cartao_sus__icontains=nr_cartao_sus.replace("%", ""))
        if dt_nascimento:
            pacientes = pacientes.filter(dt_nascimento=dt_nascimento)
        if nm_mae:
            pacientes = pacientes.filter(nm_mae__icontains=nm_mae.replace("%", ""))
        if pacientes.count() > 30:
            messages.warning(request, "Muitos pacientes encontrados. Refine a busca com CPF, prontuário ou mais dados do paciente.")
    return render(request, "atendimento/agendar_consulta_paciente.html", {"form": form, "pacientes": pacientes})


@login_required
@role_required("Recepcionista")
def cadastro_paciente(request, cd_paciente=None, fluxo_agendamento=True):
    request.current_tab_title = (
        "Atendimento > Agendamento > Agendar > Cadastro de paciente"
        if fluxo_agendamento
        else "Pacientes > Cadastro de paciente"
    )
    request.current_module_title = "Atendimento" if fluxo_agendamento else "Pacientes"
    request.current_tab_root_title = "Cadastro de paciente"
    empresa = _empresa_logada(request)
    if request.GET.get("consultar") == "1":
        registros = Paciente.objects.filter(cd_empresa=empresa)
        has_filter = False
        patient_code = request.GET.get("cd_paciente", "").strip()
        if patient_code.isdigit():
            registros = registros.filter(cd_paciente=int(patient_code))
            has_filter = True
        text_fields = (
            "nm_paciente", "nm_social", "nr_cpf", "nr_rg", "ds_orgao_emissor",
            "nr_cartao_sus", "nr_convenio", "nm_mae", "nm_pai", "nm_conjuge",
            "nr_telefone", "nr_celular", "nr_celular_2", "ds_email",
            "ds_endereco", "nr_endereco", "ds_complemento", "ds_bairro",
        )
        exact_fields = (
            "tp_sexo", "tp_genero", "ds_cor_raca", "tp_estado_civil", "tp_sanguineo",
            "ds_nacionalidade", "ds_naturalidade", "ds_profissao", "sg_estado",
            "ds_cidade", "tp_logradouro",
        )
        for field_name in text_fields:
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
                has_filter = True
        for field_name in exact_fields:
            value = request.GET.get(field_name, "").strip()
            if value:
                registros = registros.filter(**{field_name: value})
                has_filter = True
        convenio = request.GET.get("cd_convenio", "")
        if convenio.isdigit():
            registros = registros.filter(cd_convenio_id=int(convenio))
            has_filter = True
        if request.GET.get("dt_nascimento"):
            registros = registros.filter(dt_nascimento=request.GET["dt_nascimento"])
            has_filter = True
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
            has_filter = True
        if request.GET.get("cd_cep", "").isdigit():
            registros = registros.filter(cd_cep_id=int(request.GET["cd_cep"]))
            has_filter = True
        result_ids = list(registros.order_by("cd_paciente").values_list("cd_paciente", flat=True)[:200])
        request.session["consulta_pacientes"] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum paciente encontrado para os filtros informados.")
            return redirect(request.path)
        target = "atendimento:revisar-paciente-agendamento" if fluxo_agendamento else "atendimento:cadastro-paciente"
        return redirect(target, cd_paciente=result_ids[0])
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente) if cd_paciente else None
    if paciente and not fluxo_agendamento and request.user.groups.filter(name="TI").exists():
        request.current_toggle_active_url = reverse("atendimento:alternar-status-paciente", args=[paciente.pk])
        request.current_toggle_active_label = "Desativar" if paciente.sn_ativo else "Ativar"
    result_ids = request.session.get("consulta_pacientes", [])
    if paciente and paciente.cd_paciente in result_ids:
        current_index = result_ids.index(paciente.cd_paciente)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        route = "atendimento:revisar-paciente-agendamento" if fluxo_agendamento else "atendimento:cadastro-paciente"
        if current_index > 0:
            request.current_first_url = reverse(route, args=[result_ids[0]])
            request.current_previous_url = reverse(route, args=[result_ids[current_index - 1]])
        if current_index < len(result_ids) - 1:
            request.current_next_url = reverse(route, args=[result_ids[current_index + 1]])
            request.current_last_url = reverse(route, args=[result_ids[-1]])
    if fluxo_agendamento and paciente:
        request.current_continue_url = reverse("atendimento:selecionar-agenda", kwargs={"cd_paciente": paciente.cd_paciente})
    form = PacienteForm(request.POST or None, instance=paciente, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        changed_data = [
            field
            for field in form.changed_data
            if field not in {"observacao_alteracao", "motivo_alteracao"}
        ]
        if paciente and changed_data and not form.cleaned_data.get("motivo_alteracao"):
            form.add_error("motivo_alteracao", "Informe o motivo da alteração.")
            messages.error(request, "Informe o motivo da alteração para salvar o paciente.")
        elif paciente and changed_data and not form.cleaned_data.get("observacao_alteracao"):
            form.add_error("observacao_alteracao", "Informe uma observação para registrar a alteração do paciente.")
            messages.error(request, "Informe uma observação para registrar a alteração do paciente.")
        else:
            before = {field: getattr(paciente, field) for field in changed_data} if paciente else {}
            saved = form.save(commit=False)
            saved.cd_empresa = empresa
            _apply_audit(saved, request.user)
            if saved.cd_convenio:
                saved.nm_convenio = saved.cd_convenio.nm_convenio
            saved.save()
            if paciente and changed_data:
                after = {field: getattr(saved, field) for field in changed_data}
                HistoricoAlteracaoPaciente.objects.create(
                    cd_empresa=empresa,
                    cd_paciente=saved,
                    cd_usuario=request.user,
                    cd_motivo_alteracao=form.cleaned_data.get("motivo_alteracao"),
                    ds_observacao=form.cleaned_data["observacao_alteracao"],
                    ds_alteracoes={field: {"antes": str(before[field]), "depois": str(after[field])} for field in changed_data},
                    ds_antes={field: str(before[field]) for field in changed_data},
                    ds_depois={field: str(after[field]) for field in changed_data},
                )
            if fluxo_agendamento:
                messages.success(request, "Paciente salvo. Revise os dados e confirme o agendamento.")
                response = redirect("atendimento:selecionar-agenda", cd_paciente=saved.cd_paciente)
            else:
                messages.success(request, "Paciente salvo com sucesso.")
                response = redirect("atendimento:cadastro-paciente", cd_paciente=saved.cd_paciente)
            response["HX-Replace-Url"] = response["Location"]
            return response
    return render(
        request,
        "atendimento/cadastro_paciente.html",
        {"form": form, "paciente": paciente, "fluxo_agendamento": fluxo_agendamento},
    )


@login_required
@role_required("Recepcionista")
def cadastro_paciente_geral(request, cd_paciente=None):
    return cadastro_paciente(request, cd_paciente=cd_paciente, fluxo_agendamento=False)


@login_required
@role_required("TI")
def alternar_status_paciente(request, cd_paciente):
    if request.method != "POST":
        raise PermissionDenied
    empresa = _empresa_logada(request)
    patient = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    patient.sn_ativo = not patient.sn_ativo
    _apply_audit(patient, request.user)
    patient.save()
    messages.success(request, f"Paciente {'reativado' if patient.sn_ativo else 'desativado'} com sucesso.")
    return redirect("atendimento:cadastro-paciente", cd_paciente=patient.pk)


@login_required
@role_required("Recepcionista")
def selecionar_agenda(request, cd_paciente):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Selecionar agenda"
    request.current_tab_root_title = "Selecionar agenda"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    hoje = timezone.localdate()
    data_filtro = _parse_date(request.GET.get("data"), hoje)
    selecionar_intervalo = request.GET.get("intervalo") == "1"
    data_fim = _parse_date(request.GET.get("data_fim"), data_filtro) if selecionar_intervalo else data_filtro
    dias = max((data_fim - hoje).days + 1, 1)
    horarios = [
        horario
        for horario in _horarios_disponiveis(empresa, dias=dias)
        if data_filtro <= horario["dh_agendamento"].date() <= data_fim
    ]
    especialidades_selecionadas = [value for value in request.GET.getlist("especialidades") if value]
    todas_especialidades = request.GET.get("todas_especialidades", "1") == "1" and not especialidades_selecionadas
    termo = request.GET.get("q", "").strip().replace("%", "")
    if especialidades_selecionadas:
        horarios = [
            horario
            for horario in horarios
            if horario["agenda"].cd_prestador.ds_especialidade in especialidades_selecionadas
            or set(especialidades_selecionadas).intersection(horario["agenda"].cd_prestador.ds_especialidades or [])
        ]
    if termo:
        termo_lower = termo.lower()
        horarios = [
            horario
            for horario in horarios
            if termo_lower in horario["agenda"].cd_prestador.nm_prestador.lower()
            or termo_lower in (horario["agenda"].cd_prestador.nm_guerra or "").lower()
            or termo_lower in (horario["agenda"].cd_prestador.ds_especialidade or "").lower()
            or termo_lower in horario["dh_agendamento"].strftime("%H:%M")
        ]
    especialidades = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="especialidade",
        sn_ativo=True,
    ).order_by("ds_valor")
    agenda_id = request.GET.get("agenda")
    horario_iso = request.GET.get("horario")
    horario_selecionado = None
    if agenda_id and horario_iso:
        for horario in horarios:
            if str(horario["agenda"].pk) == agenda_id and horario["dh_agendamento"].isoformat() == horario_iso:
                horario_selecionado = horario
                break
    if request.method == "POST":
        agenda = get_object_or_404(AgendaProfissional, cd_empresa=empresa, cd_agenda_profissional=request.POST.get("cd_agenda_profissional"))
        dh_agendamento = parse_datetime(request.POST["dh_agendamento"])
        if dh_agendamento and timezone.is_naive(dh_agendamento):
            dh_agendamento = timezone.make_aware(dh_agendamento)
        agendamento = Agendamento(
            cd_empresa=empresa,
            cd_paciente=paciente,
            cd_agenda_profissional=agenda,
            dh_agendamento=dh_agendamento,
            ds_profissional=agenda.cd_prestador.nm_prestador,
            ds_especialidade=agenda.cd_prestador.ds_especialidade,
            ds_tipo_atendimento=request.POST.get("ds_tipo_atendimento", ""),
            ds_plano=request.POST.get("ds_plano", ""),
            sn_particular=request.POST.get("sn_particular") == "1",
            sn_encaixe=request.POST.get("sn_encaixe") == "1",
            ds_observacao=request.POST.get("ds_observacao", ""),
            sn_confirmado=True,
        )
        _apply_audit(agendamento, request.user)
        agendamento.save()
        messages.success(request, "Agendamento confirmado.")
        return redirect("atendimento:comprovante-agendamento", cd_agendamento=agendamento.pk)
    mes = int(request.GET.get("mes") or data_filtro.month)
    ano = int(request.GET.get("ano") or data_filtro.year)
    data_calendario = data_filtro.replace(year=ano, month=mes, day=min(data_filtro.day, calendar.monthrange(ano, mes)[1]))
    return render(
        request,
        "atendimento/selecionar_agenda.html",
        {
            "paciente": paciente,
            "idade": _idade(paciente.dt_nascimento),
            "horarios": horarios,
            "especialidades": especialidades,
            "data_filtro": data_filtro.isoformat(),
            "data_fim": data_fim.isoformat(),
            "selecionar_intervalo": selecionar_intervalo,
            "especialidades_selecionadas": especialidades_selecionadas,
            "todas_especialidades": todas_especialidades,
            "termo": termo,
            "calendario": _calendario_mensal(empresa, data_calendario, data_fim if selecionar_intervalo else None),
            "horario_selecionado": horario_selecionado,
        },
    )


@login_required
@role_required("Recepcionista")
def comprovante_agendamento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente", "cd_paciente__cd_convenio", "cd_agenda_profissional__cd_prestador"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    request.current_tab_title = "Atendimento > Agendamento > Comprovante"
    request.current_tab_root_title = "Comprovante"
    request.current_module_title = "Atendimento"
    return render(
        request,
        "atendimento/comprovante_agendamento.html",
        {
            "agendamento": agendamento,
            "paciente": agendamento.cd_paciente,
            "empresa": empresa,
            "idade": _idade(agendamento.cd_paciente.dt_nascimento),
            "emitido_em": timezone.now(),
        },
    )


def _horarios_disponiveis(empresa, dias=21):
    hoje = timezone.localdate()
    agendas = AgendaProfissional.objects.select_related("cd_prestador").filter(cd_empresa=empresa, sn_ativo=True, cd_prestador__sn_ativo=True)
    ocupados = set(
        Agendamento.objects.filter(cd_empresa=empresa, dh_agendamento__date__gte=hoje)
        .exclude(dh_agendamento__isnull=True)
        .values_list("cd_agenda_profissional_id", "dh_agendamento")
    )
    horarios = []
    for offset in range(dias):
        data = hoje + timedelta(days=offset)
        for agenda in agendas.filter(nr_dia_semana=data.weekday()):
            atual = datetime.combine(data, agenda.hr_inicio)
            fim = datetime.combine(data, agenda.hr_fim)
            passo = timedelta(minutes=agenda.nr_tempo_atendimento + agenda.nr_intervalo)
            while atual + timedelta(minutes=agenda.nr_tempo_atendimento) <= fim:
                aware = timezone.make_aware(atual)
                if (agenda.cd_agenda_profissional, aware) not in ocupados:
                    horarios.append({"agenda": agenda, "dh_agendamento": aware})
                atual += passo
    return horarios


@login_required
@role_required("Recepcionista")
def confirmar_agendamento(request, cd_paciente):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Confirmar agendamento"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    form = AgendamentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        agendamento = form.save(commit=False)
        agendamento.cd_empresa = empresa
        agendamento.cd_paciente = paciente
        agendamento.sn_confirmado = True
        _apply_audit(agendamento, request.user)
        agendamento.save()
        messages.success(request, "Agendamento confirmado.")
        return redirect("atendimento:agendas")
    return render(request, "atendimento/confirmar_agendamento.html", {"form": form, "paciente": paciente})


@login_required
@role_required("Recepcionista")
def demanda_espontanea(request):
    request.current_tab_title = "Atendimento > Demanda espontânea"
    request.current_tab_root_title = "Demanda espontânea"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    form = PacienteSearchForm(request.GET or None)
    pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
    if request.GET and form.is_valid():
        data = form.cleaned_data
        if data.get("cd_paciente"):
            pacientes = pacientes.filter(cd_paciente=data["cd_paciente"])
        if data.get("termo"):
            pacientes = pacientes.filter(nm_paciente__icontains=data["termo"].replace("%", ""))
        if data.get("nr_cpf"):
            pacientes = pacientes.filter(nr_cpf__icontains=data["nr_cpf"].replace("%", ""))
        if data.get("nm_mae"):
            pacientes = pacientes.filter(nm_mae__icontains=data["nm_mae"].replace("%", ""))
        if data.get("nr_cartao_sus"):
            pacientes = pacientes.filter(nr_cartao_sus__icontains=data["nr_cartao_sus"].replace("%", ""))
        if data.get("dt_nascimento"):
            pacientes = pacientes.filter(dt_nascimento=data["dt_nascimento"])
    else:
        pacientes = pacientes.none()
    if request.method == "POST":
        paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=request.POST.get("cd_paciente"))
        atendimento = Atendimento(
            cd_empresa=empresa,
            cd_paciente=paciente,
            cd_convenio=paciente.cd_convenio,
            ds_origem="DEMANDA_ESPONTANEA",
            ds_tipo_atendimento="DEMANDA_ESPONTANEA",
            ds_status="AGUARDANDO_CLASSIFICACAO",
            cd_usuario_criacao=request.user,
            cd_usuario_atualizacao=request.user,
        )
        atendimento.save()
        _registrar_fluxo(atendimento, "", atendimento.ds_status, request.user, origem="demanda_espontanea")
        messages.success(request, "Atendimento de demanda espontânea criado e encaminhado para classificação.")
        return redirect("atendimento:recepcao")
    return render(request, "atendimento/demanda_espontanea.html", {"form": form, "pacientes": pacientes})


@login_required
def verificar_paciente_unico(request):
    empresa = _empresa_logada(request)
    field = request.GET.get("field")
    value = request.GET.get("value")
    paciente_atual = request.GET.get("paciente")
    allowed_fields = {"nr_cpf": "CPF", "nr_cartao_sus": "Cartão SUS", "nr_rg": "RG"}
    if field not in allowed_fields or not value:
        return JsonResponse({"exists": False})
    if field == "nr_cpf":
        digits = "".join(character for character in value if character.isdigit())
        formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}" if len(digits) == 11 else value
        pacientes = Paciente.objects.filter(cd_empresa=empresa).filter(Q(nr_cpf=value) | Q(nr_cpf=digits) | Q(nr_cpf=formatted))
    else:
        pacientes = Paciente.objects.filter(cd_empresa=empresa, **{field: value})
    if paciente_atual:
        pacientes = pacientes.exclude(cd_paciente=paciente_atual)
    paciente = pacientes.first()
    return JsonResponse(
        {
            "exists": bool(paciente),
            "message": f"{allowed_fields[field]} já cadastrado para {paciente.nm_paciente}." if paciente else "",
        }
    )
