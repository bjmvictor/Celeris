from __future__ import annotations
import gzip
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen



URL_IBGE = (
    "https://servicodados.ibge.gov.br/"
    "api/v1/localidades/municipios?orderBy=nome"
)

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "core"
    / "operacoes_migracao"
    / "municipios_ibge.py"
)


def obter_uf(municipio: dict[str, Any]) -> str:
    regiao_imediata = municipio.get("regiao-imediata") or {}
    regiao_intermediaria = (
        regiao_imediata.get("regiao-intermediaria") or {}
    )
    uf = regiao_intermediaria.get("UF") or {}

    if uf.get("sigla"):
        return str(uf["sigla"]).upper()

    microrregiao = municipio.get("microrregiao") or {}
    mesorregiao = microrregiao.get("mesorregiao") or {}
    uf = mesorregiao.get("UF") or {}

    if uf.get("sigla"):
        return str(uf["sigla"]).upper()

    raise ValueError(
        "Não foi possível identificar a UF de "
        f"{municipio.get('nome')!r}."
    )


def baixar_municipios() -> list[dict[str, Any]]:
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
            conteudo_bytes = response.read()

            content_encoding = (
                response.headers.get("Content-Encoding", "")
                .strip()
                .lower()
            )

            # 1F 8B identifica conteúdo GZIP.
            if (
                content_encoding == "gzip"
                or conteudo_bytes.startswith(b"\x1f\x8b")
            ):
                conteudo_bytes = gzip.decompress(conteudo_bytes)

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            conteudo = conteudo_bytes.decode(charset)

    except HTTPError as exc:
        raise RuntimeError(
            f"A API do IBGE retornou HTTP {exc.code}."
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Não foi possível acessar a API do IBGE: {exc.reason}."
        ) from exc

    except gzip.BadGzipFile as exc:
        raise RuntimeError(
            "A API informou conteúdo GZIP, mas a resposta está inválida."
        ) from exc

    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "Não foi possível decodificar a resposta da API do IBGE."
        ) from exc

    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "A API do IBGE retornou um JSON inválido."
        ) from exc

    if not isinstance(dados, list):
        raise RuntimeError(
            "A API do IBGE retornou uma estrutura inesperada."
        )

    return dados


def gerar_arquivo(municipios: list[dict[str, Any]]) -> None:
    valores: list[tuple[str, str, str]] = []

    for municipio in municipios:
        codigo = str(municipio["id"])
        nome = str(municipio["nome"]).strip().upper()
        uf = obter_uf(municipio)

        valores.append((codigo, nome, uf))

    valores.sort(
        key=lambda item: (
            item[2],
            item[1],
            item[0],
        )
    )

    linhas = [
        '"""',
        "Municípios brasileiros obtidos da API oficial do IBGE.",
        "",
        "Arquivo gerado automaticamente.",
        "Não editar manualmente.",
        '"""',
        "",
        "MUNICIPIOS: list[tuple[str, str, str]] = [",
    ]

    for codigo, nome, uf in valores:
        linhas.append(
            f"    ({codigo!r}, {nome!r}, {uf!r}),"
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

    print(f"Municípios gerados: {len(valores)}")
    print(f"Arquivo: {ARQUIVO_SAIDA}")


def main() -> None:
    municipios = baixar_municipios()
    gerar_arquivo(municipios)


if __name__ == "__main__":
    main()