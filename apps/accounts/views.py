from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.utils.http import url_has_allowed_host_and_scheme
import logging
from urllib.parse import urlencode

from apps.atendimento.models import Prestador
from apps.core.table_utils import paginate_table

from .access import screen_access_required
from .forms import EmpresaAuthenticationForm, PerfilForm, UsuarioForm, UsuarioPasswordForm
from .models import Empresa, Papel, Setor, User, UsuarioEmpresa, available_username, normalize_identifier


logger = logging.getLogger("celeris")


def _safe_return_url(request):
    candidate = request.POST.get("return_to") or request.GET.get("return_to", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return ""


class EmpresaLoginView(auth_views.LoginView):
    authentication_form = EmpresaAuthenticationForm
    template_name = "accounts/login.html"

    def get_success_url(self):
        return reverse("core:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        empresa = form.cleaned_data["empresa"]
        self.request.session["cd_empresa"] = empresa.cd_empresa
        self.request.session["nm_empresa"] = empresa.nm_empresa
        return response


class EmpresaLogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        request.session.pop("cd_empresa", None)
        request.session.pop("nm_empresa", None)
        return super().post(request, *args, **kwargs)


class CelerisPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("password_change")

    def form_valid(self, form):
        messages.success(self.request, "Senha alterada com sucesso.")
        return super().form_valid(form)


def user_companies(request):
    username = normalize_identifier(request.GET.get("usuario", ""))
    links = (
        UsuarioEmpresa.objects.select_related("empresa", "usuario")
        .filter(usuario__username=username, sn_ativo=True, empresa__sn_ativo=True)
        .order_by("-sn_padrao", "empresa__cd_empresa")
    )
    return JsonResponse(
        {
            "empresas": [
                {
                    "cd_empresa": link.empresa.cd_empresa,
                    "nm_empresa": link.empresa.nm_empresa,
                    "sn_padrao": link.sn_padrao,
                }
                for link in links
            ]
        }
    )


def session_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({"authenticated": False, "login_url": reverse("login")}, status=401)
    return JsonResponse({"authenticated": True})


@login_required
@screen_access_required("usuarios")
def usuarios(request):
    return redirect("usuario_novo")


@login_required
@screen_access_required("usuarios")
def usuario_novo(request):
    return _usuario_form(request)


@login_required
@screen_access_required("usuarios")
def usuario_editar(request, pk=None):
    return _usuario_form(request, pk)


def _usuario_form(request, pk=None):
    usuario = get_object_or_404(User, pk=pk) if pk else None
    request.current_tab_title = "Configuração do Sistema > Cadastro de usuário"
    request.current_tab_root_title = "Usuários"
    request.current_module_title = "Configuração do Sistema"
    request.current_return_url = _safe_return_url(request)
    empresa = get_object_or_404(Empresa, pk=request.session.get("cd_empresa") or 1)
    if request.GET.get("consultar") == "1":
        users = User.objects.all()
        has_filter = False
        code = request.GET.get("codigo", "").strip()
        if code.isdigit():
            users = users.filter(pk=int(code))
            has_filter = True
        text_filters = {
            "username": "username__icontains",
            "full_name": "full_name__icontains",
            "nr_cpf": "nr_cpf__icontains",
            "email": "email__icontains",
            "nr_celular": "nr_celular__icontains",
            "nr_matricula_rh": "nr_matricula_rh__icontains",
            "ds_idioma": "ds_idioma__icontains",
            "ds_profissao": "ds_profissao__icontains",
        }
        for field_name, lookup in text_filters.items():
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                users = users.filter(**{lookup: value})
                has_filter = True
        for field_name in ("dt_nascimento", "cd_prestador"):
            value = request.GET.get(field_name, "").strip()
            if value:
                users = users.filter(**{field_name: value})
                has_filter = True
        status = request.GET.get("is_active", "")
        if status in {"True", "False"}:
            users = users.filter(is_active=status == "True")
            has_filter = True
        for field_name in (
            "must_change_password",
            "can_register_patient",
            "can_change_patient",
            "can_create_users",
            "can_deactivate_users",
            "can_manage_auxiliary_tables",
            "can_configure_system",
        ):
            value = request.GET.get(field_name, "")
            if value in {"true", "on", "True"}:
                users = users.filter(**{field_name: True})
                has_filter = True
        group_ids = [value for value in request.GET.getlist("grupos") if value.isdigit()]
        company_ids = [value for value in request.GET.getlist("empresas") if value.isdigit()]
        if group_ids:
            users = users.filter(groups__id__in=group_ids)
            has_filter = True
        if company_ids:
            users = users.filter(empresas__cd_empresa__in=company_ids)
            has_filter = True
        result_ids = list(users.distinct().order_by("id").values_list("id", flat=True)[:200])
        request.session["consulta_usuarios"] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum usuário encontrado para os filtros informados.")
            return redirect("usuario_novo")
        return redirect(f"{reverse('usuario_editar', args=[result_ids[0]])}?origem=consulta")
    if usuario:
        request.current_toggle_active_url = reverse("usuario_alternar_status", args=[usuario.pk])
        request.current_toggle_active_label = "Desativar" if usuario.is_active else "Ativar"
        request.current_password_url = reverse("usuario_alterar_senha", args=[usuario.pk])
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get("consulta_usuarios", []) if query_context else []
    if usuario and usuario.pk in result_ids:
        current_index = result_ids.index(usuario.pk)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        if current_index > 0:
            request.current_first_url = f"{reverse('usuario_editar', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('usuario_editar', args=[result_ids[current_index - 1]])}?origem=consulta"
        if current_index < len(result_ids) - 1:
            request.current_next_url = f"{reverse('usuario_editar', args=[result_ids[current_index + 1]])}?origem=consulta"
            request.current_last_url = f"{reverse('usuario_editar', args=[result_ids[-1]])}?origem=consulta"
    form = UsuarioForm(request.POST or None, instance=usuario, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, "Usuário salvo com sucesso.")
        edit_url = reverse("usuario_editar", args=[saved.pk])
        if request.current_return_url:
            edit_url = f"{edit_url}?{urlencode({'return_to': request.current_return_url})}"
        elif query_context:
            edit_url = f"{edit_url}?origem=consulta"
        return redirect(edit_url)
    return render(
        request,
        "accounts/usuario_form.html",
        {"form": form, "usuario": usuario, "return_to": request.current_return_url},
    )


@login_required
@screen_access_required("usuarios")
def usuario_alternar_status(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=["is_active"])
        messages.success(request, f"Usuário {'ativado' if usuario.is_active else 'desativado'} com sucesso.")
    return redirect("usuario_editar", pk=usuario.pk)


@login_required
@screen_access_required("usuarios")
@xframe_options_sameorigin
def usuario_alterar_senha(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    request.current_tab_title = "Alterar Senha"
    request.current_tab_root_title = "Alterar Senha"
    request.current_module_title = "Administração"
    form = UsuarioPasswordForm(usuario, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Senha alterada com sucesso.")
        return redirect(f"{reverse('usuario_alterar_senha', args=[usuario.pk])}?overlay=1")
    return render(request, "accounts/usuario_password.html", {"form": form, "usuario": usuario})


@login_required
@screen_access_required("usuarios")
def copia_usuario(request):
    request.current_tab_title = "AdministraÃ§Ã£o > CÃ³pia de usuÃ¡rio"
    request.current_tab_root_title = "CÃ³pia de usuÃ¡rio"
    request.current_module_title = "AdministraÃ§Ã£o"
    empresa = get_object_or_404(Empresa, pk=request.session.get("cd_empresa") or 1)
    usuarios_ativos = (
        User.objects.filter(is_active=True, empresas=empresa)
        .distinct()
        .order_by("full_name", "username")
    )
    origem = None
    destino = None
    origem_id = request.POST.get("origem") or request.GET.get("origem")
    destino_id = request.POST.get("destino") or request.GET.get("destino")
    if origem_id:
        origem = usuarios_ativos.filter(pk=origem_id).first()
    if destino_id:
        destino = usuarios_ativos.filter(pk=destino_id).first()
    if request.method == "POST":
        if not origem or not destino:
            messages.error(request, "Selecione usuÃ¡rio de origem e destino ativos.")
        elif origem.pk == destino.pk:
            messages.error(request, "Origem e destino devem ser usuÃ¡rios diferentes.")
        else:
            destino.groups.set(origem.groups.all())
            destino.setores.set(origem.setores.all())
            UsuarioEmpresa.objects.filter(usuario=destino).delete()
            for vinculo in UsuarioEmpresa.objects.filter(usuario=origem).select_related("empresa"):
                UsuarioEmpresa.objects.create(
                    usuario=destino,
                    empresa=vinculo.empresa,
                    sn_padrao=vinculo.sn_padrao,
                    sn_ativo=vinculo.sn_ativo,
                )
            for field_name in (
                "can_register_patient",
                "can_change_patient",
                "can_create_users",
                "can_deactivate_users",
                "can_manage_auxiliary_tables",
                "can_configure_system",
                "is_coordinator",
            ):
                setattr(destino, field_name, getattr(origem, field_name))
            destino.save(update_fields=[
                "can_register_patient",
                "can_change_patient",
                "can_create_users",
                "can_deactivate_users",
                "can_manage_auxiliary_tables",
                "can_configure_system",
                "is_coordinator",
            ])
            messages.success(request, "PermissÃµes copiadas para o usuÃ¡rio de destino.")
            return redirect(f"{reverse('copia_usuario')}?origem={origem.pk}&destino={destino.pk}")
    return render(
        request,
        "accounts/copia_usuario.html",
        {
            "usuarios": usuarios_ativos,
            "origem": origem,
            "destino": destino,
            "origem_id": str(origem_id or ""),
            "destino_id": str(destino_id or ""),
        },
    )


@login_required
def usuario_login_sugerido(request):
    current_user = request.GET.get("usuario", "")
    return JsonResponse(
        {
            "login": available_username(
                request.GET.get("nome", ""),
                exclude_user_id=int(current_user) if current_user.isdigit() else None,
            )
        }
    )


@login_required
def prestador_dados_usuario(request, pk):
    provider = get_object_or_404(
        Prestador,
        pk=pk,
        cd_empresa_id=request.session.get("cd_empresa") or 1,
    )
    return JsonResponse(
        {
            "full_name": provider.nm_prestador,
            "nr_cpf": provider.nr_cpf,
            "dt_nascimento": provider.dt_nascimento.isoformat() if provider.dt_nascimento else "",
            "email": provider.ds_email,
            "nr_celular": provider.nr_celular,
            "ds_profissao": provider.tp_prestador,
        }
    )


@login_required
@screen_access_required("perfis")
def perfis(request):
    request.current_tab_title = "Administração > Papéis"
    request.current_tab_root_title = "Papéis"
    request.current_module_title = "Administração"
    query = request.GET.get("q", "").strip()
    code = request.GET.get("codigo", "").strip()
    status = request.GET.get("status", "")
    try:
        for group_id in Group.objects.filter(papel__isnull=True).values_list("pk", flat=True):
            Papel.objects.get_or_create(grupo_id=group_id)
        registros = Group.objects.select_related("papel").prefetch_related("papel__modulos", "papel__telas")
        if query:
            registros = registros.filter(name__icontains=query)
        if code.isdigit():
            registros = registros.filter(pk=int(code))
        if status in {"ativo", "inativo"}:
            registros = registros.filter(papel__sn_ativo=status == "ativo")
        elif status != "todos":
            registros = registros.filter(papel__sn_ativo=True)
        registros = paginate_table(
            request,
            registros,
            {"id", "name", "papel__sn_ativo"},
            "id",
            load_on_open=True,
        )
    except Exception:
        logger.exception("Erro ao executar consulta de papeis")
        registros = []
        request.current_record_status = "Erro ao executar consulta"
        messages.error(request, "Erro ao executar consulta.")
    return render(
        request,
        "accounts/perfis.html",
        {"registros": registros, "query": query, "code": code, "status": status},
    )


@login_required
@screen_access_required("perfis")
def perfil_editar(request, pk=None):
    perfil = get_object_or_404(Group, pk=pk) if pk else None
    request.current_tab_title = "Administração > Papel"
    request.current_tab_root_title = "Papéis"
    request.current_module_title = "Administração"
    request.current_return_url = _safe_return_url(request)
    if perfil:
        papel, _ = Papel.objects.get_or_create(grupo=perfil)
        request.current_toggle_active_url = reverse("perfil_alternar_status", args=[perfil.pk])
        request.current_toggle_active_label = "Desativar" if papel.sn_ativo else "Ativar"
    form = PerfilForm(request.POST or None, instance=perfil)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, "Papel salvo com sucesso.")
        edit_url = reverse("perfil_editar", args=[saved.pk])
        if request.current_return_url:
            edit_url = f"{edit_url}?{urlencode({'return_to': request.current_return_url})}"
        return redirect(edit_url)
    selected_modules = {
        int(value)
        for value in (request.POST.getlist("modulos") if request.method == "POST" else form["modulos"].value() or [])
        if str(value).isdigit()
    }
    selected_screens = {
        int(value)
        for value in (request.POST.getlist("telas") if request.method == "POST" else form["telas"].value() or [])
        if str(value).isdigit()
    }
    return render(
        request,
        "accounts/perfil_form.html",
        {
            "form": form,
            "perfil": perfil,
            "modules": form.fields["modulos"].queryset.prefetch_related("screens"),
            "selected_modules": selected_modules,
            "selected_screens": selected_screens,
            "return_to": request.current_return_url,
        },
    )


@login_required
@screen_access_required("perfis")
def perfil_alternar_status(request, pk):
    group = get_object_or_404(Group, pk=pk)
    papel, _ = Papel.objects.get_or_create(grupo=group)
    if request.method == "POST":
        papel.sn_ativo = not papel.sn_ativo
        papel.save(update_fields=["sn_ativo"])
        messages.success(request, f"Papel {'ativado' if papel.sn_ativo else 'desativado'} com sucesso.")
    return redirect("perfil_editar", pk=group.pk)


@login_required
@screen_access_required("permissoes")
def permissoes(request):
    request.current_tab_title = "Administração > Permissões"
    request.current_tab_root_title = "Permissões"
    request.current_module_title = "Administração"
    registros = Permission.objects.select_related("content_type").order_by("content_type__app_label", "content_type__model", "codename")
    return render(request, "accounts/permissoes.html", {"registros": registros})
