from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ReportQuery(TimeStampedModel):
    BIND_TYPES = [
        ("text", "Texto"),
        ("number", "Número"),
        ("date", "Data"),
        ("month", "Mês/Ano"),
        ("year", "Ano"),
        ("select_sql", "Select SQL"),
    ]

    code = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=180)
    menu_name = models.CharField(max_length=180, blank=True)
    module = models.CharField(max_length=80)
    destination = models.CharField(max_length=120, blank=True)
    sql = models.TextField()
    active = models.BooleanField(default=True)
    show_in_menu = models.BooleanField(default=True)
    bind_config = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "consulta_relatorio"
        ordering = ("module", "name")

    def __str__(self) -> str:
        return self.menu_name or self.name


class ReportQueryVersion(TimeStampedModel):
    report = models.ForeignKey(ReportQuery, related_name="versions", on_delete=models.CASCADE)
    sql = models.TextField()
    bind_config = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "versao_consulta_relatorio"
        ordering = ("-created_at",)
