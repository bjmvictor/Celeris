from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrar_escalas_recomendadas_legadas(apps, schema_editor):
    Fluxo = apps.get_model("atendimento", "FluxoClassificacao")
    Escala = apps.get_model("atendimento", "EscalaClinica")
    Vinculo = apps.get_model("atendimento", "FluxoClassificacaoEscala")
    for fluxo in Fluxo.objects.all().iterator():
        configuracao = fluxo.ds_configuracao if isinstance(fluxo.ds_configuracao, dict) else {}
        escala_id = str(configuracao.get("escala_id") or "")
        if not escala_id.isdigit():
            continue
        escala = Escala.objects.filter(cd_empresa_id=fluxo.cd_empresa_id, pk=int(escala_id)).first()
        if escala:
            Vinculo.objects.get_or_create(
                cd_empresa_id=fluxo.cd_empresa_id,
                cd_fluxo_classificacao_id=fluxo.pk,
                cd_escala_clinica_id=escala.pk,
                defaults={"nr_ordem": 10, "sn_ativo": True},
            )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0059_ficha_classificacao_documento"),
    ]

    operations = [
        migrations.CreateModel(
            name="FluxoClassificacaoEscala",
            fields=[
                ("cd_fluxo_classificacao_escala", models.BigAutoField(primary_key=True, serialize=False)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_escala_clinica", models.ForeignKey(db_column="cd_escala_clinica", on_delete=django.db.models.deletion.PROTECT, related_name="fluxos_recomendados", to="atendimento.escalaclinica")),
                ("cd_fluxo_classificacao", models.ForeignKey(db_column="cd_fluxo_classificacao", on_delete=django.db.models.deletion.CASCADE, related_name="escalas_recomendadas", to="atendimento.fluxoclassificacao")),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "fluxo_classificacao_escala",
                "ordering": ("nr_ordem", "cd_fluxo_classificacao_escala"),
                "constraints": [
                    models.UniqueConstraint(fields=("cd_empresa", "cd_fluxo_classificacao", "cd_escala_clinica"), name="fluxo_classificacao_escala_unica"),
                ],
            },
        ),
        migrations.RunPython(migrar_escalas_recomendadas_legadas, migrations.RunPython.noop),
    ]
