import django.db.migrations.operations.special
import django.db.models.deletion
from decimal import Decimal
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0002 = import_module("apps.estoque.migrations.0002_seed_tabelas_produto")

class Migration(migrations.Migration):

    replaces = [('estoque', '0001_initial'), ('estoque', '0002_seed_tabelas_produto')]

    dependencies = [
        ('accounts', '0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more'),
        ('atendimento', '0040_paciente_obito'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Estoque',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_estoque', models.CharField(max_length=140, verbose_name='nome')),
                ('ds_codigo', models.CharField(blank=True, max_length=40, verbose_name='codigo')),
                ('sn_principal', models.BooleanField(default=False, verbose_name='principal')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_setor', models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor')),
            ],
            options={
                'db_table': 'estoque',
                'ordering': ('nm_estoque',),
                'unique_together': {('cd_empresa', 'nm_estoque')},
            },
        ),
        migrations.CreateModel(
            name='MovimentoEstoque',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_movimento_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('tp_movimento', models.CharField(choices=[('ENTRADA', 'Entrada'), ('SAIDA', 'Saida'), ('DEVOLUCAO', 'Devolucao'), ('TRANSFERENCIA', 'Transferencia'), ('FRACIONAMENTO', 'Fracionamento'), ('ACERTO', 'Acerto de estoque')], max_length=20, verbose_name='tipo')),
                ('tp_destino', models.CharField(blank=True, choices=[('SETOR', 'Setor'), ('PACIENTE', 'Paciente'), ('FORNECEDOR', 'Fornecedor'), ('GASTO_SALA', 'Gasto de sala'), ('ESTOQUE', 'Estoque')], max_length=20, verbose_name='destino')),
                ('ds_motivo', models.CharField(blank=True, max_length=180, verbose_name='motivo')),
                ('ds_observacao', models.TextField(blank=True, verbose_name='observacao')),
                ('ds_status', models.CharField(choices=[('ABERTO', 'Aberto'), ('FINALIZADO', 'Finalizado'), ('CANCELADO', 'Cancelado')], default='ABERTO', max_length=20, verbose_name='status')),
                ('cd_atendimento', models.ForeignKey(blank=True, db_column='cd_atendimento', null=True, on_delete=django.db.models.deletion.PROTECT, to='atendimento.atendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_estoque_destino', models.ForeignKey(blank=True, db_column='cd_estoque_destino', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimentos_destino', to='estoque.estoque')),
                ('cd_estoque_origem', models.ForeignKey(blank=True, db_column='cd_estoque_origem', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='movimentos_origem', to='estoque.estoque')),
                ('cd_setor', models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor')),
                ('cd_usuario', models.ForeignKey(blank=True, db_column='cd_usuario', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'movimento_estoque',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_produto', models.BigAutoField(primary_key=True, serialize=False)),
                ('cd_codigo', models.CharField(blank=True, max_length=40, verbose_name='codigo')),
                ('nm_produto', models.CharField(max_length=180, verbose_name='produto')),
                ('tp_produto', models.CharField(choices=[('MATERIAL', 'Material'), ('MEDICAMENTO', 'Medicamento'), ('EXAME', 'Exame/insumo'), ('OPME', 'OPME'), ('OUTRO', 'Outro')], default='MATERIAL', max_length=20, verbose_name='tipo')),
                ('ds_descricao', models.TextField(blank=True, verbose_name='descricao')),
                ('ds_lote', models.CharField(blank=True, max_length=60, verbose_name='lote padrao')),
                ('dt_validade', models.DateField(blank=True, null=True, verbose_name='validade padrao')),
                ('ds_carater', models.CharField(blank=True, max_length=80, verbose_name='carater')),
                ('ds_classe', models.CharField(blank=True, max_length=80, verbose_name='classe')),
                ('cd_procedimento_faturamento', models.CharField(blank=True, max_length=80, verbose_name='procedimento de faturamento')),
                ('sn_controla_lote', models.BooleanField(default=False, verbose_name='controla lote')),
                ('sn_controla_validade', models.BooleanField(default=False, verbose_name='controla validade')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'produto',
                'ordering': ('nm_produto',),
            },
        ),
        migrations.CreateModel(
            name='ItemMovimentoEstoque',
            fields=[
                ('cd_item_movimento_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('qt_movimento', models.DecimalField(decimal_places=3, max_digits=14, verbose_name='quantidade')),
                ('ds_lote', models.CharField(blank=True, max_length=60, verbose_name='lote')),
                ('dt_validade', models.DateField(blank=True, null=True, verbose_name='validade')),
                ('cd_movimento', models.ForeignKey(db_column='cd_movimento_estoque', on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='estoque.movimentoestoque')),
                ('cd_produto', models.ForeignKey(db_column='cd_produto', on_delete=django.db.models.deletion.PROTECT, to='estoque.produto')),
            ],
            options={
                'db_table': 'item_movimento_estoque',
            },
        ),
        migrations.CreateModel(
            name='CotaConsumo',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_cota_consumo', models.BigAutoField(primary_key=True, serialize=False)),
                ('qt_cota', models.DecimalField(decimal_places=3, max_digits=14, verbose_name='cota')),
                ('nr_dias', models.PositiveIntegerField(default=30, verbose_name='dias')),
                ('dt_inicio_vigencia', models.DateField(verbose_name='inicio da vigencia')),
                ('dt_fim_vigencia', models.DateField(blank=True, null=True, verbose_name='fim da vigencia')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_estoque', models.ForeignKey(db_column='cd_estoque', on_delete=django.db.models.deletion.PROTECT, to='estoque.estoque')),
                ('cd_produto', models.ForeignKey(db_column='cd_produto', on_delete=django.db.models.deletion.PROTECT, to='estoque.produto')),
            ],
            options={
                'db_table': 'cota_consumo',
                'ordering': ('cd_estoque__nm_estoque', 'cd_produto__nm_produto'),
            },
        ),
        migrations.CreateModel(
            name='ProdutoClassificacao',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_classificacao_produto', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_classificacao', models.CharField(max_length=120, verbose_name='classificacao')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'produto_classificacao',
                'ordering': ('nm_classificacao',),
                'unique_together': {('cd_empresa', 'nm_classificacao')},
            },
        ),
        migrations.AddField(
            model_name='produto',
            name='cd_classificacao',
            field=models.ForeignKey(blank=True, db_column='cd_classificacao_produto', null=True, on_delete=django.db.models.deletion.PROTECT, to='estoque.produtoclassificacao'),
        ),
        migrations.CreateModel(
            name='SolicitacaoProduto',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_solicitacao_produto', models.BigAutoField(primary_key=True, serialize=False)),
                ('tp_solicitacao', models.CharField(choices=[('SETOR', 'Para setor'), ('PACIENTE', 'Para paciente'), ('COMPRA', 'Compra'), ('DEVOLUCAO', 'Devolucao')], default='SETOR', max_length=20, verbose_name='tipo')),
                ('ds_motivo', models.CharField(blank=True, max_length=180, verbose_name='motivo')),
                ('ds_observacao', models.TextField(blank=True, verbose_name='observacao')),
                ('ds_status', models.CharField(choices=[('ABERTA', 'Aberta'), ('RECEBIDA', 'Recebida'), ('ATENDIDA', 'Atendida'), ('CANCELADA', 'Cancelada')], default='ABERTA', max_length=20, verbose_name='status')),
                ('cd_atendimento', models.ForeignKey(blank=True, db_column='cd_atendimento', null=True, on_delete=django.db.models.deletion.PROTECT, to='atendimento.atendimento')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_estoque', models.ForeignKey(blank=True, db_column='cd_estoque', null=True, on_delete=django.db.models.deletion.PROTECT, to='estoque.estoque')),
                ('cd_setor', models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor')),
                ('cd_usuario_atendente', models.ForeignKey(blank=True, db_column='cd_usuario_atendente', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='atendimentos_solicitacao_produto', to=settings.AUTH_USER_MODEL)),
                ('cd_usuario_solicitante', models.ForeignKey(blank=True, db_column='cd_usuario_solicitante', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='solicitacoes_produto', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'solicitacao_produto',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='ItemSolicitacaoProduto',
            fields=[
                ('cd_item_solicitacao_produto', models.BigAutoField(primary_key=True, serialize=False)),
                ('qt_solicitada', models.DecimalField(decimal_places=3, max_digits=14, verbose_name='quantidade')),
                ('qt_saldo_estoque', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=14, verbose_name='saldo no estoque')),
                ('sn_alerta_estoque', models.BooleanField(default=False, verbose_name='sem estoque suficiente')),
                ('cd_produto', models.ForeignKey(db_column='cd_produto', on_delete=django.db.models.deletion.PROTECT, to='estoque.produto')),
                ('cd_solicitacao', models.ForeignKey(db_column='cd_solicitacao_produto', on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='estoque.solicitacaoproduto')),
            ],
            options={
                'db_table': 'item_solicitacao_produto',
            },
        ),
        migrations.CreateModel(
            name='TabelaEstoque',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_tabela_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_chave', models.SlugField(max_length=80, verbose_name='chave')),
                ('ds_nome', models.CharField(max_length=140, verbose_name='nome')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'tabela_estoque',
                'ordering': ('ds_nome',),
                'unique_together': {('cd_empresa', 'ds_chave')},
            },
        ),
        migrations.CreateModel(
            name='UnidadeProduto',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_unidade_produto', models.BigAutoField(primary_key=True, serialize=False)),
                ('ds_sigla', models.CharField(max_length=20, verbose_name='sigla')),
                ('ds_descricao', models.CharField(max_length=120, verbose_name='descricao')),
                ('qt_fator_conversao', models.DecimalField(decimal_places=3, default=Decimal('1.000'), max_digits=10, verbose_name='fator')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'unidade_produto',
                'ordering': ('ds_sigla',),
                'unique_together': {('cd_empresa', 'ds_sigla')},
            },
        ),
        migrations.AddField(
            model_name='produto',
            name='cd_unidade',
            field=models.ForeignKey(blank=True, db_column='cd_unidade_produto', null=True, on_delete=django.db.models.deletion.PROTECT, to='estoque.unidadeproduto'),
        ),
        migrations.CreateModel(
            name='ProdutoEstoque',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_produto_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('qt_saldo', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=14, verbose_name='saldo')),
                ('qt_reservado', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=14, verbose_name='reservado')),
                ('qt_minima', models.DecimalField(decimal_places=3, default=Decimal('0.000'), max_digits=14, verbose_name='minimo')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_estoque', models.ForeignKey(db_column='cd_estoque', on_delete=django.db.models.deletion.PROTECT, related_name='produtos', to='estoque.estoque')),
                ('cd_produto', models.ForeignKey(db_column='cd_produto', on_delete=django.db.models.deletion.PROTECT, related_name='saldos', to='estoque.produto')),
            ],
            options={
                'db_table': 'produto_estoque',
                'ordering': ('cd_estoque__nm_estoque', 'cd_produto__nm_produto'),
                'unique_together': {('cd_empresa', 'cd_produto', 'cd_estoque')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='produto',
            unique_together={('cd_empresa', 'nm_produto')},
        ),
        migrations.CreateModel(
            name='ValorTabelaEstoque',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_valor_tabela_estoque', models.BigAutoField(primary_key=True, serialize=False)),
                ('cd_valor', models.CharField(max_length=40, verbose_name='codigo')),
                ('ds_valor', models.CharField(max_length=160, verbose_name='valor')),
                ('ds_observacao', models.CharField(blank=True, max_length=240, verbose_name='observacao')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_tabela', models.ForeignKey(db_column='cd_tabela_estoque', on_delete=django.db.models.deletion.CASCADE, related_name='valores', to='estoque.tabelaestoque')),
            ],
            options={
                'db_table': 'valor_tabela_estoque',
                'ordering': ('cd_tabela__ds_nome', 'ds_valor'),
                'unique_together': {('cd_tabela', 'cd_valor')},
            },
        ),
        migrations.RunPython(
            code=migracao_0002.seed_product_tables,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
