from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Ticket


@login_required
def ticket_list(request):
    tickets = Ticket.objects.all()[:100]
    return render(request, "core/table_page.html", {"title": "Chamados", "rows": tickets})
