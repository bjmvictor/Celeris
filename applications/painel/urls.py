from django.urls import path
from apps.atendimento.views_painel import midia_painel_publica, painel_chamada_publico

urlpatterns = [path("", painel_chamada_publico, name="painel_chamada_standalone"), path("midia/<int:cd_painel>/", midia_painel_publica, name="painel_chamada_midia")]
