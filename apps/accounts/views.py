from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
import logging
from urllib.parse import urlencode

from apps.atendimento.models import Prestador
from apps.core.table_utils import paginate_table

from .access import screen_access_required
from .forms import EmpresaAuthenticationForm, PerfilForm, UsuarioForm, UsuarioPasswordForm
from .models import Empresa, Papel, User, UsuarioEmpresa, available_username, normalize_identifier


logger = logging.getLogger("celeris")


def _safe_return_url(request):
    candidate = request.POST.get("return_to") or request.GET.get("return_to", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return ""


class EmpresaLoginView(auth_views.LoginView):
    authentication_form = EmpresaAuthenticationForm
    template_name = "accounts/login.html"

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


@login_required
@screen_access_required("usuarios")
def usuarios(request):
    request.current_tab_title = "Configuração do Sistema > Usuários"
    request.current_tab_root_title = "Usuários"
    request.current_module_title = "Configuração do Sistema"
    query = request.GET.get("q", "").strip()
    code = request.GET.get("codigo", "").strip()
    status = request.GET.get("status", "")
    role = request.GET.get("papel", "")
    try:
        registros = User.objects.prefetch_related("groups").order_by("id")
        if query:
            registros = registros.filter(Q(username__icontains=query) | Q(full_name__icontains=query))
        if code.isdigit():
            registros = registros.filter(pk=int(code))
        if status in {"ativo", "inativo"}:
            registros = registros.filter(is_active=status == "ativo")
        elif status != "todos":
            registros = registros.filter(is_active=True)
        if role.isdigit():
            registros = registros.filter(groups__id=int(role))
        registros = paginate_table(
            request,
            registros.distinct(),
            {"id", "username", "full_name", "email", "is_active"},
            "id",
            load_on_open=True,
        )
    except Exception:
        logger.exception("Erro ao executar consulta de usuarios")
        registros = []
        request.current_query_message = "Erro ao executar consulta."
    return render(
        request,
        "accounts/usuarios.html",
        {
            "registros": registros,
            "query": query,
            "code": code,
            "status": status,
            "selected_role": int(role) if role.isdigit() else None,
            "roles": Group.objects.filter(papel__sn_ativo=True).order_by("name"),
        },
    )


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
    if usuario:
        request.current_toggle_active_url = reverse("usuario_alternar_status", args=[usuario.pk])
        request.current_toggle_active_label = "Desativar" if usuario.is_active else "Ativar"
        request.current_password_url = reverse("usuario_alterar_senha", args=[usuario.pk])
    form = UsuarioForm(request.POST or None, instance=usuario, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, "Usuário salvo com sucesso.")
        edit_url = reverse("usuario_editar", args=[saved.pk])
        if request.current_return_url:
            edit_url = f"{edit_url}?{urlencode({'return_to': request.current_return_url})}"
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
        request.current_query_message = "Erro ao executar consulta."
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
