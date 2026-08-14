from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone as datetime_timezone
import base64
import os
import re
import warnings

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import pkcs12
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.utils import timezone

class ErroCertificadoDigital(Exception):
    """Erro seguro e apresentável durante operações com certificados."""


@dataclass(frozen=True)
class MetadadosCertificado:
    sujeito: str
    emissor: str
    numero_serie: str
    fingerprint_sha256: str
    cpf_cnpj: str
    inicio_validade: datetime
    fim_validade: datetime


def _chave_mestra(versao: str | None = None) -> bytes:
    versao = versao or settings.CELERIS_CERTIFICATE_MASTER_KEY_VERSION
    nome_especifico = f"CELERIS_CERTIFICATE_MASTER_KEY_{versao.upper().replace('-', '_')}"
    valor = os.getenv(nome_especifico) or settings.CELERIS_CERTIFICATE_MASTER_KEY
    if not valor:
        raise ImproperlyConfigured(
            "Defina CELERIS_CERTIFICATE_MASTER_KEY com uma chave Base64 de 32 bytes antes de cadastrar certificados."
        )
    try:
        chave = base64.urlsafe_b64decode(valor.encode("ascii") + b"=" * (-len(valor) % 4))
    except (ValueError, UnicodeError) as exc:
        raise ImproperlyConfigured("CELERIS_CERTIFICATE_MASTER_KEY não é uma chave Base64 válida.") from exc
    if len(chave) != 32:
        raise ImproperlyConfigured("CELERIS_CERTIFICATE_MASTER_KEY deve representar exatamente 32 bytes.")
    return chave


def gerar_chave_mestra() -> str:
    """Retorna uma chave adequada para configuração externa; nunca é salva no banco."""
    return base64.urlsafe_b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")


def chave_mestra_configurada(versao: str | None = None) -> bool:
    """Confirma que a chave atual existe, é Base64 válida e representa 32 bytes."""
    try:
        _chave_mestra(versao)
    except ImproperlyConfigured:
        return False
    return True


def criptografar(valor: bytes, *, aad: bytes, versao: str | None = None) -> tuple[bytes, bytes, str]:
    versao = versao or settings.CELERIS_CERTIFICATE_MASTER_KEY_VERSION
    nonce = os.urandom(12)
    return AESGCM(_chave_mestra(versao)).encrypt(nonce, valor, aad), nonce, versao


def descriptografar(valor: bytes, nonce: bytes, *, aad: bytes, versao: str) -> bytes:
    try:
        return AESGCM(_chave_mestra(versao)).decrypt(bytes(nonce), bytes(valor), aad)
    except Exception as exc:
        raise ErroCertificadoDigital("Não foi possível abrir o certificado com a chave mestra configurada.") from exc


def _nome_x509(nome: x509.Name) -> str:
    return ", ".join(f"{atributo.oid._name or atributo.oid.dotted_string}={atributo.value}" for atributo in nome)


def _cpf_cnpj_certificado(certificado: x509.Certificate) -> str:
    candidatos = []
    for atributo in certificado.subject:
        digitos = re.sub(r"\D", "", str(atributo.value))
        candidatos.extend(re.findall(r"\d{14}|\d{11}", digitos))
    cnpj = next((valor for valor in candidatos if len(valor) == 14), "")
    cpf = next((valor for valor in candidatos if len(valor) == 11), "")
    return cnpj or cpf


def validar_pkcs12(conteudo: bytes, senha: str) -> MetadadosCertificado:
    if not conteudo:
        raise ErroCertificadoDigital("Selecione um arquivo de certificado A1 no formato PFX ou P12.")
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"PKCS#12 bundle could not be parsed as DER.*",
                category=UserWarning,
            )
            chave_privada, certificado, _cadeia = pkcs12.load_key_and_certificates(
                conteudo,
                senha.encode("utf-8") if senha else None,
            )
    except (ValueError, TypeError) as exc:
        raise ErroCertificadoDigital("Certificado inválido ou senha incorreta.") from exc
    if not chave_privada or not certificado:
        raise ErroCertificadoDigital("O arquivo não contém certificado e chave privada utilizáveis.")
    if hasattr(certificado, "not_valid_before_utc"):
        inicio = certificado.not_valid_before_utc
        fim = certificado.not_valid_after_utc
    else:
        inicio = certificado.not_valid_before.replace(tzinfo=datetime_timezone.utc)
        fim = certificado.not_valid_after.replace(tzinfo=datetime_timezone.utc)
    agora = timezone.now()
    if agora < inicio:
        raise ErroCertificadoDigital("O certificado ainda não está válido.")
    if agora >= fim:
        raise ErroCertificadoDigital("O certificado está vencido.")
    fingerprint = certificado.fingerprint(hashes.SHA256()).hex().upper()
    fingerprint = ":".join(fingerprint[indice : indice + 2] for indice in range(0, len(fingerprint), 2))
    return MetadadosCertificado(
        sujeito=_nome_x509(certificado.subject),
        emissor=_nome_x509(certificado.issuer),
        numero_serie=format(certificado.serial_number, "X"),
        fingerprint_sha256=fingerprint,
        cpf_cnpj=_cpf_cnpj_certificado(certificado),
        inicio_validade=inicio,
        fim_validade=fim,
    )


def _aad(empresa_id: int, finalidade: str, versao: str) -> bytes:
    return f"celeris:certificado:{empresa_id}:{finalidade}:{versao}".encode("utf-8")


@transaction.atomic
def cadastrar_certificado(
    *,
    empresa,
    usuario,
    nome: str,
    tipo: str,
    arquivo_nome: str,
    conteudo: bytes,
    senha: str,
    usuario_profissional=None,
    assina_medicos: bool = False,
    assina_administrativos: bool = False,
    assina_outros: bool = False,
) -> CertificadoDigitalEmpresa:
    from apps.core.models import CertificadoDigitalEmpresa

    extensao = os.path.splitext(arquivo_nome or "")[1].lower()
    if extensao not in {".pfx", ".p12"}:
        raise ErroCertificadoDigital("Envie um certificado A1 com extensão .pfx ou .p12.")
    if len(conteudo) > settings.CELERIS_CERTIFICATE_MAX_UPLOAD_SIZE:
        raise ErroCertificadoDigital("O certificado excede o limite de tamanho permitido.")
    metadados = validar_pkcs12(conteudo, senha)
    versao = settings.CELERIS_CERTIFICATE_MASTER_KEY_VERSION
    aad_arquivo = _aad(empresa.pk, "arquivo", versao)
    aad_senha = _aad(empresa.pk, "senha", versao)
    arquivo_criptografado, arquivo_nonce, _ = criptografar(conteudo, aad=aad_arquivo, versao=versao)
    senha_criptografada, senha_nonce, _ = criptografar(senha.encode("utf-8"), aad=aad_senha, versao=versao)
    certificado = CertificadoDigitalEmpresa(
        cd_empresa=empresa,
        cd_usuario_profissional=usuario_profissional,
        nm_certificado=nome.strip(),
        tp_certificado=tipo,
        arquivo_criptografado=arquivo_criptografado,
        arquivo_nonce=arquivo_nonce,
        senha_criptografada=senha_criptografada,
        senha_nonce=senha_nonce,
        versao_chave=versao,
        ds_sujeito=metadados.sujeito,
        ds_emissor=metadados.emissor,
        nr_serie=metadados.numero_serie,
        ds_fingerprint_sha256=metadados.fingerprint_sha256,
        nr_cpf_cnpj=metadados.cpf_cnpj,
        dh_inicio_validade=metadados.inicio_validade,
        dh_fim_validade=metadados.fim_validade,
        sn_assina_documentos_medicos=assina_medicos,
        sn_assina_documentos_administrativos=assina_administrativos,
        sn_assina_outros_documentos=assina_outros,
        cd_usuario_criacao=usuario,
        cd_usuario_atualizacao=usuario,
        dh_ultima_validacao=timezone.now(),
        ds_ultima_validacao="Certificado validado no cadastro.",
    )
    try:
        certificado.full_clean()
        certificado.save()
    except ValidationError:
        raise
    except Exception as exc:
        if CertificadoDigitalEmpresa.objects.filter(
            cd_empresa=empresa,
            ds_fingerprint_sha256=metadados.fingerprint_sha256,
        ).exists():
            raise ErroCertificadoDigital("Este certificado já está cadastrado para a empresa.") from exc
        raise
    return certificado


def abrir_material_certificado(certificado: CertificadoDigitalEmpresa) -> tuple[bytes, bytes]:
    versao = certificado.versao_chave
    pfx = descriptografar(
        certificado.arquivo_criptografado,
        certificado.arquivo_nonce,
        aad=_aad(certificado.cd_empresa_id, "arquivo", versao),
        versao=versao,
    )
    senha = descriptografar(
        certificado.senha_criptografada,
        certificado.senha_nonce,
        aad=_aad(certificado.cd_empresa_id, "senha", versao),
        versao=versao,
    )
    return pfx, senha


def finalidade_habilitada(certificado: CertificadoDigitalEmpresa, finalidade: str) -> bool:
    return {
        "MEDICO": certificado.sn_assina_documentos_medicos,
        "ADMINISTRATIVO": certificado.sn_assina_documentos_administrativos,
        "OUTRO": certificado.sn_assina_outros_documentos,
    }.get(finalidade, False)


def certificado_ativo_para(empresa, finalidade: str, usuario=None) -> CertificadoDigitalEmpresa | None:
    from apps.core.models import CertificadoDigitalEmpresa

    agora = timezone.now()
    candidatos = list(
        CertificadoDigitalEmpresa.objects.filter(
        cd_empresa=empresa,
        sn_ativo=True,
        ).order_by("-created_at")
    )
    profissionais = [
        certificado
        for certificado in candidatos
        if certificado.tp_certificado == CertificadoDigitalEmpresa.TIPO_PROFISSIONAL
        and certificado.cd_usuario_profissional_id == getattr(usuario, "pk", None)
        and finalidade_habilitada(certificado, finalidade)
    ]
    institucionais = [
        certificado
        for certificado in candidatos
        if certificado.tp_certificado == CertificadoDigitalEmpresa.TIPO_INSTITUCIONAL
        and finalidade_habilitada(certificado, finalidade)
    ]
    configurados = profissionais or institucionais
    if not configurados:
        return None
    certificado = configurados[0]
    if certificado.dh_inicio_validade > agora:
        raise ErroCertificadoDigital("O certificado configurado para esta finalidade ainda não está válido.")
    if certificado.dh_fim_validade <= agora:
        raise ErroCertificadoDigital("O certificado configurado para esta finalidade está vencido.")
    try:
        pfx, senha = abrir_material_certificado(certificado)
        validar_pkcs12(pfx, senha.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ErroCertificadoDigital("A credencial protegida do certificado está inválida.") from exc
    return certificado


def validar_certificado_para_assinatura(certificado, *, empresa, finalidade: str) -> None:
    if certificado.cd_empresa_id != empresa.pk:
        raise ErroCertificadoDigital("O certificado não pertence à empresa ativa.")
    if not certificado.sn_ativo:
        raise ErroCertificadoDigital("O certificado está inativo.")
    if not finalidade_habilitada(certificado, finalidade):
        raise ErroCertificadoDigital("O certificado não está habilitado para esta finalidade.")
    agora = timezone.now()
    if certificado.dh_inicio_validade > agora:
        raise ErroCertificadoDigital("O certificado ainda não está válido.")
    if certificado.dh_fim_validade <= agora:
        raise ErroCertificadoDigital("O certificado está vencido.")


def status_certificado(certificado: CertificadoDigitalEmpresa, *, aviso_dias: int = 30) -> str:
    if not certificado.sn_ativo:
        return "INATIVO"
    agora = timezone.now()
    if certificado.dh_inicio_validade > agora:
        return "INVALIDO"
    if certificado.dh_fim_validade <= agora:
        return "VENCIDO"
    if certificado.dh_fim_validade <= agora + timedelta(days=aviso_dias):
        return "PROXIMO_DO_VENCIMENTO"
    return "VALIDO"


def testar_certificado(certificado: CertificadoDigitalEmpresa) -> MetadadosCertificado:
    pfx, senha = abrir_material_certificado(certificado)
    metadados = validar_pkcs12(pfx, senha.decode("utf-8"))
    try:
        from weasyprint import HTML

        from apps.core.services.assinatura_pdf import assinar_pdf_pades

        pdf_teste = HTML(string="<html><body><p>Teste criptográfico Celeris</p></body></html>").write_pdf()
        assinar_pdf_pades(
            pdf_teste,
            certificado,
            empresa=certificado.cd_empresa,
            finalidade=(
                "MEDICO"
                if certificado.sn_assina_documentos_medicos
                else "ADMINISTRATIVO"
                if certificado.sn_assina_documentos_administrativos
                else "OUTRO"
            ),
            motivo="Teste interno de certificado",
            localizacao="Celeris",
        )
    except Exception as exc:
        if isinstance(exc, ErroCertificadoDigital):
            raise
        raise ErroCertificadoDigital("O certificado foi aberto, mas falhou no teste de assinatura PDF.") from exc
    finally:
        pfx = b""
        senha = b""
    certificado.dh_ultima_validacao = timezone.now()
    certificado.ds_ultima_validacao = "Certificado, senha e assinatura PDF validados com sucesso."
    certificado.save(update_fields=("dh_ultima_validacao", "ds_ultima_validacao", "updated_at"))
    return metadados
