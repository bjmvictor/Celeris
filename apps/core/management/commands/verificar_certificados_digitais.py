from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import CertificadoDigitalEmpresa


class Command(BaseCommand):
    help = "Lista certificados digitais ativos vencidos ou próximos do vencimento."

    def handle(self, *args, **options):
        agora = timezone.now()
        niveis = settings.CELERIS_CERTIFICATE_EXPIRY_WARNING_LEVELS or (
            settings.CELERIS_CERTIFICATE_EXPIRY_WARNING_DAYS,
        )
        limite = agora + timedelta(days=max(niveis))
        certificados = CertificadoDigitalEmpresa.objects.filter(
            sn_ativo=True,
            dh_fim_validade__lte=limite,
        ).select_related("cd_empresa")
        if not certificados:
            self.stdout.write(self.style.SUCCESS("Nenhum certificado exige atenção."))
            return
        for certificado in certificados:
            situacao = "VENCIDO" if certificado.dh_fim_validade <= agora else "PRÓXIMO DO VENCIMENTO"
            dias = max(0, (certificado.dh_fim_validade.date() - timezone.localdate()).days)
            self.stdout.write(
                self.style.WARNING(
                    f"{situacao}: empresa={certificado.cd_empresa_id} "
                    f"certificado={certificado.nm_certificado} dias={dias} "
                    f"validade={certificado.dh_fim_validade.isoformat()}"
                )
            )
