from django.urls import path

from . import views


app_name = "ti"

urlpatterns = [
    path("agentes/", views.agentes, name="agentes"),
]
