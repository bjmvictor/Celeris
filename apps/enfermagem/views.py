from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import BoardingStatus


@login_required
def boarding(request):
    current = BoardingStatus.objects.first()
    history = BoardingStatus.objects.all()[:50]
    return render(request, "core/boarding.html", {"current": current, "history": history})
