from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class SocialPeriod(TimeStampedModel):
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "periodo_social"
        unique_together = ("month", "year")
        ordering = ("-year", "-month")

    def __str__(self) -> str:
        return f"{self.month:02d}/{self.year}"


class SocialAttendance(TimeStampedModel):
    period = models.ForeignKey(SocialPeriod, on_delete=models.PROTECT)
    patient_name = models.CharField(max_length=180)
    attendance_code = models.CharField(max_length=50, blank=True)
    patient_attended_at = models.DateTimeField(null=True, blank=True)
    social_attended_at = models.DateTimeField(auto_now_add=True)
    sector = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    bed_attendance = models.PositiveIntegerField(default=0)
    spontaneous_demand = models.PositiveIntegerField(default=0)
    routine_guidance = models.PositiveIntegerField(default=0)
    social_rights_guidance = models.PositiveIntegerField(default=0)
    family_articulation = models.PositiveIntegerField(default=0)
    network_articulation = models.PositiveIntegerField(default=0)
    victim_reception = models.PositiveIntegerField(default=0)
    socioassistential_referral = models.PositiveIntegerField(default=0)
    health_referral = models.PositiveIntegerField(default=0)
    post_death = models.PositiveIntegerField(default=0)
    report_preparation = models.PositiveIntegerField(default=0)
    social_evolution = models.PositiveIntegerField(default=0)
    attendance_declaration = models.PositiveIntegerField(default=0)
    outpatient_attendance = models.PositiveIntegerField(default=0)
    educational_activity = models.PositiveIntegerField(default=0)
    microcephaly_attendance = models.PositiveIntegerField(default=0)
    vdrl_referral = models.PositiveIntegerField(default=0)
    b24_referral = models.PositiveIntegerField(default=0)
    mental_health_reception = models.PositiveIntegerField(default=0)
    intersectoral_articulation = models.PositiveIntegerField(default=0)
    discharge_transport_request = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "atendimento_social"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.patient_name
