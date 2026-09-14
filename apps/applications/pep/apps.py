from apps.applications.base import CelerisApplicationConfig
from apps.platform.registry import ApplicationManifest, MenuRegistration


class PepConfig(CelerisApplicationConfig):
    name = "apps.applications.pep"
    verbose_name = "PEP"
    application_manifest = ApplicationManifest(
        code="PEP", name="Prontuário Eletrônico do Paciente", version="1.0.0",
        dependencies=("ATENDIMENTO", "DOCUMENTS", "ESTOQUE"),
        urlconf="apps.applications.pep.urls", url_prefix="PEP/",
        permissions=("atendimento.view_documentoclinico", "atendimento.change_documentoclinico"),
        menus=(MenuRegistration("PEP", "atendimento:pep", url_name="atendimento:pep", roles=("TI", "Médico", "Enfermeiro")),),
        events=("atendimento.criado",), reports=("prontuario",), settings=("perfis_assistenciais",),
    )
