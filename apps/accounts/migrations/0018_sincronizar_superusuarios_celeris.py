from django.db import migrations


def sincronizar_superusuarios(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Papel = apps.get_model("accounts", "Papel")
    User = apps.get_model("accounts", "User")
    UsuarioEmpresa = apps.get_model("accounts", "UsuarioEmpresa")
    Group = apps.get_model("auth", "Group")

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
    Papel.objects.update_or_create(
        grupo=grupo_ti,
        defaults={"ds_descricao": "Acesso administrativo integral", "sn_ativo": True},
    )
    empresas_ativas = list(Empresa.objects.filter(sn_ativo=True).order_by("cd_empresa"))

    for usuario in User.objects.filter(is_superuser=True):
        User.objects.filter(pk=usuario.pk).update(
            full_name=usuario.full_name or usuario.username,
            tp_usuario="ADMINISTRADOR",
            is_staff=True,
            is_active=True,
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
        ("accounts", "0017_alter_user_groups_alter_user_is_active_and_more"),
    ]

    operations = [
        migrations.RunPython(sincronizar_superusuarios, migrations.RunPython.noop),
    ]
