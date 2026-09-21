from decimal import Decimal

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html

from apps.core.permissions import role_required
from apps.core.table_utils import paginate_table
from apps.platform.tenancy import empresa_atual, proteger_contexto_tenant

from .forms import (
    CotaConsumoForm,
    EstoqueForm,
    ItemMovimentoEstoqueFormSet,
    ItemSolicitacaoProdutoFormSet,
    MovimentoEstoqueForm,
    ProdutoClassificacaoForm,
    ProdutoEstoqueForm,
    ProdutoForm,
    SaldoProdutoTabelaForm,
    SolicitacaoProdutoForm,
    UnidadeProdutoForm,
    ValorTabelaEstoqueForm,
)
from .selectors.catalogos import filtrar_catalogo
from .services.catalogos import salvar_linhas_catalogo
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


@proteger_contexto_tenant
def _cadastro_simples(request, *, model, form_class, title, search_fields, template="estoque/cadastro_simples.html", path=None, filtros=None, valores_forcados=None):
    empresa = empresa_atual(request)
    _toolbar_context(request, title, path)
    queryset = model.objects.filter(cd_empresa=empresa)
    if filtros:
        queryset = queryset.filter(**filtros)
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
    for campo, valor in (valores_forcados or {}).items():
        if campo in form.fields:
            form.fields[campo].initial = valor
            form.fields[campo].disabled = True
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        for campo, valor in (valores_forcados or {}).items():
            setattr(saved, campo, valor)
        saved.save()
        form.save_m2m()
        messages.success(request, f"{title} salvo com sucesso.")
        return redirect(f"{request.path}?id={saved.pk}")
    return render(request, template, {
        "title": title,
        "form": form,
        "instance": instance,
        "form_table": model._meta.model_name,
    })


def _widget_tabela(campo, nome, valor):
    attrs = {"data-consultable": "true", "data-editable": "true"}
    widget = campo.widget
    if isinstance(campo, forms.BooleanField):
        widget = forms.Select(choices=(("true", "Ativo"), ("false", "Inativo")))
        valor = "true" if valor in {True, "true", "True", "1", 1} else "false"
    return widget.render(nome, valor, attrs=attrs)


@proteger_contexto_tenant
def _tabela_editavel(
    request,
    *,
    model,
    form_class,
    title,
    path,
    colunas,
    search_fields,
    filtros=None,
    valores_forcados=None,
):
    empresa = empresa_atual(request)
    _toolbar_context(request, title, path)
    request.current_can_remove = True
    queryset = model.objects.filter(cd_empresa=empresa, **(filtros or {}))
    if request.method == "POST":
        try:
            alterados = salvar_linhas_catalogo(
                queryset=queryset,
                form_class=form_class,
                post=request.POST,
                empresa=empresa,
                campos=tuple(coluna[0] for coluna in colunas if coluna[0] in form_class.base_fields),
                valores_forcados=valores_forcados,
            )
        except ValidationError as exc:
            for erro in exc.messages:
                messages.error(request, erro)
        else:
            messages.success(request, f"{alterados} registro(s) salvo(s) em {title}.")
            return redirect(f"{request.path}?consultar=1")
    queryset = filtrar_catalogo(queryset, request.GET.get("q", ""), search_fields)
    pk_name = model._meta.pk.name
    allowed_ordering = {pk_name, *(coluna[2] for coluna in colunas)}
    registros = paginate_table(request, queryset, allowed_ordering, pk_name)
    linhas = []
    for registro in registros:
        formulario = form_class(instance=registro, empresa=empresa, prefix=f"linha_{registro.pk}")
        celulas = []
        for campo_nome, _titulo, _ordem in colunas:
            if campo_nome in formulario.fields:
                campo = formulario.fields[campo_nome]
                celulas.append(_widget_tabela(campo, formulario[campo_nome].html_name, formulario[campo_nome].value()))
            else:
                valor = getattr(registro, campo_nome, "")
                celulas.append(format_html('<input value="{}" readonly>', valor))
        linhas.append({"pk": registro.pk, "celulas": celulas})
    formulario_novo = form_class(empresa=empresa)
    nova_linha = []
    for campo_nome, _titulo, _ordem in colunas:
        if campo_nome in formulario_novo.fields:
            campo = formulario_novo.fields[campo_nome]
            nova_linha.append(_widget_tabela(campo, f"new_{campo_nome}", formulario_novo[campo_nome].value()))
        else:
            nova_linha.append(format_html('<input value="0" readonly>'))
    return render(request, "estoque/tabela_editavel.html", {
        "title": title,
        "table_name": model._meta.db_table,
        "pk_name": pk_name,
        "colunas": [
            {"campo": campo, "titulo": titulo, "ordem": ordem}
            for campo, titulo, ordem in colunas
        ],
        "linhas": linhas,
        "nova_linha": nova_linha,
        "total_colunas": len(colunas) + 1,
    })


@login_required
@role_required("Almoxarifado")
def estoques(request):
    return _cadastro_simples(
        request,
        model=Estoque,
        form_class=EstoqueForm,
        title="Estoques",
        search_fields=("nm_estoque", "ds_codigo"),
        template="estoque/estoques.html",
        path="Almoxarifado > Tabelas > Gerais > Estoques",
    )


@login_required
@role_required("Almoxarifado")
def unidades(request):
    return _tabela_editavel(
        request,
        model=UnidadeProduto,
        form_class=UnidadeProdutoForm,
        title="Unidades",
        path="Almoxarifado > Tabelas > Gerais > Unidades",
        colunas=(("ds_sigla", "Sigla", "ds_sigla"), ("ds_descricao", "Descrição", "ds_descricao"), ("qt_fator_conversao", "Fator de conversão", "qt_fator_conversao"), ("sn_ativo", "Status", "sn_ativo")),
        search_fields=("ds_sigla", "ds_descricao"),
    )


@login_required
@role_required("Almoxarifado")
def classificacoes_produto(request):
    return _tabela_editavel(
        request,
        model=ProdutoClassificacao,
        form_class=ProdutoClassificacaoForm,
        title="Classificação de produtos",
        path="Almoxarifado > Tabelas > Produtos > Classificação",
        colunas=(("nm_classificacao", "Classificação", "nm_classificacao"), ("sn_ativo", "Status", "sn_ativo")),
        search_fields=("nm_classificacao",),
    )


@login_required
@role_required("Almoxarifado")
def produtos(request):
    return _cadastro_simples(request, model=Produto, form_class=ProdutoForm, title="Produtos", search_fields=("nm_produto", "cd_codigo", "ds_descricao"), template="estoque/produtos.html", path="Almoxarifado > Tabelas > Produtos > Produtos")


@login_required
@role_required("Almoxarifado", "TI")
def medicamentos(request):
    return _cadastro_simples(
        request,
        model=Produto,
        form_class=ProdutoForm,
        title="Medicamentos",
        search_fields=("nm_produto", "cd_codigo", "ds_descricao"),
        template="estoque/produtos.html",
        path="Almoxarifado > Farmácia > Tabelas > Medicamentos",
        filtros={"tp_produto": Produto.TipoProduto.MEDICAMENTO},
        valores_forcados={"tp_produto": Produto.TipoProduto.MEDICAMENTO},
    )


@login_required
@role_required("Almoxarifado")
def saldos_produto(request):
    return _tabela_editavel(
        request,
        model=ProdutoEstoque,
        form_class=SaldoProdutoTabelaForm,
        title="Saldos por estoque",
        path="Almoxarifado > Tabelas > Gerais > Saldos por estoque",
        colunas=(("cd_produto", "Produto", "cd_produto__nm_produto"), ("cd_estoque", "Estoque", "cd_estoque__nm_estoque"), ("qt_saldo", "Saldo", "qt_saldo"), ("qt_reservado", "Reservado", "qt_reservado"), ("qt_minima", "Mínimo", "qt_minima"), ("sn_ativo", "Status", "sn_ativo")),
        search_fields=("cd_produto__nm_produto", "cd_estoque__nm_estoque"),
    )


@login_required
@role_required("Almoxarifado")
def cotas_consumo(request):
    return _tabela_editavel(
        request,
        model=CotaConsumo,
        form_class=CotaConsumoForm,
        title="Cotas / Consumo",
        path="Almoxarifado > Tabelas > Gerais > Cotas / Consumo",
        colunas=(("cd_estoque", "Estoque", "cd_estoque__nm_estoque"), ("cd_produto", "Produto", "cd_produto__nm_produto"), ("qt_cota", "Cota", "qt_cota"), ("nr_dias", "Dias", "nr_dias"), ("dt_inicio_vigencia", "Início", "dt_inicio_vigencia"), ("dt_fim_vigencia", "Fim", "dt_fim_vigencia"), ("sn_ativo", "Status", "sn_ativo")),
        search_fields=("cd_produto__nm_produto", "cd_estoque__nm_estoque"),
    )


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
@proteger_contexto_tenant
def tabela_estoque(request, chave):
    empresa = empresa_atual(request)
    nome = TABELAS_GERAIS.get(chave, chave.replace("-", " ").title())
    tabela, _ = TabelaEstoque.objects.get_or_create(cd_empresa=empresa, ds_chave=chave, defaults={"ds_nome": nome})
    return _tabela_editavel(
        request,
        model=ValorTabelaEstoque,
        form_class=ValorTabelaEstoqueForm,
        title=nome,
        path=f"Almoxarifado > Tabelas > Gerais > {nome}",
        colunas=(("cd_valor", "Código", "cd_valor"), ("ds_valor", "Descrição", "ds_valor"), ("ds_observacao", "Observação", "ds_observacao"), ("sn_ativo", "Status", "sn_ativo")),
        search_fields=("cd_valor", "ds_valor", "ds_observacao"),
        filtros={"cd_tabela": tabela},
        valores_forcados={"cd_tabela": tabela},
    )


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
@proteger_contexto_tenant
def solicitacoes_produto(request):
    empresa = empresa_atual(request)
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
@proteger_contexto_tenant
def atender_solicitacoes_produto(request):
    empresa = empresa_atual(request)
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
@proteger_contexto_tenant
def movimentacoes(request, tipo=None):
    empresa = empresa_atual(request)
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
