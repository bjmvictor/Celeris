"""Small in-process domain-event bus; replaceable by an outbox later."""
from dataclasses import dataclass, field
from typing import Any

from django.db import transaction
from django.dispatch import Signal


@dataclass(frozen=True)
class DomainEvent:
    name: str
    aggregate_id: int | str
    tenant_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)


domain_event = Signal()


def publish(event: DomainEvent) -> None:
    transaction.on_commit(lambda: domain_event.send_robust(sender=DomainEvent, event=event))
