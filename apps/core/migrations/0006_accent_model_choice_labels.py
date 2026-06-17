from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_accent_screen_labels"),
    ]

    operations = [
        migrations.AlterField(
            model_name="screendefinition",
            name="screen_type",
            field=models.CharField(
                choices=[
                    ("formulario", "Formulário"),
                    ("relatorio", "Relatório"),
                    ("dashboard", "Dashboard"),
                    ("consulta", "Consulta"),
                    ("wizard", "Wizard"),
                    ("fila", "Fila"),
                    ("documento", "Documento"),
                    ("configuracao", "Configuração"),
                ],
                default="formulario",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="screenfield",
            name="choices",
            field=models.TextField(blank=True, help_text="Uma opção por linha para campos de seleção."),
        ),
        migrations.AlterField(
            model_name="screenfield",
            name="field_type",
            field=models.CharField(
                choices=[
                    ("text", "Texto"),
                    ("number", "Número"),
                    ("date", "Data"),
                    ("select", "Seleção"),
                    ("textarea", "Texto longo"),
                    ("checkbox", "Checkbox"),
                ],
                default="text",
                max_length=20,
            ),
        ),
    ]
