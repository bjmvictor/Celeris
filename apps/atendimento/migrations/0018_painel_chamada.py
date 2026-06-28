from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0011_setor_setorusuario"),
        ("atendimento", "0017_patient_provider_review"),
    ]

    operations = [
        migrations.CreateModel(
            name="PainelChamada",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_painel_chamada", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_painel", models.CharField(max_length=120)),
                ("nm_maquina", models.CharField(max_length=120)),
                ("tp_painel", models.CharField(choices=[("SALA", "Sala"), ("CONSULTORIO", "Consultório"), ("GUICHE", "Guichê"), ("PAINEL", "Painel")], default="PAINEL", max_length=20)),
                ("nr_referencia", models.CharField(blank=True, max_length=20)),
                ("ds_layout", models.CharField(default="padrao", max_length=40)),
                ("ds_tamanho", models.CharField(default="medio", max_length=20)),
                ("ds_cor", models.CharField(default="azul", max_length=20)),
                ("sn_voz", models.BooleanField(default=True)),
                ("ds_midia_url", models.CharField(blank=True, max_length=500)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "painel_chamada",
                "ordering": ("nm_painel",),
                "unique_together": {("cd_empresa", "nm_maquina")},
            },
        ),
        migrations.CreateModel(
            name="PainelChamadaSetor",
            fields=[
                ("cd_painel_chamada_setor", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_painel_chamada", models.ForeignKey(db_column="cd_painel_chamada", on_delete=django.db.models.deletion.CASCADE, to="atendimento.painelchamada")),
                ("cd_setor", models.ForeignKey(db_column="cd_setor", on_delete=django.db.models.deletion.PROTECT, to="accounts.setor")),
            ],
            options={
                "db_table": "painel_chamada_setor",
                "unique_together": {("cd_painel_chamada", "cd_setor")},
            },
        ),
        migrations.CreateModel(
            name="ChamadaPainel",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_chamada_painel", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_local", models.CharField(blank=True, max_length=80)),
                ("ds_status", models.CharField(choices=[("CHAMADO", "Chamado"), ("ATENDIDO", "Atendido"), ("CANCELADO", "Cancelado")], default="CHAMADO", max_length=20)),
                ("dh_chamada", models.DateTimeField(default=django.utils.timezone.now)),
                ("cd_atendimento", models.ForeignKey(db_column="cd_atendimento", on_delete=django.db.models.deletion.PROTECT, related_name="chamadas_painel", to="atendimento.atendimento")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_painel_chamada", models.ForeignKey(blank=True, db_column="cd_painel_chamada", null=True, on_delete=django.db.models.deletion.SET_NULL, to="atendimento.painelchamada")),
                ("cd_setor", models.ForeignKey(db_column="cd_setor", on_delete=django.db.models.deletion.PROTECT, to="accounts.setor")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "chamada_painel",
                "ordering": ("-dh_chamada",),
            },
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="setores",
            field=models.ManyToManyField(blank=True, related_name="paineis_chamada", through="atendimento.PainelChamadaSetor", to="accounts.setor"),
        ),
    ]
