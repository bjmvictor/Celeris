from django.db import migrations, models
import django.db.models.deletion


def seed_default_convenio(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Convenio = apps.get_model("atendimento", "Convenio")
    for empresa in Empresa.objects.filter(sn_ativo=True):
        Convenio.objects.get_or_create(
            cd_empresa=empresa,
            nm_convenio="PARTICULAR",
            defaults={"sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_user_groups_alter_user_is_active"),
        ("atendimento", "0002_historico_motivo_alteracao"),
    ]

    operations = [
        migrations.CreateModel(
            name="Convenio",
            fields=[
                ("cd_convenio", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_convenio", models.CharField(max_length=160)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
            ],
            options={"db_table": "convenio", "ordering": ("nm_convenio",), "unique_together": {("cd_empresa", "nm_convenio")}},
        ),
        migrations.CreateModel(
            name="Prestador",
            fields=[
                ("cd_prestador", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_prestador", models.CharField(max_length=180)),
                ("ds_especialidade", models.CharField(blank=True, max_length=120)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
            ],
            options={"db_table": "prestador", "ordering": ("nm_prestador",)},
        ),
        migrations.CreateModel(
            name="AgendaProfissional",
            fields=[
                ("cd_agenda_profissional", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_agenda", models.CharField(max_length=160)),
                ("nr_dia_semana", models.PositiveSmallIntegerField(choices=[(0, "Segunda-feira"), (1, "Terça-feira"), (2, "Quarta-feira"), (3, "Quinta-feira"), (4, "Sexta-feira"), (5, "Sábado"), (6, "Domingo")])),
                ("hr_inicio", models.TimeField()),
                ("hr_fim", models.TimeField()),
                ("nr_tempo_atendimento", models.PositiveIntegerField(default=30)),
                ("nr_intervalo", models.PositiveIntegerField(default=0)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_prestador", models.ForeignKey(db_column="cd_prestador", on_delete=django.db.models.deletion.PROTECT, to="atendimento.prestador")),
            ],
            options={"db_table": "agenda_profissional", "ordering": ("cd_prestador__nm_prestador", "nr_dia_semana", "hr_inicio")},
        ),
        migrations.AddField(
            model_name="paciente",
            name="cd_convenio",
            field=models.ForeignKey(blank=True, db_column="cd_convenio", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.convenio"),
        ),
        migrations.AddField(
            model_name="agendamento",
            name="cd_agenda_profissional",
            field=models.ForeignKey(blank=True, db_column="cd_agenda_profissional", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.agendaprofissional"),
        ),
        migrations.RunPython(seed_default_convenio, migrations.RunPython.noop),
    ]
