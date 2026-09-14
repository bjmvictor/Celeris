from dataclasses import dataclass
from django.core.exceptions import PermissionDenied


@dataclass(frozen=True)
class TenantContext:
    empresa_id: int


def current_tenant(request, *, required=True) -> TenantContext | None:
    """The sole HTTP boundary for the legacy ``cd_empresa`` session contract."""
    empresa_id = request.session.get("cd_empresa")
    if empresa_id is None:
        if required:
            raise PermissionDenied("Empresa não selecionada.")
        return None
    return TenantContext(empresa_id=int(empresa_id))
