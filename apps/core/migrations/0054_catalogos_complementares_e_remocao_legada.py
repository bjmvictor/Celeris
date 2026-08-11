from django.db import migrations, models


def campos_catalogo():
    return [
        ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
        ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
        ("cd_item_catalogo", models.BigAutoField(primary_key=True, serialize=False)),
        ("cd_valor", models.CharField(max_length=40, unique=True)),
        ("ds_valor", models.CharField(max_length=500)),
        ("ds_grupo", models.CharField(blank=True, max_length=160)),
        ("sn_ativo", models.BooleanField(default=True)),
    ]


def copiar_catalogos_complementares(apps, schema_editor):
    modelos_por_tema = {
        "feriado": "Feriado",
        "plano": "Plano",
        "procedimento": "Procedimento",
        "sala": "Sala",
        "tipo_atendimento": "TipoAtendimento",
        "tipo_escala": "TipoEscala",
    }
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    valores = ValorAuxiliarGlobal.objects.select_related("cd_tabela_auxiliar_global")
    for valor in valores.iterator():
        nome_modelo = modelos_por_tema.get(valor.cd_tabela_auxiliar_global.ds_tabela)
        if not nome_modelo:
            continue
        modelo = apps.get_model("core", nome_modelo)
        modelo.objects.update_or_create(
            cd_valor=valor.cd_valor,
            defaults={
                "ds_valor": valor.ds_valor,
                "ds_grupo": valor.ds_grupo,
                "sn_ativo": valor.sn_ativo,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0056_migrar_motivos_para_catalogo_tematico"),
        ("core", "0053_separar_catalogos_tematicos"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feriado",
            fields=campos_catalogo(),
            options={"db_table": "feriados", "ordering": ("ds_valor",)},
        ),
        migrations.CreateModel(
            name="Plano",
            fields=campos_catalogo(),
            options={"db_table": "planos", "ordering": ("ds_valor",)},
        ),
        migrations.CreateModel(
            name="Procedimento",
            fields=campos_catalogo(),
            options={"db_table": "procedimentos", "ordering": ("ds_valor",)},
        ),
        migrations.CreateModel(
            name="Sala",
            fields=campos_catalogo(),
            options={"db_table": "salas", "ordering": ("ds_valor",)},
        ),
        migrations.CreateModel(
            name="TipoAtendimento",
            fields=campos_catalogo(),
            options={"db_table": "tipos_atendimento", "ordering": ("ds_valor",)},
        ),
        migrations.CreateModel(
            name="TipoEscala",
            fields=campos_catalogo(),
            options={"db_table": "tipos_escala", "ordering": ("ds_valor",)},
        ),
        migrations.RunPython(copiar_catalogos_complementares, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="valorauxiliarglobal",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="valorauxiliarglobal",
            name="cd_tabela_auxiliar_global",
        ),
        migrations.DeleteModel(name="TabelaAuxiliarGlobal"),
        migrations.DeleteModel(name="ValorAuxiliarGlobal"),
    ]
