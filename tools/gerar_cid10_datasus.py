from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URLS_DATASUS = [
    (
        "https://www2.datasus.gov.br/"
        "cid10/V2008/downloads/CID10CSV.zip"
    ),
    (
        "http://www2.datasus.gov.br/"
        "cid10/V2008/downloads/CID10CSV.zip"
    ),
]

NOME_ARQUIVO_CSV = "CID-10-SUBCATEGORIAS.CSV"

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "apps"
    / "core"
    / "operacoes_migracao"
    / "cid10_0029.py"
)


def baixar_zip() -> tuple[bytes, str]:
    ultimo_erro: Exception | None = None

    for url in URLS_DATASUS:
        request = Request(
            url,
            headers={
                "Accept": (
                    "application/zip,"
                    "application/octet-stream,*/*"
                ),
                "User-Agent": "Celeris-CID10/1.0",
            },
        )

        try:
            with urlopen(request, timeout=120) as response:
                conteudo = response.read()

            if not conteudo.startswith(b"PK"):
                raise RuntimeError(
                    "O conteúdo recebido não é um arquivo ZIP."
                )

            return conteudo, url

        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            ultimo_erro = exc

    raise RuntimeError(
        "Não foi possível baixar a tabela CID-10 do DATASUS."
    ) from ultimo_erro


def localizar_csv(arquivo_zip: zipfile.ZipFile) -> str:
    nome_esperado = NOME_ARQUIVO_CSV.upper()

    for nome in arquivo_zip.namelist():
        nome_simples = Path(nome).name.upper()

        if nome_simples == nome_esperado:
            return nome

    arquivos = ", ".join(arquivo_zip.namelist())

    raise RuntimeError(
        f"O arquivo {NOME_ARQUIVO_CSV!r} não foi encontrado "
        f"dentro do ZIP. Arquivos disponíveis: {arquivos}"
    )


def formatar_codigo(valor: str) -> str:
    """
    Converte:
        A000 -> A00.0
        E119 -> E11.9
        I10  -> I10
    """
    codigo = re.sub(
        r"[^A-Z0-9]",
        "",
        valor.strip().upper(),
    )

    if len(codigo) < 3:
        raise ValueError(
            f"Código CID inválido: {valor!r}"
        )

    if len(codigo) == 3:
        return codigo

    return f"{codigo[:3]}.{codigo[3:]}"


def ler_cids(
    conteudo_zip: bytes,
) -> list[tuple[str, str, str]]:
    with zipfile.ZipFile(
        io.BytesIO(conteudo_zip)
    ) as arquivo_zip:
        nome_csv = localizar_csv(arquivo_zip)
        conteudo_csv = arquivo_zip.read(nome_csv)

    # O DATASUS informa que os arquivos estão em ISO-8859-1.
    texto = conteudo_csv.decode("latin-1")

    leitor = csv.DictReader(
        io.StringIO(texto),
        delimiter=";",
    )

    cids_por_codigo: dict[str, tuple[str, str]] = {}

    for numero_linha, linha_original in enumerate(
        leitor,
        start=2,
    ):
        linha = {
            str(chave).strip().upper(): (
                str(valor).strip()
                if valor is not None
                else ""
            )
            for chave, valor in linha_original.items()
            if chave is not None
        }

        codigo_bruto = linha.get("SUBCAT", "")
        descricao = linha.get("DESCRICAO", "")

        if not codigo_bruto or not descricao:
            continue

        try:
            codigo = formatar_codigo(codigo_bruto)
        except ValueError as exc:
            raise ValueError(
                f"Erro na linha {numero_linha}: {exc}"
            ) from exc

        categoria = codigo[:3]

        existente = cids_por_codigo.get(codigo)

        if existente is not None:
            descricao_anterior, _ = existente

            if descricao_anterior != descricao:
                raise ValueError(
                    f"O código {codigo!r} apareceu com "
                    "descrições diferentes."
                )

            continue

        cids_por_codigo[codigo] = (
            descricao,
            categoria,
        )

    if not cids_por_codigo:
        raise RuntimeError(
            "Nenhum código CID-10 foi encontrado."
        )

    return [
        (
            codigo,
            descricao,
            categoria,
        )
        for codigo, (descricao, categoria)
        in sorted(cids_por_codigo.items())
    ]


def escrever_arquivo(
    cids: list[tuple[str, str, str]],
    fonte: str,
) -> None:
    linhas = [
        '"""',
        "CID-10 brasileira obtida da base oficial do DATASUS.",
        "",
        "Arquivo gerado automaticamente.",
        "Não editar manualmente.",
        '"""',
        "",
        f"CID10_FONTE = {fonte!r}",
        'CID10_VERSAO = "DATASUS V2008"',
        "",
        "CID10: list[tuple[str, str, str]] = [",
    ]

    for codigo, descricao, categoria in cids:
        linhas.append(
            f"    ({codigo!r}, {descricao!r}, "
            f"{categoria!r}),"
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

    print(f"Códigos CID-10 gerados: {len(cids)}")
    print(f"Arquivo criado: {ARQUIVO_SAIDA}")


def main() -> None:
    conteudo_zip, fonte = baixar_zip()
    cids = ler_cids(conteudo_zip)
    escrever_arquivo(cids, fonte)


if __name__ == "__main__":
    main()