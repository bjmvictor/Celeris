import django.db.migrations.operations.special
import django.db.models.deletion
from importlib import import_module

from django.conf import settings
from django.db import migrations, models

migracao_0013 = import_module("apps.accounts.operacoes_migracao.operacao_0013")

class Migration(migrations.Migration):

    replaces = [('accounts', '0013_sync_recent_role_screens'), ('accounts', '0014_user_cd_usuario_atualizacao_user_cd_usuario_criacao_and_more')]

    dependencies = [
        ('accounts', '0012_usuario_prestador_unico'),
        ('atendimento', '0035_modelodocumento_configuracao_assinatura'),
        ('core', '0021_screendefinition_access_key'),
    ]

    operations = [
        migrations.RunPython(
            code=migracao_0013.sync_recent_screens,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.AddField(
            model_name='user',
            name='cd_usuario_atualizacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios_atualizados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='cd_usuario_criacao',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios_criados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='dh_atualizacao',
            field=models.DateTimeField(auto_now=True, verbose_name='data de alteração'),
        ),
        migrations.AddField(
            model_name='user',
            name='tp_usuario',
            field=models.CharField(choices=[('USUARIO', 'Usuário'), ('ADMINISTRADOR', 'Administrador do sistema'), ('AUDITOR', 'Auditor')], default='USUARIO', max_length=20, verbose_name='tipo de usuário'),
        ),
    ]
