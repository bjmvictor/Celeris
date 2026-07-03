import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def cadastrar_modulo_senhas(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    modulo, _ = Module.objects.update_or_create(
        code="TOTEM_SENHAS",
        defaults={"title": "Totem de Senhas", "active": True},
    )
    telas = [
        ("Gerar senha", "acesso-totem-gerar-senha", "atendimento:gerar-senha-totem", 10, ["TI", "Recepcionista"]),
        ("Configurar", "acesso-totem-configurar-senhas", "atendimento:configurar-senhas", 20, ["TI"]),
    ]
    for titulo, slug, chave, ordem, papeis in telas:
        tela, _ = ScreenDefinition.objects.update_or_create(
            access_key=chave,
            defaults={
                "module": modulo,
                "title": titulo,
                "slug": slug,
                "screen_type": "configuracao" if "configurar" in chave else "formulario",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": False,
                "active": True,
                "order": ordem,
            },
        )
        for nome_papel in papeis:
            grupo, _ = Group.objects.get_or_create(name=nome_papel)
            papel, _ = Papel.objects.get_or_create(grupo=grupo, defaults={"sn_ativo": True})
            PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
            PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_sync_recent_role_screens"),
        ("atendimento", "0036_alter_modelodocumento_tp_documento"),
        ("core", "0025_configuracao_campo_formulario"),
    ]

    operations = [
        migrations.CreateModel(
            name="TipoSenhaAtendimento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_tipo_senha", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_tipo_senha", models.CharField(max_length=100)),
                ("sg_tipo_senha", models.CharField(max_length=4)),
                ("ds_protocolo", models.CharField(blank=True, max_length=160)),
                ("nr_tempo_minimo", models.PositiveSmallIntegerField(default=30)),
                ("nr_prioridade", models.PositiveSmallIntegerField(default=5)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "tipo_senha_atendimento",
                "ordering": ("nr_prioridade", "nm_tipo_senha"),
                "unique_together": {("cd_empresa", "sg_tipo_senha")},
            },
        ),
        migrations.CreateModel(
            name="ClasseSenhaAtendimento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_classe_senha", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_classe_senha", models.CharField(max_length=100)),
                ("sg_classe_senha", models.CharField(blank=True, max_length=4)),
                ("nr_prioridade", models.PositiveSmallIntegerField(default=5)),
                ("nr_idade_minima", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("nr_idade_maxima", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_tipo_senha", models.ForeignKey(db_column="cd_tipo_senha", on_delete=django.db.models.deletion.CASCADE, related_name="classes", to="atendimento.tiposenhaatendimento")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "classe_senha_atendimento",
                "ordering": ("nr_prioridade", "nm_classe_senha"),
                "unique_together": {("cd_tipo_senha", "sg_classe_senha")},
            },
        ),
        migrations.CreateModel(
            name="SenhaAtendimento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_senha_atendimento", models.BigAutoField(primary_key=True, serialize=False)),
                ("dt_senha", models.DateField(default=django.utils.timezone.localdate)),
                ("nr_senha", models.PositiveIntegerField()),
                ("ds_senha", models.CharField(max_length=16)),
                ("nr_prioridade", models.PositiveSmallIntegerField(default=5)),
                ("nr_tempo_limite", models.PositiveSmallIntegerField(default=30)),
                ("ds_status", models.CharField(choices=[("AGUARDANDO", "Aguardando"), ("CHAMADA", "Chamada"), ("EM_CLASSIFICACAO", "Em classificação"), ("CLASSIFICADA", "Classificada"), ("CANCELADA", "Cancelada")], default="AGUARDANDO", max_length=24)),
                ("dh_chamada", models.DateTimeField(blank=True, null=True)),
                ("dh_recepcao", models.DateTimeField(blank=True, null=True)),
                ("dh_classificacao", models.DateTimeField(blank=True, null=True)),
                ("cd_classe_senha", models.ForeignKey(db_column="cd_classe_senha", on_delete=django.db.models.deletion.PROTECT, to="atendimento.classesenhaatendimento")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_paciente", models.ForeignKey(blank=True, db_column="cd_paciente", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="senhas_atendimento", to="atendimento.paciente")),
                ("cd_tipo_senha", models.ForeignKey(db_column="cd_tipo_senha", on_delete=django.db.models.deletion.PROTECT, to="atendimento.tiposenhaatendimento")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "senha_atendimento",
                "ordering": ("nr_prioridade", "dh_criacao"),
                "unique_together": {("cd_empresa", "dt_senha", "ds_senha")},
            },
        ),
        migrations.RunPython(cadastrar_modulo_senhas, migrations.RunPython.noop),
    ]
