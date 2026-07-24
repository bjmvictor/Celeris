from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Empresa
from apps.core.permissions import role_required

from .forms import (
    CotaConsumoForm,
    EstoqueForm,
    ItemMovimentoEstoqueFormSet,
    ItemSolicitacaoProdutoFormSet,
    MovimentoEstoqueForm,
    ProdutoClassificacaoForm,
    ProdutoEstoqueForm,
    ProdutoForm,
    SolicitacaoProdutoForm,
    UnidadeProdutoForm,
    ValorTabelaEstoqueForm,
)
from .models import (
    CotaConsumo,
    Estoque,
    MovimentoEstoque,
    Produto,
    ProdutoClassificacao,
    ProdutoEstoque,
    SolicitacaoProduto,
    TabelaEstoque,
    UnidadeProduto,
    ValorTabelaEstoque,
)


def _empresa_logada(request):
    return get_object_or_404(Empresa, cd_empresa=request.session.get("cd_empresa") or 1, sn_ativo=True)


def _search(request):
    return request.GET.get("q", "").strip()


def _toolbar_context(request, title, path=None):
    request.current_tab_title = path or title
    request.current_tab_root_title = title
    request.current_module_title = "Almoxarifado"
    request.current_can_query = True


def _query_session_key(request, model):
    return f"consulta_{model._meta.app_label}_{model._meta.model_name}_{request.path.replace('/', '_')}"


def _apply_form_query(queryset, form_class, request, empresa):
    form = form_class(empresa=empresa)
    has_filter = False
    for name, field in form.fields.items():
        value = request.GET.get(name, "").strip()
        if not value:
            continue
        has_filter = True
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
    return queryset, has_filter


def _prepare_navigation(request, queryset, instance, session_key):
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


def _cadastro_simples(request, *, model, form_class, title, search_fields, template="estoque/cadastro_simples.html", path=None):
    empresa = _empresa_logada(request)
    _toolbar_context(request, title, path)
    queryset = model.objects.filter(cd_empresa=empresa)
    session_key = _query_session_key(request, model)
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        registros, _ = _apply_form_query(queryset, form_class, request, empresa)
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
    _prepare_navigation(request, queryset, instance, session_key)
    form = form_class(request.POST or None, instance=instance, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"{title} salvo com sucesso.")
        return redirect(f"{request.path}?id={saved.pk}")
    return render(request, template, {
        "title": title,
        "form": form,
        "instance": instance,
        "form_table": model._meta.model_name,
    })


@login_required
@role_required("Almoxarifado")
def estoques(request):
    return _cadastro_simples(request, model=Estoque, form_class=EstoqueForm, title="Estoques", search_fields=("nm_estoque", "ds_codigo"), path="Almoxarifado > Tabelas > Gerais > Estoques")


@login_required
@role_required("Almoxarifado")
def unidades(request):
    return _cadastro_simples(request, model=UnidadeProduto, form_class=UnidadeProdutoForm, title="Unidades", search_fields=("ds_sigla", "ds_descricao"), path="Almoxarifado > Tabelas > Gerais > Unidades")


@login_required
@role_required("Almoxarifado")
def classificacoes_produto(request):
    return _cadastro_simples(request, model=ProdutoClassificacao, form_class=ProdutoClassificacaoForm, title="Classificação de produtos", search_fields=("nm_classificacao",), path="Almoxarifado > Tabelas > Produtos > Classificação")


@login_required
@role_required("Almoxarifado")
def produtos(request):
    return _cadastro_simples(request, model=Produto, form_class=ProdutoForm, title="Produtos", search_fields=("nm_produto", "cd_codigo", "ds_descricao"), template="estoque/produtos.html", path="Almoxarifado > Tabelas > Produtos > Produtos")


@login_required
@role_required("Almoxarifado")
def saldos_produto(request):
    return _cadastro_simples(request, model=ProdutoEstoque, form_class=ProdutoEstoqueForm, title="Saldos por estoque", search_fields=("cd_produto__nm_produto", "cd_estoque__nm_estoque"), path="Almoxarifado > Tabelas > Gerais > Saldos por estoque")


@login_required
@role_required("Almoxarifado")
def cotas_consumo(request):
    return _cadastro_simples(request, model=CotaConsumo, form_class=CotaConsumoForm, title="Cotas / Consumo", search_fields=("cd_produto__nm_produto", "cd_estoque__nm_estoque"), path="Almoxarifado > Tabelas > Gerais > Cotas / Consumo")


TABELAS_GERAIS = {
    "motivos-baixa": "Motivos de baixa",
    "motivos-devolucao-solicitacao": "Motivos de devolução / solicitação",
    "programacao-reposicao": "Programação de reposição",
    "motivos-cancelamento": "Motivos de cancelamento",
    "carater-produto": "Caráter de produto",
    "classes-produto": "Classes de produto",
}


@login_required
@role_required("Almoxarifado")
def tabela_estoque(request, chave):
    empresa = _empresa_logada(request)
    nome = TABELAS_GERAIS.get(chave, chave.replace("-", " ").title())
    _toolbar_context(request, nome, f"Almoxarifado > Tabelas > Gerais > {nome}")
    tabela, _ = TabelaEstoque.objects.get_or_create(cd_empresa=empresa, ds_chave=chave, defaults={"ds_nome": nome})
    queryset = ValorTabelaEstoque.objects.filter(cd_empresa=empresa, cd_tabela=tabela)
    session_key = _query_session_key(request, ValorTabelaEstoque) + f"_{chave}"
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        registros, _ = _apply_form_query(queryset, ValorTabelaEstoqueForm, request, empresa)
        result_ids = list(registros.order_by("cd_valor_tabela_estoque").values_list("cd_valor_tabela_estoque", flat=True)[:300])
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
    _prepare_navigation(request, queryset, instance, session_key)
    form = ValorTabelaEstoqueForm(request.POST or None, instance=instance, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_tabela = tabela
        saved.save()
        messages.success(request, f"{nome} salvo com sucesso.")
        return redirect(f"{request.path}?id={saved.pk}")
    return render(request, "estoque/cadastro_simples.html", {"title": nome, "form": form, "instance": instance, "form_table": "valor_tabela_estoque"})


def _apply_stock_alerts(solicitacao, empresa):
    has_alert = False
    for item in solicitacao.itens.select_related("cd_produto"):
        saldo = ProdutoEstoque.objects.filter(cd_empresa=empresa, cd_estoque=solicitacao.cd_estoque, cd_produto=item.cd_produto).first()
        disponivel = saldo.qt_disponivel if saldo else Decimal("0.000")
        item.qt_saldo_estoque = disponivel
        item.sn_alerta_estoque = item.qt_solicitada > disponivel
        item.save(update_fields=["qt_saldo_estoque", "sn_alerta_estoque"])
        has_alert = has_alert or item.sn_alerta_estoque
    return has_alert


def _filtrar_produtos_formset(formset, empresa):
    produtos = Produto.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_produto")
    for item_form in formset.forms:
        if "cd_produto" in item_form.fields:
            item_form.fields["cd_produto"].queryset = produtos


@login_required
@role_required("Almoxarifado")
def solicitacoes_produto(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Solicitar produtos", "Almoxarifado > Solicitações > Solicitar")
    queryset = SolicitacaoProduto.objects.filter(cd_empresa=empresa).prefetch_related("itens__cd_produto")
    session_key = _query_session_key(request, SolicitacaoProduto)
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        registros, _ = _apply_form_query(queryset, SolicitacaoProdutoForm, request, empresa)
        result_ids = list(registros.order_by("cd_solicitacao_produto").values_list("cd_solicitacao_produto", flat=True)[:300])
        request.session[session_key] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhuma solicitação encontrada.")
            return redirect(f"{request.path}?sem_resultados=1")
        return redirect(f"{request.path}?id={result_ids[0]}&origem=consulta")
    instance = None
    if request.GET.get("id"):
        instance = get_object_or_404(queryset, pk=request.GET["id"])
    if request.GET.get("sem_resultados") == "1":
        request.current_start_query = True
    _prepare_navigation(request, queryset, instance, session_key)
    form = SolicitacaoProdutoForm(request.POST or None, instance=instance, empresa=empresa)
    formset = ItemSolicitacaoProdutoFormSet(request.POST or None, instance=instance)
    _filtrar_produtos_formset(formset, empresa)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        solicitacao = form.save(commit=False)
        solicitacao.cd_empresa = empresa
        if not solicitacao.cd_usuario_solicitante_id:
            solicitacao.cd_usuario_solicitante = request.user
        solicitacao.save()
        formset.instance = solicitacao
        formset.save()
        if _apply_stock_alerts(solicitacao, empresa):
            messages.warning(request, "Um ou mais produtos não têm saldo suficiente no estoque selecionado.")
        else:
            messages.success(request, "Solicitação de produto salva com sucesso.")
        return redirect(request.path + f"?id={solicitacao.pk}")
    return render(request, "estoque/solicitacao_produto.html", {"title": "Solicitar produtos", "form": form, "formset": formset, "instance": instance, "form_table": "solicitacao_produto"})


@login_required
@role_required("Almoxarifado")
def atender_solicitacoes_produto(request):
    empresa = _empresa_logada(request)
    _toolbar_context(request, "Atender solicitações de produtos", "Almoxarifado > Solicitações > Atender")
    registros = SolicitacaoProduto.objects.filter(cd_empresa=empresa).prefetch_related("itens__cd_produto").order_by("-created_at")
    if request.method == "POST":
        solicitacao = get_object_or_404(registros, pk=request.POST.get("solicitacao"))
        action = request.POST.get("action")
        if action == "receber":
            solicitacao.ds_status = SolicitacaoProduto.Status.RECEBIDA
            solicitacao.cd_usuario_atendente = request.user
        elif action == "atender":
            solicitacao.ds_status = SolicitacaoProduto.Status.ATENDIDA
            solicitacao.cd_usuario_atendente = request.user
        elif action == "cancelar":
            solicitacao.ds_status = SolicitacaoProduto.Status.CANCELADA
        solicitacao.save(update_fields=["ds_status", "cd_usuario_atendente", "updated_at"])
        messages.success(request, "Solicitação atualizada.")
        return redirect(request.path)
    return render(request, "estoque/atender_solicitacoes.html", {"title": "Atender solicitações de produtos", "registros": registros[:200]})


@login_required
@role_required("Almoxarifado")
def movimentacoes(request, tipo=None):
    empresa = _empresa_logada(request)
    movement_titles = {
        "entrada": "Entrada",
        "saida": "Saída",
        "devolucao": "Devoluções",
        "transferencia": "Transferência entre estoques",
        "fracionamento": "Fracionamento",
        "acerto": "Acerto de estoque",
    }
    movement_title = movement_titles.get((tipo or "").lower(), "Movimentação de estoque")
    _toolbar_context(request, movement_title, f"Almoxarifado > Movimentações > {movement_title}")
    queryset = MovimentoEstoque.objects.filter(cd_empresa=empresa).prefetch_related("itens__cd_produto")
    if tipo:
        queryset = queryset.filter(tp_movimento=tipo.upper())
    session_key = _query_session_key(request, MovimentoEstoque) + f"_{tipo or 'todos'}"
    if request.GET.get("abrir") == "1" or request.GET.get("consultar") == "1":
        registros, _ = _apply_form_query(queryset, MovimentoEstoqueForm, request, empresa)
        result_ids = list(registros.order_by("cd_movimento_estoque").values_list("cd_movimento_estoque", flat=True)[:300])
        request.session[session_key] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhuma movimentação encontrada.")
            return redirect(f"{request.path}?sem_resultados=1")
        return redirect(f"{request.path}?id={result_ids[0]}&origem=consulta")
    instance = None
    if request.GET.get("id"):
        instance = get_object_or_404(queryset, pk=request.GET["id"])
    if request.GET.get("sem_resultados") == "1":
        request.current_start_query = True
    _prepare_navigation(request, queryset, instance, session_key)
    initial = {"tp_movimento": tipo.upper()} if tipo else {}
    form = MovimentoEstoqueForm(request.POST or None, instance=instance, empresa=empresa, initial=initial)
    formset = ItemMovimentoEstoqueFormSet(request.POST or None, instance=instance)
    _filtrar_produtos_formset(formset, empresa)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        movimento = form.save(commit=False)
        movimento.cd_empresa = empresa
        movimento.cd_usuario = request.user
        movimento.save()
        formset.instance = movimento
        formset.save()
        messages.success(request, "Movimentação salva com sucesso.")
        return redirect(request.path + f"?id={movimento.pk}")
    return render(request, "estoque/movimentacao.html", {"title": "Movimentação de estoque", "form": form, "formset": formset, "instance": instance, "form_table": "movimento_estoque"})
