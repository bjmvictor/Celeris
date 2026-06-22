from django.db import migrations


GROUPS = {
    "Recepção": [("paciente", ["view", "add", "change"]), ("agendamento", ["view", "add", "change"]), ("atendimento", ["view", "add", "change"])],
    "Triagem": [("paciente", ["view"]), ("atendimento", ["view", "change"]), ("preatendimento", ["view", "add", "change"])],
    "Médico/Profissional": [("paciente", ["view"]), ("atendimento", ["view", "change"]), ("preatendimento", ["view"]), ("solicitacaoexame", ["view", "add", "change"]), ("resultadoexame", ["view"])],
    "Laboratório": [("paciente", ["view"]), ("atendimento", ["view"]), ("solicitacaoexame", ["view", "change"]), ("resultadoexame", ["view", "add", "change"])],
    "Administração": [],
}


def seed(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for name, rules in GROUPS.items():
        group, _ = Group.objects.get_or_create(name=name)
        if name == "Administração":
            group.permissions.set(Permission.objects.all())
            continue
        permissions = []
        for model, actions in rules:
            permissions.extend(
                Permission.objects.filter(
                    content_type__app_label="atendimento",
                    content_type__model=model,
                    codename__in=[f"{action}_{model}" for action in actions],
                )
            )
        group.permissions.set(permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0008_agendamento_ds_plano_agendamento_sn_encaixe_and_more"),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
