from django.db import migrations


def cleanup(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(
        name__in=["Recepção", "Triagem", "Médico/Profissional", "Laboratório", "Administração"]
    ).delete()
    for name in ["TI", "Recepcionista", "Enfermeiro", "Médico"]:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0011_seed_homologacao"),
    ]

    operations = [migrations.RunPython(cleanup, migrations.RunPython.noop)]
