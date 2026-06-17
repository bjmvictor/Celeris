from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import SocialAttendance


@login_required
def atendimento(request):
    return render(request, "core/form_page.html", {"title": "Atendimento Social"})


@login_required
def acompanhar(request):
    rows = SocialAttendance.objects.select_related("period", "user")[:100]
    return render(request, "social/acompanhar.html", {"rows": rows})


@login_required
def consolidado(request):
    return render(request, "core/placeholder.html", {"title": "Consolidado Social"})


@login_required
def relatorios(request):
    return render(request, "core/placeholder.html", {"title": "Relatórios Sociais"})
