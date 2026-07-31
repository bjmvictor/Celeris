import unicodedata

from django.db import migrations


def normalizar_titulo(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character for character in normalized if not unicodedata.combining(character)
    ).casefold().strip()


def mesclar_grupos_navegacao(apps, schema_editor):
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    groups_by_scope = {}
    groups = ScreenDefinition.objects.filter(screen_type="grupo", active=True).order_by(
        "module_id", "parent_id", "order", "pk"
    )
    for group in groups:
        key = (group.module_id, group.parent_id, normalizar_titulo(group.title))
        canonical = groups_by_scope.get(key)
        if canonical is None:
            groups_by_scope[key] = group
            continue
        ScreenDefinition.objects.filter(parent=group).update(
            parent=canonical,
            parent_label=canonical.title,
        )
        group.active = False
        group.save(update_fields=("active", "updated_at"))

    root_groups = {
        (group.module_id, normalizar_titulo(group.title)): group
        for group in ScreenDefinition.objects.filter(
            screen_type="grupo",
            active=True,
            parent__isnull=True,
        )
    }
    legacy_screens = ScreenDefinition.objects.filter(
        active=True,
        parent__isnull=True,
    ).exclude(parent_label="")
    for screen in legacy_screens:
        parent = root_groups.get((screen.module_id, normalizar_titulo(screen.parent_label)))
        if parent is None and screen.module.code == "TI":
            parent = root_groups.get((screen.module_id, normalizar_titulo("Usuários e acessos")))
        if parent is None:
            continue
        screen.parent = parent
        screen.parent_label = parent.title
        screen.save(update_fields=("parent", "parent_label", "updated_at"))

    ti_group = ScreenDefinition.objects.filter(
        module__code="TI",
        title="Usuários e acessos",
        screen_type="grupo",
        active=True,
    ).first()
    if ti_group:
        users_screen = ScreenDefinition.objects.filter(
            module=ti_group.module,
            access_key="usuarios",
        ).first()
        if users_screen:
            users_screen.parent = ti_group
            users_screen.parent_label = ti_group.title
            users_screen.title = "Usuários"
            users_screen.navigation_url = ""
            users_screen.active = True
            users_screen.save(
                update_fields=("parent", "parent_label", "title", "navigation_url", "active", "updated_at")
            )

        legacy_password_screen = ScreenDefinition.objects.filter(
            module=ti_group.module,
            slug="ti-alteracao-senha-usuario",
        ).first()
        password_screen = ScreenDefinition.objects.filter(
            module=ti_group.module,
            access_key="ti:alteracao_senha_usuario",
        ).first()
        if password_screen is None:
            password_screen = legacy_password_screen
        if password_screen:
            password_screen.parent = ti_group
            password_screen.parent_label = ti_group.title
            password_screen.title = "Alteração de senha"
            password_screen.access_key = "ti:alteracao_senha_usuario"
            password_screen.navigation_url = ""
            password_screen.screen_type = "configuracao"
            password_screen.active = True
            password_screen.save(
                update_fields=(
                    "parent",
                    "parent_label",
                    "title",
                    "access_key",
                    "navigation_url",
                    "screen_type",
                    "active",
                    "updated_at",
                )
            )
        if legacy_password_screen and legacy_password_screen.pk != getattr(password_screen, "pk", None):
            legacy_password_screen.active = False
            legacy_password_screen.save(update_fields=("active", "updated_at"))

        ScreenDefinition.objects.filter(
            module=ti_group.module,
            title="Cadastro / Cópia de usuário",
        ).update(active=False)

    children_by_scope = {}
    children = ScreenDefinition.objects.filter(active=True).exclude(parent__isnull=True).order_by(
        "module_id", "parent_id", "order", "pk"
    )
    for child in children:
        key = (child.module_id, child.parent_id, normalizar_titulo(child.title))
        canonical = children_by_scope.get(key)
        if canonical is None:
            children_by_scope[key] = child
            continue
        preferred = canonical
        duplicate = child
        if str(canonical.access_key or "").startswith("/telas/") and not str(child.access_key or "").startswith("/telas/"):
            preferred, duplicate = child, canonical
            children_by_scope[key] = preferred
        ScreenDefinition.objects.filter(parent=duplicate).update(
            parent=preferred,
            parent_label=preferred.title,
        )
        duplicate.active = False
        duplicate.save(update_fields=("active", "updated_at"))


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0036_normalizar_catalogos_iniciais"),
    ]

    operations = [
        migrations.RunPython(mesclar_grupos_navegacao, migrations.RunPython.noop),
    ]
