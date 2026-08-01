import django.db.migrations.operations.special
import django.db.models.deletion
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0002 = import_module("apps.core.operacoes_migracao.operacao_0002")
migracao_0003 = import_module("apps.core.operacoes_migracao.operacao_0003")
migracao_0004 = import_module("apps.core.operacoes_migracao.operacao_0004")
migracao_0005 = import_module("apps.core.operacoes_migracao.operacao_0005")
migracao_0008 = import_module("apps.core.operacoes_migracao.operacao_0008")
migracao_0009 = import_module("apps.core.operacoes_migracao.operacao_0009")
migracao_0010 = import_module("apps.core.operacoes_migracao.operacao_0010")
migracao_0011 = import_module("apps.core.operacoes_migracao.operacao_0011")
migracao_0012 = import_module("apps.core.operacoes_migracao.operacao_0012")
migracao_0014 = import_module("apps.core.operacoes_migracao.operacao_0014")
migracao_0015 = import_module("apps.core.operacoes_migracao.operacao_0015")
migracao_0016 = import_module("apps.core.operacoes_migracao.operacao_0016")
migracao_0017 = import_module("apps.core.operacoes_migracao.operacao_0017")
migracao_0018 = import_module("apps.core.operacoes_migracao.operacao_0018")
migracao_0019 = import_module("apps.core.operacoes_migracao.operacao_0019")
migracao_0020 = import_module("apps.core.operacoes_migracao.operacao_0020")
migracao_0022 = import_module("apps.core.operacoes_migracao.operacao_0022")
migracao_0023 = import_module("apps.core.operacoes_migracao.operacao_0023")

class Migration(migrations.Migration):

    replaces = [('core', '0001_initial'), ('core', '0002_screendefinition_screenfield'), ('core', '0003_screendefinition_capabilities'), ('core', '0004_seed_clinic_erp_screens'), ('core', '0005_accent_screen_labels'), ('core', '0006_accent_model_choice_labels'), ('core', '0007_screenfield_lookup'), ('core', '0008_global_auxiliary_tables'), ('core', '0009_seed_city_state_auxiliary'), ('core', '0010_auxiliary_value_group'), ('core', '0011_seed_patient_auxiliaries'), ('core', '0012_seed_provider_types'), ('core', '0013_tipoprestadorconselho_alter_module_table_and_more'), ('core', '0014_seed_tipo_prestador_conselho'), ('core', '0015_seed_erp_auxiliaries'), ('core', '0016_seed_provider_auxiliaries'), ('core', '0017_seed_global_usability_tables'), ('core', '0018_cep'), ('core', '0019_cleanup_legacy_cep_bairro_auxiliaries'), ('core', '0020_seed_idiomas'), ('core', '0021_screendefinition_access_key'), ('core', '0022_populate_dynamic_screen_access_keys'), ('core', '0023_seed_minimum_test_auxiliary_values')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('title', models.CharField(max_length=120)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.module')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'module')},
            },
        ),
        migrations.CreateModel(
            name='ScreenDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('title', models.CharField(max_length=140)),
                ('slug', models.SlugField(max_length=160, unique=True)),
                ('screen_type', models.CharField(choices=[('formulario', 'Formulario'), ('relatorio', 'Relatorio'), ('dashboard', 'Dashboard'), ('consulta', 'Consulta'), ('wizard', 'Wizard'), ('fila', 'Fila'), ('documento', 'Documento'), ('configuracao', 'Configuracao')], default='formulario', max_length=30)),
                ('parent_label', models.CharField(blank=True, max_length=120)),
                ('table_name', models.CharField(blank=True, max_length=80)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='screens', to='core.module')),
            ],
            options={
                'ordering': ('module__title', 'parent_label', 'order', 'title'),
            },
        ),
        migrations.CreateModel(
            name='ScreenField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('label', models.CharField(max_length=120)),
                ('table_name', models.CharField(blank=True, max_length=80)),
                ('field_name', models.CharField(max_length=80)),
                ('field_type', models.CharField(choices=[('text', 'Texto'), ('number', 'Numero'), ('date', 'Data'), ('select', 'Selecao'), ('textarea', 'Texto longo'), ('checkbox', 'Checkbox')], default='text', max_length=20)),
                ('required', models.BooleanField(default=False)),
                ('consultable', models.BooleanField(default=True)),
                ('editable', models.BooleanField(default=True)),
                ('primary_key', models.BooleanField(default=False)),
                ('visible', models.BooleanField(default=True)),
                ('choices', models.TextField(blank=True, help_text='Uma opcao por linha para campos de selecao.')),
                ('order', models.PositiveIntegerField(default=0)),
                ('screen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='core.screendefinition')),
            ],
            options={
                'ordering': ('order', 'label'),
            },
        ),
        migrations.RunPython(
            code=migracao_0002.seed_user_screens,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='allow_delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='allow_insert',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='allow_query',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='allow_update',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(
            code=migracao_0003.update_screen_capabilities,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0004.seed_erp,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0005.apply_replacements,
            reverse_code=migracao_0005.revert_replacements,
        ),
        migrations.AlterField(
            model_name='screendefinition',
            name='screen_type',
            field=models.CharField(choices=[('formulario', 'Formulário'), ('relatorio', 'Relatório'), ('dashboard', 'Dashboard'), ('consulta', 'Consulta'), ('wizard', 'Wizard'), ('fila', 'Fila'), ('documento', 'Documento'), ('configuracao', 'Configuração')], default='formulario', max_length=30),
        ),
        migrations.AlterField(
            model_name='screenfield',
            name='choices',
            field=models.TextField(blank=True, help_text='Uma opção por linha para campos de seleção.'),
        ),
        migrations.AlterField(
            model_name='screenfield',
            name='field_type',
            field=models.CharField(choices=[('text', 'Texto'), ('number', 'Número'), ('date', 'Data'), ('select', 'Seleção'), ('textarea', 'Texto longo'), ('checkbox', 'Checkbox')], default='text', max_length=20),
        ),
        migrations.AddField(
            model_name='screenfield',
            name='lookup_display_field',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='screenfield',
            name='lookup_table',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='screenfield',
            name='lookup_value_field',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.CreateModel(
            name='TabelaAuxiliarGlobal',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_tabela_auxiliar_global', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_tabela', models.CharField(max_length=120, unique=True)),
                ('ds_descricao', models.CharField(blank=True, max_length=220)),
                ('sn_ativo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tabela_auxiliar_global',
                'ordering': ('ds_tabela',),
            },
        ),
        migrations.CreateModel(
            name='ValorAuxiliarGlobal',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_valor_auxiliar_global', models.BigAutoField(primary_key=True, serialize=False)),
                ('cd_valor', models.CharField(max_length=40)),
                ('ds_valor', models.CharField(max_length=160)),
                ('sn_ativo', models.BooleanField(default=True)),
                ('cd_tabela_auxiliar_global', models.ForeignKey(db_column='cd_tabela_auxiliar_global', on_delete=django.db.models.deletion.CASCADE, related_name='valores', to='core.tabelaauxiliarglobal')),
            ],
            options={
                'db_table': 'valor_auxiliar_global',
                'ordering': ('cd_tabela_auxiliar_global__ds_tabela', 'ds_valor'),
                'unique_together': {('cd_tabela_auxiliar_global', 'cd_valor')},
            },
        ),
        migrations.RunPython(
            code=migracao_0008.seed_global_auxiliary,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0009.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='valorauxiliarglobal',
            name='ds_grupo',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.RunPython(
            code=migracao_0010.seed_city_groups,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0011.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0012.seed_provider_types,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name='TipoPrestadorConselho',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('tp_prestador', models.CharField(max_length=40, unique=True)),
                ('ds_conselho', models.CharField(max_length=20)),
                ('sn_ativo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tipo_prestador_conselho',
                'ordering': ('tp_prestador',),
            },
        ),
        migrations.AlterModelTable(
            name='module',
            table='modulo',
        ),
        migrations.AlterModelTable(
            name='screendefinition',
            table='definicao_tela',
        ),
        migrations.AlterModelTable(
            name='screenfield',
            table='campo_tela',
        ),
        migrations.AlterModelTable(
            name='tabelaauxiliarglobal',
            table='tabela_auxiliar',
        ),
        migrations.AlterModelTable(
            name='usermodule',
            table='modulo_usuario',
        ),
        migrations.AlterModelTable(
            name='valorauxiliarglobal',
            table='valor_auxiliar',
        ),
        migrations.RunPython(
            code=migracao_0014.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0015.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0016.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0017.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name='Cep',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_cep', models.BigAutoField(primary_key=True, serialize=False)),
                ('nr_cep', models.CharField(max_length=8, unique=True)),
                ('sg_estado', models.CharField(blank=True, max_length=2)),
                ('cd_cidade', models.CharField(blank=True, max_length=40)),
                ('ds_cidade', models.CharField(blank=True, max_length=160)),
                ('tp_logradouro', models.CharField(blank=True, max_length=40)),
                ('ds_logradouro', models.CharField(blank=True, max_length=220)),
                ('ds_bairro', models.CharField(blank=True, max_length=160)),
                ('sn_ativo', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cep',
                'ordering': ('nr_cep',),
            },
        ),
        migrations.RunPython(
            code=migracao_0018.migrate_auxiliary_ceps,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0019.cleanup,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0020.seed,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='screendefinition',
            name='access_key',
            field=models.CharField(blank=True, db_index=True, max_length=220, null=True, unique=True),
        ),
        migrations.RunPython(
            code=migracao_0022.populate_access_keys,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RunPython(
            code=migracao_0023.cadastrar_catalogos,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
