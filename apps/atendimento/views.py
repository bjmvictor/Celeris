from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime, timedelta

from apps.accounts.models import Empresa
from apps.core.models import TabelaAuxiliarGlobal, ValorAuxiliarGlobal

from .forms import AgendamentoForm, PacienteForm, PacienteSearchForm
from .models import AgendaProfissional, Agendamento, Convenio, HistoricoAlteracaoPaciente, Paciente, Prestador


FORM_SCREENS = {
    "agendar",
    "atender-agendamento",
    "atendimento",
    "cadastro-paciente-agendamento",
    "cadastro-paciente-atendimento",
}


def _query_text(request):
    return request.GET.get("q", "").strip().replace("%", "")

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
    "profissionais": "Profissionais",
    "salas": "Salas",
    "relatorio-agendamentos": "Relatório de Agendamentos",
    "relatorio-atendimentos": "Relatório de Atendimentos",
    "relatorio-produtividade": "Relatório de Produtividade",
}


@login_required
def screen(request, screen):
    title = SCREEN_TITLES.get(screen, "Atendimento")
    if screen in {"convenios-agendamento", "convenios-atendimento", "convenios"}:
        return _editable_convenios(request, title)
    if screen in {"profissionais"}:
        return _editable_prestadores(request, title)
    if screen in {"escalas"}:
        return _editable_escalas(request, title)
    if screen in {"agendas"}:
        return _agenda_dashboard(request)
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
    if request.method == "POST":
        for convenio in registros:
            if request.POST.get(f"delete_{convenio.pk}") == "1":
                convenio.delete()
                continue
            convenio.nm_convenio = request.POST.get(f"name_{convenio.pk}", convenio.nm_convenio)
            convenio.sn_ativo = request.POST.get(f"active_{convenio.pk}") == "true"
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
        return redirect(request.path)
    return render(request, "atendimento/editable_convenios.html", {"title": title, "registros": registros})


def _editable_prestadores(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
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
            if request.POST.get(f"delete_{prestador.pk}") == "1":
                prestador.delete()
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
        messages.success(request, "Profissionais salvos com sucesso.")
        return redirect(request.path)
    return render(request, "atendimento/editable_prestadores.html", {"title": title, "registros": registros})


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
                valor.delete()
                continue
            valor.cd_valor = request.POST.get(f"code_{valor.pk}", valor.cd_valor)
            valor.ds_valor = request.POST.get(f"description_{valor.pk}", valor.ds_valor)
            valor.sn_ativo = request.POST.get(f"active_{valor.pk}") == "true"
            valor.save()
        new_codes = request.POST.getlist("new_code")
        new_descriptions = request.POST.getlist("new_description")
        new_actives = request.POST.getlist("new_active")
        for index, code in enumerate(new_codes):
            code = code.strip()
            description = new_descriptions[index].strip() if index < len(new_descriptions) else ""
            if not code or not description:
                continue
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": (new_actives[index] if index < len(new_actives) else "true") == "true"},
            )
        messages.success(request, f"{title} salvo com sucesso.")
        return redirect(request.path)
    valores = tabela.valores.all()
    if query:
        valores = valores.filter(Q(cd_valor__icontains=query) | Q(ds_valor__icontains=query))
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
    prestadores = Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True)
    if request.method == "POST":
        for escala in registros:
            if request.POST.get(f"delete_{escala.pk}") == "1":
                escala.delete()
                continue
            escala.cd_prestador_id = request.POST.get(f"provider_{escala.pk}") or escala.cd_prestador_id
            escala.ds_agenda = request.POST.get(f"name_{escala.pk}", escala.ds_agenda)
            escala.nr_dia_semana = request.POST.get(f"weekday_{escala.pk}", escala.nr_dia_semana)
            escala.hr_inicio = request.POST.get(f"start_{escala.pk}", escala.hr_inicio)
            escala.hr_fim = request.POST.get(f"end_{escala.pk}", escala.hr_fim)
            escala.nr_tempo_atendimento = request.POST.get(f"duration_{escala.pk}", escala.nr_tempo_atendimento)
            escala.nr_intervalo = request.POST.get(f"interval_{escala.pk}", escala.nr_intervalo)
            escala.sn_ativo = request.POST.get(f"active_{escala.pk}") == "true"
            escala.save()
        new_providers = request.POST.getlist("new_provider")
        for index, provider_id in enumerate(new_providers):
            if not provider_id:
                continue
            AgendaProfissional.objects.create(
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
        messages.success(request, "Escalas salvas com sucesso.")
        return redirect(request.path)
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
        },
    )


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
def agendar_consultar_paciente(request):
    request.current_tab_title = "Atendimento > Agendamento > Agendar"
    request.current_module_title = "Atendimento"
    request.current_start_query = True
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
def cadastro_paciente(request, cd_paciente=None, fluxo_agendamento=True):
    request.current_tab_title = (
        "Atendimento > Agendamento > Agendar > Cadastro de paciente"
        if fluxo_agendamento
        else "Pacientes > Cadastro de paciente"
    )
    request.current_module_title = "Atendimento" if fluxo_agendamento else "Pacientes"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente) if cd_paciente else None
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
def cadastro_paciente_geral(request, cd_paciente=None):
    return cadastro_paciente(request, cd_paciente=cd_paciente, fluxo_agendamento=False)


@login_required
def selecionar_agenda(request, cd_paciente):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Selecionar agenda"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    horarios = _horarios_disponiveis(empresa)
    if request.method == "POST":
        agenda = get_object_or_404(AgendaProfissional, cd_empresa=empresa, cd_agenda_profissional=request.POST.get("cd_agenda_profissional"))
        dh_agendamento = parse_datetime(request.POST["dh_agendamento"])
        if dh_agendamento and timezone.is_naive(dh_agendamento):
            dh_agendamento = timezone.make_aware(dh_agendamento)
        Agendamento.objects.create(
            cd_empresa=empresa,
            cd_paciente=paciente,
            cd_agenda_profissional=agenda,
            dh_agendamento=dh_agendamento,
            ds_profissional=agenda.cd_prestador.nm_prestador,
            ds_especialidade=agenda.cd_prestador.ds_especialidade,
            sn_confirmado=True,
        )
        messages.success(request, "Agendamento confirmado.")
        return redirect("atendimento:agendas")
    return render(request, "atendimento/selecionar_agenda.html", {"paciente": paciente, "horarios": horarios})


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
        agendamento.save()
        messages.success(request, "Agendamento confirmado.")
        return redirect("atendimento:agendas")
    return render(request, "atendimento/confirmar_agendamento.html", {"form": form, "paciente": paciente})


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
