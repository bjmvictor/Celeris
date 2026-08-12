import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.catalogos import atualizar_item_catalogo, modelo_catalogo
from apps.core.models import Cep


class Command(BaseCommand):
    help = "Importa CEP, CID ou tipos de logradouro de um CSV com colunas codigo,descricao,grupo."

    def add_arguments(self, parser):
        parser.add_argument("tabela", choices=("cep", "cid", "tipo_logradouro"))
        parser.add_argument("arquivo")
        parser.add_argument("--separador", default=";")

    def handle(self, *args, **options):
        path = Path(options["arquivo"])
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        tema = options["tabela"]
        if tema != "cep":
            modelo_catalogo(tema)
        imported = 0
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=options["separador"])
            required = {"codigo", "descricao"}
            if not required.issubset(reader.fieldnames or []):
                raise CommandError("O CSV deve conter as colunas codigo e descricao; grupo é opcional.")
            for row in reader:
                code = (row.get("codigo") or "").strip()[:40]
                description = (row.get("descricao") or "").strip()[:160]
                if not code or not description:
                    continue
                grupo = (row.get("grupo") or "").strip()[:40]
                if tema == "cep":
                    Cep.objects.update_or_create(
                        nr_cep="".join(character for character in code if character.isdigit())[:8],
                        defaults={"ds_logradouro": description, "ds_cidade": grupo, "sn_ativo": True},
                    )
                else:
                    atualizar_item_catalogo(
                        tema,
                        code,
                        ds_valor=description,
                        ds_grupo=grupo,
                        sn_ativo=True,
                    )
                imported += 1
        self.stdout.write(self.style.SUCCESS(f"{imported} registro(s) importado(s) em {options['tabela']}."))
