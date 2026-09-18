from dataclasses import dataclass

from django.core.exceptions import PermissionDenied

from apps.accounts.models import Empresa, UsuarioEmpresa


@dataclass(frozen=True)
class TenantContext:
    empresa_id: int


class TenantContextError(Exception):
    """Raised when an HTTP request has no valid, authorized company context."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__("Contexto de empresa inválido ou ausente.")


def current_tenant(request, *, required=True) -> TenantContext | None:
    """Expose the selected identifier from the legacy ``cd_empresa`` session contract."""
    empresa_id = request.session.get("cd_empresa")
    if empresa_id is None:
        if required:
            raise PermissionDenied("Empresa não selecionada.")
        return None
    return TenantContext(empresa_id=int(empresa_id))


def empresa_atual(request) -> Empresa:
    """Resolve a empresa explicitamente selecionada e autorizada na sessão."""
    usuario = getattr(request, "user", None)
    if not usuario or not usuario.is_authenticated:
        raise TenantContextError("anonymous_user")

    cd_empresa = request.session.get("cd_empresa")
    if cd_empresa is None:
        raise TenantContextError("missing_company")

    empresa = Empresa.objects.filter(cd_empresa=cd_empresa).first()
    if empresa is None:
        raise TenantContextError("company_not_found")
    if not empresa.sn_ativo:
        raise TenantContextError("company_inactive")
    if not UsuarioEmpresa.objects.filter(usuario=usuario, empresa=empresa, sn_ativo=True).exists():
        raise TenantContextError("membership_invalid")
    return empresa
