import apps.atendimento.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def _audit_fields():
    return [
        ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
        ("dh_atualizacao", models.DateTimeField(auto_now=True)),
        (
            "cd_usuario_criacao",
            models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(app_label)s_%(class)s_criados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        (
            "cd_usuario_atualizacao",
            models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(app_label)s_%(class)s_atualizados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]


def migrar_dados_legados(apps, schema_editor):
    Prestador = apps.get_model("atendimento", "Prestador")
    PrestadorTipo = apps.get_model("atendimento", "PrestadorTipo")
    Perfil = apps.get_model("atendimento", "PerfilAssistencial")
    PerfilTipo = apps.get_model("atendimento", "PerfilAssistencialTipo")
    PerfilVersao = apps.get_model("atendimento", "PerfilAssistencialVersao")
    Item = apps.get_model("atendimento", "ItemMenuAssistencial")
    Documento = apps.get_model("atendimento", "DocumentoClinico")

    for prestador in Prestador.objects.exclude(tp_prestador="").iterator():
        PrestadorTipo.objects.get_or_create(
            cd_empresa_id=prestador.cd_empresa_id,
            cd_prestador_id=prestador.pk,
            cd_tipo_prestador=prestador.tp_prestador,
            defaults={
                "sn_principal": True,
                "sn_ativo": True,
                "cd_usuario_criacao_id": prestador.cd_usuario_criacao_id,
                "cd_usuario_atualizacao_id": prestador.cd_usuario_atualizacao_id,
            },
        )

    for perfil in Perfil.objects.order_by("pk").iterator():
        for tipo in perfil.tipos_prestador or []:
            PerfilTipo.objects.get_or_create(
                cd_empresa_id=perfil.cd_empresa_id,
                cd_tipo_prestador=tipo,
                defaults={
                    "cd_perfil_assistencial_id": perfil.pk,
                    "sn_ativo": True,
                    "cd_usuario_criacao_id": perfil.cd_usuario_criacao_id,
                    "cd_usuario_atualizacao_id": perfil.cd_usuario_atualizacao_id,
                },
            )
        versao, _ = PerfilVersao.objects.get_or_create(
            cd_empresa_id=perfil.cd_empresa_id,
            cd_perfil_assistencial_id=perfil.pk,
            nr_versao=1,
            defaults={
                "ds_status": "PUBLICADO",
                "ds_descricao_versao": "Versão inicial migrada",
                "dh_publicacao": django.utils.timezone.now(),
                "cd_usuario_criacao_id": perfil.cd_usuario_criacao_id,
                "cd_usuario_atualizacao_id": perfil.cd_usuario_atualizacao_id,
                "cd_usuario_publicacao_id": perfil.cd_usuario_atualizacao_id or perfil.cd_usuario_criacao_id,
            },
        )
        Item.objects.filter(cd_perfil_assistencial_id=perfil.pk, cd_versao_perfil__isnull=True).update(
            cd_versao_perfil_id=versao.pk
        )
    for item in Item.objects.filter(cd_item_tecnico="").iterator():
        item.cd_item_tecnico = f"ITEM_{item.pk}"
        item.save(update_fields=["cd_item_tecnico"])

    Documento.objects.filter(ds_status="RASCUNHO").update(ds_status="ABERTO")
    Documento.objects.filter(ds_status__in=["FINALIZADO", "ASSINADO"]).update(ds_status="FECHADO")
    for documento in Documento.objects.filter(cd_usuario_responsavel__isnull=True).iterator():
        documento.cd_usuario_responsavel_id = documento.cd_usuario_emissor_id
        documento.save(update_fields=["cd_usuario_responsavel"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_usuario_prestador_unico"),
        ("atendimento", "0032_alter_modelodocumento_tp_elemento"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilassistencial",
            name="sn_sigiloso",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="cd_item_tecnico",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="ds_configuracao",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="sn_imprimivel",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="sn_permite_abandonar",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="sn_permite_cancelar",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="sn_permite_criar",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="sn_somente_historico",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="itemmenuassistencial",
            name="tp_item",
            field=models.CharField(
                choices=[
                    ("GRUPO", "Grupo"),
                    ("ACAO", "Ação do sistema"),
                    ("DOCUMENTO", "Modelo de documento"),
                    ("LINK_EXTERNO", "Link externo"),
                    ("ANCORA", "Seção da ficha"),
                    ("ESCALA", "Escala clínica"),
                    ("ANEXO", "Anexo clínico"),
                    ("HISTORICO", "Histórico somente leitura"),
                ],
                default="ACAO",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="documentoclinico",
            name="ds_status",
            field=models.CharField(
                choices=[
                    ("ABERTO", "Aberto"),
                    ("FECHADO", "Fechado"),
                    ("ABANDONADO", "Abandonado"),
                    ("RASCUNHO", "Rascunho"),
                    ("FINALIZADO", "Finalizado"),
                    ("ASSINADO", "Assinado"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="ABERTO",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="cd_item_menu_assistencial",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_item_menu_assistencial",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documentos",
                to="atendimento.itemmenuassistencial",
            ),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="cd_usuario_cancelamento",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_usuario_cancelamento",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="documentos_clinicos_cancelados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="cd_usuario_responsavel",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_usuario_responsavel",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="documentos_clinicos_responsaveis",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="ds_hash_conteudo",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="ds_motivo_cancelamento",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.CreateModel(
            name="PrestadorTipo",
            fields=_audit_fields()
            + [
                ("cd_prestador_tipo", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_tipo_prestador", models.CharField(max_length=60)),
                ("sn_principal", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_prestador",
                    models.ForeignKey(
                        db_column="cd_prestador",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tipos_vinculados",
                        to="atendimento.prestador",
                    ),
                ),
            ],
            options={
                "db_table": "prestador_tipo",
                "ordering": ("cd_prestador", "-sn_principal", "cd_tipo_prestador"),
            },
        ),
        migrations.CreateModel(
            name="PerfilAssistencialTipo",
            fields=_audit_fields()
            + [
                ("cd_perfil_assistencial_tipo", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_tipo_prestador", models.CharField(max_length=60)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_perfil_assistencial",
                    models.ForeignKey(
                        db_column="cd_perfil_assistencial",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tipos_vinculados",
                        to="atendimento.perfilassistencial",
                    ),
                ),
            ],
            options={"db_table": "perfil_assistencial_tipo", "ordering": ("cd_tipo_prestador",)},
        ),
        migrations.CreateModel(
            name="PerfilAssistencialVersao",
            fields=_audit_fields()
            + [
                ("cd_perfil_assistencial_versao", models.BigAutoField(primary_key=True, serialize=False)),
                ("nr_versao", models.PositiveIntegerField(default=1)),
                (
                    "ds_status",
                    models.CharField(
                        choices=[
                            ("RASCUNHO", "Rascunho"),
                            ("PUBLICADO", "Publicado"),
                            ("ARQUIVADO", "Arquivado"),
                        ],
                        default="RASCUNHO",
                        max_length=20,
                    ),
                ),
                ("ds_descricao_versao", models.CharField(blank=True, max_length=500)),
                ("ds_configuracao", models.JSONField(blank=True, default=dict)),
                ("dh_publicacao", models.DateTimeField(blank=True, null=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_perfil_assistencial",
                    models.ForeignKey(
                        db_column="cd_perfil_assistencial",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versoes",
                        to="atendimento.perfilassistencial",
                    ),
                ),
                (
                    "cd_usuario_publicacao",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_usuario_publicacao",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="perfis_assistenciais_publicados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "perfil_assistencial_versao", "ordering": ("-nr_versao",)},
        ),
        migrations.AddField(
            model_name="itemmenuassistencial",
            name="cd_versao_perfil",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_versao_perfil",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="itens",
                to="atendimento.perfilassistencialversao",
            ),
        ),
        migrations.AddField(
            model_name="documentoclinico",
            name="cd_versao_perfil",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_versao_perfil",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documentos",
                to="atendimento.perfilassistencialversao",
            ),
        ),
        migrations.CreateModel(
            name="RascunhoEditorDocumento",
            fields=[
                ("cd_rascunho_editor_documento", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_chave_guia", models.CharField(max_length=180)),
                ("ds_estado", models.JSONField(default=dict)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_modelo_documento",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_modelo_documento",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="atendimento.modelodocumento",
                    ),
                ),
                (
                    "cd_usuario",
                    models.ForeignKey(
                        db_column="cd_usuario",
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "rascunho_editor_documento"},
        ),
        migrations.CreateModel(
            name="EventoDocumentoClinico",
            fields=[
                ("cd_evento_documento_clinico", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "tp_evento",
                    models.CharField(
                        choices=[
                            ("CRIADO", "Criado"),
                            ("ATUALIZADO", "Atualizado"),
                            ("ASSUMIDO", "Assumido"),
                            ("FECHADO", "Fechado"),
                            ("ABANDONADO", "Abandonado"),
                            ("CANCELADO", "Cancelado"),
                            ("ACESSO_EXCEPCIONAL", "Acesso excepcional"),
                            ("IMPRESSO", "Impresso"),
                        ],
                        max_length=30,
                    ),
                ),
                ("ds_motivo", models.CharField(blank=True, max_length=500)),
                ("ds_dados", models.JSONField(blank=True, default=dict)),
                ("dh_evento", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                (
                    "cd_documento_clinico",
                    models.ForeignKey(
                        db_column="cd_documento_clinico",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos",
                        to="atendimento.documentoclinico",
                    ),
                ),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_usuario",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_usuario",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "evento_documento_clinico", "ordering": ("-dh_evento",)},
        ),
        migrations.CreateModel(
            name="DominioExternoPermitido",
            fields=_audit_fields()
            + [
                ("cd_dominio_externo_permitido", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_dominio", models.CharField(max_length=253)),
                ("sn_permite_iframe", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.empresa",
                    ),
                ),
            ],
            options={"db_table": "dominio_externo_permitido", "ordering": ("ds_dominio",)},
        ),
        migrations.CreateModel(
            name="EscalaClinica",
            fields=_audit_fields()
            + [
                ("cd_escala_clinica", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_escala", models.CharField(max_length=160)),
                ("ds_descricao", models.CharField(blank=True, max_length=500)),
                (
                    "tp_calculo",
                    models.CharField(
                        choices=[("SOMA", "Soma"), ("MEDIA", "Média")],
                        default="SOMA",
                        max_length=10,
                    ),
                ),
                ("ds_perguntas", models.JSONField(default=list)),
                ("ds_faixas_resultado", models.JSONField(default=list)),
                ("nr_versao", models.PositiveIntegerField(default=1)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
            ],
            options={"db_table": "escala_clinica", "ordering": ("nm_escala", "-nr_versao")},
        ),
        migrations.CreateModel(
            name="AnexoClinico",
            fields=_audit_fields()
            + [
                ("cd_anexo_clinico", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_arquivo", models.CharField(max_length=255)),
                ("ds_tipo_mime", models.CharField(max_length=120)),
                ("nr_tamanho", models.PositiveBigIntegerField()),
                ("ds_checksum_sha256", models.CharField(max_length=64)),
                (
                    "ds_arquivo",
                    models.FileField(
                        storage=apps.atendimento.models.armazenamento_clinico_privado,
                        upload_to=apps.atendimento.models.caminho_anexo_clinico,
                    ),
                ),
                ("ds_status_antivirus", models.CharField(default="PENDENTE", max_length=20)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_atendimento",
                    models.ForeignKey(
                        db_column="cd_atendimento",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anexos_clinicos",
                        to="atendimento.atendimento",
                    ),
                ),
                (
                    "cd_documento_clinico",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_documento_clinico",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anexos",
                        to="atendimento.documentoclinico",
                    ),
                ),
                (
                    "cd_item_menu_assistencial",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_item_menu_assistencial",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anexos_clinicos",
                        to="atendimento.itemmenuassistencial",
                    ),
                ),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
            ],
            options={"db_table": "anexo_clinico", "ordering": ("-dh_criacao",)},
        ),
        migrations.CreateModel(
            name="ResultadoEscalaClinica",
            fields=_audit_fields()
            + [
                ("cd_resultado_escala_clinica", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_respostas", models.JSONField(default=dict)),
                ("nr_resultado", models.DecimalField(decimal_places=2, max_digits=10)),
                ("ds_classificacao", models.CharField(max_length=160)),
                ("ds_cor", models.CharField(blank=True, max_length=20)),
                (
                    "cd_atendimento",
                    models.ForeignKey(
                        db_column="cd_atendimento",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultados_escalas",
                        to="atendimento.atendimento",
                    ),
                ),
                (
                    "cd_documento_clinico",
                    models.OneToOneField(
                        blank=True,
                        db_column="cd_documento_clinico",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resultado_escala",
                        to="atendimento.documentoclinico",
                    ),
                ),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_escala_clinica",
                    models.ForeignKey(
                        db_column="cd_escala_clinica",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="atendimento.escalaclinica",
                    ),
                ),
            ],
            options={"db_table": "resultado_escala_clinica", "ordering": ("-dh_criacao",)},
        ),
        migrations.CreateModel(
            name="AcessoClinicoAuditado",
            fields=[
                ("cd_acesso_clinico_auditado", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "tp_acesso",
                    models.CharField(
                        choices=[
                            ("VISUALIZACAO", "Visualização"),
                            ("DOWNLOAD", "Download"),
                            ("ACESSO_EXCEPCIONAL", "Acesso excepcional"),
                        ],
                        max_length=30,
                    ),
                ),
                ("ds_motivo", models.CharField(blank=True, max_length=500)),
                ("ds_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("dh_acesso", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                (
                    "cd_empresa",
                    models.ForeignKey(
                        db_column="cd_empresa",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="accounts.empresa",
                    ),
                ),
                (
                    "cd_usuario",
                    models.ForeignKey(
                        db_column="cd_usuario",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "cd_documento_clinico",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_documento_clinico",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="atendimento.documentoclinico",
                    ),
                ),
                (
                    "cd_anexo_clinico",
                    models.ForeignKey(
                        blank=True,
                        db_column="cd_anexo_clinico",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="atendimento.anexoclinico",
                    ),
                ),
            ],
            options={"db_table": "acesso_clinico_auditado", "ordering": ("-dh_acesso",)},
        ),
        migrations.AddConstraint(
            model_name="prestadortipo",
            constraint=models.UniqueConstraint(
                fields=("cd_empresa", "cd_prestador", "cd_tipo_prestador"),
                name="prestador_tipo_unico_empresa",
            ),
        ),
        migrations.AddConstraint(
            model_name="prestadortipo",
            constraint=models.UniqueConstraint(
                condition=models.Q(sn_ativo=True, sn_principal=True),
                fields=("cd_prestador",),
                name="prestador_tipo_principal_unico",
            ),
        ),
        migrations.AddConstraint(
            model_name="perfilassistencialtipo",
            constraint=models.UniqueConstraint(
                condition=models.Q(sn_ativo=True),
                fields=("cd_empresa", "cd_tipo_prestador"),
                name="perfil_tipo_prestador_unico_empresa",
            ),
        ),
        migrations.AddConstraint(
            model_name="perfilassistencialversao",
            constraint=models.UniqueConstraint(
                fields=("cd_perfil_assistencial", "nr_versao"),
                name="perfil_assistencial_versao_unica",
            ),
        ),
        migrations.AddConstraint(
            model_name="perfilassistencialversao",
            constraint=models.UniqueConstraint(
                condition=models.Q(ds_status="PUBLICADO"),
                fields=("cd_perfil_assistencial",),
                name="perfil_assistencial_publicado_unico",
            ),
        ),
        migrations.AddConstraint(
            model_name="rascunhoeditordocumento",
            constraint=models.UniqueConstraint(
                fields=("cd_empresa", "cd_usuario", "cd_modelo_documento", "ds_chave_guia"),
                name="rascunho_editor_unico",
            ),
        ),
        migrations.AddConstraint(
            model_name="dominioexternopermitido",
            constraint=models.UniqueConstraint(
                fields=("cd_empresa", "ds_dominio"),
                name="dominio_externo_empresa_unico",
            ),
        ),
        migrations.AddConstraint(
            model_name="escalaclinica",
            constraint=models.UniqueConstraint(
                fields=("cd_empresa", "nm_escala", "nr_versao"),
                name="escala_clinica_versao_unica",
            ),
        ),
        migrations.RunPython(migrar_dados_legados, migrations.RunPython.noop),
    ]
