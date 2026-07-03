import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0037_totem_senhas"),
    ]

    operations = [
        migrations.AddField(
            model_name="tiposenhaatendimento",
            name="cd_setor_atendimento",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_setor_atendimento",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tipos_senha",
                to="accounts.setor",
            ),
        ),
        migrations.AlterField(
            model_name="senhaatendimento",
            name="ds_status",
            field=models.CharField(
                choices=[
                    ("AGUARDANDO", "Aguardando"),
                    ("CHAMADA", "Chamada"),
                    ("EM_CLASSIFICACAO", "Em classificação"),
                    ("CLASSIFICADA", "Classificada"),
                    ("RECEPCIONADA", "Recepcionada"),
                    ("CANCELADA", "Cancelada"),
                ],
                default="AGUARDANDO",
                max_length=24,
            ),
        ),
        migrations.AlterField(
            model_name="chamadapainel",
            name="cd_atendimento",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_atendimento",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="chamadas_painel",
                to="atendimento.atendimento",
            ),
        ),
        migrations.AlterField(
            model_name="chamadapainel",
            name="cd_setor",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_setor",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="accounts.setor",
            ),
        ),
        migrations.AddField(
            model_name="chamadapainel",
            name="cd_senha_atendimento",
            field=models.ForeignKey(
                blank=True,
                db_column="cd_senha_atendimento",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="chamadas_painel",
                to="atendimento.senhaatendimento",
            ),
        ),
    ]
