import django.db.models.deletion
import django.utils.timezone
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0007 = import_module("apps.tickets.migrations.0007_motivoconclusaosuporte_and_more")

class Migration(migrations.Migration):

    replaces = [('tickets', '0001_initial'), ('tickets', '0002_alter_ticket_table'), ('tickets', '0003_ticket_cd_empresa_ticket_cd_setor_ticket_conclusion_and_more'), ('tickets', '0004_alter_motivoservicosuporte_options_and_more'), ('tickets', '0005_suporte_atendimento_oficina'), ('tickets', '0006_alter_ticket_status'), ('tickets', '0007_motivoconclusaosuporte_and_more'), ('tickets', '0008_ticket_ds_observacao_conclusao')]

    dependencies = [
        ('accounts', '0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('module', models.CharField(max_length=80)),
                ('title', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('sector', models.CharField(blank=True, max_length=120)),
                ('priority', models.CharField(default='normal', max_length=30)),
                ('status', models.CharField(choices=[('open', 'Aberto'), ('done', 'Concluido'), ('cancelled', 'Cancelado')], default='open', max_length=20)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL)),
                ('requester', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requested_tickets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterModelTable(
            name='ticket',
            table='chamado',
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_empresa',
            field=models.ForeignKey(blank=True, db_column='cd_empresa', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_setor',
            field=models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='conclusion',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='performers',
            field=models.ManyToManyField(blank=True, related_name='performed_tickets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ticket',
            name='received_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(choices=[('open', 'Aberto'), ('received', 'Recebido'), ('done', 'Concluido'), ('cancelled', 'Cancelado')], default='open', max_length=20),
        ),
        migrations.CreateModel(
            name='MotivoServicoSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_motivo_servico_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_motivo', models.CharField(max_length=120, verbose_name='motivo')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'suporte_motivo_servico',
                'ordering': ('cd_oficina__nm_oficina', 'nm_motivo'),
                'unique_together': set(),
                'verbose_name': 'Motivo de serviço',
                'verbose_name_plural': 'Motivos de serviço',
            },
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_motivo',
            field=models.ForeignKey(blank=True, db_column='cd_motivo_servico_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.motivoservicosuporte'),
        ),
        migrations.CreateModel(
            name='OficinaSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_oficina_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_oficina', models.CharField(max_length=120, verbose_name='oficina')),
                ('ds_descricao', models.CharField(blank=True, max_length=220, verbose_name='descricao')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('usuarios', models.ManyToManyField(blank=True, related_name='oficinas_suporte', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'suporte_oficina',
                'ordering': ('nm_oficina',),
                'unique_together': {('cd_empresa', 'nm_oficina')},
                'verbose_name': 'Oficina de suporte',
                'verbose_name_plural': 'Oficinas de suporte',
            },
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_oficina',
            field=models.ForeignKey(blank=True, db_column='cd_oficina_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.oficinasuporte'),
        ),
        migrations.CreateModel(
            name='PrioridadeSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_prioridade_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_prioridade', models.CharField(max_length=80, verbose_name='prioridade')),
                ('nr_peso', models.PositiveIntegerField(default=0, verbose_name='peso')),
                ('ds_cor', models.CharField(blank=True, max_length=20, verbose_name='cor')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
            ],
            options={
                'db_table': 'suporte_prioridade',
                'ordering': ('nr_peso', 'nm_prioridade'),
                'unique_together': {('cd_empresa', 'nm_prioridade')},
                'verbose_name': 'Prioridade de suporte',
                'verbose_name_plural': 'Prioridades de suporte',
            },
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_prioridade',
            field=models.ForeignKey(blank=True, db_column='cd_prioridade_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.prioridadesuporte'),
        ),
        migrations.AlterModelOptions(
            name='ticket',
            options={'ordering': ('-created_at',), 'verbose_name': 'Chamado', 'verbose_name_plural': 'Chamados'},
        ),
        migrations.AddField(
            model_name='motivoservicosuporte',
            name='cd_oficina',
            field=models.ForeignKey(blank=True, db_column='cd_oficina_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.oficinasuporte'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='cd_motivo',
            field=models.ForeignKey(blank=True, db_column='cd_motivo_servico_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.motivoservicosuporte', verbose_name='motivo'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='cd_oficina',
            field=models.ForeignKey(blank=True, db_column='cd_oficina_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.oficinasuporte', verbose_name='oficina'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='cd_prioridade',
            field=models.ForeignKey(blank=True, db_column='cd_prioridade_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.prioridadesuporte', verbose_name='prioridade'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='cd_setor',
            field=models.ForeignKey(blank=True, db_column='cd_setor', null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.setor', verbose_name='setor'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='description',
            field=models.TextField(blank=True, verbose_name='descrição'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='module',
            field=models.CharField(max_length=80, verbose_name='módulo'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='priority',
            field=models.CharField(default='normal', max_length=30, verbose_name='prioridade textual'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='sector',
            field=models.CharField(blank=True, max_length=120, verbose_name='setor textual'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='title',
            field=models.CharField(max_length=180, verbose_name='título'),
        ),
        migrations.AlterUniqueTogether(
            name='motivoservicosuporte',
            unique_together={('cd_empresa', 'cd_oficina', 'nm_motivo')},
        ),
        migrations.AddField(
            model_name='ticket',
            name='cd_motivo_conclusao',
            field=models.ForeignKey(blank=True, db_column='cd_motivo_conclusao_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tickets_concluidos', to='tickets.motivoservicosuporte', verbose_name='motivo da conclusao'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='performed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='TicketTransferenciaSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_transferencia_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('dh_transferencia', models.DateTimeField(default=django.utils.timezone.now)),
                ('ds_observacao', models.CharField(blank=True, max_length=240, verbose_name='observacao')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_oficina_destino', models.ForeignKey(db_column='cd_oficina_destino', on_delete=django.db.models.deletion.PROTECT, related_name='+', to='tickets.oficinasuporte')),
                ('cd_oficina_origem', models.ForeignKey(blank=True, db_column='cd_oficina_origem', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='tickets.oficinasuporte')),
                ('cd_ticket', models.ForeignKey(db_column='cd_ticket', on_delete=django.db.models.deletion.CASCADE, related_name='transferencias', to='tickets.ticket')),
                ('cd_usuario', models.ForeignKey(blank=True, db_column='cd_usuario', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Transferencia de chamado',
                'verbose_name_plural': 'Transferencias de chamados',
                'db_table': 'suporte_ticket_transferencia',
                'ordering': ('-dh_transferencia',),
            },
        ),
        migrations.CreateModel(
            name='UsuarioOficinaSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_usuario_oficina_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('sn_atende', models.BooleanField(default=True, verbose_name='atende')),
                ('sn_solicita', models.BooleanField(default=True, verbose_name='solicita')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_oficina', models.ForeignKey(db_column='cd_oficina_suporte', on_delete=django.db.models.deletion.PROTECT, to='tickets.oficinasuporte', verbose_name='oficina')),
                ('cd_usuario', models.ForeignKey(db_column='cd_usuario', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'Usuario x oficina',
                'verbose_name_plural': 'Usuarios x oficinas',
                'db_table': 'suporte_usuario_oficina',
                'ordering': ('cd_usuario__username', 'cd_oficina__nm_oficina'),
                'unique_together': {('cd_empresa', 'cd_usuario', 'cd_oficina')},
            },
        ),
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(choices=[('open', 'Aberto'), ('received', 'Recebido'), ('done', 'Concluido'), ('not_done', 'Não concluído'), ('cancelled', 'Cancelado')], default='open', max_length=20),
        ),
        migrations.CreateModel(
            name='MotivoConclusaoSuporte',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('cd_motivo_conclusao_suporte', models.BigAutoField(primary_key=True, serialize=False)),
                ('nm_motivo', models.CharField(max_length=120, verbose_name='motivo')),
                ('sn_ativo', models.BooleanField(default=True, verbose_name='ativo')),
                ('cd_empresa', models.ForeignKey(db_column='cd_empresa', on_delete=django.db.models.deletion.PROTECT, to='accounts.empresa')),
                ('cd_oficina', models.ForeignKey(blank=True, db_column='cd_oficina_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, to='tickets.oficinasuporte')),
            ],
            options={
                'verbose_name': 'Motivo de conclusão',
                'verbose_name_plural': 'Motivos de conclusão',
                'db_table': 'suporte_motivo_conclusao',
                'ordering': ('cd_oficina__nm_oficina', 'nm_motivo'),
                'unique_together': {('cd_empresa', 'cd_oficina', 'nm_motivo')},
            },
        ),
        migrations.RunPython(
            code=migracao_0007.copiar_motivos_conclusao,
            reverse_code=migracao_0007.reverter_motivos_conclusao,
        ),
        migrations.AlterField(
            model_name='ticket',
            name='cd_motivo_conclusao',
            field=models.ForeignKey(blank=True, db_column='cd_motivo_conclusao_suporte', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tickets_concluidos', to='tickets.motivoconclusaosuporte', verbose_name='motivo da conclusão'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='ds_observacao_conclusao',
            field=models.TextField(blank=True, verbose_name='observação da conclusão'),
        ),
    ]
