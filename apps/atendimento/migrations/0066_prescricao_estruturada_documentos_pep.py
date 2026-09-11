from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


VIAS = (
    ("VO", "Via oral", 10),
    ("IV", "Intravenosa", 20),
    ("IM", "Intramuscular", 30),
    ("SC", "Subcutânea", 40),
    ("SL", "Sublingual", 50),
    ("INAL", "Inalatória", 60),
    ("TOP", "Tópica", 70),
    ("RET", "Retal", 80),
)


def configurar_prescricao_e_documentos(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Classe = apps.get_model("atendimento", "ClasseItemPrescricao")
    Via = apps.get_model("atendimento", "ViaAplicacaoPrescricao")
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    ItemMenu = apps.get_model("atendimento", "ItemMenuAssistencial")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")

    for empresa in Empresa.objects.all():
        Classe.objects.update_or_create(
            cd_empresa=empresa,
            sg_classe="MED",
            defaults={"ds_classe": "Medicamentos", "tp_classe": "MEDICAMENTO", "nr_ordem": 10, "sn_ativo": True},
        )
        Classe.objects.update_or_create(
            cd_empresa=empresa,
            sg_classe="EXA",
            defaults={"ds_classe": "Exames", "tp_classe": "EXAME", "nr_ordem": 20, "sn_ativo": True},
        )
        for sigla, descricao, ordem in VIAS:
            Via.objects.update_or_create(
                cd_empresa=empresa,
                sg_via=sigla,
                defaults={"ds_via": descricao, "nr_ordem": ordem, "sn_ativo": True},
            )
        for acao, tipo, nome, corpo in (
            (
                "EVOLUIR",
                "EVOLUCAO",
                "Evolução clínica",
                "<h2>Evolução clínica</h2><p><strong>Paciente:</strong> {{ paciente.nome }}</p><section>{{ documento.conteudo }}</section>",
            ),
            (
                "ADMISSAO",
                "ADMISSAO_ANAMNESE",
                "Admissão / Anamnese",
                "<h2>Admissão / Anamnese</h2><p><strong>Paciente:</strong> {{ paciente.nome }}</p><section>{{ documento.conteudo }}</section>",
            ),
        ):
            modelo = ModeloDocumento.objects.filter(
                cd_empresa=empresa,
                tp_documento=tipo,
                tp_elemento="DOCUMENTO",
                sn_versao_atual=True,
                sn_ativo=True,
            ).order_by("-nr_versao", "pk").first()
            if not modelo:
                modelo = ModeloDocumento.objects.create(
                    cd_empresa=empresa,
                    nm_modelo=nome,
                    tp_documento=tipo,
                    tp_elemento="DOCUMENTO",
                    ds_html_tela=corpo,
                    ds_html_impressao=corpo,
                    sn_exibe_assinatura=True,
                    tp_finalidade_assinatura="MEDICO",
                    sn_sistema=True,
                    sn_editavel=True,
                    sn_versao_atual=True,
                    sn_ativo=True,
                )
            ItemMenu.objects.filter(cd_empresa=empresa, ds_acao=acao).update(
                tp_item="DOCUMENTO",
                cd_modelo_documento=modelo,
            )

    atendimento = Module.objects.filter(code="ATENDIMENTO").first()
    if atendimento:
        grupo, _ = Screen.objects.update_or_create(
            slug="pep-cadastros",
            defaults={
                "module": atendimento,
                "title": "Cadastros",
                "navigation_url": "",
                "icon": "database",
                "roles": ["TI", "Médico"],
                "screen_type": "grupo",
                "parent_label": "PEP",
                "allow_query": False,
                "allow_insert": False,
                "allow_update": False,
                "active": True,
                "order": 80,
            },
        )
        for ordem, titulo, slug, chave, url in (
            (10, "Classes de itens de prescrição", "pep-classes-itens-prescricao", "atendimento:classes-itens-prescricao", "/atendimento/pep/cadastros/classes-itens-prescricao/"),
            (20, "Formas de aplicação", "pep-formas-aplicacao", "atendimento:vias-aplicacao-prescricao", "/atendimento/pep/cadastros/formas-aplicacao/"),
            (30, "Itens de prescrição", "pep-itens-prescricao", "atendimento:itens-prescricao", "/atendimento/pep/cadastros/itens-prescricao/"),
        ):
            Screen.objects.update_or_create(
                slug=slug,
                defaults={
                    "module": atendimento,
                    "parent": grupo,
                    "title": titulo,
                    "access_key": chave,
                    "navigation_url": url,
                    "icon": "circle",
                    "roles": ["TI", "Médico"],
                    "screen_type": "formulario",
                    "parent_label": "PEP",
                    "table_name": slug.replace("pep-", "").replace("-", "_"),
                    "allow_query": True,
                    "allow_insert": True,
                    "allow_update": True,
                    "active": True,
                    "order": ordem,
                },
            )

    almoxarifado = Module.objects.filter(code__in=("ALMOXARIFADO", "ESTOQUE")).order_by("pk").first()
    if almoxarifado:
        Screen.objects.update_or_create(
            slug="farmacia-medicamentos",
            defaults={
                "module": almoxarifado,
                "title": "Medicamentos",
                "access_key": "estoque:medicamentos",
                "navigation_url": "/almoxarifado/farmacia/tabelas/medicamentos/",
                "icon": "pill",
                "roles": ["TI", "Almoxarifado"],
                "screen_type": "formulario",
                "parent_label": "Farmácia > Tabelas",
                "table_name": "produto",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "active": True,
                "order": 10,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0065_classificar_finalidade_assinatura_documentos"),
        ("core", "0060_navegacao_dominios_externos"),
        ("estoque", "0001_estrutura_produtos_consolidada"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="modelodocumento",
            name="tp_documento",
            field=models.CharField(
                choices=[
                    ("COMPROVANTE_AGENDAMENTO", "Comprovante de agendamento"),
                    ("COMPROVANTE_CHAMADO", "Comprovante de chamado"),
                    ("FICHA_CLASSIFICACAO", "Ficha de classificação"),
                    ("FICHA_ATENDIMENTO", "Ficha de atendimento"),
                    ("ETIQUETA_ATENDIMENTO", "Etiqueta de atendimento"),
                    ("PRESCRICAO", "Prescrição"),
                    ("SOLICITACAO_EXAME", "Solicitação de exame"),
                    ("ADMISSAO_ANAMNESE", "Admissão / Anamnese"),
                    ("EVOLUCAO", "Evolução"),
                    ("RESUMO_ALTA", "Resumo de alta"),
                    ("RECEITUARIO", "Receituário"),
                    ("ATESTADO", "Atestado"),
                    ("ENCAMINHAMENTO", "Encaminhamento"),
                    ("AIH", "AIH"),
                    ("ADMINISTRATIVO", "Administrativo"),
                ],
                max_length=40,
            ),
        ),
        migrations.CreateModel(
            name="ClasseItemPrescricao",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_classe_item_prescricao", models.BigAutoField(primary_key=True, serialize=False)),
                ("sg_classe", models.CharField(max_length=8)),
                ("ds_classe", models.CharField(max_length=120)),
                ("tp_classe", models.CharField(choices=[("MEDICAMENTO", "Medicamentos"), ("EXAME", "Exames"), ("OUTRO", "Outros")], max_length=20)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "classe_item_prescricao", "ordering": ("nr_ordem", "ds_classe")},
        ),
        migrations.CreateModel(
            name="ViaAplicacaoPrescricao",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_via_aplicacao_prescricao", models.BigAutoField(primary_key=True, serialize=False)),
                ("sg_via", models.CharField(max_length=8)),
                ("ds_via", models.CharField(max_length=120)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "via_aplicacao_prescricao", "ordering": ("nr_ordem", "ds_via")},
        ),
        migrations.CreateModel(
            name="ItemPrescricao",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_item_prescricao", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_item", models.CharField(max_length=180)),
                ("ds_dose_padrao", models.CharField(blank=True, max_length=80)),
                ("ds_frequencia_padrao", models.CharField(blank=True, max_length=120)),
                ("ds_duracao_padrao", models.CharField(blank=True, max_length=80)),
                ("ds_posologia_padrao", models.CharField(blank=True, max_length=500)),
                ("sn_exige_posologia", models.BooleanField(default=False)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_classe", models.ForeignKey(db_column="cd_classe_item_prescricao", on_delete=django.db.models.deletion.PROTECT, related_name="itens", to="atendimento.classeitemprescricao")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_produto", models.ForeignKey(blank=True, db_column="cd_produto", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="itens_prescricao", to="estoque.produto")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
                ("cd_via_padrao", models.ForeignKey(blank=True, db_column="cd_via_padrao", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="itens_padrao", to="atendimento.viaaplicacaoprescricao")),
            ],
            options={"db_table": "item_prescricao", "ordering": ("cd_classe__nr_ordem", "nm_item")},
        ),
        migrations.CreateModel(
            name="ItemPrescricaoDocumento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_item_prescricao_documento", models.BigAutoField(primary_key=True, serialize=False)),
                ("sn_obrigatorio", models.BooleanField(default=True)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_item_prescricao", models.ForeignKey(db_column="cd_item_prescricao", on_delete=django.db.models.deletion.CASCADE, related_name="documentos_exigidos", to="atendimento.itemprescricao")),
                ("cd_modelo_documento", models.ForeignKey(db_column="cd_modelo_documento", on_delete=django.db.models.deletion.PROTECT, to="atendimento.modelodocumento")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "item_prescricao_documento", "ordering": ("cd_modelo_documento__nm_modelo",)},
        ),
        migrations.CreateModel(
            name="PrescricaoItem",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_prescricao_item", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_dose", models.CharField(blank=True, max_length=80)),
                ("ds_frequencia", models.CharField(blank=True, max_length=120)),
                ("ds_duracao", models.CharField(blank=True, max_length=80)),
                ("ds_posologia", models.CharField(blank=True, max_length=500)),
                ("ds_observacao", models.CharField(blank=True, max_length=500)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_item_prescricao", models.ForeignKey(db_column="cd_item_prescricao", on_delete=django.db.models.deletion.PROTECT, to="atendimento.itemprescricao")),
                ("cd_prescricao", models.ForeignKey(db_column="cd_prescricao", on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="atendimento.prescricao")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
                ("cd_via_aplicacao", models.ForeignKey(blank=True, db_column="cd_via_aplicacao_prescricao", null=True, on_delete=django.db.models.deletion.PROTECT, to="atendimento.viaaplicacaoprescricao")),
            ],
            options={"db_table": "prescricao_item", "ordering": ("nr_ordem", "cd_prescricao_item")},
        ),
        migrations.AddConstraint(model_name="classeitemprescricao", constraint=models.UniqueConstraint(fields=("cd_empresa", "sg_classe"), name="classe_item_prescricao_sigla_unica")),
        migrations.AddConstraint(model_name="viaaplicacaoprescricao", constraint=models.UniqueConstraint(fields=("cd_empresa", "sg_via"), name="via_aplicacao_prescricao_sigla_unica")),
        migrations.AddConstraint(model_name="itemprescricao", constraint=models.UniqueConstraint(fields=("cd_empresa", "cd_classe", "nm_item"), name="item_prescricao_nome_unico_classe")),
        migrations.AddConstraint(model_name="itemprescricaodocumento", constraint=models.UniqueConstraint(fields=("cd_empresa", "cd_item_prescricao", "cd_modelo_documento"), name="item_prescricao_documento_unico")),
        migrations.RunPython(configurar_prescricao_e_documentos, migrations.RunPython.noop),
    ]
