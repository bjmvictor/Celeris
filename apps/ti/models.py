from django.db import models

from apps.core.models import TimeStampedModel


class AgentMachine(TimeStampedModel):
    STATUS = [("online", "Conectada"), ("offline", "Sem conexao")]

    agent_key = models.CharField(max_length=160, unique=True)
    machine_name = models.CharField(max_length=120)
    username = models.CharField(max_length=120, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="offline")
    operating_system = models.CharField(max_length=180, blank=True)
    cpu = models.CharField(max_length=220, blank=True)
    memory_mb = models.PositiveIntegerField(null=True, blank=True)
    storage_total_mb = models.PositiveIntegerField(null=True, blank=True)
    storage_free_mb = models.PositiveIntegerField(null=True, blank=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    disconnected_at = models.DateTimeField(null=True, blank=True)
    display_enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "maquina_agente"
        ordering = ("machine_name",)

    def __str__(self) -> str:
        return self.machine_name


class AgentEvent(TimeStampedModel):
    machine = models.ForeignKey(AgentMachine, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=40)
    title = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "evento_agente"
        ordering = ("-created_at",)
