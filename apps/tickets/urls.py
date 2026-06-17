from django.urls import path

from . import views


app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list, name="list"),
]
