from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class BoardingStatus(TimeStampedModel):
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="green")
    level = models.CharField(max_length=40, default="Rotina")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "status_painel"
        ordering = ("-created_at",)


class BoardingAutoConfig(TimeStampedModel):
    enabled = models.BooleanField(default=False)
    database = models.CharField(max_length=40, default="principal")
    sql = models.TextField(blank=True)
    refresh_seconds = models.PositiveIntegerField(default=300)

    class Meta:
        db_table = "configuracao_automatica_painel"
