from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class PrioridadeSuporte(TimeStampedModel):
    cd_prioridade_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    nm_prioridade = models.CharField("prioridade", max_length=80)
    nr_peso = models.PositiveIntegerField("peso", default=0)
    ds_cor = models.CharField("cor", max_length=20, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "suporte_prioridade"
        verbose_name = "Prioridade de suporte"
        verbose_name_plural = "Prioridades de suporte"
        ordering = ("nr_peso", "nm_prioridade")
        unique_together = ("cd_empresa", "nm_prioridade")

    def __str__(self):
        return self.nm_prioridade


class MotivoServicoSuporte(TimeStampedModel):
    cd_motivo_servico_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    cd_oficina = models.ForeignKey("tickets.OficinaSuporte", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_oficina_suporte")
    nm_motivo = models.CharField("motivo", max_length=120)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "suporte_motivo_servico"
        verbose_name = "Motivo de serviço"
        verbose_name_plural = "Motivos de serviço"
        ordering = ("cd_oficina__nm_oficina", "nm_motivo")
        unique_together = ("cd_empresa", "cd_oficina", "nm_motivo")

    def __str__(self):
        return self.nm_motivo


class MotivoConclusaoSuporte(TimeStampedModel):
    cd_motivo_conclusao_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    cd_oficina = models.ForeignKey("tickets.OficinaSuporte", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_oficina_suporte")
    nm_motivo = models.CharField("motivo", max_length=120)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "suporte_motivo_conclusao"
        verbose_name = "Motivo de conclusão"
        verbose_name_plural = "Motivos de conclusão"
        ordering = ("cd_oficina__nm_oficina", "nm_motivo")
        unique_together = ("cd_empresa", "cd_oficina", "nm_motivo")

    def __str__(self):
        return self.nm_motivo


class OficinaSuporte(TimeStampedModel):
    cd_oficina_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    nm_oficina = models.CharField("oficina", max_length=120)
    ds_descricao = models.CharField("descricao", max_length=220, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)
    usuarios = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="oficinas_suporte", blank=True)

    class Meta:
        db_table = "suporte_oficina"
        verbose_name = "Oficina de suporte"
        verbose_name_plural = "Oficinas de suporte"
        ordering = ("nm_oficina",)
        unique_together = ("cd_empresa", "nm_oficina")

    def __str__(self):
        return self.nm_oficina


class Ticket(TimeStampedModel):
    STATUS = [
        ("open", "Aberto"),
        ("received", "Recebido"),
        ("done", "Concluido"),
        ("not_done", "Não concluído"),
        ("cancelled", "Cancelado"),
    ]

    cd_empresa = models.ForeignKey("accounts.Empresa", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_empresa")
    module = models.CharField("módulo", max_length=80)
    title = models.CharField("título", max_length=180)
    description = models.TextField("descrição", blank=True)
    sector = models.CharField("setor textual", max_length=120, blank=True)
    priority = models.CharField("prioridade textual", max_length=30, default="normal")
    cd_setor = models.ForeignKey("accounts.Setor", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor", verbose_name="setor")
    cd_prioridade = models.ForeignKey(PrioridadeSuporte, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_prioridade_suporte", verbose_name="prioridade")
    cd_motivo = models.ForeignKey(MotivoServicoSuporte, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_motivo_servico_suporte", verbose_name="motivo")
    cd_oficina = models.ForeignKey(OficinaSuporte, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_oficina_suporte", verbose_name="oficina")
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="requested_tickets", null=True, blank=True, on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_tickets", null=True, blank=True, on_delete=models.SET_NULL)
    received_at = models.DateTimeField(null=True, blank=True)
    cd_motivo_conclusao = models.ForeignKey(MotivoConclusaoSuporte, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_motivo_conclusao_suporte", related_name="tickets_concluidos", verbose_name="motivo da conclusão")
    performed_at = models.DateTimeField(null=True, blank=True)
    conclusion = models.TextField(blank=True)
    ds_observacao_conclusao = models.TextField("observação da conclusão", blank=True)
    performers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="performed_tickets", blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "chamado"
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.module} - {self.title}"


class UsuarioOficinaSuporte(TimeStampedModel):
    cd_usuario_oficina_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_column="cd_usuario", verbose_name="usuario")
    cd_oficina = models.ForeignKey(OficinaSuporte, on_delete=models.PROTECT, db_column="cd_oficina_suporte", verbose_name="oficina")
    sn_ativo = models.BooleanField("ativo", default=True)
    sn_atende = models.BooleanField("atende", default=True)
    sn_solicita = models.BooleanField("solicita", default=True)

    class Meta:
        db_table = "suporte_usuario_oficina"
        verbose_name = "Usuario x oficina"
        verbose_name_plural = "Usuarios x oficinas"
        ordering = ("cd_usuario__username", "cd_oficina__nm_oficina")
        unique_together = ("cd_empresa", "cd_usuario", "cd_oficina")

    def __str__(self):
        return f"{self.cd_usuario} - {self.cd_oficina}"


class TicketTransferenciaSuporte(TimeStampedModel):
    cd_transferencia_suporte = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey("accounts.Empresa", on_delete=models.PROTECT, db_column="cd_empresa")
    cd_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, db_column="cd_ticket", related_name="transferencias")
    cd_oficina_origem = models.ForeignKey(OficinaSuporte, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_oficina_origem", related_name="+")
    cd_oficina_destino = models.ForeignKey(OficinaSuporte, on_delete=models.PROTECT, db_column="cd_oficina_destino", related_name="+")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario")
    dh_transferencia = models.DateTimeField(default=timezone.now)
    ds_observacao = models.CharField("observacao", max_length=240, blank=True)

    class Meta:
        db_table = "suporte_ticket_transferencia"
        verbose_name = "Transferencia de chamado"
        verbose_name_plural = "Transferencias de chamados"
        ordering = ("-dh_transferencia",)
