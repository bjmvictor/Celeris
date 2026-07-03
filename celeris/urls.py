from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/logo.png"), permanent=False)),
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("atendimento/", include("apps.atendimento.urls")),
    path("reports/", include("apps.reports.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("social/", include("apps.social.urls")),
    path("enfermagem/", include("apps.enfermagem.urls")),
    path("ti/", include("apps.ti.urls")),
]
