from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from apps.platform.events import DomainEvent, publish

from .models import Atendimento


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


@receiver(post_save, sender=Atendimento)
def publish_atendimento_created(sender, instance, created, raw=False, **kwargs):
    """Compatibility publisher for consumers such as PEP and billing.

    No consumer is imported here.  New applications subscribe to the platform
    event bus and can later be extracted behind an outbox without changing the
    attendance workflow.
    """
    if created and not raw:
        publish(
            DomainEvent(
                name="atendimento.criado",
                aggregate_id=instance.pk,
                tenant_id=instance.cd_empresa_id,
                payload={"paciente_id": instance.cd_paciente_id},
            )
        )
