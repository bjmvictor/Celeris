import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('ti', '0001_initial'), ('ti', '0002_alter_agentevent_table_alter_agentmachine_table')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AgentMachine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('agent_key', models.CharField(max_length=160, unique=True)),
                ('machine_name', models.CharField(max_length=120)),
                ('username', models.CharField(blank=True, max_length=120)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('status', models.CharField(choices=[('online', 'Conectada'), ('offline', 'Sem conexao')], default='offline', max_length=20)),
                ('operating_system', models.CharField(blank=True, max_length=180)),
                ('cpu', models.CharField(blank=True, max_length=220)),
                ('memory_mb', models.PositiveIntegerField(blank=True, null=True)),
                ('storage_total_mb', models.PositiveIntegerField(blank=True, null=True)),
                ('storage_free_mb', models.PositiveIntegerField(blank=True, null=True)),
                ('connected_at', models.DateTimeField(blank=True, null=True)),
                ('last_seen_at', models.DateTimeField(blank=True, null=True)),
                ('disconnected_at', models.DateTimeField(blank=True, null=True)),
                ('display_enabled', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('machine_name',),
            },
        ),
        migrations.CreateModel(
            name='AgentEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='atualizado em')),
                ('event_type', models.CharField(max_length=40)),
                ('title', models.CharField(blank=True, max_length=160)),
                ('message', models.TextField(blank=True)),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('machine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ti.agentmachine')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AlterModelTable(
            name='agentevent',
            table='evento_agente',
        ),
        migrations.AlterModelTable(
            name='agentmachine',
            table='maquina_agente',
        ),
    ]
