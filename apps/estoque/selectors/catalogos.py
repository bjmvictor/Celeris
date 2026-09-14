from django.db.models import Q


def filtrar_catalogo(queryset, termo: str, campos_busca: tuple[str, ...]):
    termo = (termo or "").strip().replace("%", "")
    if not termo:
        return queryset
    filtro = Q()
    for campo in campos_busca:
        filtro |= Q(**{f"{campo}__icontains": termo})
    if termo.isdigit():
        filtro |= Q(**{queryset.model._meta.pk.name: int(termo)})
    return queryset.filter(filtro)

