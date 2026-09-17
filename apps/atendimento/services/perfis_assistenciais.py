"""Public resolution of the clinical profiles available to a user."""

from apps.atendimento.models import PerfilAssistencial


def perfis_assistenciais_usuario(usuario, empresa):
    """Preserve the legacy provider-type and compatibility-profile resolution."""
    prestador = getattr(usuario, "cd_prestador", None)
    tipos = prestador.tipos_prestador_ativos if prestador else []
    if not tipos:
        return PerfilAssistencial.objects.none()
    base_normalizados = PerfilAssistencial.objects.filter(
        cd_empresa=empresa,
        tipos_vinculados__sn_ativo=True,
        tipos_vinculados__cd_tipo_prestador__in=tipos,
    )
    normalizados = base_normalizados.filter(sn_ativo=True).distinct()
    if normalizados.exists():
        return normalizados
    normalizados_inativos = base_normalizados.distinct()
    if normalizados_inativos.exists():
        return normalizados_inativos
    ids_legados = [
        perfil.pk
        for perfil in PerfilAssistencial.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if set(perfil.tipos_prestador or []).intersection(tipos)
    ]
    return PerfilAssistencial.objects.filter(pk__in=ids_legados)
