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
            name="Ticket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("module", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("sector", models.CharField(blank=True, max_length=120)),
                ("priority", models.CharField(default="normal", max_length=30)),
                ("status", models.CharField(choices=[("open", "Aberto"), ("done", "Concluido"), ("cancelled", "Cancelado")], default="open", max_length=20)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tickets", to=settings.AUTH_USER_MODEL)),
                ("requester", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="requested_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
