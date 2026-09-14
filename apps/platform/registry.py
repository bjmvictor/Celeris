"""Application discovery and the compatibility bridge to Module/ScreenDefinition.

An application owns its manifest.  The platform discovers manifests through
Django's app registry; it never contains a list of clinical applications.
"""
from dataclasses import dataclass, field
from importlib import import_module
from typing import Iterable

from django.apps import apps
from django.db import OperationalError, ProgrammingError, transaction
from django.db.models.signals import post_migrate


@dataclass(frozen=True)
class MenuRegistration:
    title: str
    access_key: str
    url_name: str = ""
    url: str = ""
    roles: tuple[str, ...] = ()
    icon: str = ""
    order: int = 0
    screen_type: str = "formulario"


@dataclass(frozen=True)
class ApplicationManifest:
    code: str
    name: str
    version: str
    dependencies: tuple[str, ...] = ()
    urlconf: str = ""
    url_prefix: str = ""
    permissions: tuple[str, ...] = ()
    menus: tuple[MenuRegistration, ...] = ()
    events: tuple[str, ...] = ()
    reports: tuple[str, ...] = ()
    settings: tuple[str, ...] = ()
    # Existing database modules can be claimed without changing their code or
    # invalidating PapelTela records during the transition.
    navigation_module: str = ""
    navigation_title: str = ""
    navigation_icon: str = "grid"
    navigation_order: int = 0


class ApplicationRegistry:
    def manifests(self) -> tuple[ApplicationManifest, ...]:
        result = []
        seen = set()
        for config in apps.get_app_configs():
            manifest = getattr(config, "application_manifest", None)
            if manifest is None:
                continue
            if manifest.code in seen:
                raise RuntimeError(f"Application code duplicated: {manifest.code}")
            seen.add(manifest.code)
            result.append(manifest)
        return tuple(sorted(result, key=lambda item: item.code))

    def urlpatterns(self):
        from django.urls import include, path

        patterns = []
        for manifest in self.manifests():
            if manifest.urlconf and manifest.url_prefix:
                module = import_module(manifest.urlconf)
                patterns.append(path(manifest.url_prefix, include(module)))
        return patterns

    def sync_navigation(self) -> None:
        """Idempotently persist only manifest-owned navigation declarations."""
        from apps.core.models import Module, ScreenDefinition

        with transaction.atomic():
            for manifest in self.manifests():
                if not manifest.navigation_module:
                    continue
                module, _ = Module.objects.get_or_create(
                    code=manifest.navigation_module,
                    defaults={
                        "title": manifest.navigation_title or manifest.name,
                        "icon": manifest.navigation_icon,
                        "order": manifest.navigation_order,
                    },
                )
                for menu in manifest.menus:
                    ScreenDefinition.objects.update_or_create(
                        access_key=menu.access_key,
                        defaults={
                            "module": module,
                            "title": menu.title,
                            "slug": f"app-{manifest.code.lower()}-{menu.access_key}"[:160],
                            "navigation_url": menu.url,
                            "icon": menu.icon,
                            "roles": list(menu.roles),
                            "screen_type": menu.screen_type,
                            "order": menu.order,
                        },
                    )


registry = ApplicationRegistry()


def _sync_after_migrate(**kwargs):
    try:
        registry.sync_navigation()
    except (OperationalError, ProgrammingError):
        # Tables do not exist while the first migration plan is being applied.
        return


def install_catalog_sync() -> None:
    post_migrate.connect(_sync_after_migrate, dispatch_uid="celeris.platform.application_catalog")
