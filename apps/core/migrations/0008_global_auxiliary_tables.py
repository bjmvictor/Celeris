from django.db import migrations, models
import django.db.models.deletion


TABLES = {
    "tipo_sanguineo": [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ],
    "sexo": [
        ("F", "FEMININO"),
        ("M", "MASCULINO"),
        ("I", "INTERSEXO"),
        ("N", "NÃO INFORMADO"),
    ],
    "estado_civil": [
        ("SOLTEIRO", "SOLTEIRO(A)"),
        ("CASADO", "CASADO(A)"),
        ("DIVORCIADO", "DIVORCIADO(A)"),
        ("VIUVO", "VIÚVO(A)"),
        ("UNIAO_ESTAVEL", "UNIÃO ESTÁVEL"),
        ("NAO_INFORMADO", "NÃO INFORMADO"),
    ],
    "naturalidade": [
        ("BRASILEIRA", "BRASILEIRA"),
        ("ESTRANGEIRA", "ESTRANGEIRA"),
    ],
    "nacionalidade": [
        ("BRASILEIRA", "BRASILEIRA"),
        ("ESTRANGEIRA", "ESTRANGEIRA"),
    ],
    "motivo_alteracao": [
        ("CORRECAO_CADASTRAL", "CORREÇÃO CADASTRAL"),
        ("ATUALIZACAO_DOCUMENTAL", "ATUALIZAÇÃO DOCUMENTAL"),
        ("SOLICITACAO_PACIENTE", "SOLICITAÇÃO DO PACIENTE"),
        ("REVISAO_ATENDIMENTO", "REVISÃO DE ATENDIMENTO"),
        ("OUTROS", "OUTROS"),
    ],
}


def seed_global_auxiliary(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    descriptions = {
        "tipo_sanguineo": "Tipos sanguíneos",
        "sexo": "Sexos",
        "estado_civil": "Estados civis",
        "naturalidade": "Naturalidades",
        "nacionalidade": "Nacionalidades",
        "motivo_alteracao": "Motivos de alteração cadastral",
    }
    for table_name, values in TABLES.items():
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=table_name,
            defaults={"ds_descricao": descriptions[table_name], "sn_ativo": True},
        )
        for code, description in values:
            ValorAuxiliarGlobal.objects.get_or_create(
                cd_tabela_auxiliar_global=table,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_screenfield_lookup"),
    ]

    operations = [
        migrations.CreateModel(
            name="TabelaAuxiliarGlobal",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("cd_tabela_auxiliar_global", models.BigAutoField(primary_key=True, serialize=False)),
                ("ds_tabela", models.CharField(max_length=120, unique=True)),
                ("ds_descricao", models.CharField(blank=True, max_length=220)),
                ("sn_ativo", models.BooleanField(default=True)),
            ],
            options={"db_table": "tabela_auxiliar_global", "ordering": ("ds_tabela",)},
        ),
        migrations.CreateModel(
            name="ValorAuxiliarGlobal",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("cd_valor_auxiliar_global", models.BigAutoField(primary_key=True, serialize=False)),
                ("cd_valor", models.CharField(max_length=40)),
                ("ds_valor", models.CharField(max_length=160)),
                ("sn_ativo", models.BooleanField(default=True)),
                (
                    "cd_tabela_auxiliar_global",
                    models.ForeignKey(
                        db_column="cd_tabela_auxiliar_global",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="valores",
                        to="core.tabelaauxiliarglobal",
                    ),
                ),
            ],
            options={
                "db_table": "valor_auxiliar_global",
                "ordering": ("cd_tabela_auxiliar_global__ds_tabela", "ds_valor"),
                "unique_together": {("cd_tabela_auxiliar_global", "cd_valor")},
            },
        ),
        migrations.RunPython(seed_global_auxiliary, migrations.RunPython.noop),
    ]
