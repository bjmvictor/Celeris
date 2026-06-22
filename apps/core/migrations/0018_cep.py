from django.db import migrations, models


def migrate_auxiliary_ceps(apps, schema_editor):
    Cep = apps.get_model("core", "Cep")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    values = ValorAuxiliarGlobal.objects.filter(cd_tabela_auxiliar_global__ds_tabela="cep")
    for value in values.iterator():
        parts = (value.ds_grupo or "").split("|")
        digits = "".join(character for character in value.cd_valor if character.isdigit())[:8]
        if not digits:
            continue
        Cep.objects.update_or_create(
            nr_cep=digits,
            defaults={
                "sg_estado": parts[0] if parts else "",
                "cd_cidade": parts[1] if len(parts) > 1 else "",
                "ds_cidade": parts[1] if len(parts) > 1 else "",
                "ds_logradouro": value.ds_valor,
                "sn_ativo": value.sn_ativo,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_seed_global_usability_tables"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cep",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="atualizado em")),
                ("cd_cep", models.BigAutoField(primary_key=True, serialize=False)),
                ("nr_cep", models.CharField(max_length=8, unique=True)),
                ("sg_estado", models.CharField(blank=True, max_length=2)),
                ("cd_cidade", models.CharField(blank=True, max_length=40)),
                ("ds_cidade", models.CharField(blank=True, max_length=160)),
                ("tp_logradouro", models.CharField(blank=True, max_length=40)),
                ("ds_logradouro", models.CharField(blank=True, max_length=220)),
                ("ds_bairro", models.CharField(blank=True, max_length=160)),
                ("sn_ativo", models.BooleanField(default=True)),
            ],
            options={"db_table": "cep", "ordering": ("nr_cep",)},
        ),
        migrations.RunPython(migrate_auxiliary_ceps, migrations.RunPython.noop),
    ]
