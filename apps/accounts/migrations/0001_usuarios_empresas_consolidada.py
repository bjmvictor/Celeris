import apps.core.validators
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.migrations.operations.special
import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0002 = import_module("apps.accounts.migrations.0002_empresa_usuarioempresa")
migracao_0003 = import_module("apps.accounts.migrations.0003_normalize_existing_usernames")

class Migration(migrations.Migration):

    replaces = [('accounts', '0001_initial'), ('accounts', '0002_empresa_usuarioempresa'), ('accounts', '0003_normalize_existing_usernames'), ('accounts', '0004_alter_user_groups_alter_user_is_active'), ('accounts', '0005_alter_user_options_alter_empresa_table_and_more'), ('accounts', '0006_empresa_cd_usuario_atualizacao_and_more')]

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('full_name', models.CharField(blank=True, max_length=180, verbose_name='nome completo')),
                ('is_coordinator', models.BooleanField(default=False, verbose_name='coordenador')),
                ('must_change_password', models.BooleanField(default=False, verbose_name='alterar senha')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('cd_empresa', models.PositiveIntegerField(primary_key=True, serialize=False, verbose_name='codigo')),
                ('nm_empresa', models.CharField(max_length=180, verbose_name='nome')),
                ('nr_cnpj', models.CharField(blank=True, max_length=18, verbose_name='CNPJ')),
                ('ds_razao_social', models.CharField(blank=True, max_length=220, verbose_name='razao social')),
                ('ds_nome_fantasia', models.CharField(blank=True, max_length=180, verbose_name='nome fantasia')),
                ('ds_email', models.EmailField(blank=True, max_length=254, verbose_name='email')),
                ('nr_telefone', models.CharField(blank=True, max_length=30, verbose_name='telefone')),
                ('ds_endereco', models.CharField(blank=True, max_length=220, verbose_name='endereco')),
                ('nr_endereco', models.CharField(blank=True, max_length=20, verbose_name='numero')),
                ('ds_bairro', models.CharField(blank=True, max_length=120, verbose_name='bairro')),
                ('ds_cidade', models.CharField(blank=True, max_length=120, verbose_name='cidade')),
                ('sg_estado', models.CharField(blank=True, max_length=2, verbose_name='UF')),
                ('nr_cep', models.CharField(blank=True, max_length=10, verbose_name='CEP')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
            ],
            options={
                'ordering': ('cd_empresa',),
            },
        ),
        migrations.CreateModel(
            name='UsuarioEmpresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sn_padrao', models.BooleanField(default=False, verbose_name='padrao')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('usuario__username', 'empresa__cd_empresa'),
                'unique_together': {('usuario', 'empresa')},
            },
        ),
        migrations.AddField(
            model_name='user',
            name='empresas',
            field=models.ManyToManyField(blank=True, related_name='usuarios', through='accounts.UsuarioEmpresa', to='accounts.empresa'),
        ),
        migrations.RunPython(
            code=migracao_0002.seed_default_company,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0003.normalize_usernames,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active'),
        ),
        migrations.AlterModelOptions(
            name='user',
            options={},
        ),
        migrations.AlterModelTable(
            name='empresa',
            table='empresa',
        ),
        migrations.AlterModelTable(
            name='user',
            table='usuario',
        ),
        migrations.AlterModelTable(
            name='usuarioempresa',
            table='usuario_empresa',
        ),
        migrations.AddField(
            model_name='empresa',
            name='cd_usuario_atualizacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='empresas_atualizadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='empresa',
            name='cd_usuario_criacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='empresas_criadas', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='empresa',
            name='dh_atualizacao',
            field=models.DateTimeField(auto_now=True, verbose_name='data de alteração'),
        ),
        migrations.AddField(
            model_name='empresa',
            name='dh_criacao',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='data de criação'),
        ),
        migrations.AddField(
            model_name='empresa',
            name='nr_cnes',
            field=models.CharField(blank=True, max_length=7, validators=[apps.core.validators.validate_cnes], verbose_name='CNES'),
        ),
    ]
