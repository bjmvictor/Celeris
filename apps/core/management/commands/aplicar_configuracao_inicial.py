import tomllib
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Empresa, Setor
from apps.atendimento.models import Convenio
from apps.core.models import TabelaAuxiliarGlobal, ValorAuxiliarGlobal


class Command(BaseCommand):
    help = "Aplica os arquivos TOML de configuração inicial da empresa e dos catálogos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--diretorio",
            default=str(settings.BASE_DIR / "configuracao_inicial"),
            help="Diretório que contém os arquivos TOML.",
        )
        parser.add_argument(
            "--validar",
            action="store_true",
            help="Valida todos os arquivos habilitados sem alterar o banco.",
        )

    def handle(self, *args, **options):
        directory = Path(options["diretorio"]).resolve()
        if not directory.is_dir():
            raise CommandError(f"Diretório de configuração não encontrado: {directory}")

        fixed_files = {
            "empresas": directory / "empresas.toml",
            "setores": directory / "setores.toml",
            "convenios": directory / "convenios.toml",
        }
        missing = [str(path) for path in fixed_files.values() if not path.is_file()]
        if missing:
            raise CommandError("Arquivos obrigatórios não encontrados:\n- " + "\n- ".join(missing))

        documents = {name: self._load(path) for name, path in fixed_files.items()}
        catalog_documents = [
            (path, self._load(path))
            for path in sorted(directory.glob("catalogo_*.toml"))
        ]
        enabled_documents = [document for document in documents.values() if document["habilitado"]]
        enabled_documents.extend(document for _, document in catalog_documents if document["habilitado"])
        if not enabled_documents:
            raise CommandError(
                "Nenhum arquivo está habilitado. Preencha os arquivos e altere habilitado para true."
            )

        self._validate(documents, catalog_documents)
        if options["validar"]:
            total = sum(len(document["registros"]) for document in enabled_documents)
            self.stdout.write(self.style.SUCCESS(f"Configuração válida: {total} registro(s) pronto(s) para aplicação."))
            return

        counters = {"empresas": 0, "setores": 0, "convenios": 0, "catalogos": 0}
        with transaction.atomic():
            if documents["empresas"]["habilitado"]:
                for record in documents["empresas"]["registros"]:
                    Empresa.objects.update_or_create(
                        cd_empresa=int(record["codigo"]),
                        defaults={
                            "nm_empresa": record["nome"].strip(),
                            "nr_cnpj": record.get("cnpj", "").strip(),
                            "nr_cnes": record.get("cnes", "").strip(),
                            "ds_razao_social": record.get("razao_social", "").strip(),
                            "ds_nome_fantasia": record.get("nome_fantasia", "").strip(),
                            "ds_email": record.get("email", "").strip(),
                            "nr_telefone": record.get("telefone", "").strip(),
                            "ds_endereco": record.get("endereco", "").strip(),
                            "nr_endereco": str(record.get("numero", "")).strip(),
                            "ds_bairro": record.get("bairro", "").strip(),
                            "ds_cidade": record.get("cidade", "").strip(),
                            "sg_estado": record.get("uf", "").strip().upper(),
                            "nr_cep": record.get("cep", "").strip(),
                            "sn_ativo": record.get("ativo", True),
                        },
                    )
                    counters["empresas"] += 1

            if documents["setores"]["habilitado"]:
                for record in documents["setores"]["registros"]:
                    company = Empresa.objects.get(cd_empresa=int(record["empresa_codigo"]))
                    Setor.objects.update_or_create(
                        cd_empresa=company,
                        tp_setor=record["tipo"].strip().upper(),
                        nm_setor=record["nome"].strip(),
                        defaults={
                            "ds_observacao": record.get("observacao", "").strip(),
                            "sn_ativo": record.get("ativo", True),
                        },
                    )
                    counters["setores"] += 1

            if documents["convenios"]["habilitado"]:
                for record in documents["convenios"]["registros"]:
                    company = Empresa.objects.get(cd_empresa=int(record["empresa_codigo"]))
                    Convenio.objects.update_or_create(
                        cd_empresa=company,
                        nm_convenio=record["nome"].strip(),
                        defaults={"sn_ativo": record.get("ativo", True)},
                    )
                    counters["convenios"] += 1

            for _, document in catalog_documents:
                if not document["habilitado"]:
                    continue
                table, _ = TabelaAuxiliarGlobal.objects.update_or_create(
                    ds_tabela=document["tabela"].strip(),
                    defaults={
                        "ds_descricao": document["descricao"].strip(),
                        "sn_ativo": True,
                    },
                )
                for record in document["registros"]:
                    ValorAuxiliarGlobal.objects.update_or_create(
                        cd_tabela_auxiliar_global=table,
                        cd_valor=record["codigo"].strip(),
                        defaults={
                            "ds_valor": record["descricao"].strip(),
                            "ds_grupo": record.get("grupo", "").strip(),
                            "sn_ativo": record.get("ativo", True),
                        },
                    )
                    counters["catalogos"] += 1

        total = sum(counters.values())
        details = ", ".join(f"{name}: {value}" for name, value in counters.items())
        self.stdout.write(self.style.SUCCESS(f"Configuração aplicada: {total} registro(s) ({details})."))

    def _load(self, path):
        try:
            with path.open("rb") as source:
                document = tomllib.load(source)
        except tomllib.TOMLDecodeError as exc:
            raise CommandError(f"TOML inválido em {path}: {exc}") from exc
        records = document.get("registros", [])
        if not isinstance(records, list):
            raise CommandError(f'O campo "registros" deve ser uma lista em {path}.')
        document["registros"] = records
        document["habilitado"] = document.get("habilitado", False) is True
        document["_arquivo"] = str(path)
        return document

    def _validate(self, documents, catalog_documents):
        errors = []
        configured_company_codes = {
            self._positive_integer(record.get("codigo"), "codigo", document, errors)
            for document in (documents["empresas"],)
            if document["habilitado"]
            for record in document["registros"]
        }
        configured_company_codes.discard(None)
        existing_company_codes = set(Empresa.objects.values_list("cd_empresa", flat=True))

        if documents["empresas"]["habilitado"]:
            for record in documents["empresas"]["registros"]:
                self._required_text(record, "nome", documents["empresas"], errors)
                uf = str(record.get("uf", "")).strip()
                if uf and len(uf) != 2:
                    errors.append(f'{documents["empresas"]["_arquivo"]}: uf deve possuir 2 caracteres.')

        for name in ("setores", "convenios"):
            document = documents[name]
            if not document["habilitado"]:
                continue
            for record in document["registros"]:
                company_code = self._positive_integer(record.get("empresa_codigo"), "empresa_codigo", document, errors)
                if company_code and company_code not in configured_company_codes | existing_company_codes:
                    errors.append(f'{document["_arquivo"]}: empresa_codigo {company_code} não existe.')
                self._required_text(record, "nome", document, errors)
                if name == "setores":
                    sector_type = str(record.get("tipo", "")).strip().upper()
                    if sector_type not in Setor.TipoSetor.values:
                        errors.append(
                            f'{document["_arquivo"]}: tipo deve ser EMPRESA ou ATENDIMENTO.'
                        )

        seen_tables = set()
        for path, document in catalog_documents:
            if not document["habilitado"]:
                continue
            table_name = self._required_text(document, "tabela", document, errors)
            self._required_text(document, "descricao", document, errors)
            if table_name in seen_tables:
                errors.append(f"{path}: o catálogo {table_name} está repetido em outro arquivo.")
            seen_tables.add(table_name)
            seen_codes = set()
            for record in document["registros"]:
                code = self._required_text(record, "codigo", document, errors)
                self._required_text(record, "descricao", document, errors)
                if code in seen_codes:
                    errors.append(f"{path}: código de catálogo repetido: {code}.")
                seen_codes.add(code)

        if errors:
            raise CommandError("Configuração inicial inválida:\n- " + "\n- ".join(errors))

    @staticmethod
    def _required_text(record, field, document, errors):
        value = str(record.get(field, "")).strip()
        if not value:
            errors.append(f'{document["_arquivo"]}: campo obrigatório ausente: {field}.')
        return value

    @staticmethod
    def _positive_integer(value, field, document, errors):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 0
        if parsed <= 0:
            errors.append(f'{document["_arquivo"]}: {field} deve ser um número inteiro positivo.')
            return None
        return parsed
