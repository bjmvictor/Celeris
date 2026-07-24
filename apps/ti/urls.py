from django.urls import path

from apps.accounts import views as accounts_views

from . import views


app_name = "ti"

urlpatterns = [
    path("agentes/", views.agentes, name="agentes"),
    path("alteracao-senha-usuario/", accounts_views.usuario_alterar_senha, name="alteracao_senha_usuario"),
]
