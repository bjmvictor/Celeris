import django.db.models.deletion
from django.db import migrations, models


def migrar_motivos_historicos(apps, schema_editor):
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")
    MotivoAlteracao = apps.get_model("core", "MotivoAlteracao")
    HistoricoPaciente = apps.get_model("atendimento", "HistoricoAlteracaoPaciente")
    HistoricoAtendimento = apps.get_model("atendimento", "HistoricoAlteracaoAtendimento")

    motivos_legados = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="motivo_alteracao"
    )
    for motivo_legado in motivos_legados.iterator():
        motivo_novo, _ = MotivoAlteracao.objects.update_or_create(
            cd_valor=motivo_legado.cd_valor,
            defaults={
                "ds_valor": motivo_legado.ds_valor,
                "ds_grupo": motivo_legado.ds_grupo,
                "sn_ativo": motivo_legado.sn_ativo,
            },
        )
        HistoricoPaciente.objects.filter(
            cd_motivo_alteracao_id=motivo_legado.pk
        ).update(cd_motivo_alteracao_id=motivo_novo.pk)
        HistoricoAtendimento.objects.filter(
            cd_motivo_alteracao_id=motivo_legado.pk
        ).update(cd_motivo_alteracao_id=motivo_novo.pk)


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0055_pergunta_classificacao_obrigatoria"),
        ("core", "0053_separar_catalogos_tematicos"),
    ]

    operations = [
        migrations.RunPython(migrar_motivos_historicos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="historicoalteracaoatendimento",
            name="cd_motivo_alteracao",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_motivo_alteracao",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.motivoalteracao",
            ),
        ),
        migrations.AlterField(
            model_name="historicoalteracaopaciente",
            name="cd_motivo_alteracao",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_motivo_alteracao",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.motivoalteracao",
            ),
        ),
    ]
