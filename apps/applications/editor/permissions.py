"""Authorization rules for clinical documents."""

from apps.atendimento.services.perfis_assistenciais import perfis_assistenciais_usuario


def usuario_pode_operar_documento(usuario, documento):
    if usuario.is_superuser:
        return True
    item = documento.cd_item_menu_assistencial
    if not item:
        grupos = set(usuario.groups.values_list("name", flat=True))
        return bool(grupos.intersection({
            "TI", "M\u00e9dico", "M\u00e9dico", "Enfermeiro", "Laborat\u00f3rio", "Laboratorio",
        }))
    return perfis_assistenciais_usuario(usuario, documento.cd_empresa).filter(
        pk=item.cd_perfil_assistencial_id
    ).exists()


def usuario_pode_visualizar_documento(usuario, documento):
    if usuario_pode_operar_documento(usuario, documento):
        return True
    item = documento.cd_item_menu_assistencial
    if not item:
        return False
    if item.sn_privado or item.cd_perfil_assistencial.sn_sigiloso:
        return False
    return perfis_assistenciais_usuario(usuario, documento.cd_empresa).exists()
