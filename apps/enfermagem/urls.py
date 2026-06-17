from django.urls import path

from . import views


app_name = "enfermagem"

urlpatterns = [
    path("boarding/", views.boarding, name="boarding"),
]
