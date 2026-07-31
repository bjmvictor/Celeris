from django.db import OperationalError, ProgrammingError
from django.urls import NoReverseMatch, reverse
from urllib.parse import urlencode
import unicodedata

from apps.accounts.models import Empresa
from apps.accounts.access import user_access_keys

from .models import Module, ScreenDefinition
from .navigation import MODULES, item


HIDDEN_UNIMPLEMENTED_MODULE_CODES = {"COMPRAS", "FINANCEIRO", "RH"}


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

    static_access_keys = {
        nav_item.get("access_key")
        for module in MODULES
        for nav_item in _flatten_items(module["items"])
        if not nav_item.get("children")
    }
    configured = {}
    for screen in screens:
        access_key = screen.access_key or ""
        if screen.module.code in HIDDEN_UNIMPLEMENTED_MODULE_CODES:
            continue
        if (
            screen.module.code == "ESTOQUE"
            or screen.module.code == "ALMOXARIFADO"
            or screen.access_key in {"estoque-produtos", "estoque-entradas", "estoque-saidas", "estoque-inventario"}
            or screen.slug.startswith("estoque-")
            or screen.slug.startswith("almoxarifado-")
            or screen.slug.startswith("produtos-")
            or screen.slug.startswith("inventario")
            or screen.slug.startswith("entradas")
            or screen.slug.startswith("saidas")
            or screen.slug.startswith("movimentacao")
            or screen.slug.startswith("movimentacoes")
            or screen.slug.startswith("produto")
            or screen.slug.startswith("produtos")
            or screen.slug.startswith("solicitacao-produto")
            or screen.slug.startswith("solicitacoes-produto")
            or screen.slug.startswith("estoques")
            or screen.slug.startswith("unidades")
            or screen.slug.startswith("cotas")
            or screen.slug.startswith("saldos")
            or screen.slug.startswith("classificacao-produto")
            or screen.slug.startswith("classificacoes-produto")
            or screen.slug.startswith("motivos-baixa")
            or screen.slug.startswith("motivos-devolucao")
            or screen.slug.startswith("programacao-reposicao")
            or screen.slug.startswith("motivos-cancelamento")
            or screen.slug.startswith("carater-produto")
            or screen.slug.startswith("classes-produto")
            or screen.slug.startswith("recebimento-cadastro-produto")
            or screen.slug.startswith("alteracao-exclusao-produto")
            or screen.slug.startswith("fracionamento")
            or screen.slug.startswith("acerto-estoque")
            or screen.slug == "cadastros-profissionais"
            or screen.slug.startswith("acesso-")
            or screen.slug.startswith("totem-")
            or access_key.startswith("acesso-totem-")
            or screen.slug in {"ti-alteracao-senha-usuario", "ti-cadastro-copia-usuario"}
            or access_key in static_access_keys
        ):
            continue
        configured.setdefault(screen.module.code, {})
        parent_label = screen.parent_label or ""
        configured[screen.module.code].setdefault(parent_label, [])
        if screen.slug == "pacientes-cadastro":
            configured[screen.module.code][parent_label].append(
                item(
                    screen.title,
                    url=reverse("atendimento:cadastro-paciente-novo"),
                    access_key=screen.access_key,
                )
            )
            continue
        configured[screen.module.code][parent_label].append(
            item(
                screen.title,
                url=reverse("core:dynamic_screen", kwargs={"slug": screen.slug}),
                access_key=screen.access_key,
            )
        )
    return configured


def _organize_runtime_modules(modules):
    modules = list(modules)

    def pop_module(code):
        for index, module in enumerate(modules):
            if module["code"] == code:
                return modules.pop(index)
        return None

    def append_group(target_code, label, source):
        if not source or not source.get("items"):
            return
        target = next((module for module in modules if module["code"] == target_code), None)
        if target:
            target["items"].append(item(label, children=source["items"]))

    pacientes = pop_module("PACIENTES")
    indicadores = pop_module("BI")
    fiscal = pop_module("FISCAL")
    relacionamento = pop_module("RELACIONAMENTO")
    append_group("ATENDIMENTO", "Pacientes", pacientes)
    append_group("ATENDIMENTO", "Indicadores", indicadores)
    append_group("FINANCEIRO", "Fiscal", fiscal)

    if relacionamento and relacionamento.get("items"):
        global_module = next((module for module in modules if module["code"] == "GLOBAL"), None)
        empresa_group = next(
            (nav_item for nav_item in global_module["items"] if nav_item["label"] == "Empresa"),
            None,
        ) if global_module else None
        if empresa_group:
            empresa_group["children"].append(item("Relacionamentos", children=relacionamento["items"]))

    return modules


def _merge_configured_menu():
    database_menu = _database_navigation_menu()
    if database_menu:
        return database_menu
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
        modules = (
            Module.objects.filter(active=True)
            .exclude(code__in=HIDDEN_UNIMPLEMENTED_MODULE_CODES)
            .order_by("title")
        )
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
    return _organize_runtime_modules(merged)


def _database_navigation_menu():
    try:
        if not ScreenDefinition.objects.filter(
            active=True,
            screen_type=ScreenDefinition.TYPE_GROUP,
        ).exists():
            return []
        modules = list(
            Module.objects.filter(active=True)
            .exclude(code__in=HIDDEN_UNIMPLEMENTED_MODULE_CODES)
            .order_by("order", "title")
        )
        screens = list(
            ScreenDefinition.objects.filter(active=True, module__in=modules)
            .select_related("module", "parent")
            .order_by("module__order", "module__title", "order", "title")
        )
    except (OperationalError, ProgrammingError):
        return []

    children_by_parent = {}
    roots_by_module = {}
    legacy_by_module = {}
    for screen in screens:
        if screen.parent_id:
            children_by_parent.setdefault(screen.parent_id, []).append(screen)
        elif screen.parent_label:
            legacy_by_module.setdefault(screen.module_id, {}).setdefault(screen.parent_label, []).append(screen)
        else:
            roots_by_module.setdefault(screen.module_id, []).append(screen)

    def screen_destination(screen):
        if screen.navigation_url:
            return "", screen.navigation_url
        access_key = screen.access_key or ""
        if access_key.startswith("/"):
            return "", access_key
        if access_key:
            try:
                reverse(access_key)
                return access_key, ""
            except NoReverseMatch:
                pass
        if screen.screen_type != ScreenDefinition.TYPE_GROUP:
            return "", reverse("core:dynamic_screen", kwargs={"slug": screen.slug})
        return "", ""

    def build_item(screen):
        children = [build_item(child) for child in children_by_parent.get(screen.pk, [])]
        route_name, url = screen_destination(screen)
        navigation_item = item(
            screen.title,
            route_name=route_name or None,
            url=url or None,
            children=children,
            roles=screen.roles or [],
            access_key=screen.access_key,
            icon=screen.icon,
        )
        navigation_item["is_group"] = screen.screen_type == ScreenDefinition.TYPE_GROUP
        return navigation_item

    def label_key(value):
        normalized = unicodedata.normalize("NFKD", value or "")
        return "".join(
            character for character in normalized if not unicodedata.combining(character)
        ).casefold().strip()

    def merge_items(menu_items):
        merged = []
        items_by_label = {}
        for menu_item in menu_items:
            normalized_item = {
                **menu_item,
                "children": merge_items(menu_item.get("children", [])),
            }
            key = label_key(normalized_item.get("label"))
            existing = items_by_label.get(key)
            if existing is None:
                items_by_label[key] = normalized_item
                merged.append(normalized_item)
                continue
            existing["children"] = merge_items(
                [*existing.get("children", []), *normalized_item.get("children", [])]
            )
            for attribute in ("route_name", "url", "access_key", "icon"):
                if not existing.get(attribute) and normalized_item.get(attribute):
                    existing[attribute] = normalized_item[attribute]
        return merged

    result = []
    for module in modules:
        module_items = [build_item(screen) for screen in roots_by_module.get(module.pk, [])]
        for label, legacy_screens in legacy_by_module.get(module.pk, {}).items():
            module_items.append(item(label, children=[build_item(screen) for screen in legacy_screens]))
        module_items = merge_items(module_items)
        if module_items:
            result.append(
                {
                    "code": module.code,
                    "title": module.title,
                    "icon": module.icon or "grid",
                    "items": module_items,
                }
            )
    return result


def _filter_menu_for_user(menu, user):
    allowed_keys = user_access_keys(user) if user.is_authenticated and not user.is_superuser else set()

    def filter_items(items):
        visible = []
        for index, nav_item in enumerate(items):
            children = filter_items(nav_item.get("children", []))
            if nav_item.get("is_group") and not children:
                continue
            if nav_item.get("children"):
                if not children:
                    continue
            elif not user.is_superuser and nav_item.get("access_key") not in allowed_keys:
                continue
            visible.append((index, {**nav_item, "children": children}))
        return [nav_item for _, nav_item in visible]

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
        "atendimento:escalas": reverse("atendimento:escalas"),
        "atendimento:cadastro-escala": reverse("atendimento:escalas"),
        "atendimento:paineis-chamada": reverse("atendimento:paineis-chamada"),
        "atendimento:cadastro-painel-chamada": reverse("atendimento:paineis-chamada"),
        "atendimento:perfis-assistenciais": reverse("atendimento:perfis-assistenciais"),
        "atendimento:configurar-senhas": reverse("atendimento:configurar-senhas"),
        "atendimento:editar-configuracao-senha": reverse("atendimento:configurar-senhas"),
        "usuarios": reverse("usuario_novo"),
        "perfis": reverse("perfil_novo"),
    }
    workflow_routes = {
        "atendimento:cadastro-paciente-agendamento",
        "atendimento:revisar-paciente-agendamento",
        "atendimento:selecionar-agenda",
        "atendimento:confirmar-horario-agenda",
        "atendimento:confirmar-agendamento",
    }
    tab_key = request.path
    close_mode = ""
    unified_tab_routes = {
        "atendimento:cadastro-paciente": reverse("atendimento:cadastro-paciente-novo"),
        "atendimento:cadastro-paciente-novo": reverse("atendimento:cadastro-paciente-novo"),
        "atendimento:cadastro-profissional": reverse("atendimento:cadastro-profissional-novo"),
        "atendimento:cadastro-profissional-novo": reverse("atendimento:cadastro-profissional-novo"),
        "atendimento:escalas": reverse("atendimento:escalas"),
        "atendimento:cadastro-escala": reverse("atendimento:escalas"),
        "atendimento:paineis-chamada": reverse("atendimento:paineis-chamada"),
        "atendimento:cadastro-painel-chamada": reverse("atendimento:paineis-chamada"),
        "atendimento:editar-configuracao-senha": reverse("atendimento:configurar-senhas"),
        "atendimento:pep-prontuario-paciente": reverse("atendimento:pep"),
        "atendimento:novo-atendimento-agendado": reverse("atendimento:agendamentos-operacionais"),
        "atendimento:cadastro-atendimento": reverse("atendimento:agendamentos-operacionais"),
    }
    if route_name in unified_tab_routes:
        tab_key = unified_tab_routes[route_name]
    if route_name in workflow_routes:
        tab_key = reverse("atendimento:agendar")
        close_mode = "back"
    if route_name == "atendimento:revisar-paciente-agendamento" and request.GET.get("recepcionar"):
        tab_key = reverse("atendimento:agendamentos-operacionais")
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
    current_new_url = getattr(request, "current_new_url", new_url_by_route.get(route_name, ""))
    if route_name in {"perfis", "atendimento:profissionais"} and current_new_url:
        separator = "&" if "?" in current_new_url else "?"
        current_new_url = f"{current_new_url}{separator}{urlencode({'return_to': request.get_full_path()})}"
    return {
        "modules_menu": _filter_menu_for_user(_merge_configured_menu(), request.user),
        "current_tab_title": current_tab_title,
        "current_module_title": current_module_title,
        "current_can_query": getattr(request, "current_can_query", current_tab_title not in {"Início", "Alterar senha"}),
        "current_can_save": getattr(request, "current_can_save", True),
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
        "current_reload_url": getattr(request, "current_reload_url", ""),
        "current_print_url": getattr(request, "current_print_url", ""),
        "current_return_url": return_url,
        "current_close_url": return_url or (tab_key if close_mode == "back" else ""),
        "current_overlay_mode": request.GET.get("overlay") == "1",
        "current_user_short_name": _short_user_name(request.user),
        "can_view_audit": bool(
            request.user.is_authenticated
            and getattr(request.user, "pode_visualizar_auditoria", False)
        ),
    }
