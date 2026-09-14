from applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest


class PainelConfig(CelerisApplicationConfig):
    name = "applications.painel"
    verbose_name = "Painel de Chamada"
    application_manifest = ApplicationManifest(
        code="PAINEL", name="Painel de Chamada", version="1.0.0", dependencies=("ATENDIMENTO",),
        urlconf="applications.painel.urls", url_prefix="painel/", events=("senha.chamada",), settings=("paineis",),
    )
