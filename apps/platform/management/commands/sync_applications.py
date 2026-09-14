from django.core.management.base import BaseCommand

from apps.platform.registry import registry


class Command(BaseCommand):
    help = "Descobre manifests de applications e sincroniza menus declarados."

    def handle(self, *args, **options):
        manifests = registry.manifests()
        registry.sync_navigation()
        self.stdout.write(self.style.SUCCESS(f"{len(manifests)} aplicações descobertas."))
