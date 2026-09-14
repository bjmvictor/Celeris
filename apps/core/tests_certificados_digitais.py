import base64
from datetime import timedelta
import warnings

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from weasyprint import HTML

from apps.accounts.models import Empresa
from apps.core.models import CertificadoDigitalEmpresa
from apps.core.services.assinatura_pdf import ErroAssinaturaPdf, assinar_pdf_pades, validar_pdf_pades
from apps.core.services.certificados_digitais import (
    ErroCertificadoDigital,
    abrir_material_certificado,
    cadastrar_certificado,
    certificado_ativo_para,
    chave_mestra_configurada,
    criptografar,
    descriptografar,
    validar_pkcs12,
)


CHAVE_MESTRA_TESTE = base64.urlsafe_b64encode(b"K" * 32).decode("ascii")


def gerar_pkcs12_teste(*, senha="senha-segura", inicio=None, fim=None, com_chave=True):
    agora = timezone.now()
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Celeris Testes"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Certificado A1 de teste"),
        ]
    )
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(inicio or agora - timedelta(days=1))
        .not_valid_after(fim or agora + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(chave, hashes.SHA256())
    )
    conteudo = pkcs12.serialize_key_and_certificates(
        name=b"celeris-test",
        key=chave if com_chave else None,
        cert=certificado,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(senha.encode("utf-8")),
    )
    return conteudo


@override_settings(
    CELERIS_CERTIFICATE_MASTER_KEY=CHAVE_MESTRA_TESTE,
    CELERIS_CERTIFICATE_MASTER_KEY_VERSION="teste-v1",
    CELERIS_CERTIFICATE_MAX_UPLOAD_SIZE=10 * 1024 * 1024,
)
class CertificadoDigitalTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=9901, nm_empresa="Empresa Certificado", sn_ativo=True)
        self.outra_empresa = Empresa.objects.create(cd_empresa=9902, nm_empresa="Outra Empresa", sn_ativo=True)
        self.usuario = get_user_model().objects.create_user(username="cert-test", password="senha-teste")
        self.usuario.empresas.add(self.empresa)
        self.senha = "senha-segura"
        self.pfx = gerar_pkcs12_teste(senha=self.senha)

    def cadastrar(self, **kwargs):
        dados = {
            "empresa": self.empresa,
            "usuario": self.usuario,
            "nome": "A1 institucional",
            "tipo": CertificadoDigitalEmpresa.TIPO_INSTITUCIONAL,
            "arquivo_nome": "certificado.p12",
            "conteudo": self.pfx,
            "senha": self.senha,
            "assina_medicos": True,
        }
        dados.update(kwargs)
        return cadastrar_certificado(**dados)

    def test_upload_valido_criptografa_certificado_e_senha(self):
        self.assertTrue(chave_mestra_configurada())
        certificado = self.cadastrar()
        self.assertNotEqual(bytes(certificado.arquivo_criptografado), self.pfx)
        self.assertNotIn(self.senha.encode("utf-8"), bytes(certificado.senha_criptografada))
        pfx, senha = abrir_material_certificado(certificado)
        self.assertEqual(pfx, self.pfx)
        self.assertEqual(senha, self.senha.encode("utf-8"))
        self.assertTrue(certificado.ds_fingerprint_sha256)

    def test_senha_incorreta_arquivo_invalido_e_arquivo_sem_chave_sao_rejeitados(self):
        with self.assertRaisesRegex(ErroCertificadoDigital, "senha incorreta"):
            validar_pkcs12(self.pfx, "senha-errada")
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            with self.assertRaisesRegex(ErroCertificadoDigital, "senha incorreta"):
                validar_pkcs12(b"nao-e-pkcs12", self.senha)
        self.assertFalse(any("PKCS#12 bundle could not be parsed" in str(aviso.message) for aviso in avisos))
        sem_chave = gerar_pkcs12_teste(senha=self.senha, com_chave=False)
        with self.assertRaisesRegex(ErroCertificadoDigital, "chave privada"):
            validar_pkcs12(sem_chave, self.senha)

    def test_certificados_vencido_e_ainda_nao_valido_sao_rejeitados(self):
        agora = timezone.now()
        vencido = gerar_pkcs12_teste(
            senha=self.senha,
            inicio=agora - timedelta(days=10),
            fim=agora - timedelta(days=1),
        )
        futuro = gerar_pkcs12_teste(
            senha=self.senha,
            inicio=agora + timedelta(days=1),
            fim=agora + timedelta(days=10),
        )
        with self.assertRaisesRegex(ErroCertificadoDigital, "vencido"):
            validar_pkcs12(vencido, self.senha)
        with self.assertRaisesRegex(ErroCertificadoDigital, "ainda não está válido"):
            validar_pkcs12(futuro, self.senha)

    def test_aes_gcm_usa_nonce_unico_e_detecta_adulteracao_e_chave_incorreta(self):
        cifrado_1, nonce_1, versao = criptografar(b"segredo", aad=b"teste")
        cifrado_2, nonce_2, _ = criptografar(b"segredo", aad=b"teste")
        self.assertNotEqual(nonce_1, nonce_2)
        self.assertNotEqual(cifrado_1, cifrado_2)
        self.assertEqual(descriptografar(cifrado_1, nonce_1, aad=b"teste", versao=versao), b"segredo")
        adulterado = bytearray(cifrado_1)
        adulterado[-1] ^= 1
        with self.assertRaises(ErroCertificadoDigital):
            descriptografar(bytes(adulterado), nonce_1, aad=b"teste", versao=versao)
        with override_settings(
            CELERIS_CERTIFICATE_MASTER_KEY=base64.urlsafe_b64encode(b"Z" * 32).decode("ascii")
        ):
            with self.assertRaises(ErroCertificadoDigital):
                descriptografar(cifrado_1, nonce_1, aad=b"teste", versao=versao)

    def test_selecao_respeita_empresa_finalidade_e_estado(self):
        certificado = self.cadastrar()
        self.assertEqual(certificado_ativo_para(self.empresa, "MEDICO", self.usuario), certificado)
        self.assertIsNone(certificado_ativo_para(self.outra_empresa, "MEDICO", self.usuario))
        certificado.sn_ativo = False
        certificado.save(update_fields=("sn_ativo", "updated_at"))
        self.assertIsNone(certificado_ativo_para(self.empresa, "MEDICO", self.usuario))

    def test_certificado_exige_finalidade_e_profissional_da_empresa(self):
        with self.assertRaises(ValidationError):
            self.cadastrar(assina_medicos=False)
        profissional_externo = get_user_model().objects.create_user(
            username="profissional-externo",
            password="senha-teste",
        )
        with self.assertRaises(ValidationError):
            self.cadastrar(
                tipo=CertificadoDigitalEmpresa.TIPO_PROFISSIONAL,
                conteudo=gerar_pkcs12_teste(senha=self.senha),
                usuario_profissional=profissional_externo,
            )

    def test_certificado_profissional_tem_prioridade_somente_para_o_titular(self):
        institucional = self.cadastrar()
        profissional = self.cadastrar(
            nome="A1 profissional",
            tipo=CertificadoDigitalEmpresa.TIPO_PROFISSIONAL,
            conteudo=gerar_pkcs12_teste(senha=self.senha),
            usuario_profissional=self.usuario,
        )
        outro_usuario = get_user_model().objects.create_user(username="outro-cert", password="senha-teste")
        self.assertEqual(certificado_ativo_para(self.empresa, "MEDICO", self.usuario), profissional)
        self.assertEqual(certificado_ativo_para(self.empresa, "MEDICO", outro_usuario), institucional)

    def test_pdf_recebe_assinatura_pades_valida_e_bloqueia_empresa_incorreta(self):
        certificado = self.cadastrar()
        pdf = HTML(string="<html><body><h1>Documento final</h1></body></html>").write_pdf()
        resultado = assinar_pdf_pades(
            pdf,
            certificado,
            empresa=self.empresa,
            finalidade="MEDICO",
            motivo="Documento de teste",
        )
        self.assertTrue(resultado.pdf.startswith(b"%PDF"))
        self.assertNotEqual(resultado.pdf, pdf)
        self.assertEqual(len(resultado.hash_sha256), 64)
        self.assertIn(resultado.campo_assinatura.encode("ascii"), resultado.pdf)
        validar_pdf_pades(resultado.pdf, certificado)
        adulterado = bytearray(resultado.pdf)
        posicao_campo = adulterado.find(resultado.campo_assinatura.encode("ascii"))
        self.assertGreater(posicao_campo, 0)
        adulterado[posicao_campo] = ord("X")
        with self.assertRaises(ErroAssinaturaPdf):
            validar_pdf_pades(bytes(adulterado), certificado)
        with self.assertRaises(ErroCertificadoDigital):
            assinar_pdf_pades(
                pdf,
                certificado,
                empresa=self.outra_empresa,
                finalidade="MEDICO",
                motivo="Empresa incorreta",
            )
        with self.assertRaises(ErroAssinaturaPdf):
            assinar_pdf_pades(
                b"conteudo-invalido",
                certificado,
                empresa=self.empresa,
                finalidade="MEDICO",
                motivo="PDF inválido",
            )
        with override_settings(CELERIS_TSA_URL="http://tsa-insegura.example"):
            with self.assertRaises(ErroAssinaturaPdf):
                assinar_pdf_pades(
                    pdf,
                    certificado,
                    empresa=self.empresa,
                    finalidade="MEDICO",
                    motivo="TSA insegura",
                )
