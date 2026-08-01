"""Operações históricas de dados da migration 0025."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def cadastrar_tela_configuracao_formularios(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modulo = Module.objects.get(code="GLOBAL")
    tela, _ = ScreenDefinition.objects.update_or_create(
        access_key="core:configurar_formularios",
        defaults={
            "module": modulo,
            "title": "Configurar formulários",
            "slug": "acesso-global-configurar-formularios",
            "screen_type": "configuracao",
            "parent_label": "Formulários",
            "description": "Configura a obrigatoriedade dos campos dos formulários padrões do sistema.",
            "allow_query": True,
            "allow_insert": False,
            "allow_update": True,
            "allow_delete": False,
            "active": True,
            "order": 30,
        },
    )
    grupo, _ = Group.objects.get_or_create(name="TI")
    papel, _ = Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
    PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
    PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_sync_recent_role_screens"),
        ("core", "0024_refresh_minimum_auxiliary_values"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConfiguracaoCampoFormulario",
            fields=[
                (
                    "cd_configuracao_campo_formulario",
                    models.BigAutoField(primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("cd_formulario", models.CharField(max_length=80)),
                ("cd_campo", models.CharField(max_length=120)),
                ("sn_obrigatorio", models.BooleanField(default=False)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="configuracoes_campos_formularios",
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_usuario_atualizacao",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_usuario_atualizacao",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="configuracoes_formularios_atualizadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "cd_usuario_criacao",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_usuario_criacao",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="configuracoes_formularios_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "configuracao_campo_formulario",
                "ordering": ("cd_formulario", "cd_campo"),
                "unique_together": {("cd_empresa", "cd_formulario", "cd_campo")},
            },
        ),
        migrations.RunPython(
            cadastrar_tela_configuracao_formularios,
            migrations.RunPython.noop,
        ),
    ]
