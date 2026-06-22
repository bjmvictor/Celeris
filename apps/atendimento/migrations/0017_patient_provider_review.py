from django.db import migrations, models
import django.db.models.deletion


def link_existing_ceps(apps, schema_editor):
    Cep = apps.get_model("core", "Cep")
    Paciente = apps.get_model("atendimento", "Paciente")
    Prestador = apps.get_model("atendimento", "Prestador")

    def find_cep(value):
        digits = "".join(character for character in value or "" if character.isdigit())[:8]
        return Cep.objects.filter(nr_cep=digits).first() if digits else None

    for patient in Paciente.objects.exclude(nr_cep="").iterator():
        cep = find_cep(patient.nr_cep)
        if cep:
            patient.cd_cep_id = cep.pk
            patient.save(update_fields=["cd_cep"])
    for provider in Prestador.objects.iterator():
        residential = find_cep(provider.nr_cep)
        commercial = find_cep(provider.nr_cep_comercial)
        update_fields = []
        if residential:
            provider.cd_cep_id = residential.pk
            update_fields.append("cd_cep")
        if commercial:
            provider.cd_cep_comercial_id = commercial.pk
            update_fields.append("cd_cep_comercial")
        if update_fields:
            provider.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0018_cep"),
        ("atendimento", "0016_prestador_nm_guerra"),
    ]

    operations = [
        migrations.AddField(
            model_name="paciente",
            name="cd_cep",
            field=models.ForeignKey(blank=True, db_column="cd_cep", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pacientes", to="core.cep"),
        ),
        migrations.AddField(
            model_name="paciente",
            name="ds_orgao_emissor",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="paciente",
            name="dt_expedicao",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="paciente",
            name="nr_celular_2",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="paciente",
            name="tp_logradouro",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="prestador",
            name="cd_cep",
            field=models.ForeignKey(blank=True, db_column="cd_cep", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="prestadores_residenciais", to="core.cep"),
        ),
        migrations.AddField(
            model_name="prestador",
            name="cd_cep_comercial",
            field=models.ForeignKey(blank=True, db_column="cd_cep_comercial", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="prestadores_comerciais", to="core.cep"),
        ),
        migrations.AddField(
            model_name="prestador",
            name="dt_nascimento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(link_existing_ceps, migrations.RunPython.noop),
    ]
