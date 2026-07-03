from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0011_setor_setorusuario"),
        ("atendimento", "0027_cadastro_recepcao_atendimento"),
    ]

    operations = [
        migrations.AddField(
            model_name="atendimento",
            name="ds_motivo_alta",
            field=models.TextField(blank=True),
        ),
        migrations.CreateModel(
            name="PerfilAssistencial",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_perfil_assistencial", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_perfil", models.CharField(max_length=120)),
                ("ds_descricao", models.CharField(blank=True, max_length=300)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("tipos_prestador", models.JSONField(blank=True, default=list)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "perfil_assistencial",
                "ordering": ("nm_perfil",),
                "unique_together": {("cd_empresa", "nm_perfil")},
            },
        ),
        migrations.CreateModel(
            name="ItemMenuAssistencial",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_item_menu_assistencial", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_item", models.CharField(max_length=120)),
                ("ds_icone", models.CharField(blank=True, max_length=40)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=0)),
                ("tp_item", models.CharField(choices=[("GRUPO", "Grupo"), ("ACAO", "Ação do sistema"), ("DOCUMENTO", "Modelo de documento"), ("LINK_EXTERNO", "Link externo"), ("ANCORA", "Seção da ficha")], default="ACAO", max_length=20)),
                ("ds_acao", models.CharField(blank=True, max_length=60)),
                ("ds_url", models.CharField(blank=True, max_length=500)),
                ("sn_privado", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_item_pai", models.ForeignKey(blank=True, db_column="cd_item_pai", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="filhos", to="atendimento.itemmenuassistencial")),
                ("cd_modelo_documento", models.ForeignKey(blank=True, db_column="cd_modelo_documento", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.modelodocumento")),
                ("cd_perfil_assistencial", models.ForeignKey(db_column="cd_perfil_assistencial", on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="atendimento.perfilassistencial")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "item_menu_assistencial", "ordering": ("nr_ordem", "nm_item")},
        ),
    ]
