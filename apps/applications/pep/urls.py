from django.urls import path
from . import views

urlpatterns = [
    path("", views.pep_standalone, name="pep_standalone"),
    path("pacientes/<int:cd_paciente>/", views.pep_prontuario_paciente_standalone, name="pep_prontuario_standalone"),
]
