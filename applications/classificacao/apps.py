from applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest, MenuRegistration


class ClassificacaoConfig(CelerisApplicationConfig):
    name = "applications.classificacao"
    verbose_name = "Classificação de Risco"
    application_manifest = ApplicationManifest(
        code="CLASSIFICACAO", name="Classificação de Risco", version="1.0.0",
        dependencies=("ATENDIMENTO",), urlconf="applications.classificacao.urls", url_prefix="class/",
        permissions=("atendimento.view_classificacao",),
        menus=(MenuRegistration("Classificação de Risco", "atendimento:fila-classificacao", url_name="atendimento:fila-classificacao", roles=("TI", "Enfermeiro")),),
        events=("atendimento.criado",), settings=("fluxos", "escalas", "senhas"),
    )
