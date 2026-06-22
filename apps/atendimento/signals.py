from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


GROUPS = {
    "Recepcionista": [("paciente", ["view", "add", "change"]), ("agendamento", ["view", "add", "change"]), ("atendimento", ["view", "add", "change"])],
    "Enfermeiro": [("paciente", ["view"]), ("atendimento", ["view", "change"]), ("preatendimento", ["view", "add", "change"])],
    "Médico": [
        ("paciente", ["view"]), ("atendimento", ["view", "change"]), ("preatendimento", ["view"]),
        ("solicitacaoexame", ["view", "add", "change"]), ("resultadoexame", ["view"]),
        ("prescricao", ["view", "add", "change"]), ("evolucaoatendimento", ["view", "add", "change"]),
    ],
}


@receiver(post_migrate)
def sync_clinical_profiles(**kwargs):
    for name, rules in GROUPS.items():
        group, _ = Group.objects.get_or_create(name=name)
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
    ti_group, _ = Group.objects.get_or_create(name="TI")
    ti_group.permissions.set(Permission.objects.all())
