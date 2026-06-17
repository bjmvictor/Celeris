from django.urls import path

from . import views


app_name = "social"

urlpatterns = [
    path("atendimento/", views.atendimento, name="atendimento"),
    path("acompanhar/", views.acompanhar, name="acompanhar"),
    path("consolidado/", views.consolidado, name="consolidado"),
    path("relatorios/", views.relatorios, name="relatorios"),
]
