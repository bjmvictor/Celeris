from django.urls import path
from apps.atendimento import views

urlpatterns = [
    path("", views.classificacao_standalone, name="classificacao_standalone"),
    path("senhas/", views.configurar_senhas_standalone, name="class_senhas"),
    path("senhas/<int:cd_tipo>/", views.configurar_senhas_standalone, name="class_senha_editar"),
    path("perguntas/", views.perguntas_classificacao_standalone, name="class_perguntas"),
    path("fluxos/", views.fluxos_classificacao_standalone, name="class_fluxos"),
    path("fluxos/<int:cd_fluxo>/escalas/", views.fluxo_escalas_classificacao_standalone, name="class_fluxo_escalas"),
    path("cores/", views.cores_classificacao_standalone, name="class_cores"),
    path("escalas/", views.escalas_classificacao_standalone, name="class_escalas"),
    path("escalas/<int:cd_escala>/", views.escalas_classificacao_standalone, name="class_escala_editar"),
    path("protocolos/", views.protocolos_senha_standalone, name="class_protocolos"),
    path("icones/", views.icones_chamada_standalone, name="class_icones"),
]
