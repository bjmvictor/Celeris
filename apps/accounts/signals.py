from django.contrib.auth.models import Group
from django.db import OperationalError, ProgrammingError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import Module, ScreenDefinition

from .models import Empresa, Papel, PapelModulo, PapelTela, User, UsuarioEmpresa


def garantir_acesso_total_superusuario(usuario: User) -> None:
    if not usuario.is_superuser:
        return

    try:
        empresa_celeris, _ = Empresa.objects.update_or_create(
            cd_empresa=1,
            defaults={
                "nm_empresa": "Celeris",
                "ds_razao_social": "Celeris",
                "ds_nome_fantasia": "Celeris",
                "sn_ativo": True,
            },
        )
        empresas = list(Empresa.objects.filter(sn_ativo=True).order_by("cd_empresa"))
        for empresa in empresas:
            UsuarioEmpresa.objects.update_or_create(
                usuario=usuario,
                empresa=empresa,
                defaults={
                    "sn_padrao": empresa.pk == empresa_celeris.pk,
                    "sn_ativo": True,
                },
            )

        grupo_ti, _ = Group.objects.get_or_create(name="TI")
        usuario.groups.add(grupo_ti)
        papel_ti, _ = Papel.objects.update_or_create(
            grupo=grupo_ti,
            defaults={"ds_descricao": "Acesso administrativo integral", "sn_ativo": True},
        )
        PapelModulo.objects.bulk_create(
            [PapelModulo(papel=papel_ti, modulo=modulo) for modulo in Module.objects.all()],
            ignore_conflicts=True,
        )
        PapelTela.objects.bulk_create(
            [PapelTela(papel=papel_ti, tela=tela) for tela in ScreenDefinition.objects.all()],
            ignore_conflicts=True,
        )
    except (OperationalError, ProgrammingError):
        return


def provisionar_superusuario_apos_commit(usuario_id: int) -> None:
    try:
        usuario = User.objects.filter(pk=usuario_id, is_superuser=True).first()
        if usuario:
            garantir_acesso_total_superusuario(usuario)
    except (OperationalError, ProgrammingError):
        return


def vincular_empresa_apos_commit(empresa_id: int) -> None:
    try:
        empresa = Empresa.objects.filter(pk=empresa_id, sn_ativo=True).first()
        if not empresa:
            return
        for usuario in User.objects.filter(is_superuser=True, is_active=True):
            UsuarioEmpresa.objects.update_or_create(
                usuario=usuario,
                empresa=empresa,
                defaults={"sn_padrao": empresa.pk == 1, "sn_ativo": True},
            )
    except (OperationalError, ProgrammingError):
        return


@receiver(post_save, sender=User)
def configurar_superusuario(sender, instance: User, **kwargs) -> None:
    if kwargs.get("raw") or not instance.is_superuser:
        return

    campos_administrativos = {
        "tp_usuario": "ADMINISTRADOR",
        "is_staff": True,
        "is_active": True,
        "is_blocked": False,
        "can_register_patient": True,
        "can_change_patient": True,
        "can_create_users": True,
        "can_deactivate_users": True,
        "can_manage_auxiliary_tables": True,
        "can_configure_system": True,
    }
    alteracoes = {
        campo: valor
        for campo, valor in campos_administrativos.items()
        if getattr(instance, campo) != valor
    }
    if alteracoes:
        User.objects.filter(pk=instance.pk).update(**alteracoes)
        for campo, valor in alteracoes.items():
            setattr(instance, campo, valor)
    transaction.on_commit(
        lambda usuario_id=instance.pk: provisionar_superusuario_apos_commit(usuario_id)
    )


@receiver(post_save, sender=Empresa)
def vincular_superusuarios_a_nova_empresa(sender, instance: Empresa, **kwargs) -> None:
    if kwargs.get("raw") or not instance.sn_ativo:
        return
    transaction.on_commit(lambda empresa_id=instance.pk: vincular_empresa_apos_commit(empresa_id))
