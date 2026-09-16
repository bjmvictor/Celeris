"""PEP application entry points, delegating to legacy controllers temporarily."""
from apps.atendimento import views as legacy_views


def pep_standalone(request):
    return legacy_views.pep_standalone(request)


def pep_prontuario_paciente_standalone(request, cd_paciente):
    return legacy_views.pep_prontuario_paciente_standalone(request, cd_paciente)
