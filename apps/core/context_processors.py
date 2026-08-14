from django.db import OperationalError, ProgrammingError, connection
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode
import unicodedata

from apps.accounts.models import Empresa
from apps.accounts.access import request_access_key_candidates, user_access_keys

from .models import CertificadoDigitalEmpresa, IconeSistema, Module, ScreenDefinition
from .navigation import item
from .navigation_cache import (
    NAVIGATION_CACHE_KEY,
    NAVIGATION_CACHE_TIMEOUT,
    SYSTEM_ICONS_CACHE_KEY,
)


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

    try:
        candidates = request_access_key_candidates(request)
        screen = (
            ScreenDefinition.objects.select_related("module")
            .filter(active=True, module__active=True)
            .filter(Q(access_key__in=candidates) | Q(navigation_url=request.path))
            .first()
        )
        if screen:
            return screen.title, screen.module.title
    except (OperationalError, ProgrammingError):
        pass

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


def _merge_configured_menu():
    return _database_navigation_menu()


def _database_navigation_menu():
    use_cache = not connection.in_atomic_block
    if use_cache:
        cached_menu = cache.get(NAVIGATION_CACHE_KEY)
        if cached_menu is not None:
            return cached_menu
    try:
        modules = list(
            Module.objects.filter(active=True)
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
        children = [
            child_item
            for child in children_by_parent.get(screen.pk, [])
            if (child_item := build_item(child)) is not None
        ]
        if screen.screen_type == ScreenDefinition.TYPE_GROUP and not children:
            return None
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
        module_items = [
            navigation_item
            for screen in roots_by_module.get(module.pk, [])
            if (navigation_item := build_item(screen)) is not None
        ]
        for label, legacy_screens in legacy_by_module.get(module.pk, {}).items():
            children = [
                navigation_item
                for screen in legacy_screens
                if (navigation_item := build_item(screen)) is not None
            ]
            if children:
                module_items.append(item(label, children=children))
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
    if use_cache:
        cache.set(NAVIGATION_CACHE_KEY, result, NAVIGATION_CACHE_TIMEOUT)
    return result


def _filter_menu_for_user(menu, user, allowed_keys=None):
    if allowed_keys is None:
        allowed_keys = user_access_keys(user) if user.is_authenticated and not user.is_superuser else set()

    def filter_items(items):
        visible = []
        for index, nav_item in enumerate(items):
            children = filter_items(nav_item.get("children", []))
            if nav_item.get("is_group") and not children:
                continue
            if (
                not nav_item.get("is_group")
                and not user.is_superuser
                and nav_item.get("access_key") not in allowed_keys
                and not children
            ):
                continue
            visible.append((index, {**nav_item, "children": children}))
        return [nav_item for _, nav_item in visible]

    filtered_modules = []
    for module in menu:
        filtered_items = filter_items(module["items"])
        if filtered_items:
            filtered_modules.append({**module, "items": filtered_items})
    return filtered_modules


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
        "core:system_screen_new": reverse("core:system_screens"),
        "core:system_screen_edit": reverse("core:system_screens"),
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
    if route_name in {
        "atendimento:cadastro-paciente-agendamento",
        "atendimento:revisar-paciente-agendamento",
    } and request.GET.get("recepcao_direta") == "1":
        tab_key = reverse("atendimento:recepcao")
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
    system_icon_svgs = cache.get(SYSTEM_ICONS_CACHE_KEY)
    if system_icon_svgs is None:
        try:
            system_icon_svgs = dict(IconeSistema.objects.values_list("cd_icone", "ds_svg"))
        except (OperationalError, ProgrammingError):
            system_icon_svgs = {}
        else:
            cache.set(SYSTEM_ICONS_CACHE_KEY, system_icon_svgs, NAVIGATION_CACHE_TIMEOUT)
    current_new_url = getattr(request, "current_new_url", new_url_by_route.get(route_name, ""))
    if route_name in {"perfis", "atendimento:profissionais"} and current_new_url:
        separator = "&" if "?" in current_new_url else "?"
        current_new_url = f"{current_new_url}{separator}{urlencode({'return_to': request.get_full_path()})}"
    certificate_notifications = []
    if (
        current_empresa
        and request.user.is_authenticated
        and (request.user.is_superuser or request.user.groups.filter(name="TI").exists())
    ):
        try:
            niveis = settings.CELERIS_CERTIFICATE_EXPIRY_WARNING_LEVELS or (
                settings.CELERIS_CERTIFICATE_EXPIRY_WARNING_DAYS,
            )
            limite = timezone.now() + timedelta(days=max(niveis))
            certificados_alerta = CertificadoDigitalEmpresa.objects.filter(
                cd_empresa=current_empresa,
                sn_ativo=True,
                dh_fim_validade__lte=limite,
            ).only("nm_certificado", "dh_fim_validade")
            for certificado in certificados_alerta:
                vencido = certificado.dh_fim_validade <= timezone.now()
                dias_restantes = max(0, (certificado.dh_fim_validade.date() - timezone.localdate()).days)
                certificate_notifications.append(
                    {
                        "level": "error" if vencido else "warning",
                        "text": (
                            f"Certificado digital {certificado.nm_certificado} vencido."
                            if vencido
                            else f"Certificado digital {certificado.nm_certificado} vence em "
                            f"{dias_restantes} dia(s), em {certificado.dh_fim_validade:%d/%m/%Y}."
                        ),
                    }
                )
        except (OperationalError, ProgrammingError):
            certificate_notifications = []
    return {
        "modules_menu": _filter_menu_for_user(
            _merge_configured_menu(),
            request.user,
            getattr(request, "_celeris_access_keys", None),
        ),
        "current_tab_title": current_tab_title,
        "current_module_title": current_module_title,
        "current_can_query": getattr(request, "current_can_query", current_tab_title not in {"Início", "Alterar senha"}),
        "current_can_save": getattr(request, "current_can_save", True),
        "current_can_remove": getattr(request, "current_can_remove", False),
        "current_new_url": current_new_url,
        "current_continue_url": getattr(request, "current_continue_url", ""),
        "current_empresa": current_empresa,
        "system_icon_svgs": system_icon_svgs,
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
        "class_can_configure": bool(
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.groups.filter(name="TI", papel__sn_ativo=True).exists()
            )
        ),
        "certificate_notifications": certificate_notifications,
    }
