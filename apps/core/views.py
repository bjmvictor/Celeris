from django.contrib import messages
from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import CharField, Max, Q, TextField
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from io import BytesIO, StringIO
import csv
import re
import unicodedata

from apps.accounts.models import Empresa
from .permissions import role_required

from .forms import EmpresaForm, ScreenDefinitionForm, ScreenFieldForm
from .models import Cep, ScreenDefinition, ScreenField, TabelaAuxiliarGlobal, TipoPrestadorConselho, ValorAuxiliarGlobal
from .table_utils import paginate_table


@login_required
def home(request):
    return render(request, "core/home.html")


def _query_text(request):
    return request.GET.get("q", "").strip().replace("%", "")


def _auxiliary_code(value):
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    return re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_")[:40]


@login_required
def placeholder(request):
    return render(request, "core/placeholder.html")


@login_required
def dynamic_screen(request, slug):
    screen = get_object_or_404(
        ScreenDefinition.objects.select_related("module").prefetch_related("fields"),
        slug=slug,
        active=True,
        module__active=True,
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
    empresas = paginate_table(
        request,
        empresas,
        {"cd_empresa", "nm_empresa", "nr_cnpj", "ds_cidade", "sg_estado", "sn_ativo"},
        "cd_empresa",
    )
    if request.method == "POST":
        for empresa in empresas:
            if request.POST.get(f"delete_{empresa.pk}") == "1":
                if empresa.cd_empresa != 1:
                    empresa.delete()
                continue
            if f"name_{empresa.pk}" not in request.POST:
                continue
            empresa.nm_empresa = request.POST.get(f"name_{empresa.pk}", empresa.nm_empresa)
            empresa.nr_cnpj = request.POST.get(f"cnpj_{empresa.pk}", empresa.nr_cnpj)
            empresa.ds_cidade = request.POST.get(f"city_{empresa.pk}", empresa.ds_cidade)
            empresa.sg_estado = request.POST.get(f"state_{empresa.pk}", empresa.sg_estado)
            empresa.sn_ativo = request.POST.get(f"active_{empresa.pk}") == "true"
            empresa.save()
        new_names = request.POST.getlist("new_name")
        next_code = (Empresa.objects.aggregate(max_code=Max("cd_empresa"))["max_code"] or 0) + 1
        for index, name in enumerate(new_names):
            name = name.strip()
            if not name:
                continue
            Empresa.objects.create(
                cd_empresa=next_code,
                nm_empresa=name,
                nr_cnpj=request.POST.getlist("new_cnpj")[index].strip() if index < len(request.POST.getlist("new_cnpj")) else "",
                ds_cidade=request.POST.getlist("new_city")[index].strip() if index < len(request.POST.getlist("new_city")) else "",
                sg_estado=request.POST.getlist("new_state")[index].strip() if index < len(request.POST.getlist("new_state")) else "",
                sn_ativo=True,
            )
            next_code += 1
        messages.success(request, "Empresas salvas com sucesso.")
        return redirect(request.path)
    return render(request, "core/system_companies.html", {"empresas": empresas})


@login_required
def system_company_edit(request, pk=None):
    empresa = get_object_or_404(Empresa, pk=pk) if pk else None
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == "POST" and form.is_valid():
        saved_empresa = form.save(commit=False)
        if not saved_empresa.pk:
            saved_empresa.cd_usuario_criacao = request.user
        saved_empresa.cd_usuario_atualizacao = request.user
        saved_empresa.save()
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
        "cep": "CEPs",
        "bairro": "Bairros",
        "tipo_logradouro": "Tipos de Logradouro",
        "especialidade": "Especialidades",
        "conselho_profissional": "Conselhos Profissionais",
        "orgao_emissor": "Órgãos Emissores",
        "banco": "Bancos",
        "pais": "Nacionalidades",
        "tipo_prestador": "Tipos de Prestador",
        "tipo_vinculo": "Tipos de Vínculo",
        "motivo_alteracao": "Motivos de alteração",
    }
    label = labels.get(tabela, tabela.replace("_", " ").title())
    request.current_tab_title = f"Global > Tabelas > Auxiliares > {label}"
    request.current_tab_root_title = label
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
            if f"description_{valor.pk}" not in request.POST:
                continue
            valor.ds_valor = request.POST.get(f"description_{valor.pk}", valor.ds_valor)
            valor.ds_grupo = request.POST.get(f"group_{valor.pk}", valor.ds_grupo)
            valor.sn_ativo = request.POST.get(f"active_{valor.pk}") == "true"
            valor.save()
        new_descriptions = request.POST.getlist("new_description")
        new_groups = request.POST.getlist("new_group")
        new_actives = request.POST.getlist("new_active")
        created = 0
        for index, new_description in enumerate(new_descriptions):
            new_description = new_description.strip()
            if not new_description:
                continue
            new_code = _auxiliary_code(new_description)
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela_auxiliar,
                cd_valor=new_code,
                defaults={
                    "ds_valor": new_description,
                    "ds_grupo": new_groups[index].strip() if index < len(new_groups) else "",
                    "sn_ativo": (new_actives[index] if index < len(new_actives) else "true") == "true",
                },
            )
            created += 1
        if new_descriptions and not created and not tabela_auxiliar.valores.exists():
            messages.error(request, "Informe a descrição obrigatória antes de salvar.")
        else:
            messages.success(request, "Tabela auxiliar salva com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    valores = tabela_auxiliar.valores.all()
    if query:
        valores = valores.filter(Q(cd_valor__icontains=query) | Q(ds_valor__icontains=query) | Q(ds_grupo__icontains=query))
    valores = paginate_table(
        request,
        valores,
        {"cd_valor_auxiliar_global", "cd_valor", "ds_valor", "ds_grupo", "sn_ativo"},
        "cd_valor_auxiliar_global",
    )
    return render(request, "core/global_auxiliary_values.html", {"tabela": tabela_auxiliar, "valores": valores})


@login_required
@role_required("TI")
def global_tables(request):
    request.current_tab_title = "Global > Tabelas Auxiliares"
    request.current_tab_root_title = "Tabelas Auxiliares"
    request.current_module_title = "Global"
    tables = TabelaAuxiliarGlobal.objects.filter(sn_ativo=True).order_by("ds_descricao", "ds_tabela")
    return render(request, "core/global_tables.html", {"tables": tables})


@login_required
@role_required("TI")
def global_ceps(request):
    request.current_tab_title = "Global > CEPs"
    request.current_tab_root_title = "CEPs"
    request.current_module_title = "Global"
    request.current_can_query = True
    request.current_can_remove = False
    records = Cep.objects.all()
    query = _query_text(request)
    if query:
        digits = "".join(character for character in query if character.isdigit())
        records = records.filter(
            Q(nr_cep__icontains=digits)
            | Q(ds_logradouro__icontains=query)
            | Q(ds_bairro__icontains=query)
            | Q(ds_cidade__icontains=query)
            | Q(sg_estado__icontains=query)
        )
    if request.method == "POST":
        for record in Cep.objects.all():
            if f"postal_code_{record.pk}" not in request.POST:
                continue
            record.nr_cep = "".join(character for character in request.POST.get(f"postal_code_{record.pk}", "") if character.isdigit())[:8]
            record.sg_estado = request.POST.get(f"state_{record.pk}", "").strip().upper()[:2]
            record.cd_cidade = request.POST.get(f"city_code_{record.pk}", "").strip()[:40]
            record.ds_cidade = request.POST.get(f"city_{record.pk}", "").strip()[:160]
            record.tp_logradouro = request.POST.get(f"street_type_{record.pk}", "").strip()[:40]
            record.ds_logradouro = request.POST.get(f"street_{record.pk}", "").strip()[:220]
            record.ds_bairro = request.POST.get(f"district_{record.pk}", "").strip()[:160]
            record.sn_ativo = request.POST.get(f"active_{record.pk}") == "true"
            record.save()
        new_codes = request.POST.getlist("new_postal_code")
        for index, postal_code in enumerate(new_codes):
            digits = "".join(character for character in postal_code if character.isdigit())[:8]
            if not digits:
                continue
            Cep.objects.update_or_create(
                nr_cep=digits,
                defaults={
                    "sg_estado": (request.POST.getlist("new_state")[index] if index < len(request.POST.getlist("new_state")) else "").strip().upper()[:2],
                    "cd_cidade": (request.POST.getlist("new_city_code")[index] if index < len(request.POST.getlist("new_city_code")) else "").strip()[:40],
                    "ds_cidade": (request.POST.getlist("new_city")[index] if index < len(request.POST.getlist("new_city")) else "").strip()[:160],
                    "tp_logradouro": (request.POST.getlist("new_street_type")[index] if index < len(request.POST.getlist("new_street_type")) else "").strip()[:40],
                    "ds_logradouro": (request.POST.getlist("new_street")[index] if index < len(request.POST.getlist("new_street")) else "").strip()[:220],
                    "ds_bairro": (request.POST.getlist("new_district")[index] if index < len(request.POST.getlist("new_district")) else "").strip()[:160],
                    "sn_ativo": (request.POST.getlist("new_active")[index] if index < len(request.POST.getlist("new_active")) else "true") == "true",
                },
            )
        messages.success(request, "CEPs salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    records = paginate_table(
        request,
        records,
        {"cd_cep", "nr_cep", "sg_estado", "ds_cidade", "ds_logradouro", "ds_bairro", "sn_ativo"},
        "cd_cep",
    )
    return render(request, "core/global_ceps.html", {"records": records})


IMPORT_TABLES = {
    "cep": "CEPs",
    "estado": "Estados",
    "cidade": "Cidades",
    "tipo_logradouro": "Tipos de Logradouro",
}


def _import_rows(upload):
    suffix = upload.name.rsplit(".", 1)[-1].lower()
    content = upload.read()
    if suffix == "csv":
        text = content.decode("utf-8-sig")
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=";,")
        except csv.Error:
            dialect = csv.excel_semicolon
        return list(csv.DictReader(StringIO(text), dialect=dialect))
    if suffix == "xlsx":
        try:
            from openpyxl import load_workbook
        except ModuleNotFoundError as error:
            raise ValueError("A importação XLSX requer a dependência openpyxl instalada.") from error
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value or "").strip() for value in next(rows, [])]
        return [dict(zip(headers, values)) for values in rows]
    raise ValueError("Formato não suportado. Utilize CSV ou XLSX.")


def _normalized_import_row(row):
    normalized = {}
    for key, value in row.items():
        normalized_key = _auxiliary_code(str(key or "")).lower()
        normalized[normalized_key] = str(value or "").strip()
    return normalized


@login_required
@role_required("TI")
def global_integrations(request):
    request.current_tab_title = "Global > Integrações"
    request.current_tab_root_title = "Importação de dados"
    request.current_module_title = "Global"
    report = None
    if request.method == "POST":
        table_name = request.POST.get("table_name", "")
        upload = request.FILES.get("file")
        errors = []
        processed = 0
        created = 0
        updated = 0
        if table_name not in IMPORT_TABLES:
            errors.append("Selecione uma integração válida.")
        if not upload:
            errors.append("Selecione um arquivo CSV ou XLSX.")
        if not errors:
            try:
                rows = _import_rows(upload)
                with transaction.atomic():
                    for row_number, source_row in enumerate(rows, start=2):
                        row = _normalized_import_row(source_row)
                        description = row.get("descricao") or row.get("nome") or row.get("logradouro")
                        code = row.get("codigo") or row.get("cep") or row.get("sigla")
                        group = row.get("grupo", "")
                        if table_name == "cidade":
                            group = row.get("uf") or row.get("estado") or group
                        elif table_name == "bairro":
                            group = row.get("cidade") or group
                        elif table_name == "cep":
                            state = row.get("uf") or row.get("estado")
                            city = row.get("cidade")
                            group = "|".join(part for part in (state, city) if part) or group
                        if not description:
                            errors.append(f"Linha {row_number}: descrição obrigatória.")
                            continue
                        code = (code or _auxiliary_code(description))[:40]
                        if not code:
                            errors.append(f"Linha {row_number}: código inválido.")
                            continue
                        active = row.get("ativo", "SIM").upper() not in {"0", "NAO", "NÃO", "FALSE", "INATIVO"}
                        if table_name == "cep":
                            digits = "".join(character for character in (row.get("cep") or code) if character.isdigit())[:8]
                            if not digits:
                                errors.append(f"Linha {row_number}: CEP inválido.")
                                continue
                            _, was_created = Cep.objects.update_or_create(
                                nr_cep=digits,
                                defaults={
                                    "sg_estado": (row.get("uf") or row.get("estado") or "")[:2].upper(),
                                    "cd_cidade": (row.get("codigo_cidade") or row.get("cidade") or "")[:40],
                                    "ds_cidade": (row.get("cidade") or "")[:160],
                                    "tp_logradouro": (row.get("tipo_logradouro") or "")[:40],
                                    "ds_logradouro": description[:220],
                                    "ds_bairro": (row.get("bairro") or "")[:160],
                                    "sn_ativo": active,
                                },
                            )
                        else:
                            table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
                                ds_tabela=table_name,
                                defaults={"ds_descricao": IMPORT_TABLES[table_name], "sn_ativo": True},
                            )
                            _, was_created = ValorAuxiliarGlobal.objects.update_or_create(
                                cd_tabela_auxiliar_global=table,
                                cd_valor=code,
                                defaults={
                                    "ds_valor": description[:160],
                                    "ds_grupo": group[:40],
                                    "sn_ativo": active,
                                },
                            )
                        processed += 1
                        created += int(was_created)
                        updated += int(not was_created)
            except (ValueError, UnicodeDecodeError, StopIteration) as error:
                errors.append(str(error))
            except Exception as error:
                errors.append(f"Falha ao processar o arquivo: {error}")
        report = {
            "processed": processed,
            "created": created,
            "updated": updated,
            "errors": errors,
        }
        if processed:
            messages.success(request, f"Importação concluída: {processed} registro(s) processado(s).")
        elif errors:
            messages.error(request, "A importação não processou registros.")
    return render(
        request,
        "core/global_integrations.html",
        {"import_tables": IMPORT_TABLES, "report": report},
    )




@login_required
def tipo_prestador_conselho(request):
    request.current_tab_title = "Global > Tabelas > Tipo de prestador x conselho"
    request.current_tab_root_title = "Tipo de prestador x conselho"
    request.current_module_title = "Global"
    request.current_can_query = True
    request.current_can_remove = True
    registros = TipoPrestadorConselho.objects.all()
    query = _query_text(request)
    if query:
        registros = registros.filter(Q(tp_prestador__icontains=query) | Q(ds_conselho__icontains=query))
    registros = paginate_table(
        request,
        registros,
        {"id", "tp_prestador", "ds_conselho", "sn_ativo"},
        "id",
    )
    tipos = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="tipo_prestador",
        sn_ativo=True,
    ).order_by("ds_valor")
    if request.method == "POST":
        for registro in registros:
            if request.POST.get(f"delete_{registro.pk}") == "1":
                registro.delete()
                continue
            if f"type_{registro.pk}" not in request.POST:
                continue
            registro.tp_prestador = request.POST.get(f"type_{registro.pk}", registro.tp_prestador)
            registro.ds_conselho = request.POST.get(f"council_{registro.pk}", registro.ds_conselho).strip().upper()
            registro.sn_ativo = request.POST.get(f"active_{registro.pk}") == "true"
            registro.save()
        councils = request.POST.getlist("new_council")
        for index, provider_type in enumerate(request.POST.getlist("new_type")):
            provider_type = provider_type.strip()
            if not provider_type or index >= len(councils) or not councils[index].strip():
                continue
            TipoPrestadorConselho.objects.update_or_create(
                tp_prestador=provider_type,
                defaults={"ds_conselho": councils[index].strip().upper(), "sn_ativo": True},
            )
        messages.success(request, "Vínculos de prestador e conselho salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "core/tipo_prestador_conselho.html", {"registros": registros, "tipos": tipos})


@login_required
def city_options(request):
    uf = request.GET.get("uf", "")
    cidades = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="cidade",
        sn_ativo=True,
        ds_grupo=uf,
    ).order_by("ds_valor")
    return JsonResponse({"cidades": [{"value": cidade.cd_valor, "label": cidade.ds_valor} for cidade in cidades]})


@login_required
def cep_option(request):
    raw_value = request.GET.get("cep", "")
    value = Cep.objects.filter(sn_ativo=True)
    value = value.filter(pk=int(raw_value)) if raw_value.isdigit() and len(raw_value) < 8 else value.filter(
        nr_cep="".join(character for character in raw_value if character.isdigit())
    )
    value = value.first()
    if not value:
        return JsonResponse({"estado": "", "cidade": "", "bairro": "", "logradouro": "", "tipo_logradouro": ""})
    return JsonResponse(
        {
            "estado": value.sg_estado,
            "cidade": value.cd_cidade or value.ds_cidade,
            "bairro": value.ds_bairro,
            "logradouro": value.ds_logradouro,
            "tipo_logradouro": value.tp_logradouro,
        }
    )
