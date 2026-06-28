from django.db import OperationalError, ProgrammingError
from django.urls import reverse
from urllib.parse import urlencode

from apps.accounts.models import Empresa
from apps.accounts.access import user_access_keys

from .models import Module, ScreenDefinition
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


def _short_tab_title(title):
    if not title:
        return title
    short_title = title.split(">")[-1].strip() or title
    return short_title.title() if short_title.isupper() else short_title


def _short_user_name(user):
    if not getattr(user, "is_authenticated", False):
        return ""
    name = getattr(user, "display_name", lambda: "")() or user.get_username()
    parts = [part for part in name.split() if part]
    return " ".join(parts[:2]).upper() if parts else user.get_username().upper()


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
        if screen.slug == "cadastros-profissionais" or screen.slug.startswith("acesso-"):
            continue
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
    merged = []
    known_codes = set()
    for module in MODULES:
        known_codes.add(module["code"])
        items = [*module["items"]]
        for parent_label, screens in configured.get(module["code"], {}).items():
            if parent_label:
                items.append(item(parent_label, children=screens))
            else:
                items.extend(screens)
        merged.append({**module, "items": items})
    try:
        modules = Module.objects.filter(active=True).order_by("title")
    except (OperationalError, ProgrammingError):
        modules = []
    for module in modules:
        if module.code in known_codes or module.code not in configured:
            continue
        items = []
        for parent_label, screens in configured[module.code].items():
            if parent_label:
                items.append(item(parent_label, children=screens))
            else:
                items.extend(screens)
        merged.append({"code": module.code, "title": module.title, "icon": "grid", "items": items})
    return merged


def _filter_menu_for_user(menu, user):
    allowed_keys = user_access_keys(user) if user.is_authenticated and not user.is_superuser else set()

    def filter_items(items):
        visible = []
        for index, nav_item in enumerate(items):
            children = filter_items(nav_item.get("children", []))
            if nav_item.get("children"):
                if not children:
                    continue
            elif not user.is_superuser and nav_item.get("access_key") not in allowed_keys:
                continue
            visible.append((index, {**nav_item, "children": children}))
        return [nav_item for _, nav_item in sorted(visible, key=lambda item: (bool(item[1].get("children")), item[0]))]

    return [
        {**module, "items": filter_items(module["items"])}
        for module in menu
        if filter_items(module["items"])
    ]


def navigation(request):
    current_tab_title, current_module_title = _current_navigation(request)
    match = getattr(request, "resolver_match", None)
    route_name = f"{match.namespace}:{match.url_name}" if match and match.namespace else getattr(match, "url_name", "")
    new_url_by_route = {
        "core:system_screens": reverse("core:system_screen_new"),
        "core:system_fields": reverse("core:system_field_new"),
        "atendimento:agendar": reverse("atendimento:cadastro-paciente-agendamento"),
        "atendimento:cadastro-paciente": reverse("atendimento:cadastro-paciente-novo"),
        "atendimento:profissionais": reverse("atendimento:cadastro-profissional-novo"),
        "atendimento:cadastro-profissional": reverse("atendimento:cadastro-profissional-novo"),
        "atendimento:cadastro-profissional-novo": reverse("atendimento:cadastro-profissional-novo"),
        "usuarios": reverse("usuario_novo"),
        "perfis": reverse("perfil_novo"),
    }
    workflow_routes = {
        "atendimento:cadastro-paciente-agendamento",
        "atendimento:revisar-paciente-agendamento",
        "atendimento:selecionar-agenda",
        "atendimento:confirmar-agendamento",
    }
    tab_key = request.path
    close_mode = ""
    unified_tab_routes = {
        "atendimento:cadastro-paciente": reverse("atendimento:cadastro-paciente-novo"),
        "atendimento:cadastro-paciente-novo": reverse("atendimento:cadastro-paciente-novo"),
        "atendimento:cadastro-profissional": reverse("atendimento:cadastro-profissional-novo"),
        "atendimento:cadastro-profissional-novo": reverse("atendimento:cadastro-profissional-novo"),
    }
    if route_name in unified_tab_routes:
        tab_key = unified_tab_routes[route_name]
    if route_name in workflow_routes:
        tab_key = reverse("atendimento:agendar")
        close_mode = "back"
    return_url = getattr(request, "current_return_url", "")
    if return_url:
        close_mode = "back"
    tab_root_title = getattr(request, "current_tab_root_title", None)
    if not tab_root_title and route_name in workflow_routes:
        tab_root_title = "Agendar"
    if not tab_root_title:
        tab_root_title = _short_tab_title(current_tab_title)
    cd_empresa = request.session.get("cd_empresa") or 1
    try:
        current_empresa = Empresa.objects.get(cd_empresa=cd_empresa, sn_ativo=True)
    except (Empresa.DoesNotExist, OperationalError, ProgrammingError):
        current_empresa = None
    current_new_url = new_url_by_route.get(route_name, "")
    if route_name in {"perfis", "atendimento:profissionais"} and current_new_url:
        current_new_url = f"{current_new_url}?{urlencode({'return_to': request.get_full_path()})}"
    return {
        "modules_menu": _filter_menu_for_user(_merge_configured_menu(), request.user),
        "current_tab_title": current_tab_title,
        "current_module_title": current_module_title,
        "current_can_query": getattr(request, "current_can_query", current_tab_title not in {"Início", "Alterar senha"}),
        "current_can_remove": getattr(request, "current_can_remove", False),
        "current_new_url": current_new_url,
        "current_continue_url": getattr(request, "current_continue_url", ""),
        "current_empresa": current_empresa,
        "current_tab_key": tab_key,
        "current_tab_root_title": tab_root_title,
        "current_close_mode": close_mode,
        "current_start_query": getattr(request, "current_start_query", False),
        "current_previous_url": getattr(request, "current_previous_url", ""),
        "current_next_url": getattr(request, "current_next_url", ""),
        "current_first_url": getattr(request, "current_first_url", ""),
        "current_last_url": getattr(request, "current_last_url", ""),
        "current_record_status": getattr(request, "current_record_status", ""),
        "current_toggle_active_url": getattr(request, "current_toggle_active_url", ""),
        "current_toggle_active_label": getattr(request, "current_toggle_active_label", ""),
        "current_password_url": getattr(request, "current_password_url", ""),
        "current_return_url": return_url,
        "current_close_url": return_url or (tab_key if close_mode == "back" else ""),
        "current_overlay_mode": request.GET.get("overlay") == "1",
        "current_user_short_name": _short_user_name(request.user),
    }
