from django.db import migrations, models
import django.db.models.deletion
import apps.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0017_patient_provider_review"),
        ("accounts", "0006_empresa_cd_usuario_atualizacao_and_more"),
    ]

    operations = [
        migrations.AddField(model_name="user", name="can_change_patient", field=models.BooleanField(default=False, verbose_name="altera paciente")),
        migrations.AddField(model_name="user", name="can_configure_system", field=models.BooleanField(default=False, verbose_name="configura sistema")),
        migrations.AddField(model_name="user", name="can_create_users", field=models.BooleanField(default=False, verbose_name="cria usuários")),
        migrations.AddField(model_name="user", name="can_deactivate_users", field=models.BooleanField(default=False, verbose_name="desativa usuários")),
        migrations.AddField(model_name="user", name="can_manage_auxiliary_tables", field=models.BooleanField(default=False, verbose_name="gerencia tabelas auxiliares")),
        migrations.AddField(model_name="user", name="can_register_patient", field=models.BooleanField(default=False, verbose_name="cadastra paciente")),
        migrations.AddField(
            model_name="user",
            name="cd_prestador",
            field=models.ForeignKey(blank=True, db_column="cd_prestador", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="usuarios", to="atendimento.prestador"),
        ),
        migrations.AddField(model_name="user", name="ds_idioma", field=models.CharField(blank=True, max_length=40, verbose_name="idioma")),
        migrations.AddField(model_name="user", name="ds_profissao", field=models.CharField(blank=True, max_length=120, verbose_name="profissão")),
        migrations.AddField(model_name="user", name="dt_nascimento", field=models.DateField(blank=True, null=True, verbose_name="data de nascimento")),
        migrations.AddField(model_name="user", name="invalid_login_attempts", field=models.PositiveIntegerField(default=0, verbose_name="tentativas inválidas")),
        migrations.AddField(model_name="user", name="is_blocked", field=models.BooleanField(default=False, verbose_name="usuário bloqueado")),
        migrations.AddField(model_name="user", name="nr_celular", field=models.CharField(blank=True, max_length=30, verbose_name="celular")),
        migrations.AddField(model_name="user", name="nr_cpf", field=models.CharField(blank=True, max_length=14, validators=[apps.core.validators.validate_cpf], verbose_name="CPF")),
        migrations.AddField(model_name="user", name="nr_matricula_rh", field=models.CharField(blank=True, max_length=40, verbose_name="matrícula RH")),
        migrations.AddField(model_name="user", name="password_expires_at", field=models.DateTimeField(blank=True, null=True, verbose_name="senha expira em")),
    ]
