import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.core.models import TabelaAuxiliarGlobal, ValorAuxiliarGlobal


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
        table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
            ds_tabela=options["tabela"],
            defaults={"ds_descricao": options["tabela"].replace("_", " ").upper(), "sn_ativo": True},
        )
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
                ValorAuxiliarGlobal.objects.update_or_create(
                    cd_tabela_auxiliar_global=table,
                    cd_valor=code,
                    defaults={
                        "ds_valor": description,
                        "ds_grupo": (row.get("grupo") or "").strip()[:40],
                        "sn_ativo": True,
                    },
                )
                imported += 1
        self.stdout.write(self.style.SUCCESS(f"{imported} registro(s) importado(s) em {options['tabela']}."))
