from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0054_subdivisoes_protocolos_e_catalogo_classificacao")]
    operations = [
        migrations.AddField(
            model_name="perguntaclassificacao",
            name="sn_obrigatoria",
            field=models.BooleanField(default=False),
        ),
    ]
