from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("atendimento", "0019_atendimento_central"),
    ]

    operations = [
        migrations.AddField(
            model_name="painelchamada",
            name="ds_descricao",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_local_exibicao",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_mensagem_padrao",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="nr_tempo_exibicao",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_prioridade_visual",
            field=models.CharField(default="normal", max_length=30),
        ),
        migrations.AddField(
            model_name="painelchamada",
            name="ds_observacao",
            field=models.TextField(blank=True),
        ),
    ]
