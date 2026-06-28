from urllib.parse import urlencode

from django.core.paginator import Paginator


def paginate_table(request, queryset, allowed_ordering, default_ordering, *, load_on_open=False):
    if request.method == "GET" and not request.GET and not load_on_open:
        request.current_record_status = "Nenhum item carregado"
        return queryset.none()

    ordering = request.GET.get("ordem", default_ordering)
    descending = ordering.startswith("-")
    field_name = ordering[1:] if descending else ordering
    if field_name not in allowed_ordering:
        field_name = default_ordering
        descending = False
    ordering = f"-{field_name}" if descending else field_name

    paginator = Paginator(queryset.order_by(ordering), 20)
    page = paginator.get_page(request.GET.get("pagina", 1))
    request.current_record_status = (
        f"{paginator.count} encontrado(s) · {len(page.object_list)} exibido(s) · "
        f"Página {page.number} de {paginator.num_pages}"
    )

    def page_url(number):
        params = request.GET.copy()
        params["pagina"] = number
        return f"{request.path}?{urlencode(params, doseq=True)}"

    if page.has_previous():
        request.current_first_url = page_url(1)
        request.current_previous_url = page_url(page.previous_page_number())
    if page.has_next():
        request.current_next_url = page_url(page.next_page_number())
        request.current_last_url = page_url(paginator.num_pages)
    return page
