from apps.applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest, MenuRegistration


class EditorConfig(CelerisApplicationConfig):
    name = "apps.applications.editor"
    verbose_name = "Editor de Documentos"
    application_manifest = ApplicationManifest(
        code="EDITOR", name="Editor de Documentos", version="1.0.0", dependencies=("DOCUMENTS",),
        permissions=("atendimento.change_modelodocumento",),
        menus=(MenuRegistration("Editor de documentos", "atendimento:modelos-documento", url_name="atendimento:modelos-documento", roles=("TI",)),),
        settings=("modelos_documento",),
    )
