from django.urls import path
from apps.atendimento import views

urlpatterns = [path("", views.gerar_senha_totem, name="totem_standalone")]
