from django.conf import settings
from django.conf.urls.static import static as media_static
from django.contrib import admin
from django.templatetags.static import static
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView

from apps.atendimento import views as atendimento_views
from apps.atendimento.views_painel import midia_painel_publica, painel_chamada_publico


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=static("img/logo.png"), permanent=False)),
    path("PEP/", atendimento_views.pep_standalone, name="pep_standalone"),
    path("class/", atendimento_views.classificacao_standalone, name="classificacao_standalone"),
    path("class/senhas/", atendimento_views.configurar_senhas_standalone, name="class_senhas"),
    path("class/senhas/<int:cd_tipo>/", atendimento_views.configurar_senhas_standalone, name="class_senha_editar"),
    path("class/perguntas/", atendimento_views.perguntas_classificacao_standalone, name="class_perguntas"),
    path("class/fluxos/", atendimento_views.fluxos_classificacao_standalone, name="class_fluxos"),
    path("class/fluxos/<int:cd_fluxo>/escalas/", atendimento_views.fluxo_escalas_classificacao_standalone, name="class_fluxo_escalas"),
    path("class/cores/", atendimento_views.cores_classificacao_standalone, name="class_cores"),
    path("class/escalas/", atendimento_views.escalas_classificacao_standalone, name="class_escalas"),
    path("class/escalas/<int:cd_escala>/", atendimento_views.escalas_classificacao_standalone, name="class_escala_editar"),
    path("class/protocolos/", atendimento_views.protocolos_senha_standalone, name="class_protocolos"),
    path("class/icones/", atendimento_views.icones_chamada_standalone, name="class_icones"),
    path("PEP/pacientes/<int:cd_paciente>/", atendimento_views.pep_prontuario_paciente_standalone, name="pep_prontuario_standalone"),
    path("painel/", painel_chamada_publico, name="painel_chamada_standalone"),
    path("painel/midia/<int:cd_painel>/", midia_painel_publica, name="painel_chamada_midia"),
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
    path("pesquisas/", include("apps.pesquisas.urls")),
]

if settings.DEBUG:
    urlpatterns += media_static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += media_static("/painel_chamada/", document_root=settings.BASE_DIR / "painel_chamada")
