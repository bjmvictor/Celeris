from django.contrib import messages
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db.models import CharField, Q, TextField
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Empresa

from .forms import EmpresaForm, ScreenDefinitionForm, ScreenFieldForm
from .models import ScreenDefinition, ScreenField, TabelaAuxiliarGlobal, ValorAuxiliarGlobal


@login_required
def home(request):
    return render(request, "core/home.html")


def _query_text(request):
    return request.GET.get("q", "").strip().replace("%", "")


@login_required
def placeholder(request):
    return render(request, "core/placeholder.html")


@login_required
def dynamic_screen(request, slug):
    screen = get_object_or_404(
        ScreenDefinition.objects.select_related("module").prefetch_related("fields"),
        slug=slug,
        active=True,
    )
    request.current_tab_title = screen.title
    request.current_module_title = screen.module.title
    request.current_can_query = screen.allow_query
    request.current_can_remove = screen.allow_delete

    template_by_type = {
        ScreenDefinition.TYPE_FORM: "core/dynamic_form.html",
        ScreenDefinition.TYPE_REPORT: "core/dynamic_report.html",
        ScreenDefinition.TYPE_DASHBOARD: "core/dynamic_dashboard.html",
    }
    template = template_by_type.get(screen.screen_type, "core/dynamic_form.html")
    return render(request, template, {"screen": screen, "fields": screen.fields.filter(visible=True)})


def _model_for_table(table_name):
    normalized = (table_name or "").lower()
    if not normalized:
        return None
    for model in apps.get_models():
        meta = model._meta
        if meta.db_table.lower() == normalized or meta.model_name.lower() == normalized:
            return model
    return None


@login_required
def lookup_options(request):
    table_name = request.GET.get("table", "")
    query = request.GET.get("q", "")
    value_field = request.GET.get("value", "")
    display_field = request.GET.get("display", "")
    model = _model_for_table(table_name)
    if not model:
        return JsonResponse({"results": []})

    model_fields = {field.name: field for field in model._meta.fields}
    pk_field = model._meta.pk.name
    value_field = value_field if value_field in model_fields else pk_field
    display_field = display_field if display_field in model_fields else ""
    if not display_field:
        display_field = next(
            (
                field.name
                for field in model._meta.fields
                if isinstance(field, (CharField, TextField)) and field.name != value_field
            ),
            value_field,
        )

    records = model.objects.all()
    if "cd_empresa" in model_fields and model_fields["cd_empresa"].remote_field:
        records = records.filter(cd_empresa_id=request.session.get("cd_empresa") or 1)
    if "sn_ativo" in model_fields:
        records = records.filter(sn_ativo=True)
    if query:
        search_filter = Q()
        for field in model._meta.fields:
            if isinstance(field, (CharField, TextField)):
                search_filter |= Q(**{f"{field.name}__icontains": query.replace("%", "")})
        if search_filter:
            records = records.filter(search_filter)

    results = [
        {
            "value": str(getattr(record, value_field, "")),
            "label": str(getattr(record, display_field, "")),
        }
        for record in records.order_by(display_field)[:20]
    ]
    return JsonResponse({"results": results})


@login_required
def system_screens(request):
    screens = ScreenDefinition.objects.select_related("module").all()
    return render(request, "core/system_screens.html", {"screens": screens})


@login_required
def system_screen_edit(request, pk=None):
    screen = get_object_or_404(ScreenDefinition, pk=pk) if pk else None
    form = ScreenDefinitionForm(request.POST or None, instance=screen)
    if request.method == "POST" and form.is_valid():
        saved_screen = form.save()
        messages.success(request, "Tela salva com sucesso.")
        return redirect("core:system_screen_edit", pk=saved_screen.pk)
    return render(request, "core/system_screen_form.html", {"form": form, "screen": screen})


@login_required
def system_fields(request):
    fields = ScreenDefinition.objects.prefetch_related("fields").select_related("module").all()
    return render(request, "core/system_fields.html", {"screens": fields})


@login_required
def system_field_edit(request, pk=None):
    field = get_object_or_404(ScreenField, pk=pk) if pk else None
    form = ScreenFieldForm(request.POST or None, instance=field)
    if request.method == "POST" and form.is_valid():
        saved_field = form.save()
        messages.success(request, "Campo salvo com sucesso.")
        return redirect("core:system_field_edit", pk=saved_field.pk)
    return render(request, "core/system_field_form.html", {"form": form, "field": field})


@login_required
def system_companies(request):
    request.current_can_query = True
    request.current_can_remove = True
    empresas = Empresa.objects.all()
    query = _query_text(request)
    if query:
        filtro = Q(nm_empresa__icontains=query) | Q(nr_cnpj__icontains=query) | Q(ds_cidade__icontains=query)
        if query.isdigit():
            filtro |= Q(cd_empresa=int(query))
        empresas = empresas.filter(filtro)
    if request.method == "POST":
        for empresa in empresas:
            if request.POST.get(f"delete_{empresa.pk}") == "1":
                if empresa.cd_empresa != 1:
                    empresa.delete()
                continue
            empresa.nm_empresa = request.POST.get(f"name_{empresa.pk}", empresa.nm_empresa)
            empresa.nr_cnpj = request.POST.get(f"cnpj_{empresa.pk}", empresa.nr_cnpj)
            empresa.ds_cidade = request.POST.get(f"city_{empresa.pk}", empresa.ds_cidade)
            empresa.sg_estado = request.POST.get(f"state_{empresa.pk}", empresa.sg_estado)
            empresa.sn_ativo = request.POST.get(f"active_{empresa.pk}") == "true"
            empresa.save()
        for index, code in enumerate(request.POST.getlist("new_code")):
            code = code.strip()
            name = request.POST.getlist("new_name")[index].strip() if index < len(request.POST.getlist("new_name")) else ""
            if not code or not name:
                continue
            Empresa.objects.update_or_create(
                cd_empresa=code,
                defaults={
                    "nm_empresa": name,
                    "nr_cnpj": request.POST.getlist("new_cnpj")[index].strip() if index < len(request.POST.getlist("new_cnpj")) else "",
                    "ds_cidade": request.POST.getlist("new_city")[index].strip() if index < len(request.POST.getlist("new_city")) else "",
                    "sg_estado": request.POST.getlist("new_state")[index].strip() if index < len(request.POST.getlist("new_state")) else "",
                    "sn_ativo": True,
                },
            )
        messages.success(request, "Empresas salvas com sucesso.")
        return redirect(request.path)
    return render(request, "core/system_companies.html", {"empresas": empresas})


@login_required
def system_company_edit(request, pk=None):
    empresa = get_object_or_404(Empresa, pk=pk) if pk else None
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == "POST" and form.is_valid():
        saved_empresa = form.save()
        messages.success(request, "Empresa salva com sucesso.")
        return redirect("core:system_company_edit", pk=saved_empresa.pk)
    return render(request, "core/system_company_form.html", {"form": form, "empresa": empresa})


@login_required
def global_auxiliary_values(request, tabela):
    labels = {
        "tipo_sanguineo": "Tipo sanguíneo",
        "sexo": "Sexo",
        "estado_civil": "Estado civil",
        "naturalidade": "Naturalidade",
        "nacionalidade": "Nacionalidade",
        "cidade": "Cidade",
        "estado": "Estado",
        "motivo_alteracao": "Motivos de alteração",
    }
    request.current_tab_title = f"Global > Tabelas > Auxiliares > {labels.get(tabela, 'Tabela auxiliar')}"
    request.current_module_title = "Global"
    request.current_can_query = True
    request.current_can_remove = True
    tabela_auxiliar = get_object_or_404(TabelaAuxiliarGlobal.objects.prefetch_related("valores"), ds_tabela=tabela)
    query = _query_text(request)
    if request.method == "POST":
        for valor in tabela_auxiliar.valores.all():
            if request.POST.get(f"delete_{valor.pk}") == "1":
                valor.delete()
                continue
            valor.cd_valor = request.POST.get(f"code_{valor.pk}", valor.cd_valor)
            valor.ds_valor = request.POST.get(f"description_{valor.pk}", valor.ds_valor)
            valor.ds_grupo = request.POST.get(f"group_{valor.pk}", valor.ds_grupo)
            valor.sn_ativo = request.POST.get(f"active_{valor.pk}") == "true"
            valor.save()
        new_codes = request.POST.getlist("new_code")
        new_descriptions = request.POST.getlist("new_description")
        new_groups = request.POST.getlist("new_group")
        new_actives = request.POST.getlist("new_active")
        for index, new_code in enumerate(new_codes):
            new_code = new_code.strip()
            new_description = new_descriptions[index].strip() if index < len(new_descriptions) else ""
            if not new_code or not new_description:
                continue
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela_auxiliar,
                cd_valor=new_code,
                defaults={
                    "ds_valor": new_description,
                    "ds_grupo": new_groups[index].strip() if index < len(new_groups) else "",
                    "sn_ativo": (new_actives[index] if index < len(new_actives) else "true") == "true",
                },
            )
        messages.success(request, "Tabela auxiliar salva com sucesso.")
        return redirect(request.path)
    valores = tabela_auxiliar.valores.all()
    if query:
        valores = valores.filter(Q(cd_valor__icontains=query) | Q(ds_valor__icontains=query) | Q(ds_grupo__icontains=query))
    return render(request, "core/global_auxiliary_values.html", {"tabela": tabela_auxiliar, "valores": valores})


@login_required
def city_options(request):
    uf = request.GET.get("uf", "")
    cidades = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="cidade",
        sn_ativo=True,
        ds_grupo=uf,
    ).order_by("ds_valor")
    return JsonResponse({"cidades": [{"value": cidade.cd_valor, "label": cidade.ds_valor} for cidade in cidades]})
