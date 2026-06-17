from django.db import migrations
from django.utils.text import slugify


def normalize_usernames(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    used = set()
    for user in User.objects.order_by("id"):
        normalized = slugify(user.username or "", allow_unicode=False).replace("-", "_").upper()
        if not normalized:
            continue
        candidate = normalized
        index = 2
        while candidate in used or User.objects.exclude(pk=user.pk).filter(username=candidate).exists():
            candidate = f"{normalized}_{index}"
            index += 1
        user.username = candidate
        user.save(update_fields=["username"])
        used.add(candidate)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_empresa_usuarioempresa"),
    ]

    operations = [
        migrations.RunPython(normalize_usernames, migrations.RunPython.noop),
    ]
