"""Operações históricas de dados da migration 0010."""

from django.db import migrations, models

from apps.core.operacoes_migracao.municipios_ibge import MUNICIPIOS


def seed_cities(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    tabela_cidade, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="cidade",
        defaults={
            "ds_descricao": "Cidade",
            "sn_ativo": True,
        },
    )

    codigos_existentes = set(
        ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global=tabela_cidade,
        ).values_list("cd_valor", flat=True)
    )

    novas_cidades = [
        ValorAuxiliarGlobal(
            cd_tabela_auxiliar_global=tabela_cidade,
            cd_valor=codigo_ibge,
            ds_valor=nome,
            ds_grupo=uf,
            sn_ativo=True,
        )
        for codigo_ibge, nome, uf in MUNICIPIOS
        if codigo_ibge not in codigos_existentes
    ]

    ValorAuxiliarGlobal.objects.bulk_create(
        novas_cidades,
        batch_size=500,
    )


def unseed_cities(apps, schema_editor):
    TabelaAuxiliarGlobal = apps.get_model(
        "core",
        "TabelaAuxiliarGlobal",
    )
    ValorAuxiliarGlobal = apps.get_model(
        "core",
        "ValorAuxiliarGlobal",
    )

    tabela_cidade = TabelaAuxiliarGlobal.objects.filter(
        ds_tabela="cidade",
    ).first()

    if tabela_cidade is None:
        return

    codigos_ibge = [
        codigo_ibge
        for codigo_ibge, _, _ in MUNICIPIOS
    ]

    ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global=tabela_cidade,
        cd_valor__in=codigos_ibge,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_seed_states_auxiliary"),
    ]

    operations = [
        migrations.AddField(
            model_name="valorauxiliarglobal",
            name="ds_grupo",
            field=models.CharField(
                blank=True,
                default="",
                max_length=160,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(
            seed_cities,
            unseed_cities,
        ),
    ]