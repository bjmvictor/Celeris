from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_global_auxiliary_tables"),
        ("atendimento", "0001_clinic_patient_agendamento"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicoalteracaopaciente",
            name="cd_motivo_alteracao",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_motivo_alteracao",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.valorauxiliarglobal",
            ),
        ),
    ]
