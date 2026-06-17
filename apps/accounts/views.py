from django.contrib.auth import views as auth_views
from django.http import JsonResponse

from .forms import EmpresaAuthenticationForm
from .models import UsuarioEmpresa, normalize_identifier


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
