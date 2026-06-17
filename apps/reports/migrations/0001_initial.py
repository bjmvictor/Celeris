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
            name="ReportQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("code", models.CharField(max_length=120, unique=True)),
                ("name", models.CharField(max_length=180)),
                ("menu_name", models.CharField(blank=True, max_length=180)),
                ("module", models.CharField(max_length=80)),
                ("destination", models.CharField(blank=True, max_length=120)),
                ("sql", models.TextField()),
                ("active", models.BooleanField(default=True)),
                ("show_in_menu", models.BooleanField(default=True)),
                ("bind_config", models.JSONField(blank=True, default=list)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("module", "name")},
        ),
        migrations.CreateModel(
            name="ReportQueryVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("sql", models.TextField()),
                ("bind_config", models.JSONField(blank=True, default=list)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="reports.reportquery")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
