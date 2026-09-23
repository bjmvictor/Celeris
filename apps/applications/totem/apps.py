from apps.applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest


class TotemConfig(CelerisApplicationConfig):
    name = "apps.applications.totem"
    verbose_name = "Totem"
    application_manifest = ApplicationManifest(
        code="TOTEM", name="Totem de Senhas", version="1.0.0", dependencies=("CLASSIFICACAO",),
        urlconf="apps.applications.totem.urls", url_prefix="totem/", events=("senha.gerada",),
    )
