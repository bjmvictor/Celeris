import inspect

from django.core.exceptions import PermissionDenied
from django.db import OperationalError, ProgrammingError
from django.http import JsonResponse

from .access import resolve_request_access, user_access_keys


def _is_login_required_view(view_func) -> bool:
    """Recognize Django 5.0's login_required wrapper without trusting any wrapper."""
    if hasattr(view_func, "login_url"):
        return True
    try:
        closure = inspect.getclosurevars(view_func).nonlocals
    except (TypeError, ValueError):
        return False
    test_func = closure.get("test_func")
    return bool(
        callable(test_func)
        and "login_required.<locals>.<lambda>" in getattr(test_func, "__qualname__", "")
        and callable(closure.get("view_func"))
    )


class ScreenAccessMiddleware:
    public_routes = {
        "login",
        "logout",
        "session_status",
        "user_companies",
        "core:home",
        "home",
        "core:health",
        "atendimento:painel-chamada-publico",
        "painel_chamada_standalone",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            raise PermissionDenied
        response = self.get_response(request)
        accepts_json = "application/json" in request.headers.get("Accept", "")
        is_fetch = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if not request.user.is_authenticated and response.status_code in {301, 302} and (accepts_json or is_fetch):
            return JsonResponse({"authenticated": False, "login_url": "/accounts/login/"}, status=401)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        route_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
        if not request.user.is_authenticated or route_name in self.public_routes:
            return None
        try:
            registered_key, registered_route = resolve_request_access(request)
        except (OperationalError, ProgrammingError) as error:
            raise PermissionDenied("Não foi possível validar a permissão desta rota.") from error
        if registered_key:
            if request.user.is_superuser:
                request._celeris_access_keys = set()
            else:
                request._celeris_access_keys = user_access_keys(request.user)
            if not request.user.is_superuser and registered_key not in request._celeris_access_keys:
                raise PermissionDenied
            return None
        if registered_route:
            raise PermissionDenied
        access_policy = getattr(view_func, "_celeris_access_policy", "")
        explicitly_authenticated = _is_login_required_view(view_func)
        if access_policy or explicitly_authenticated:
            return None
        if route_name:
            raise PermissionDenied
        return None
