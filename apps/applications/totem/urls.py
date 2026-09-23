from django.urls import path
from . import views

urlpatterns = [path("", views.gerar_senha_totem, name="totem_standalone")]
