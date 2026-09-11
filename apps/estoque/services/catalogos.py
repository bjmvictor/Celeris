from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError


def _mensagens_formulario(form) -> list[str]:
    return [
        f"{form.fields.get(campo).label if campo in form.fields else campo}: {mensagem}"
        for campo, mensagens in form.errors.items()
        for mensagem in mensagens
    ]


@transaction.atomic
def salvar_linhas_catalogo(
    *,
    queryset,
    form_class,
    post,
    empresa,
    campos: tuple[str, ...],
    valores_forcados: dict | None = None,
) -> int:
    valores_forcados = valores_forcados or {}
    ids = {
        int(resultado.group(1))
        for chave in post.keys()
        if (resultado := re.match(r"linha_(\d+)-", chave))
    }
    ids.update(
        int(chave.removeprefix("delete_"))
        for chave in post.keys()
        if chave.startswith("delete_") and chave.removeprefix("delete_").isdigit()
    )
    registros = {
        registro.pk: registro
        for registro in queryset.select_for_update().filter(pk__in=ids)
    }
    erros = []
    alterados = 0
    for registro_id in sorted(ids):
        registro = registros.get(registro_id)
        if not registro:
            continue
        if post.get(f"delete_{registro_id}") == "1":
            if hasattr(registro, "sn_ativo"):
                registro.sn_ativo = False
                registro.save(update_fields=["sn_ativo", "updated_at"])
            else:
                try:
                    registro.delete()
                except ProtectedError:
                    erros.append(f"{registro} está em uso e não pode ser excluído.")
            alterados += 1
            continue
        prefixo = f"linha_{registro_id}"
        if not any(chave.startswith(f"{prefixo}-") for chave in post.keys()):
            continue
        formulario = form_class(post, instance=registro, empresa=empresa, prefix=prefixo)
        if formulario.is_valid():
            objeto = formulario.save(commit=False)
            for campo, valor in valores_forcados.items():
                setattr(objeto, campo, valor)
            objeto.save()
            formulario.save_m2m()
            alterados += 1
        else:
            erros.extend(_mensagens_formulario(formulario))

    listas = {campo: post.getlist(f"new_{campo}") for campo in campos}
    total_novos = max((len(valores) for valores in listas.values()), default=0)
    for indice in range(total_novos):
        dados = {
            campo: valores[indice] if indice < len(valores) else ""
            for campo, valores in listas.items()
        }
        if not any(str(valor).strip() for campo, valor in dados.items() if not campo.startswith("sn_")):
            continue
        formulario = form_class(dados, empresa=empresa)
        if formulario.is_valid():
            objeto = formulario.save(commit=False)
            for campo, valor in valores_forcados.items():
                setattr(objeto, campo, valor)
            objeto.save()
            formulario.save_m2m()
            alterados += 1
        else:
            erros.extend(_mensagens_formulario(formulario))
    if erros:
        raise ValidationError(erros)
    return alterados
