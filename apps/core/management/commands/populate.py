from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.platform.seeding import DemoSeedContext, seed_registry


DEMO_COMPANY_CODE = 9000
DEFAULT_PASSWORD = "12345678"


class Command(BaseCommand):
    help = "Popula uma empresa fictícia com dados realistas para teste e homologação."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa-codigo",
            type=int,
            default=DEMO_COMPANY_CODE,
            help=f"Código da empresa fictícia (padrão: {DEMO_COMPANY_CODE}).",
        )
        parser.add_argument(
            "--senha-padrao",
            default=DEFAULT_PASSWORD,
            help="Senha inicial dos usuários demo criados.",
        )
        parser.add_argument(
            "--permitir-fora-debug",
            action="store_true",
            help="Confirma conscientemente a execução quando DEBUG=False.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["permitir_fora_debug"]:
            raise CommandError(
                "O comando cria dados fictícios e está bloqueado com DEBUG=False. "
                "Em um ambiente de homologação, execute novamente com --permitir-fora-debug."
            )
        company_code = options["empresa_codigo"]
        if company_code <= 0:
            raise CommandError("--empresa-codigo deve ser um número inteiro positivo.")
        password = options["senha_padrao"]
        if len(password) < 8:
            raise CommandError("--senha-padrao deve possuir ao menos 8 caracteres.")
        if not seed_registry.providers():
            raise CommandError("Nenhum provider de dados demo está registrado.")

        seed_registry.run(
            DemoSeedContext(
                company_code=company_code,
                password=password,
                allow_non_debug=options["permitir_fora_debug"],
                stdout=self.stdout,
                style=self.style,
            )
        )
