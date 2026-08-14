from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Protocol
import hashlib
import uuid

from django.conf import settings

from apps.core.services.certificados_digitais import (
    abrir_material_certificado,
    validar_certificado_para_assinatura,
)


class ErroAssinaturaPdf(Exception):
    """Falha segura na produção ou validação de uma assinatura PDF."""


@dataclass(frozen=True)
class ResultadoAssinaturaPdf:
    pdf: bytes
    hash_sha256: str
    campo_assinatura: str
    timestamp_aplicado: bool = False


class SignerBackend(Protocol):
    def sign(
        self,
        pdf: bytes,
        certificado,
        *,
        empresa,
        finalidade: str,
        motivo: str,
        localizacao: str,
    ) -> ResultadoAssinaturaPdf: ...


class PKCS12SignerBackend:
    """Backend A1 em memória; pode ser substituído futuramente por HSM ou assinatura remota."""

    def sign(
        self,
        pdf: bytes,
        certificado,
        *,
        empresa,
        finalidade: str,
        motivo: str,
        localizacao: str = "Celeris",
    ) -> ResultadoAssinaturaPdf:
        if not pdf.startswith(b"%PDF"):
            raise ErroAssinaturaPdf("O conteúdo final não é um PDF válido.")
        validar_certificado_para_assinatura(
            certificado,
            empresa=empresa,
            finalidade=finalidade,
        )
        try:
            from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
            from pyhanko.pdf_utils.reader import PdfFileReader
            from pyhanko.sign import signers
            from pyhanko.sign.fields import SigSeedSubFilter
            from pyhanko.sign.timestamps.requests_client import HTTPTimeStamper
            from pyhanko.sign.validation import validate_pdf_signature
            from pyhanko_certvalidator import ValidationContext
        except ImportError as exc:
            raise ErroAssinaturaPdf("O componente pyHanko não está instalado no servidor.") from exc

        pfx, senha = abrir_material_certificado(certificado)
        try:
            signer = signers.SimpleSigner.load_pkcs12_data(
                pfx,
                other_certs=[],
                passphrase=senha or None,
            )
            if signer is None:
                raise ValueError("PKCS#12 sem material de assinatura")
            campo = f"CelerisSignature{uuid.uuid4().hex}"
            metadata = signers.PdfSignatureMetadata(
                field_name=campo,
                md_algorithm="sha256",
                reason=motivo,
                location=localizacao,
                name=certificado.ds_sujeito[:256],
                subfilter=SigSeedSubFilter.PADES,
            )
            tsa_url = str(getattr(settings, "CELERIS_TSA_URL", "") or "").strip()
            if tsa_url and not tsa_url.lower().startswith("https://"):
                raise ValueError("a TSA deve utilizar HTTPS")
            timestamper = (
                HTTPTimeStamper(
                    tsa_url,
                    https=True,
                    timeout=int(getattr(settings, "CELERIS_TSA_TIMEOUT", 10)),
                )
                if tsa_url
                else None
            )
            saida = BytesIO()
            signers.PdfSigner(metadata, signer=signer, timestamper=timestamper).sign_pdf(
                IncrementalPdfFileWriter(BytesIO(pdf)),
                output=saida,
            )
            assinado = saida.getvalue()
            _validar_com_certificado_pyhanko(
                assinado,
                signer.signing_cert,
                campo_esperado=campo,
                reader_class=PdfFileReader,
                validation_context_class=ValidationContext,
                validate_function=validate_pdf_signature,
            )
        except Exception as exc:
            raise ErroAssinaturaPdf("Não foi possível assinar e validar o PDF final.") from exc
        finally:
            pfx = b""
            senha = b""
        return ResultadoAssinaturaPdf(
            pdf=assinado,
            hash_sha256=hashlib.sha256(assinado).hexdigest(),
            campo_assinatura=campo,
            timestamp_aplicado=bool(tsa_url),
        )


def assinar_pdf_pades(
    pdf: bytes,
    certificado,
    *,
    empresa,
    finalidade: str,
    motivo: str,
    localizacao: str = "Celeris",
    backend: SignerBackend | None = None,
) -> ResultadoAssinaturaPdf:
    return (backend or PKCS12SignerBackend()).sign(
        pdf,
        certificado,
        empresa=empresa,
        finalidade=finalidade,
        motivo=motivo,
        localizacao=localizacao,
    )


def _validar_com_certificado_pyhanko(
    pdf: bytes,
    certificado_assinante,
    *,
    campo_esperado="",
    reader_class=None,
    validation_context_class=None,
    validate_function=None,
) -> None:
    if reader_class is None:
        from pyhanko.pdf_utils.reader import PdfFileReader as reader_class
        from pyhanko.sign.validation import validate_pdf_signature as validate_function
        from pyhanko_certvalidator import ValidationContext as validation_context_class
    leitor = reader_class(BytesIO(pdf))
    assinaturas = list(leitor.embedded_signatures)
    if not assinaturas:
        raise ValueError("assinatura não encontrada no PDF")
    assinatura = assinaturas[-1]
    if campo_esperado and assinatura.field_name != campo_esperado:
        raise ValueError("campo de assinatura divergente")
    status = validate_function(
        assinatura,
        signer_validation_context=validation_context_class(
            trust_roots=[certificado_assinante],
            allow_fetching=False,
        ),
        skip_diff=False,
    )
    if not status.intact or not status.valid:
        raise ValueError("assinatura sem integridade criptográfica")


def validar_pdf_pades(pdf: bytes, certificado) -> None:
    """Revalida um PDF persistido sem expor o material privado fora do backend."""
    pfx = b""
    senha = b""
    try:
        from pyhanko.sign import signers

        pfx, senha = abrir_material_certificado(certificado)
        signer = signers.SimpleSigner.load_pkcs12_data(pfx, other_certs=[], passphrase=senha or None)
        if signer is None:
            raise ValueError("PKCS#12 sem material de assinatura")
        _validar_com_certificado_pyhanko(pdf, signer.signing_cert)
    except Exception as exc:
        raise ErroAssinaturaPdf("A assinatura do PDF não é válida ou o documento foi alterado.") from exc
    finally:
        pfx = b""
        senha = b""
