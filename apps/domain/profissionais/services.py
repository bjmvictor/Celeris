from django.apps import apps


def active_professionals(empresa):
    """Transitional port for the existing Prestador table.

    The storage model remains ``atendimento.Prestador`` until a schema-moving
    migration is explicitly scheduled; callers no longer import it directly.
    """
    prestador = apps.get_model("atendimento", "Prestador")
    return prestador.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_prestador")
