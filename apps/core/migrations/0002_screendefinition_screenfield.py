from django.db import migrations, models
import django.db.models.deletion


def seed_user_screens(apps, schema_editor):
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    ScreenField = apps.get_model("core", "ScreenField")

    ti_module, _ = Module.objects.get_or_create(
        code="TI",
        defaults={"title": "TI", "active": True},
    )

    screens = [
        {
            "title": "Cadastro / Copia de usuario",
            "slug": "ti-cadastro-copia-usuario",
            "screen_type": "formulario",
            "parent_label": "Gerenciamento de Usuarios",
            "table_name": "accounts_user",
            "order": 10,
            "fields": [
                ("ID", "accounts_user", "id", "number", False, True, False, True, True, 10),
                ("Usuario", "accounts_user", "username", "text", True, True, True, False, True, 20),
                ("Nome completo", "accounts_user", "full_name", "text", False, True, True, False, True, 30),
                ("Email", "accounts_user", "email", "text", False, True, True, False, True, 40),
                ("Ativo", "accounts_user", "is_active", "checkbox", False, True, True, False, True, 50),
                ("Coordenador", "accounts_user", "is_coordinator", "checkbox", False, True, True, False, True, 60),
                ("Copiar permissoes de", "accounts_user", "copy_from_user", "text", False, True, True, False, True, 70),
            ],
        },
        {
            "title": "Alteracao de senha",
            "slug": "ti-alteracao-senha-usuario",
            "screen_type": "formulario",
            "parent_label": "Gerenciamento de Usuarios",
            "table_name": "accounts_user",
            "order": 20,
            "fields": [
                ("Usuario", "accounts_user", "username", "text", True, True, False, False, True, 10),
                ("Nova senha", "accounts_user", "password", "text", True, False, True, False, True, 20),
                ("Alterar no proximo login", "accounts_user", "must_change_password", "checkbox", False, False, True, False, True, 30),
            ],
        },
    ]

    for screen_data in screens:
        fields = screen_data.pop("fields")
        screen, _ = ScreenDefinition.objects.update_or_create(
            slug=screen_data["slug"],
            defaults={**screen_data, "module": ti_module, "active": True},
        )
        for label, table_name, field_name, field_type, required, consultable, editable, primary_key, visible, order in fields:
            ScreenField.objects.update_or_create(
                screen=screen,
                field_name=field_name,
                defaults={
                    "label": label,
                    "table_name": table_name,
                    "field_type": field_type,
                    "required": required,
                    "consultable": consultable,
                    "editable": editable,
                    "primary_key": primary_key,
                    "visible": visible,
                    "order": order,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScreenDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("title", models.CharField(max_length=140)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                ("screen_type", models.CharField(choices=[("formulario", "Formulario"), ("relatorio", "Relatorio"), ("dashboard", "Dashboard"), ("consulta", "Consulta"), ("wizard", "Wizard"), ("fila", "Fila"), ("documento", "Documento"), ("configuracao", "Configuracao")], default="formulario", max_length=30)),
                ("parent_label", models.CharField(blank=True, max_length=120)),
                ("table_name", models.CharField(blank=True, max_length=80)),
                ("description", models.TextField(blank=True)),
                ("active", models.BooleanField(default=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="screens", to="core.module")),
            ],
            options={"ordering": ("module__title", "parent_label", "order", "title")},
        ),
        migrations.CreateModel(
            name="ScreenField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("label", models.CharField(max_length=120)),
                ("table_name", models.CharField(blank=True, max_length=80)),
                ("field_name", models.CharField(max_length=80)),
                ("field_type", models.CharField(choices=[("text", "Texto"), ("number", "Numero"), ("date", "Data"), ("select", "Selecao"), ("textarea", "Texto longo"), ("checkbox", "Checkbox")], default="text", max_length=20)),
                ("required", models.BooleanField(default=False)),
                ("consultable", models.BooleanField(default=True)),
                ("editable", models.BooleanField(default=True)),
                ("primary_key", models.BooleanField(default=False)),
                ("visible", models.BooleanField(default=True)),
                ("choices", models.TextField(blank=True, help_text="Uma opcao por linha para campos de selecao.")),
                ("order", models.PositiveIntegerField(default=0)),
                ("screen", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="core.screendefinition")),
            ],
            options={"ordering": ("order", "label")},
        ),
        migrations.RunPython(seed_user_screens, migrations.RunPython.noop),
    ]
