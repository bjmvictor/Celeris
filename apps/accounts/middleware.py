from django.core.exceptions import PermissionDenied
from django.db import OperationalError, ProgrammingError

from apps.core.models import ScreenDefinition

from .access import has_screen_access, request_access_keys


class ScreenAccessMiddleware:
    public_routes = {"login", "logout", "user_companies", "core:home", "home"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            raise PermissionDenied
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        route_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
        if not request.user.is_authenticated or route_name in self.public_routes:
            return None
        try:
            matching_screens = ScreenDefinition.objects.filter(access_key__in=request_access_keys(request))
            if not matching_screens.exists():
                return None
            registered_keys = set(
                matching_screens.filter(
                    active=True,
                    module__active=True,
                ).values_list("access_key", flat=True)
            )
        except (OperationalError, ProgrammingError):
            registered_keys = set()
        if not registered_keys or not any(has_screen_access(request.user, key) for key in registered_keys):
            raise PermissionDenied
        return None
