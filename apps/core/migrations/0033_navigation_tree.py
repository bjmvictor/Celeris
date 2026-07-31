import hashlib

from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


def _stable_slug(module_code, labels):
    source = "-".join([module_code, *labels])
    base = slugify(source)[:140] or "item"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return f"{base}-{digest}"[:160]


def seed_navigation_tree(apps, schema_editor):
    from apps.core.navigation import MODULES

    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    seen_access_keys = set(
        ScreenDefinition.objects.exclude(access_key__isnull=True)
        .exclude(access_key="")
        .values_list("access_key", flat=True)
    )

    def import_items(module, items, parent=None, path=()):
        for order, nav_item in enumerate(items, start=1):
            label = nav_item.get("label") or "Item"
            labels = (*path, label)
            children = nav_item.get("children") or []
            route_name = nav_item.get("route_name") or ""
            navigation_url = nav_item.get("url") or ""
            access_key = nav_item.get("access_key") or route_name or navigation_url or None
            if children:
                node, _ = ScreenDefinition.objects.update_or_create(
                    slug=_stable_slug(module.code, labels),
                    defaults={
                        "module": module,
                        "parent": parent,
                        "title": label,
                        "screen_type": "grupo",
                        "parent_label": parent.title if parent else "",
                        "navigation_url": "",
                        "access_key": None,
                        "roles": nav_item.get("roles") or [],
                        "allow_query": False,
                        "allow_insert": False,
                        "allow_update": False,
                        "allow_delete": False,
                        "active": True,
                        "order": order * 10,
                    },
                )
                import_items(module, children, node, labels)
                continue

            if access_key in seen_access_keys:
                existing = ScreenDefinition.objects.filter(access_key=access_key).first()
                if existing and not existing.parent_id:
                    existing.parent = parent
                    existing.parent_label = parent.title if parent else ""
                    existing.navigation_url = navigation_url
                    existing.roles = nav_item.get("roles") or []
                    existing.order = order * 10
                    existing.save(update_fields=("parent", "parent_label", "navigation_url", "roles", "order"))
                continue

            ScreenDefinition.objects.update_or_create(
                slug=_stable_slug(module.code, labels),
                defaults={
                    "module": module,
                    "parent": parent,
                    "title": label,
                    "screen_type": "formulario",
                    "parent_label": parent.title if parent else "",
                    "navigation_url": navigation_url,
                    "access_key": access_key,
                    "roles": nav_item.get("roles") or [],
                    "allow_query": True,
                    "allow_insert": True,
                    "allow_update": True,
                    "allow_delete": False,
                    "active": True,
                    "order": order * 10,
                },
            )
            if access_key:
                seen_access_keys.add(access_key)

    for module_order, module_data in enumerate(MODULES, start=1):
        module, _ = Module.objects.update_or_create(
            code=module_data["code"],
            defaults={
                "title": module_data["title"],
                "icon": module_data.get("icon") or "grid",
                "order": module_order * 10,
                "active": True,
            },
        )
        import_items(module, module_data.get("items") or [])

    def merge_legacy_module(source_code, target_code, group_title, parent_title=None):
        source = Module.objects.filter(code=source_code).first()
        target = Module.objects.filter(code=target_code).first()
        if not source or not target or source.pk == target.pk:
            return
        parent = None
        if parent_title:
            parent = ScreenDefinition.objects.filter(module=target, title=parent_title, screen_type="grupo").first()
        group_path = (parent_title, group_title) if parent_title else (group_title,)
        group, _ = ScreenDefinition.objects.update_or_create(
            slug=_stable_slug(target.code, tuple(part for part in group_path if part)),
            defaults={
                "module": target,
                "parent": parent,
                "title": group_title,
                "screen_type": "grupo",
                "access_key": None,
                "allow_query": False,
                "allow_insert": False,
                "allow_update": False,
                "allow_delete": False,
                "active": True,
                "order": 500,
            },
        )
        for screen in ScreenDefinition.objects.filter(module=source, parent__isnull=True):
            screen.module = target
            screen.parent = group
            screen.parent_label = group.title
            screen.save(update_fields=("module", "parent", "parent_label"))
        source.active = False
        source.save(update_fields=("active",))

    merge_legacy_module("PACIENTES", "ATENDIMENTO", "Pacientes")
    merge_legacy_module("BI", "ATENDIMENTO", "Indicadores")
    merge_legacy_module("RELACIONAMENTO", "GLOBAL", "Relacionamentos", "Empresa")


class Migration(migrations.Migration):
    dependencies = [("core", "0032_corrigir_tela_alteracao_senha")]

    operations = [
        migrations.AddField(
            model_name="module",
            name="icon",
            field=models.CharField(blank=True, default="grid", max_length=50),
        ),
        migrations.AddField(
            model_name="module",
            name="order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="module",
            options={"ordering": ("order", "title")},
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="icon",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="navigation_url",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="parent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="core.screendefinition"),
        ),
        migrations.AddField(
            model_name="screendefinition",
            name="roles",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name="screendefinition",
            name="screen_type",
            field=models.CharField(choices=[("grupo", "Grupo"), ("formulario", "Formulário"), ("relatorio", "Relatório"), ("dashboard", "Dashboard"), ("consulta", "Consulta"), ("wizard", "Wizard"), ("fila", "Fila"), ("documento", "Documento"), ("configuracao", "Configuração")], default="formulario", max_length=30),
        ),
        migrations.AlterModelOptions(
            name="screendefinition",
            options={"ordering": ("module__order", "module__title", "parent__order", "parent_label", "order", "title")},
        ),
        migrations.RunPython(seed_navigation_tree, migrations.RunPython.noop),
    ]
