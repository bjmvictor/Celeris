from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import AgentMachine


@login_required
def agentes(request):
    machines = AgentMachine.objects.all()
    return render(request, "ti/agentes.html", {"machines": machines})
