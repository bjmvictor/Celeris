from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.EmpresaLoginView.as_view(), name="login"),
    path("empresas-usuario/", views.user_companies, name="user_companies"),
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
