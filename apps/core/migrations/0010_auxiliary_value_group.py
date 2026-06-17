from django.db import migrations, models


CITY_GROUPS = {
    "SAO_PAULO": "SP",
    "RIO_DE_JANEIRO": "RJ",
    "BELO_HORIZONTE": "MG",
    "CURITIBA": "PR",
    "PORTO_ALEGRE": "RS",
    "BRASILIA": "DF",
}


def seed_city_groups(apps, schema_editor):
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    for code, state in CITY_GROUPS.items():
        ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela="cidade",
            cd_valor=code,
        ).update(ds_grupo=state)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_seed_city_state_auxiliary"),
    ]

    operations = [
        migrations.AddField(
            model_name="valorauxiliarglobal",
            name="ds_grupo",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.RunPython(seed_city_groups, migrations.RunPython.noop),
    ]
