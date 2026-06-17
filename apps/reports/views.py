from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import ReportQuery


@login_required
def report_list(request):
    reports = ReportQuery.objects.all()
    return render(request, "reports/list.html", {"reports": reports})


@login_required
def report_run(request):
    reports = ReportQuery.objects.filter(active=True, show_in_menu=True)
    return render(request, "reports/run.html", {"reports": reports})
