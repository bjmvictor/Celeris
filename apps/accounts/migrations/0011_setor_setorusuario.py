from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_setores(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Setor = apps.get_model("accounts", "Setor")
    nomes = [
        ("Recepção", "EMPRESA"),
        ("Triagem", "ATENDIMENTO"),
        ("Consultório Clínico", "ATENDIMENTO"),
        ("Medicação", "ATENDIMENTO"),
        ("Observação", "ATENDIMENTO"),
        ("Coleta", "ATENDIMENTO"),
    ]
    for empresa in Empresa.objects.all():
        for nome, tipo in nomes:
            Setor.objects.get_or_create(
                cd_empresa=empresa,
                nm_setor=nome,
                tp_setor=tipo,
                defaults={"sn_ativo": True},
            )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0010_sync_ti_dynamic_access"),
    ]

    operations = [
        migrations.CreateModel(
            name="Setor",
            fields=[
                ("cd_setor", models.BigAutoField(primary_key=True, serialize=False, verbose_name="codigo")),
                ("nm_setor", models.CharField(max_length=120, verbose_name="nome")),
                ("tp_setor", models.CharField(choices=[("EMPRESA", "Setor da empresa"), ("ATENDIMENTO", "Setor de atendimento")], max_length=20, verbose_name="tipo")),
                ("ds_observacao", models.CharField(blank=True, max_length=240, verbose_name="observacao")),
                ("sn_ativo", models.BooleanField(default=True, verbose_name="ativo")),
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name="data de criacao")),
                ("dh_atualizacao", models.DateTimeField(auto_now=True, verbose_name="data de alteracao")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, related_name="setores", to="accounts.empresa")),
            ],
            options={
                "db_table": "setor",
                "ordering": ("cd_empresa", "tp_setor", "nm_setor"),
                "unique_together": {("cd_empresa", "tp_setor", "nm_setor")},
            },
        ),
        migrations.CreateModel(
            name="SetorUsuario",
            fields=[
                ("cd_setor_usuario", models.BigAutoField(primary_key=True, serialize=False, verbose_name="codigo")),
                ("cd_setor", models.ForeignKey(db_column="cd_setor", on_delete=django.db.models.deletion.CASCADE, to="accounts.setor")),
                ("cd_usuario", models.ForeignKey(db_column="cd_usuario", on_delete=django.db.models.deletion.CASCADE, to="accounts.user")),
            ],
            options={
                "db_table": "setor_usuario",
                "unique_together": {("cd_setor", "cd_usuario")},
            },
        ),
        migrations.AddField(
            model_name="setor",
            name="usuarios",
            field=models.ManyToManyField(blank=True, related_name="setores", through="accounts.SetorUsuario", to="accounts.user"),
        ),
        migrations.RunPython(seed_setores, migrations.RunPython.noop),
    ]
