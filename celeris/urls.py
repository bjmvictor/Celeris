from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from apps.atendimento import views as atendimento_views
from apps.atendimento.views_painel import painel_chamada_publico


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/logo.png"), permanent=False)),
    path("PEP/", atendimento_views.pep_standalone, name="pep_standalone"),
    path("PEP/pacientes/<int:cd_paciente>/", atendimento_views.pep_prontuario_paciente_standalone, name="pep_prontuario_standalone"),
    path("painel/", painel_chamada_publico, name="painel_chamada_standalone"),
    path("totem/", atendimento_views.gerar_senha_totem, name="totem_standalone"),
    path("TI/alteracao-senha-usuario/", RedirectView.as_view(url=reverse_lazy("ti:alteracao_senha_usuario"), permanent=False)),
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("atendimento/", include("apps.atendimento.urls")),
    path("almoxarifado/", include("apps.estoque.urls")),
    path("reports/", include("apps.reports.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("social/", include("apps.social.urls")),
    path("enfermagem/", include("apps.enfermagem.urls")),
    path("ti/", include("apps.ti.urls")),
]
