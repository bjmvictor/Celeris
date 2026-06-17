from django.contrib import admin
from django.urls import include, path


urlpatterns = [
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
