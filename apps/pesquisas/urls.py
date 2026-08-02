from django.urls import path

from . import views


app_name = "pesquisas"

urlpatterns = [
    path("configuracao/", views.configuracao, name="configuracao"),
    path("perguntas/", views.perguntas_parametros, name="perguntas_parametros"),
    path("calculos/", views.calculos_resultados, name="calculos_resultados"),
    path("disponiveis/", views.disponiveis, name="disponiveis"),
    path("resultados/", views.resultados, name="resultados"),
    path("responder/<uuid:token>/", views.responder, name="responder"),
    path("concluida/<int:resposta_id>/", views.concluida, name="concluida"),
]
