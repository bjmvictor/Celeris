from django.db import OperationalError, ProgrammingError
from django.urls import reverse

from apps.accounts.models import Empresa

from .models import ScreenDefinition
from .navigation import MODULES, item


def _flatten_items(items):
    for nav_item in items:
        yield nav_item
        yield from _flatten_items(nav_item.get("children", []))


def _current_navigation(request):
    match = getattr(request, "resolver_match", None)
    if not match:
        return "Início", "Sistema"

    route_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    if route_name in {"core:home", "home"}:
        return "Início", "Sistema"
    if route_name == "password_change":
        return "Alterar senha", "Conta"

    view_title = getattr(request, "current_tab_title", None)
    if view_title:
        return view_title, getattr(request, "current_module_title", "Sistema")

    if match.namespace == "core" and match.url_name == "dynamic_screen":
        slug = match.kwargs.get("slug")
        try:
            screen = ScreenDefinition.objects.select_related("module").get(slug=slug, active=True)
            return screen.title, screen.module.title
        except (ScreenDefinition.DoesNotExist, OperationalError, ProgrammingError):
            return "Celeris", "Sistema"

    for module in MODULES:
        for nav_item in _flatten_items(module["items"]):
            if nav_item.get("route_name") == route_name:
                return nav_item["label"], module["title"]

    return "Celeris", "Sistema"


def _configured_screen_items():
    try:
        screens = (
            ScreenDefinition.objects.select_related("module")
            .filter(active=True, module__active=True)
            .order_by("module__title", "parent_label", "order", "title")
        )
    except (OperationalError, ProgrammingError):
        return {}

    configured = {}
    for screen in screens:
        configured.setdefault(screen.module.code, {})
        parent_label = screen.parent_label or ""
        configured[screen.module.code].setdefault(parent_label, [])
        if screen.slug == "pacientes-cadastro":
            configured[screen.module.code][parent_label].append(
                item(screen.title, url=reverse("atendimento:cadastro-paciente-novo"))
            )
            continue
        configured[screen.module.code][parent_label].append(
            item(screen.title, url=reverse("core:dynamic_screen", kwargs={"slug": screen.slug}))
        )
    return configured


def _merge_configured_menu():
    configured = _configured_screen_items()
    menu = []
    for module in MODULES:
        module_copy = {
            **module,
            "items": [*module["items"]],
        }
        module_screens = configured.get(module["code"], {})
        for parent_label, screen_items in module_screens.items():
            if parent_label:
                module_copy["items"].append(item(parent_label, children=screen_items))
            else:
                module_copy["items"].extend(screen_items)
        menu.append(module_copy)
    return menu


def navigation(request):
    current_tab_title, current_module_title = _current_navigation(request)
    match = getattr(request, "resolver_match", None)
    route_name = f"{match.namespace}:{match.url_name}" if match and match.namespace else getattr(match, "url_name", "")
    new_url_by_route = {
        "core:system_screens": reverse("core:system_screen_new"),
        "core:system_fields": reverse("core:system_field_new"),
        "atendimento:agendar": reverse("atendimento:cadastro-paciente-agendamento"),
        "atendimento:cadastro-paciente": reverse("atendimento:cadastro-paciente-novo"),
    }
    workflow_routes = {
        "atendimento:revisar-paciente-agendamento",
        "atendimento:cadastro-paciente-agendamento",
        "atendimento:selecionar-agenda",
        "atendimento:confirmar-agendamento",
    }
    tab_key = request.path
    close_mode = ""
    if route_name in workflow_routes:
        tab_key = reverse("atendimento:agendar")
        close_mode = "back"
    tab_root_title = getattr(request, "current_tab_root_title", None)
    if not tab_root_title and route_name in workflow_routes:
        tab_root_title = "Agendar"
    if not tab_root_title:
        tab_root_title = current_tab_title
    cd_empresa = request.session.get("cd_empresa") or 1
    try:
        current_empresa = Empresa.objects.get(cd_empresa=cd_empresa, sn_ativo=True)
    except (Empresa.DoesNotExist, OperationalError, ProgrammingError):
        current_empresa = None
    return {
        "modules_menu": _merge_configured_menu(),
        "current_tab_title": current_tab_title,
        "current_module_title": current_module_title,
        "current_can_query": getattr(request, "current_can_query", current_tab_title not in {"Início", "Alterar senha"}),
        "current_can_remove": getattr(request, "current_can_remove", False),
        "current_new_url": new_url_by_route.get(route_name, ""),
        "current_continue_url": getattr(request, "current_continue_url", ""),
        "current_empresa": current_empresa,
        "current_tab_key": tab_key,
        "current_tab_root_title": tab_root_title,
        "current_close_mode": close_mode,
        "current_start_query": getattr(request, "current_start_query", False),
    }
