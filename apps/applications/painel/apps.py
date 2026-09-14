from apps.applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest


class PainelConfig(CelerisApplicationConfig):
    name = "apps.applications.painel"
    verbose_name = "Painel de Chamada"
    application_manifest = ApplicationManifest(
        code="PAINEL", name="Painel de Chamada", version="1.0.0", dependencies=("ATENDIMENTO",),
        urlconf="apps.applications.painel.urls", url_prefix="painel/", events=("senha.chamada",), settings=("paineis",),
    )
