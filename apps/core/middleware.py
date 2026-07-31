from django.utils import timezone


class SessionActivityMiddleware:
    ignored_prefixes = ("/static/", "/media/", "/favicon.ico")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return response
        if request.path.startswith(self.ignored_prefixes):
            return response
        if response.status_code >= 500:
            return response

        now = timezone.now().isoformat()
        if not request.session.get("inicio_sessao_em"):
            request.session["inicio_sessao_em"] = now
        request.session["ultimo_acesso_em"] = now
        request.session["ultimo_sistema"] = "Celeris PEP" if request.path.startswith("/PEP") else "Celeris"
        request.session["ultima_rota"] = request.get_full_path()
        request.session["ultima_tela"] = (
            getattr(request, "current_tab_title", "")
            or getattr(getattr(request, "resolver_match", None), "view_name", "")
            or request.path
        )
        empresa = getattr(request, "current_empresa", None)
        if empresa:
            request.session["empresa_nome"] = empresa.nm_empresa
        return response


class SecurityHeadersMiddleware:
    """Apply a conservative CSP that still supports the existing inline UI."""

    policy = "; ".join(
        (
            "default-src 'self'",
            "base-uri 'self'",
            "object-src 'none'",
            "frame-ancestors 'self'",
            "frame-src 'self' blob:",
            "img-src 'self' data: blob:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "script-src 'self' 'unsafe-inline'",
        )
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self.policy)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
