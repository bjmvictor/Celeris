from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estoque", "0001_estrutura_produtos_consolidada"),
    ]

    operations = [
        migrations.AddField(
            model_name="estoque",
            name="sn_controla_lote_validade",
            field=models.BooleanField(default=True, verbose_name="controla lote e validade"),
        ),
        migrations.AddField(
            model_name="estoque",
            name="sn_saida_fornecedor",
            field=models.BooleanField(default=False, verbose_name="permite devolução para fornecedor"),
        ),
        migrations.AddField(
            model_name="estoque",
            name="sn_saida_gasto_sala",
            field=models.BooleanField(default=True, verbose_name="permite gasto de sala"),
        ),
        migrations.AddField(
            model_name="estoque",
            name="sn_saida_paciente",
            field=models.BooleanField(default=True, verbose_name="permite saída para paciente"),
        ),
        migrations.AddField(
            model_name="estoque",
            name="sn_saida_setor",
            field=models.BooleanField(default=True, verbose_name="permite saída para setor"),
        ),
        migrations.AddField(
            model_name="estoque",
            name="sn_transferencia",
            field=models.BooleanField(default=True, verbose_name="permite transferência entre estoques"),
        ),
    ]
