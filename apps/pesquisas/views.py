from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa
from apps.core.permissions import role_required
from apps.core.table_utils import paginate_table

from .forms import FaixaResultadoPesquisaForm, OpcaoRespostaPesquisaForm, PerguntaPesquisaForm, PesquisaForm
from .models import (
    FaixaResultadoPesquisa,
    ItemRespostaPesquisa,
    OpcaoRespostaPesquisa,
    PerguntaPesquisa,
    Pesquisa,
    RespostaPesquisa,
)


def _empresa_logada(request):
    return get_object_or_404(Empresa, cd_empresa=request.session.get("cd_empresa") or 1, sn_ativo=True)


def _pesquisa_empresa(request, pk):
    return get_object_or_404(Pesquisa, pk=pk, cd_empresa=_empresa_logada(request))


def _cabecalho(request, titulo):
    request.current_tab_title = f"Pesquisas > {titulo}"
    request.current_tab_root_title = titulo
    request.current_module_title = "Pesquisas"


@login_required
@role_required("TI")
def configuracao(request):
    empresa = _empresa_logada(request)
    _cabecalho(request, "Pesquisas")
    request.current_can_query = False
    request.current_can_save = True
    pesquisa_id = request.POST.get("pesquisa_id") or request.GET.get("pesquisa")
    pesquisa = Pesquisa.objects.filter(pk=pesquisa_id, cd_empresa=empresa).first() if pesquisa_id else None
    form = PesquisaForm(request.POST or None, instance=pesquisa)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.cd_empresa = empresa
        item.save()
        messages.success(request, "Pesquisa salva com sucesso.")
        return redirect(f"{reverse('pesquisas:configuracao')}?pesquisa={item.pk}")
    pesquisas = Pesquisa.objects.filter(cd_empresa=empresa).annotate(
        total_perguntas=Count("perguntas", distinct=True), total_respostas=Count("respostas", distinct=True)
    )
    return render(request, "pesquisas/configuracao.html", {"form": form, "pesquisa": pesquisa, "pesquisas": pesquisas})


@login_required
@role_required("TI")
def perguntas_parametros(request):
    empresa = _empresa_logada(request)
    _cabecalho(request, "Perguntas e parâmetros")
    request.current_can_query = False
    request.current_can_save = False
    pesquisas = Pesquisa.objects.filter(cd_empresa=empresa, sn_ativo=True)
    pesquisa_id = request.POST.get("pesquisa_id") or request.GET.get("pesquisa")
    pesquisa = pesquisas.filter(pk=pesquisa_id).first() if pesquisa_id else pesquisas.first()
    pergunta_id = request.POST.get("pergunta_id") or request.GET.get("pergunta")
    pergunta = (
        PerguntaPesquisa.objects.filter(pk=pergunta_id, cd_pesquisa=pesquisa).first()
        if pergunta_id and pesquisa else None
    )

    question_form = PerguntaPesquisaForm(prefix="pergunta", instance=pergunta)
    option_id = request.POST.get("opcao_id") or request.GET.get("opcao")
    option = (
        OpcaoRespostaPesquisa.objects.filter(pk=option_id, cd_pergunta_pesquisa=pergunta).first()
        if option_id and pergunta else None
    )
    option_form = OpcaoRespostaPesquisaForm(prefix="opcao", instance=option)
    if request.method == "POST" and pesquisa:
        action = request.POST.get("action")
        if action == "save_question":
            question_form = PerguntaPesquisaForm(request.POST, prefix="pergunta", instance=pergunta)
            if question_form.is_valid():
                pergunta = question_form.save(commit=False)
                pergunta.cd_pesquisa = pesquisa
                pergunta.save()
                messages.success(request, "Pergunta salva com sucesso.")
                return redirect(
                    f"{reverse('pesquisas:perguntas_parametros')}?pesquisa={pesquisa.pk}&pergunta={pergunta.pk}"
                )
        elif action == "save_option" and pergunta:
            option_form = OpcaoRespostaPesquisaForm(request.POST, prefix="opcao", instance=option)
            if option_form.is_valid():
                option = option_form.save(commit=False)
                option.cd_pergunta_pesquisa = pergunta
                option.save()
                messages.success(request, "Resposta possível salva com sucesso.")
                return redirect(
                    f"{reverse('pesquisas:perguntas_parametros')}?pesquisa={pesquisa.pk}&pergunta={pergunta.pk}"
                )
        elif action == "toggle_question" and pergunta:
            pergunta.sn_ativo = not pergunta.sn_ativo
            pergunta.save(update_fields=["sn_ativo"])
            return redirect(f"{reverse('pesquisas:perguntas_parametros')}?pesquisa={pesquisa.pk}")
        elif action == "toggle_option" and pergunta:
            option = get_object_or_404(
                OpcaoRespostaPesquisa, pk=request.POST.get("opcao_id"), cd_pergunta_pesquisa=pergunta
            )
            option.sn_ativo = not option.sn_ativo
            option.save(update_fields=["sn_ativo"])
            return redirect(
                f"{reverse('pesquisas:perguntas_parametros')}?pesquisa={pesquisa.pk}&pergunta={pergunta.pk}"
            )

    perguntas = pesquisa.perguntas.prefetch_related("opcoes").all() if pesquisa else []
    return render(request, "pesquisas/perguntas_parametros.html", {
        "pesquisas": pesquisas, "pesquisa": pesquisa, "perguntas": perguntas, "pergunta": pergunta,
        "question_form": question_form, "option_form": option_form, "option": option,
    })


@login_required
@role_required("TI")
def calculos_resultados(request):
    empresa = _empresa_logada(request)
    _cabecalho(request, "Cálculos e mensagens")
    request.current_can_query = False
    request.current_can_save = False
    pesquisas = Pesquisa.objects.filter(cd_empresa=empresa, sn_ativo=True)
    pesquisa_id = request.POST.get("pesquisa_id") or request.GET.get("pesquisa")
    pesquisa = pesquisas.filter(pk=pesquisa_id).first() if pesquisa_id else pesquisas.first()
    faixa_id = request.POST.get("faixa_id") or request.GET.get("faixa")
    faixa = pesquisa.faixas_resultado.filter(pk=faixa_id).first() if pesquisa and faixa_id else None
    form = FaixaResultadoPesquisaForm(prefix="faixa", instance=faixa)
    if request.method == "POST" and pesquisa:
        action = request.POST.get("action")
        if action == "save_calculation":
            tipo = request.POST.get("tp_calculo")
            if tipo in dict(Pesquisa.CALCULOS):
                pesquisa.tp_calculo = tipo
                pesquisa.save(update_fields=["tp_calculo", "dh_atualizacao"])
                messages.success(request, "Regra de cálculo atualizada.")
            return redirect(f"{reverse('pesquisas:calculos_resultados')}?pesquisa={pesquisa.pk}")
        if action == "save_range":
            form = FaixaResultadoPesquisaForm(request.POST, prefix="faixa", instance=faixa)
            form.instance.cd_pesquisa = pesquisa
            if form.is_valid():
                faixa = form.save(commit=False)
                faixa.cd_pesquisa = pesquisa
                faixa.save()
                messages.success(request, "Faixa de resultado salva com sucesso.")
                return redirect(f"{reverse('pesquisas:calculos_resultados')}?pesquisa={pesquisa.pk}")
        if action == "toggle_range" and faixa:
            faixa.sn_ativo = not faixa.sn_ativo
            faixa.save(update_fields=["sn_ativo"])
            return redirect(f"{reverse('pesquisas:calculos_resultados')}?pesquisa={pesquisa.pk}")
    return render(request, "pesquisas/calculos_resultados.html", {
        "pesquisas": pesquisas, "pesquisa": pesquisa, "faixas": pesquisa.faixas_resultado.all() if pesquisa else [],
        "faixa": faixa, "form": form, "calculos": Pesquisa.CALCULOS,
    })


@login_required
@role_required("Recepcionista", "Enfermeiro", "Médico")
def disponiveis(request):
    _cabecalho(request, "Pesquisas disponíveis")
    request.current_can_query = False
    request.current_can_save = False
    agora = timezone.now()
    pesquisas = Pesquisa.objects.filter(cd_empresa=_empresa_logada(request), sn_ativo=True).filter(
        (Q(dh_inicio__isnull=True) | Q(dh_inicio__lte=agora)),
        (Q(dh_fim__isnull=True) | Q(dh_fim__gte=agora)),
    )
    return render(request, "pesquisas/disponiveis.html", {"pesquisas": pesquisas})


@login_required
@role_required("TI")
def resultados(request):
    empresa = _empresa_logada(request)
    _cabecalho(request, "Resultados")
    request.current_can_query = True
    request.current_can_save = False
    pesquisa_id = request.GET.get("pesquisa")
    pesquisas = Pesquisa.objects.filter(cd_empresa=empresa)
    respostas = RespostaPesquisa.objects.select_related("cd_pesquisa", "cd_usuario", "cd_faixa_resultado").filter(
        cd_pesquisa__cd_empresa=empresa
    )
    if pesquisa_id:
        respostas = respostas.filter(cd_pesquisa_id=pesquisa_id)
    respostas = paginate_table(
        request, respostas, {"cd_resposta_pesquisa", "dh_resposta", "nr_resultado"}, "-dh_resposta", load_on_open=True
    )
    return render(request, "pesquisas/resultados.html", {"pesquisas": pesquisas, "respostas": respostas})


def _decimal(value):
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _calcular_resultado(pesquisa, question_scores, max_scores, weights):
    if not question_scores:
        return Decimal("0")
    if pesquisa.tp_calculo == "SOMA":
        return sum(question_scores, Decimal("0"))
    if pesquisa.tp_calculo == "PERCENTUAL":
        maximum = sum(max_scores, Decimal("0"))
        return (sum(question_scores, Decimal("0")) / maximum * Decimal("100")) if maximum else Decimal("0")
    weight_total = sum(weights, Decimal("0"))
    return (sum(question_scores, Decimal("0")) / weight_total) if weight_total else Decimal("0")


def responder(request, token):
    pesquisa = get_object_or_404(
        Pesquisa.objects.prefetch_related("perguntas__opcoes", "faixas_resultado"), cd_token_publico=token
    )
    if not pesquisa.sn_publica and not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if not pesquisa.sn_anonima and not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if not pesquisa.disponivel:
        return render(request, "pesquisas/indisponivel.html", {"pesquisa": pesquisa}, status=404)
    perguntas = list(pesquisa.perguntas.filter(sn_ativo=True).prefetch_related("opcoes"))
    errors = {}
    if request.method == "POST":
        pending_items = []
        question_scores, max_scores, weights = [], [], []
        for pergunta in perguntas:
            field = f"pergunta_{pergunta.pk}"
            values = request.POST.getlist(field) if pergunta.tp_resposta == "MULTIPLA" else [request.POST.get(field, "")]
            values = [value for value in values if str(value).strip()]
            if pergunta.sn_obrigatoria and not values:
                errors[field] = "Esta pergunta é obrigatória."
                continue
            if not values:
                continue
            peso = pergunta.nr_peso or Decimal("1")
            if pergunta.tp_resposta in {"UNICA", "MULTIPLA", "ESCALA"}:
                opcoes = {str(item.pk): item for item in pergunta.opcoes.filter(sn_ativo=True)}
                selecionadas = [opcoes[value] for value in values if value in opcoes]
                if len(selecionadas) != len(values):
                    errors[field] = "Selecione uma resposta válida."
                    continue
                valor_bruto = sum((item.nr_valor for item in selecionadas), Decimal("0"))
                for item in selecionadas:
                    pending_items.append((pergunta, item, item.ds_resposta, item.nr_valor * peso))
                ativos = list(opcoes.values())
                if pergunta.tp_resposta == "MULTIPLA":
                    maximo = sum((max(item.nr_valor, Decimal("0")) for item in ativos), Decimal("0"))
                else:
                    maximo = max((item.nr_valor for item in ativos), default=Decimal("0"))
            elif pergunta.tp_resposta == "NUMERO":
                valor_bruto = _decimal(values[0])
                if valor_bruto is None:
                    errors[field] = "Informe um número válido."
                    continue
                if pergunta.nr_minimo is not None and valor_bruto < pergunta.nr_minimo:
                    errors[field] = f"O valor mínimo é {pergunta.nr_minimo}."
                    continue
                if pergunta.nr_maximo is not None and valor_bruto > pergunta.nr_maximo:
                    errors[field] = f"O valor máximo é {pergunta.nr_maximo}."
                    continue
                maximo = pergunta.nr_maximo if pergunta.nr_maximo is not None else valor_bruto
                pending_items.append((pergunta, None, values[0], valor_bruto * peso))
            else:
                pending_items.append((pergunta, None, values[0], None))
                continue
            question_scores.append(valor_bruto * peso)
            max_scores.append(maximo * peso)
            weights.append(peso)

        if not errors:
            resultado = _calcular_resultado(pesquisa, question_scores, max_scores, weights).quantize(Decimal("0.001"))
            faixa = pesquisa.faixas_resultado.filter(
                sn_ativo=True, nr_minimo__lte=resultado, nr_maximo__gte=resultado
            ).first()
            with transaction.atomic():
                resposta = RespostaPesquisa.objects.create(
                    cd_pesquisa=pesquisa,
                    cd_usuario=None if pesquisa.sn_anonima else request.user,
                    cd_faixa_resultado=faixa,
                    nr_resultado=resultado,
                )
                ItemRespostaPesquisa.objects.bulk_create([
                    ItemRespostaPesquisa(
                        cd_resposta_pesquisa=resposta,
                        cd_pergunta_pesquisa=pergunta,
                        cd_opcao_resposta=opcao,
                        ds_resposta=texto,
                        nr_valor=valor,
                    )
                    for pergunta, opcao, texto, valor in pending_items
                ])
            request.session[f"pesquisa_resposta_{resposta.pk}"] = True
            return redirect("pesquisas:concluida", resposta_id=resposta.pk)
    for pergunta in perguntas:
        field = f"pergunta_{pergunta.pk}"
        pergunta.form_error = errors.get(field, "")
        pergunta.valores_postados = request.POST.getlist(field) if request.method == "POST" else []
        pergunta.valor_postado = request.POST.get(field, "") if request.method == "POST" else ""
    return render(request, "pesquisas/responder.html", {"pesquisa": pesquisa, "perguntas": perguntas})


def concluida(request, resposta_id):
    if not request.session.get(f"pesquisa_resposta_{resposta_id}"):
        return redirect("core:home")
    resposta = get_object_or_404(RespostaPesquisa.objects.select_related("cd_pesquisa", "cd_faixa_resultado"), pk=resposta_id)
    return render(request, "pesquisas/concluida.html", {"resposta": resposta, "pesquisa": resposta.cd_pesquisa})
