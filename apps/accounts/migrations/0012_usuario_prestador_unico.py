from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_setor_setorusuario"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("cd_prestador__isnull", False)),
                fields=("cd_prestador",),
                name="usuario_prestador_unico",
            ),
        ),
    ]
