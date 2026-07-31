from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.accounts.access import has_screen_access, resolve_request_access_key


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view(request, *args, **kwargs)
            access_key = resolve_request_access_key(request)
            if access_key:
                if has_screen_access(request.user, access_key):
                    return view(request, *args, **kwargs)
                raise PermissionDenied
            if request.user.groups.filter(
                name__in=("TI", *roles),
                papel__sn_ativo=True,
            ).exists():
                return view(request, *args, **kwargs)
            raise PermissionDenied

        wrapped._celeris_access_policy = "role"
        wrapped._celeris_roles = roles
        return wrapped

    return decorator
