from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL_CBO = (
    "https://terminologia.saude.gov.br/"
    "fhir/ValueSet-BROcupacao.json"
)

SISTEMA_CBO = (
    "https://terminologia.saude.gov.br/"
    "fhir/CodeSystem/BRCBO"
)

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "core"
    / "operacoes_migracao"
    / "ocupacoes_cbo_0012.py"
)


def baixar_json() -> dict[str, Any]:
    request = Request(
        URL_CBO,
        headers={
            "Accept": "application/fhir+json, application/json",
            "Accept-Encoding": "gzip, identity",
            "User-Agent": "Celeris/1.0",
        },
    )

    try:
        with urlopen(request, timeout=120) as response:
            conteudo = response.read()

            content_encoding = (
                response.headers.get("Content-Encoding", "")
                .strip()
                .lower()
            )

            if (
                content_encoding == "gzip"
                or conteudo.startswith(b"\x1f\x8b")
            ):
                conteudo = gzip.decompress(conteudo)

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            dados = json.loads(
                conteudo.decode(charset)
            )

    except HTTPError as exc:
        raise RuntimeError(
            f"O servidor retornou HTTP {exc.code}."
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            "Não foi possível acessar a terminologia "
            f"do Ministério da Saúde: {exc.reason}."
        ) from exc

    except gzip.BadGzipFile as exc:
        raise RuntimeError(
            "A resposta GZIP recebida está inválida."
        ) from exc

    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "Não foi possível decodificar a resposta."
        ) from exc

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "O servidor retornou um JSON inválido."
        ) from exc

    if not isinstance(dados, dict):
        raise RuntimeError(
            "A resposta possui uma estrutura inesperada."
        )

    if dados.get("resourceType") != "ValueSet":
        raise RuntimeError(
            "O recurso recebido não é um FHIR ValueSet."
        )

    return dados


def extrair_ocupacoes(
    dados: dict[str, Any],
) -> list[tuple[str, str, str]]:
    ocupacoes_por_codigo: dict[str, str] = {}

    includes = (
        dados
        .get("compose", {})
        .get("include", [])
    )

    for include in includes:
        if include.get("system") != SISTEMA_CBO:
            continue

        for conceito in include.get("concept", []):
            codigo = str(
                conceito.get("code", "")
            ).strip()

            descricao = str(
                conceito.get("display", "")
            ).strip().upper()

            if not codigo or not descricao:
                continue

            descricao_anterior = ocupacoes_por_codigo.get(
                codigo
            )

            if (
                descricao_anterior is not None
                and descricao_anterior != descricao
            ):
                raise ValueError(
                    "Código CBO repetido com descrições "
                    f"diferentes: {codigo!r}."
                )

            ocupacoes_por_codigo[codigo] = descricao

    if not ocupacoes_por_codigo:
        raise RuntimeError(
            "Nenhuma ocupação CBO foi encontrada."
        )

    ocupacoes = [
        (
            codigo,
            descricao,
            codigo[:4],
        )
        for codigo, descricao
        in ocupacoes_por_codigo.items()
    ]

    ocupacoes.sort(
        key=lambda item: (
            item[1],
            item[0],
        )
    )

    return ocupacoes


def escrever_arquivo(
    ocupacoes: list[tuple[str, str, str]],
) -> None:
    linhas = [
        '"""',
        "Ocupações da Classificação Brasileira de Ocupações.",
        "",
        "Fonte: Terminologia FHIR do Ministério da Saúde.",
        "Arquivo gerado automaticamente.",
        "Não editar manualmente.",
        '"""',
        "",
        (
            "OCUPACOES_CBO: "
            "list[tuple[str, str, str]] = ["
        ),
    ]

    for codigo, descricao, familia in ocupacoes:
        linhas.append(
            f"    ({codigo!r}, {descricao!r}, "
            f"{familia!r}),"
        )

    linhas.extend(
        [
            "]",
            "",
        ]
    )

    ARQUIVO_SAIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ARQUIVO_SAIDA.write_text(
        "\n".join(linhas),
        encoding="utf-8",
    )

    print(f"Ocupações CBO geradas: {len(ocupacoes)}")
    print(f"Arquivo criado: {ARQUIVO_SAIDA}")


def main() -> None:
    dados = baixar_json()
    ocupacoes = extrair_ocupacoes(dados)
    escrever_arquivo(ocupacoes)


if __name__ == "__main__":
    main()