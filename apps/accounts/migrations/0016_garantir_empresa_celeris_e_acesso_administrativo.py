from django.db import migrations
from django.db.models import Q


def garantir_empresa_e_acessos(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")
    User = apps.get_model("accounts", "User")
    UsuarioEmpresa = apps.get_model("accounts", "UsuarioEmpresa")
    Group = apps.get_model("auth", "Group")
    Module = apps.get_model("core", "Module")
    ScreenDefinition = apps.get_model("core", "ScreenDefinition")

    empresa_celeris, _ = Empresa.objects.update_or_create(
        cd_empresa=1,
        defaults={
            "nm_empresa": "Celeris",
            "ds_razao_social": "Celeris",
            "ds_nome_fantasia": "Celeris",
            "sn_ativo": True,
        },
    )
    grupo_ti, _ = Group.objects.get_or_create(name="TI")
    papel_ti, _ = Papel.objects.update_or_create(
        grupo=grupo_ti,
        defaults={"ds_descricao": "Acesso administrativo integral", "sn_ativo": True},
    )

    for modulo in Module.objects.all():
        PapelModulo.objects.get_or_create(papel=papel_ti, modulo=modulo)
    for tela in ScreenDefinition.objects.all():
        PapelTela.objects.get_or_create(papel=papel_ti, tela=tela)

    empresas_ativas = list(Empresa.objects.filter(sn_ativo=True).order_by("cd_empresa"))
    administradores = User.objects.filter(Q(is_superuser=True) | Q(username__iexact="ADMIN"))
    for usuario in administradores:
        User.objects.filter(pk=usuario.pk).update(
            is_superuser=True,
            is_staff=True,
            is_active=True,
            tp_usuario="ADMINISTRADOR",
            is_blocked=False,
            can_register_patient=True,
            can_change_patient=True,
            can_create_users=True,
            can_deactivate_users=True,
            can_manage_auxiliary_tables=True,
            can_configure_system=True,
        )
        usuario.groups.add(grupo_ti)
        for empresa in empresas_ativas:
            UsuarioEmpresa.objects.update_or_create(
                usuario=usuario,
                empresa=empresa,
                defaults={
                    "sn_padrao": empresa.pk == empresa_celeris.pk,
                    "sn_ativo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_sync_navigation_role_catalog"),
        ("core", "0037_mesclar_grupos_navegacao_duplicados"),
    ]

    operations = [
        migrations.RunPython(garantir_empresa_e_acessos, migrations.RunPython.noop),
    ]
