from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.accounts.access import has_screen_access, request_access_keys


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view(request, *args, **kwargs)
            if any(has_screen_access(request.user, key) for key in request_access_keys(request)):
                return view(request, *args, **kwargs)
            if request.user.groups.filter(
                name__in=("TI", *roles),
                papel__sn_ativo=True,
            ).exists():
                return view(request, *args, **kwargs)
            raise PermissionDenied

        return wrapped

    return decorator
