from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.EmpresaLoginView.as_view(), name="login"),
    path("empresas-usuario/", views.user_companies, name="user_companies"),
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/novo/", views.usuario_novo, name="usuario_novo"),
    path("usuarios/<int:pk>/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/alternar-status/", views.usuario_alternar_status, name="usuario_alternar_status"),
    path("usuarios/<int:pk>/alterar-senha/", views.usuario_alterar_senha, name="usuario_alterar_senha"),
    path("usuarios/login-sugerido/", views.usuario_login_sugerido, name="usuario_login_sugerido"),
    path("usuarios/prestador/<int:pk>/dados/", views.prestador_dados_usuario, name="prestador_dados_usuario"),
    path("perfis/", views.perfis, name="perfis"),
    path("perfis/novo/", views.perfil_editar, name="perfil_novo"),
    path("perfis/<int:pk>/", views.perfil_editar, name="perfil_editar"),
    path("perfis/<int:pk>/alternar-status/", views.perfil_alternar_status, name="perfil_alternar_status"),
    path("permissoes/", views.permissoes, name="permissoes"),
    path("logout/", views.EmpresaLogoutView.as_view(), name="logout"),
    path(
        "alterar-senha/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/alterar-senha/concluido/",
        ),
        name="password_change",
    ),
    path(
        "alterar-senha/concluido/",
        auth_views.PasswordChangeDoneView.as_view(template_name="accounts/password_change_done.html"),
        name="password_change_done",
    ),
]
