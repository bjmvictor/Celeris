from functools import wraps

from django.core.exceptions import PermissionDenied
from django.db import models

from .models import PapelTela


def request_access_keys(request) -> set[str]:
    match = getattr(request, "resolver_match", None)
    route_name = ""
    if match:
        route_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    return {key for key in (route_name, request.path) if key}


def user_access_keys(user) -> set[str]:
    if not user.is_authenticated or not user.is_active:
        return set()
    return set(
        PapelTela.objects.filter(
            papel__grupo__user=user,
            papel__sn_ativo=True,
            papel__modulos__modulo=models.F("tela__module"),
            tela__active=True,
            tela__module__active=True,
        )
        .exclude(tela__access_key__isnull=True)
        .values_list("tela__access_key", flat=True)
        .distinct()
    )


def has_screen_access(user, access_key: str) -> bool:
    if user.is_superuser:
        return user.is_active
    if not access_key:
        return False
    return access_key in user_access_keys(user)


def ensure_screen_access(request, access_key: str):
    if not has_screen_access(request.user, access_key):
        raise PermissionDenied


def screen_access_required(access_key: str):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            ensure_screen_access(request, access_key)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
