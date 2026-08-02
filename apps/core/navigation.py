"""Estruturas genéricas para montar a navegação carregada do banco de dados."""


def item(label, route_name=None, children=None, url=None, roles=None, access_key=None, icon=None):
    """Cria o dicionário consumido pelo template do menu lateral.

    O catálogo de módulos e telas não pertence a este arquivo. Ele é carregado
    de ``Module`` e ``ScreenDefinition`` pelo context processor.
    """
    return {
        "label": label,
        "route_name": route_name,
        "url": url,
        "children": children or [],
        "roles": roles or [],
        "access_key": access_key or route_name or url,
        "icon": icon or "",
    }
