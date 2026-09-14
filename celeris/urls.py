from django.conf import settings
from django.conf.urls.static import static as media_static
from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from apps.platform.registry import registry


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/logo.png"), permanent=False)),
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
    path("pesquisas/", include("apps.pesquisas.urls")),
]

# Applications contribute their own public URLs.  The root project no longer
# imports PEP, classification, panel or totem controllers directly.
urlpatterns = [*registry.urlpatterns(), *urlpatterns]

if settings.DEBUG:
    urlpatterns += media_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += media_static("/painel_chamada/", document_root=settings.BASE_DIR / "painel_chamada")
