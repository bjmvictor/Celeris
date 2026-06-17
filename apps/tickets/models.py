from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Ticket(TimeStampedModel):
    STATUS = [
        ("open", "Aberto"),
        ("done", "Concluido"),
        ("cancelled", "Cancelado"),
    ]

    module = models.CharField(max_length=80)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    sector = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=30, default="normal")
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="requested_tickets", null=True, blank=True, on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_tickets", null=True, blank=True, on_delete=models.SET_NULL)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.module} - {self.title}"
