from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL_IBGE = (
    "https://servicodados.ibge.gov.br/"
    "api/v1/localidades/paises?orderBy=nome"
)

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "core"
    / "operacoes_migracao"
    / "paises_ibge_0011.py"
)


def baixar_json() -> list[dict[str, Any]]:
    request = Request(
        URL_IBGE,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip, identity",
            "User-Agent": "Celeris/1.0",
        },
    )

    try:
        with urlopen(request, timeout=60) as response:
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
            f"A API do IBGE retornou HTTP {exc.code}."
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Não foi possível acessar a API do IBGE: "
            f"{exc.reason}."
        ) from exc

    except gzip.BadGzipFile as exc:
        raise RuntimeError(
            "A resposta GZIP do IBGE está inválida."
        ) from exc

    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "Não foi possível decodificar a resposta do IBGE."
        ) from exc

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "O IBGE retornou um JSON inválido."
        ) from exc

    if not isinstance(dados, list):
        raise RuntimeError(
            "A API do IBGE retornou uma estrutura inesperada."
        )

    return dados


def obter_codigo_alpha2(pais: dict[str, Any]) -> str:
    identificadores = pais.get("id")

    if not isinstance(identificadores, dict):
        raise ValueError(
            f"Identificadores ausentes para o país "
            f"{pais.get('nome')!r}."
        )

    codigo = identificadores.get("ISO-ALPHA-2")

    if not codigo:
        raise ValueError(
            f"Código ISO Alpha-2 ausente para "
            f"{pais.get('nome')!r}."
        )

    return str(codigo).upper()


def gerar_arquivo(paises_api: list[dict[str, Any]]) -> None:
    paises: list[tuple[str, str]] = []

    for pais in paises_api:
        codigo = obter_codigo_alpha2(pais)
        nome = str(pais["nome"]).strip().upper()

        paises.append((codigo, nome))

    paises.sort(
        key=lambda item: (
            item[1],
            item[0],
        )
    )

    linhas = [
        '"""',
        "Países obtidos do Registro de Referência do IBGE.",
        "",
        "Arquivo gerado automaticamente para a migration 0011.",
        "Não editar nem substituir depois que a migration for publicada.",
        '"""',
        "",
        "PAISES: list[tuple[str, str]] = [",
    ]

    for codigo, nome in paises:
        linhas.append(
            f"    ({codigo!r}, {nome!r}),"
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

    print(f"Países gerados: {len(paises)}")
    print(f"Arquivo criado: {ARQUIVO_SAIDA}")


def main() -> None:
    gerar_arquivo(baixar_json())


if __name__ == "__main__":
    main()