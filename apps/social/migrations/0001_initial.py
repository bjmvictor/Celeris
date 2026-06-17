from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SocialPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("month", models.PositiveSmallIntegerField()),
                ("year", models.PositiveSmallIntegerField()),
                ("active", models.BooleanField(default=True)),
            ],
            options={"ordering": ("-year", "-month"), "unique_together": {("month", "year")}},
        ),
        migrations.CreateModel(
            name="SocialAttendance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("patient_name", models.CharField(max_length=180)),
                ("attendance_code", models.CharField(blank=True, max_length=50)),
                ("patient_attended_at", models.DateTimeField(blank=True, null=True)),
                ("social_attended_at", models.DateTimeField(auto_now_add=True)),
                ("sector", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("bed_attendance", models.PositiveIntegerField(default=0)),
                ("spontaneous_demand", models.PositiveIntegerField(default=0)),
                ("routine_guidance", models.PositiveIntegerField(default=0)),
                ("social_rights_guidance", models.PositiveIntegerField(default=0)),
                ("family_articulation", models.PositiveIntegerField(default=0)),
                ("network_articulation", models.PositiveIntegerField(default=0)),
                ("victim_reception", models.PositiveIntegerField(default=0)),
                ("socioassistential_referral", models.PositiveIntegerField(default=0)),
                ("health_referral", models.PositiveIntegerField(default=0)),
                ("post_death", models.PositiveIntegerField(default=0)),
                ("report_preparation", models.PositiveIntegerField(default=0)),
                ("social_evolution", models.PositiveIntegerField(default=0)),
                ("attendance_declaration", models.PositiveIntegerField(default=0)),
                ("outpatient_attendance", models.PositiveIntegerField(default=0)),
                ("educational_activity", models.PositiveIntegerField(default=0)),
                ("microcephaly_attendance", models.PositiveIntegerField(default=0)),
                ("vdrl_referral", models.PositiveIntegerField(default=0)),
                ("b24_referral", models.PositiveIntegerField(default=0)),
                ("mental_health_reception", models.PositiveIntegerField(default=0)),
                ("intersectoral_articulation", models.PositiveIntegerField(default=0)),
                ("discharge_transport_request", models.PositiveIntegerField(default=0)),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="social.socialperiod")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
