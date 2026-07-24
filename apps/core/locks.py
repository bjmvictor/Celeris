from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import TravaEdicao


TEMPO_PADRAO_TRAVA_MINUTOS = 120


@dataclass
class ResultadoTrava:
    permitido: bool
    trava: TravaEdicao | None = None
    mensagem: str = ""


def nome_usuario_trava(usuario):
    if not usuario:
        return ""
    if hasattr(usuario, "display_name"):
        nome = usuario.display_name()
        if nome:
            return nome
    nome_completo = getattr(usuario, "get_full_name", lambda: "")()
    return nome_completo or usuario.get_username()


def _desativar_travas_expiradas():
    agora = timezone.now()
    TravaEdicao.objects.filter(sn_ativa=True, dh_expiracao__lt=agora).update(
        sn_ativa=False,
        ds_liberacao="Liberada automaticamente por expiração.",
        updated_at=agora,
    )


def consultar_trava_ativa(empresa, tipo, recurso_id):
    _desativar_travas_expiradas()
    return (
        TravaEdicao.objects.select_related("cd_usuario")
        .filter(
            cd_empresa=empresa,
            ds_recurso_tipo=tipo,
            ds_recurso_id=str(recurso_id),
            sn_ativa=True,
        )
        .first()
    )


def adquirir_trava_edicao(
    empresa,
    usuario,
    tipo,
    recurso_id,
    titulo="",
    identificador_guia="",
    tempo_minutos=TEMPO_PADRAO_TRAVA_MINUTOS,
):
    agora = timezone.now()
    expiracao = agora + timedelta(minutes=tempo_minutos)
    with transaction.atomic():
        _desativar_travas_expiradas()
        trava = (
            TravaEdicao.objects.select_for_update()
            .select_related("cd_usuario")
            .filter(
                cd_empresa=empresa,
                ds_recurso_tipo=tipo,
                ds_recurso_id=str(recurso_id),
                sn_ativa=True,
            )
            .first()
        )
        if trava and trava.cd_usuario_id == usuario.pk:
            trava.ds_recurso_titulo = titulo or trava.ds_recurso_titulo
            trava.ds_identificador_guia = identificador_guia or trava.ds_identificador_guia
            trava.dh_expiracao = expiracao
            trava.save(update_fields=["ds_recurso_titulo", "ds_identificador_guia", "dh_expiracao", "updated_at"])
            return ResultadoTrava(True, trava)
        if trava:
            trava.nr_tentativas_bloqueadas += 1
            trava.ds_ultimo_usuario_bloqueado = nome_usuario_trava(usuario)
            trava.dh_ultimo_bloqueio = agora
            trava.save(
                update_fields=[
                    "nr_tentativas_bloqueadas",
                    "ds_ultimo_usuario_bloqueado",
                    "dh_ultimo_bloqueio",
                    "updated_at",
                ]
            )
            return ResultadoTrava(
                False,
                trava,
                f"Este registro está em edição por {nome_usuario_trava(trava.cd_usuario)}.",
            )
        try:
            trava = TravaEdicao.objects.create(
                cd_empresa=empresa,
                cd_usuario=usuario,
                ds_recurso_tipo=tipo,
                ds_recurso_id=str(recurso_id),
                ds_recurso_titulo=titulo,
                ds_identificador_guia=identificador_guia,
                dh_expiracao=expiracao,
            )
        except IntegrityError:
            trava = consultar_trava_ativa(empresa, tipo, recurso_id)
            return ResultadoTrava(
                False,
                trava,
                f"Este registro está em edição por {nome_usuario_trava(trava.cd_usuario) if trava else 'outro usuário'}.",
            )
    return ResultadoTrava(True, trava)


def liberar_trava_edicao(empresa, usuario, tipo, recurso_id, motivo="Liberada pelo usuário.", forcar=False):
    filtros = {
        "cd_empresa": empresa,
        "ds_recurso_tipo": tipo,
        "ds_recurso_id": str(recurso_id),
        "sn_ativa": True,
    }
    if not forcar:
        filtros["cd_usuario"] = usuario
    return TravaEdicao.objects.filter(**filtros).update(
        sn_ativa=False,
        ds_liberacao=motivo,
        updated_at=timezone.now(),
    )


def usuario_tem_trava_ou_livre(empresa, usuario, tipo, recurso_id):
    trava = consultar_trava_ativa(empresa, tipo, recurso_id)
    if not trava or trava.cd_usuario_id == usuario.pk:
        return ResultadoTrava(True, trava)
    return ResultadoTrava(
        False,
        trava,
        f"Este registro está em edição por {nome_usuario_trava(trava.cd_usuario)}.",
    )
