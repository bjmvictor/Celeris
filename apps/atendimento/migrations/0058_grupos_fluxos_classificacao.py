from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def criar_grupos_fluxos(apps, schema_editor):
    Fluxo = apps.get_model("atendimento", "FluxoClassificacao")
    Grupo = apps.get_model("atendimento", "GrupoFluxoClassificacao")
    grupos = {}
    for fluxo in Fluxo.objects.all().order_by("cd_empresa_id", "nm_grupo", "nr_ordem"):
        chave = (fluxo.cd_empresa_id, fluxo.nm_grupo.strip())
        grupo = grupos.get(chave)
        if grupo is None:
            grupo, _ = Grupo.objects.get_or_create(
                cd_empresa_id=fluxo.cd_empresa_id,
                nm_grupo=chave[1],
                defaults={"nr_ordem": fluxo.nr_ordem, "sn_ativo": True},
            )
            grupos[chave] = grupo
        fluxo.cd_grupo_id = grupo.pk
        fluxo.save(update_fields=["cd_grupo"])


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0057_condicoes_calculo_escala"),
    ]

    operations = [
        migrations.CreateModel(
            name="GrupoFluxoClassificacao",
            fields=[
                ("cd_grupo_fluxo_classificacao", models.BigAutoField(primary_key=True, serialize=False)),
                ("nm_grupo", models.CharField(max_length=100)),
                ("ds_descricao", models.CharField(blank=True, max_length=300)),
                ("nr_ordem", models.PositiveSmallIntegerField(default=10)),
                ("sn_ativo", models.BooleanField(default=True)),
                ("dh_criacao", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ("dh_atualizacao", models.DateTimeField(auto_now=True)),
                ("cd_empresa", models.ForeignKey(db_column="cd_empresa", on_delete=django.db.models.deletion.PROTECT, to="accounts.empresa")),
                ("cd_usuario_criacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_criados", to=settings.AUTH_USER_MODEL)),
                ("cd_usuario_atualizacao", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_atualizados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "grupo_fluxo_classificacao",
                "ordering": ("nr_ordem", "nm_grupo"),
                "unique_together": {("cd_empresa", "nm_grupo")},
            },
        ),
        migrations.AddField(
            model_name="fluxoclassificacao",
            name="cd_grupo",
            field=models.ForeignKey(blank=True, db_column="cd_grupo_fluxo_classificacao", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="sintomas", to="atendimento.grupofluxoclassificacao"),
        ),
        migrations.RunPython(criar_grupos_fluxos, migrations.RunPython.noop),
    ]
