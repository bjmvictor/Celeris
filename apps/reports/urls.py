from django.urls import path

from . import views


app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("gerar/", views.report_run, name="run"),
]
