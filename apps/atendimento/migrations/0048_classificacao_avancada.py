from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def criar_perguntas_padrao(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Pergunta = apps.get_model("atendimento", "PerguntaClassificacao")
    perguntas = (
        ("Paciente admitido diretamente na sala de estabilização?", "SIM_NAO", 10),
        ("Paciente reclassificado após permanência superior a 24 horas?", "SIM_NAO", 20),
        ("Possui alergias conhecidas?", "SIM_NAO", 30),
        ("Utiliza medicamento contínuo?", "SIM_NAO", 40),
        ("Está com dor?", "SIM_NAO", 50),
    )
    for empresa in Empresa.objects.all():
        for nome, tipo, ordem in perguntas:
            Pergunta.objects.get_or_create(
                cd_empresa=empresa,
                nm_pergunta=nome,
                defaults={
                    "tp_resposta": tipo,
                    "nr_ordem": ordem,
                    "sn_padrao": True,
                    "sn_editavel": False,
                    "sn_ativo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0047_cores_e_pre_cadastro_classificacao"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="chamadapainel",
            name="cd_agendamento",
            field=models.ForeignKey(blank=True, db_column="cd_agendamento", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="chamadas_painel", to="atendimento.agendamento"),
        ),
        migrations.AddField(
            model_name="protocolosenhaatendimento",
            name="sg_protocolo",
            field=models.CharField(blank=True, max_length=8),
        ),
        migrations.AddField(
            model_name="regrasubdivisaosenha",
            name="cd_icone_chamada",
            field=models.ForeignKey(blank=True, db_column="cd_icone_chamada", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="regras_subdivisao", to="atendimento.iconechamada"),
        ),
        migrations.AddField(
            model_name="regrasubdivisaosenha",
            name="sg_regra",
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="cd_atendimento",
            field=models.ForeignKey(blank=True, db_column="cd_atendimento", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="senhas_classificacao", to="atendimento.atendimento"),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="nr_chamadas",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="senhaatendimento",
            name="tp_sexo_pre_cadastro",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.CreateModel(
            name="PerguntaClassificacao",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_pergunta_classificacao", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_pergunta", models.CharField(max_length=240)),
                ("tp_resposta", models.CharField(choices=[("SIM_NAO", "Sim/Não"), ("TEXTO", "Texto"), ("NUMERO", "Número")], default="SIM_NAO", max_length=20)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_padrao", models.BooleanField(default=False)),
                ("sn_editavel", models.BooleanField(default=True)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "pergunta_classificacao", "ordering": ("nr_ordem", "nm_pergunta")},
        ),
        migrations.CreateModel(
            name="FluxoClassificacao",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_fluxo_classificacao", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_grupo", models.CharField(max_length=100)),
                ("nm_fluxo", models.CharField(max_length=160)),
                ("ds_orientacao", models.TextField(blank=True)),
                ("ds_configuracao", models.JSONField(blank=True, default=dict)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("cd_cor_recomendada", models.ForeignKey(blank=True, db_column="cd_cor_recomendada", null=True, on_delete=django.db.models.deletion.SET_NULL, to="atendimento.corclassificacaorisco")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "fluxo_classificacao", "ordering": ("nm_grupo", "nr_ordem", "nm_fluxo")},
        ),
        migrations.RunPython(criar_perguntas_padrao, migrations.RunPython.noop),
    ]
