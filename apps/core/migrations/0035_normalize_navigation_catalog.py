import hashlib

from django.db import migrations
from django.utils.text import slugify


def _stable_slug(module_code, labels):
    source = "-".join([module_code, *labels])
    base = slugify(source)[:140] or "item"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return f"{base}-{digest}"[:160]


def normalize_navigation_catalog(apps, schema_editor):
    from apps.core.navigation import MODULES

    Group = apps.get_model("auth", "Group")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    def sync_items(module, items, parent=None, path=()):
        for position, navigation_item in enumerate(items, start=1):
            title = navigation_item.get("label") or "Item"
            labels = (*path, title)
            children = navigation_item.get("children") or []
            access_key = (
                navigation_item.get("access_key")
                or navigation_item.get("route_name")
                or navigation_item.get("url")
                or None
            )
            defaults = {
                "module": module,
                "parent": parent,
                "title": title,
                "parent_label": parent.title if parent else "",
                "navigation_url": navigation_item.get("url") or "",
                "icon": navigation_item.get("icon") or "",
                "roles": navigation_item.get("roles") or [],
                "active": True,
                "order": position * 10,
            }
            if children:
                defaults.update(
                    {
                        "screen_type": "grupo",
                        "access_key": None,
                        "allow_query": False,
                        "allow_insert": False,
                        "allow_update": False,
                        "allow_delete": False,
                    }
                )
                node, _created = ScreenDefinition.objects.update_or_create(
                    slug=_stable_slug(module.code, labels),
                    defaults=defaults,
                )
                sync_items(module, children, node, labels)
                continue

            screen = ScreenDefinition.objects.filter(access_key=access_key).first() if access_key else None
            if screen:
                for field, value in defaults.items():
                    setattr(screen, field, value)
                screen.access_key = access_key
                screen.save()
            else:
                defaults.update(
                    {
                        "screen_type": "formulario",
                        "access_key": access_key,
                        "allow_query": True,
                        "allow_insert": True,
                        "allow_update": True,
                        "allow_delete": False,
                    }
                )
                ScreenDefinition.objects.update_or_create(
                    slug=_stable_slug(module.code, labels),
                    defaults=defaults,
                )

    for module_position, module_data in enumerate(MODULES, start=1):
        module, _created = Module.objects.update_or_create(
            code=module_data["code"],
            defaults={
                "title": module_data["title"],
                "icon": module_data.get("icon") or "grid",
                "order": module_position * 10,
                "active": True,
            },
        )
        sync_items(module, module_data.get("items") or [])

    ScreenDefinition.objects.filter(
        access_key__in={
            "atendimento:atendimentos",
            "atendimento:fila-medica",
            "atendimento:demanda-espontanea",
            "atendimento:pep",
        }
    ).update(active=False)
    Module.objects.filter(code__in={"ADMINISTRACAO", "ESTOQUE", "FISCAL"}).update(active=False)

    for screen in ScreenDefinition.objects.filter(active=True).exclude(access_key__isnull=True).exclude(access_key=""):
        for role_name in screen.roles or []:
            group, _created = Group.objects.get_or_create(name=role_name)
            role, _created = Papel.objects.get_or_create(grupo=group, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=role, modulo=screen.module)
            PapelTela.objects.get_or_create(papel=role, tela=screen)


class Migration(migrations.Migration):
    dependencies = [("core", "0034_sync_navigation_roles")]

    operations = [
        migrations.RunPython(normalize_navigation_catalog, migrations.RunPython.noop),
    ]
