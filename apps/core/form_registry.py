"""Persistence-backed configuration for forms registered by applications."""
from django.db import OperationalError, ProgrammingError

from apps.platform.form_registry import form_registry

from .models import ConfiguracaoCampoFormulario


def opcoes_formularios():
    return [(definition.code, definition.name) for definition in form_registry.definitions()]


def construir_formulario_referencia(codigo, empresa):
    return form_registry.build(codigo, empresa)


def listar_campos_formulario(codigo, empresa):
    definition = form_registry.get(codigo)
    formulario = construir_formulario_referencia(codigo, empresa)
    if definition is None or formulario is None:
        return []
    try:
        configuracoes = {
            item.cd_campo: item
            for item in ConfiguracaoCampoFormulario.objects.filter(
                cd_empresa=empresa,
                cd_formulario=codigo,
            )
        }
    except (OperationalError, ProgrammingError):
        configuracoes = {}
    campos = []
    for ordem, (nome, campo) in enumerate(formulario.fields.items()):
        configuracao = configuracoes.get(nome)
        campos.append(
            {
                "formulario": codigo,
                "nome_formulario": definition.name,
                "chave": f"{codigo}::{nome}",
                "codigo": nome,
                "nome": definition.field_labels.get(
                    nome,
                    campo.label or nome.replace("_", " ").title(),
                ),
                "tipo": campo.__class__.__name__,
                "obrigatorio": configuracao.sn_obrigatorio if configuracao else campo.required,
                "editavel": not campo.disabled,
                "ordem": ordem,
            }
        )
    return campos


def consultar_campos_formularios(empresa, codigo_formulario="", nome_campo=""):
    codigos = [codigo_formulario] if form_registry.get(codigo_formulario) else [
        definition.code for definition in form_registry.definitions()
    ]
    termo = (nome_campo or "").strip().casefold()
    campos = []
    for codigo in codigos:
        for campo in listar_campos_formulario(codigo, empresa):
            if termo and termo not in campo["nome"].casefold() and termo not in campo["codigo"].casefold():
                continue
            campos.append(campo)
    return campos


def aplicar_configuracao_formulario(formulario, codigo, empresa):
    if not empresa:
        return formulario
    try:
        configuracoes = ConfiguracaoCampoFormulario.objects.filter(
            cd_empresa=empresa,
            cd_formulario=codigo,
            cd_campo__in=formulario.fields,
        )
        for configuracao in configuracoes:
            campo = formulario.fields.get(configuracao.cd_campo)
            if not campo or campo.disabled:
                continue
            campo.required = configuracao.sn_obrigatorio
            campo.widget.attrs["aria-required"] = "true" if campo.required else "false"
            if campo.required:
                campo.widget.attrs["required"] = "required"
            else:
                campo.widget.attrs.pop("required", None)
    except (OperationalError, ProgrammingError):
        pass
    return formulario
