from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.accounts.models import Empresa


@dataclass(frozen=True)
class TenantContext:
    empresa_id: int


def current_tenant(request, *, required=True) -> TenantContext | None:
    """Expose the selected identifier from the legacy ``cd_empresa`` session contract."""
    empresa_id = request.session.get("cd_empresa")
    if empresa_id is None:
        if required:
            raise PermissionDenied("Empresa não selecionada.")
        return None
    return TenantContext(empresa_id=int(empresa_id))


def empresa_atual(request) -> Empresa:
    """Resolve a empresa operacional pelo contrato legado da sessão HTTP.

    O fallback para a empresa ``1`` e a exigência de empresa ativa são parte do
    comportamento legado; a escolha nunca é lida de parâmetros GET ou POST.
    """
    cd_empresa = request.session.get("cd_empresa") or 1
    return get_object_or_404(Empresa, cd_empresa=cd_empresa, sn_ativo=True)
