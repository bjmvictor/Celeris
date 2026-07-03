from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import apps.core.validators


def seed_auxiliares(apps, schema_editor):
    Tabela = apps.get_model("core", "TabelaAuxiliarGlobal")
    Valor = apps.get_model("core", "ValorAuxiliarGlobal")
    dados = {
        "local_procedencia": (
            "Locais de procedência do paciente",
            (("DOMICILIO", "Domicílio"), ("OUTRA_UNIDADE", "Outra unidade hospitalar")),
        ),
        "destino_atendimento": (
            "Destinos iniciais do atendimento",
            (("CONSULTORIO", "Consultório"), ("SALA", "Sala"), ("OBSERVACAO", "Observação")),
        ),
        "meio_transporte": (
            "Meios de transporte do paciente",
            (("PROPRIO", "Meios próprios"), ("AMBULANCIA", "Ambulância"), ("CADEIRA_RODAS", "Cadeira de rodas"), ("MACA", "Maca")),
        ),
        "origem_recepcao": (
            "Recepções de origem do atendimento",
            (("RECEPCAO_PRINCIPAL", "Recepção principal"),),
        ),
        "parentesco": (
            "Parentescos de responsáveis",
            (("MAE", "Mãe"), ("PAI", "Pai"), ("CONJUGE", "Cônjuge"), ("FILHO", "Filho(a)"), ("OUTRO", "Outro")),
        ),
    }
    for nome, (descricao, valores) in dados.items():
        tabela, _ = Tabela.objects.get_or_create(
            ds_tabela=nome,
            defaults={"ds_descricao": descricao, "sn_ativo": True},
        )
        for codigo, valor in valores:
            Valor.objects.get_or_create(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=codigo,
                defaults={"ds_valor": valor, "sn_ativo": True},
            )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0011_setor_setorusuario"),
        ("core", "0023_seed_minimum_test_auxiliary_values"),
        ("atendimento", "0026_documentoclinico_ds_dados_formulario_and_more"),
    ]

    operations = [
        migrations.AddField(model_name="atendimento", name="ds_cbo_prestador", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="atendimento", name="ds_cid", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="atendimento", name="ds_local_procedencia", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="atendimento", name="ds_meio_transporte", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="atendimento", name="ds_recepcao_origem", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="atendimento", name="ds_subplano", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="atendimento", name="nr_senha_chamada", field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name="atendimento", name="sn_retorno", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="atendimento", name="sn_visita", field=models.BooleanField(default=False)),
        migrations.CreateModel(
            name="ResponsavelAtendimento",
            fields=[
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_responsavel_atendimento", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_parentesco", models.CharField(blank=True, max_length=80)),
                ("nm_responsavel", models.CharField(blank=True, max_length=160)),
                ("tp_estado_civil", models.CharField(blank=True, max_length=80)),
                ("nr_identidade", models.CharField(blank=True, max_length=30)),
                ("ds_orgao_emissor", models.CharField(blank=True, max_length=30)),
                ("dt_expedicao", models.DateField(blank=True, null=True)),
                ("nr_cpf", models.CharField(blank=True, max_length=14, validators=[apps.core.validators.validate_cpf])),
                ("ds_profissao", models.CharField(blank=True, max_length=120)),
                ("ds_nacionalidade", models.CharField(blank=True, max_length=120)),
                ("nr_celular", models.CharField(blank=True, max_length=20)),
                ("sn_mesmo_endereco_paciente", models.BooleanField(default=False)),
                ("sg_estado", models.CharField(blank=True, max_length=2)),
                ("ds_cidade", models.CharField(blank=True, max_length=120)),
                ("tp_logradouro", models.CharField(blank=True, max_length=80)),
                ("ds_endereco", models.CharField(blank=True, max_length=180)),
                ("nr_endereco", models.CharField(blank=True, max_length=20)),
                ("ds_complemento", models.CharField(blank=True, max_length=120)),
                ("ds_bairro", models.CharField(blank=True, max_length=120)),
                ("cd_atendimento", models.OneToOneField(db_column="cd_atendimento", on_delete=django.db.models.deletion.CASCADE, related_name="responsavel", to="atendimento.atendimento")),
                ("cd_cep", models.ForeignKey(blank=True, db_column="cd_cep", null=True, on_delete=django.db.models.deletion.PROTECT, to="core.cep")),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "responsavel_atendimento"},
        ),
        migrations.RunPython(seed_auxiliares, migrations.RunPython.noop),
    ]
