from django.db import migrations, models
import django.db.models.deletion


def seed_default_company(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    UsuarioEmpresa = apps.get_model("accounts", "UsuarioEmpresa")
    User = apps.get_model("accounts", "User")
    empresa, _ = Empresa.objects.update_or_create(
        cd_empresa=1,
        defaults={
            "nm_empresa": "Celeris",
            "ds_razao_social": "Celeris",
            "ds_nome_fantasia": "Celeris",
            "sn_ativo": True,
        },
    )
    for user in User.objects.all():
        UsuarioEmpresa.objects.get_or_create(
            usuario=user,
            empresa=empresa,
            defaults={"sn_padrao": True, "sn_ativo": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
            fields=[
                ("cd_empresa", models.PositiveIntegerField(primary_key=True, serialize=False, verbose_name="codigo")),
                ("nm_empresa", models.CharField(max_length=180, verbose_name="nome")),
                ("nr_cnpj", models.CharField(blank=True, max_length=18, verbose_name="CNPJ")),
                ("ds_razao_social", models.CharField(blank=True, max_length=220, verbose_name="razao social")),
                ("ds_nome_fantasia", models.CharField(blank=True, max_length=180, verbose_name="nome fantasia")),
                ("ds_email", models.EmailField(blank=True, max_length=254, verbose_name="email")),
                ("nr_telefone", models.CharField(blank=True, max_length=30, verbose_name="telefone")),
                ("ds_endereco", models.CharField(blank=True, max_length=220, verbose_name="endereco")),
                ("nr_endereco", models.CharField(blank=True, max_length=20, verbose_name="numero")),
                ("ds_bairro", models.CharField(blank=True, max_length=120, verbose_name="bairro")),
                ("ds_cidade", models.CharField(blank=True, max_length=120, verbose_name="cidade")),
                ("sg_estado", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("nr_cep", models.CharField(blank=True, max_length=10, verbose_name="CEP")),
                ("sn_ativo", models.BooleanField(default=True, verbose_name="ativo")),
            ],
            options={"ordering": ("cd_empresa",)},
        ),
        migrations.CreateModel(
            name="UsuarioEmpresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sn_padrao", models.BooleanField(default=False, verbose_name="padrao")),
                ("sn_ativo", models.BooleanField(default=True, verbose_name="ativo")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.empresa")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.user")),
            ],
            options={"ordering": ("usuario__username", "empresa__cd_empresa"), "unique_together": {("usuario", "empresa")}},
        ),
        migrations.AddField(
            model_name="user",
            name="empresas",
            field=models.ManyToManyField(blank=True, related_name="usuarios", through="accounts.UsuarioEmpresa", to="accounts.empresa"),
        ),
        migrations.RunPython(seed_default_company, migrations.RunPython.noop),
    ]
