from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, RequestDataTooBig
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Max, Prefetch, Q
from django import forms
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from datetime import datetime, timedelta
from html import escape as html_escape, unescape as html_unescape
from html.parser import HTMLParser
from io import BytesIO
import calendar
import ast
import base64
import copy
import gzip
import hashlib
import json
import logging
import random
import re
from types import SimpleNamespace
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import bleach
from bleach.css_sanitizer import CSSSanitizer
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.accounts.models import Empresa, Setor
from apps.core.locks import (
    adquirir_trava_edicao,
    consultar_trava_ativa,
    liberar_trava_edicao,
    nome_usuario_trava,
    usuario_tem_trava_ou_livre,
)
from apps.core.models import TabelaAuxiliarGlobal, ValorAuxiliarGlobal
from apps.core.permissions import role_required
from apps.core.table_utils import paginate_table

from .forms import AgendamentoForm, AtendimentoForm, CadastroAtendimentoForm, EscalaForm, EvolucaoAtendimentoForm, PacienteForm, PacienteSearchForm, PainelChamadaForm, PreAtendimentoForm, PrescricaoForm, PrestadorForm, RegraSubdivisaoSenhaForm, ResponsavelAtendimentoForm, ResultadoExameForm, SolicitacaoExameForm, TipoSenhaAtendimentoForm
from .models import (
    AcessoClinicoAuditado,
    AnexoClinico,
    Atendimento,
    AtendimentoFluxo,
    AtendimentoPrestador,
    AgendaGerada,
    AgendaProfissional,
    Agendamento,
    ChamadaPainel,
    ClasseSenhaAtendimento,
    Convenio,
    DocumentoClinico,
    DominioExternoPermitido,
    EscalaClinica,
    EventoDocumentoClinico,
    EvolucaoAtendimento,
    HistoricoAlteracaoPaciente,
    HorarioAgenda,
    IconeChamada,
    ItemMenuAssistencial,
    MaquinaChamada,
    ModeloDocumento,
    Paciente,
    PainelChamada,
    PainelChamadaSetor,
    PastaDocumento,
    PerfilAssistencial,
    PerfilAssistencialTipo,
    PerfilAssistencialVersao,
    PreAtendimento,
    Prescricao,
    Prestador,
    PrestadorTipo,
    ProtocoloSenhaAtendimento,
    RascunhoEditorDocumento,
    RegraSubdivisaoSenha,
    ResponsavelAtendimento,
    ResultadoEscalaClinica,
    ResultadoExame,
    SolicitacaoExame,
    SenhaAtendimento,
    TipoSenhaAtendimento,
)


logger = logging.getLogger("celeris.atendimento")

def _tipos_prestador_usuario(usuario):
    prestador = getattr(usuario, "cd_prestador", None)
    if not prestador:
        return []
    return prestador.tipos_prestador_ativos


def _perfis_assistenciais_usuario(usuario, empresa):
    tipos = _tipos_prestador_usuario(usuario)
    if not tipos:
        return PerfilAssistencial.objects.none()
    base_normalizados = PerfilAssistencial.objects.filter(
        cd_empresa=empresa,
        tipos_vinculados__sn_ativo=True,
        tipos_vinculados__cd_tipo_prestador__in=tipos,
    )
    normalizados = base_normalizados.filter(sn_ativo=True).distinct()
    if normalizados.exists():
        return normalizados
    normalizados_inativos = base_normalizados.distinct()
    if normalizados_inativos.exists():
        return normalizados_inativos
    ids_legados = [
        perfil.pk
        for perfil in PerfilAssistencial.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if set(perfil.tipos_prestador or []).intersection(tipos)
    ]
    return PerfilAssistencial.objects.filter(pk__in=ids_legados)


def _itens_menu_assistencial_mesclados(usuario, empresa):
    perfis = list(_perfis_assistenciais_usuario(usuario, empresa))
    if not perfis:
        return perfis, []
    itens = []
    for perfil in perfis:
        versao = (
            perfil.versoes.filter(ds_status="RASCUNHO").first()
            or perfil.versoes.filter(ds_status="PUBLICADO").first()
        )
        queryset = perfil.itens.select_related(
            "cd_modelo_documento",
            "cd_item_pai",
            "cd_versao_perfil",
            "cd_perfil_assistencial",
        ).filter(sn_ativo=True)
        if versao:
            queryset = queryset.filter(Q(cd_versao_perfil=versao) | Q(cd_versao_perfil__isnull=True))
        itens.extend(queryset)

    mesclados = {}
    id_para_chave = {}
    for item in sorted(itens, key=lambda value: (value.nr_ordem, value.pk)):
        chave = item.cd_item_tecnico or f"{item.tp_item}:{item.nm_item.strip().upper()}"
        id_para_chave[item.pk] = chave
        if chave not in mesclados:
            mesclados[chave] = copy.copy(item)
            mesclados[chave].perfis_origem = [item.cd_perfil_assistencial]
            continue
        atual = mesclados[chave]
        if item.cd_perfil_assistencial.sn_sigiloso and not atual.cd_perfil_assistencial.sn_sigiloso:
            perfis_origem = atual.perfis_origem
            anterior = atual
            atual = copy.copy(item)
            atual.perfis_origem = perfis_origem
            atual.sn_privado = anterior.sn_privado
            atual.sn_imprimivel = anterior.sn_imprimivel
            atual.sn_permite_criar = anterior.sn_permite_criar
            atual.sn_permite_abandonar = anterior.sn_permite_abandonar
            atual.sn_permite_cancelar = anterior.sn_permite_cancelar
            atual.sn_somente_historico = anterior.sn_somente_historico
            mesclados[chave] = atual
        atual.sn_privado = atual.sn_privado or item.sn_privado
        atual.sn_imprimivel = atual.sn_imprimivel and item.sn_imprimivel
        atual.sn_permite_criar = atual.sn_permite_criar and item.sn_permite_criar
        atual.sn_permite_abandonar = atual.sn_permite_abandonar and item.sn_permite_abandonar
        atual.sn_permite_cancelar = atual.sn_permite_cancelar and item.sn_permite_cancelar
        atual.sn_somente_historico = atual.sn_somente_historico or item.sn_somente_historico
        atual.nr_ordem = min(atual.nr_ordem, item.nr_ordem)
        atual.perfis_origem.append(item.cd_perfil_assistencial)

    resultado = list(mesclados.values())
    for item in resultado:
        item.chave_mesclagem = item.cd_item_tecnico or f"{item.tp_item}:{item.nm_item.strip().upper()}"
        item.chave_pai_mesclagem = id_para_chave.get(item.cd_item_pai_id)
        item.filhos_renderizados = []
    return perfis, sorted(resultado, key=lambda value: (value.nr_ordem, value.pk))


def _marcar_ramo_menu_assistencial(itens, item_selecionado):
    selecionado_id = getattr(item_selecionado, "pk", None)

    def marcar(item):
        filhos = list(getattr(item, "filhos_renderizados", []) or [])
        ativo = item.pk == selecionado_id
        for filho in filhos:
            ativo = marcar(filho) or ativo
        item.tem_item_ativo = ativo
        return ativo

    for item in itens:
        marcar(item)


def _preparar_arvore_menu_assistencial(itens, grupo_atual=None):
    grupo_atual_id = getattr(grupo_atual, "pk", None)

    def preparar(item):
        filhos = list(getattr(item, "filhos_renderizados", []) or [])
        for filho in filhos:
            preparar(filho)
        item.tem_subgrupo_renderizado = any(getattr(filho, "tp_item", "") == "GRUPO" for filho in filhos)
        item.eh_grupo_atual = bool(grupo_atual_id and item.pk == grupo_atual_id)
        primeira_tela = next((filho for filho in filhos if getattr(filho, "tp_item", "") != "GRUPO"), None)
        if not primeira_tela:
            primeira_tela = next((getattr(filho, "primeira_tela_renderizada", None) for filho in filhos if getattr(filho, "primeira_tela_renderizada", None)), None)
        item.primeira_tela_renderizada = primeira_tela
        item.url_abrir_grupo = getattr(primeira_tela, "url_renderizada", "") or getattr(item, "url_inicio_renderizada", "") or getattr(item, "url_renderizada", "#")

    for item in itens:
        preparar(item)


def _normalizar_chave_tecnica_assistencial(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return re.sub(r"[^A-Z0-9]+", "_", texto.upper()).strip("_")


def _url_externa_permitida(empresa, url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    return DominioExternoPermitido.objects.filter(
        cd_empresa=empresa,
        ds_dominio__iexact=parsed.hostname,
        sn_ativo=True,
    ).first()


def _calcular_expressao_escala(expressao, pontos):
    texto = str(expressao or "").strip()
    if not texto:
        return None
    texto = re.sub(
        r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}",
        lambda match: match.group(1),
        texto,
    )
    operadores = {
        ast.Add: lambda left, right: left + right,
        ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right,
        ast.Div: lambda left, right: left / right,
        ast.Mod: lambda left, right: left % right,
    }

    def avaliar(node):
        if isinstance(node, ast.Expression):
            return avaliar(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in pontos:
            return float(pontos[node.id])
        if isinstance(node, ast.BinOp) and type(node.op) in operadores:
            return operadores[type(node.op)](avaliar(node.left), avaliar(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = avaliar(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        raise ValueError("A expressão contém uma operação não permitida.")

    return avaliar(ast.parse(texto, mode="eval"))


def _calcular_resultado_escala(escala, pontos):
    resultado_expressao = _calcular_expressao_escala(escala.ds_expressao_calculo, pontos)
    if resultado_expressao is not None:
        return resultado_expressao
    valores = list(pontos.values())
    resultado = sum(valores)
    if escala.tp_calculo == "MEDIA" and valores:
        resultado /= len(valores)
    return resultado


def _faixa_resultado_escala(faixas, resultado):
    def numero(valor, padrao):
        if valor in (None, ""):
            return padrao
        return float(valor)

    for faixa in faixas or []:
        operador = str(faixa.get("operador") or "INTERVALO").upper()
        valor = numero(faixa.get("valor", faixa.get("min")), float("-inf"))
        valor_final = numero(faixa.get("valor_final", faixa.get("max")), float("inf"))
        corresponde = {
            ">=": resultado >= valor,
            ">": resultado > valor,
            "<=": resultado <= valor,
            "<": resultado < valor,
            "=": resultado == valor,
            "INTERVALO": valor <= resultado <= valor_final,
        }.get(operador, False)
        if corresponde:
            return faixa
    return {}


def _usuario_pode_operar_documento(usuario, documento):
    if usuario.is_superuser:
        return True
    item = documento.cd_item_menu_assistencial
    if not item:
        grupos = set(usuario.groups.values_list("name", flat=True))
        return bool(grupos.intersection({
            "TI", "Médico", "Médico", "Enfermeiro", "Laboratório", "Laboratorio",
        }))
    return _perfis_assistenciais_usuario(usuario, documento.cd_empresa).filter(
        pk=item.cd_perfil_assistencial_id
    ).exists()


def _usuario_pode_visualizar_documento(usuario, documento):
    if _usuario_pode_operar_documento(usuario, documento):
        return True
    item = documento.cd_item_menu_assistencial
    if not item:
        return False
    if item.sn_privado or item.cd_perfil_assistencial.sn_sigiloso:
        return False
    return _perfis_assistenciais_usuario(usuario, documento.cd_empresa).exists()


def _configurar_assinatura_prestador(html, modelo):
    conteudo = html or ""
    conteudo = re.sub(
        r'<section[^>]*data-celeris-signature="true"[^>]*>.*</section>',
        "",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not modelo.sn_exibe_assinatura:
        return conteudo
    alinhamento = {
        "ESQUERDA": "left",
        "DIREITA": "right",
    }.get(modelo.tp_alinhamento_assinatura, "center")
    margem_bloco = {
        "left": "40px auto 0 0",
        "right": "40px 0 0 auto",
        "center": "40px auto 0",
    }[alinhamento]
    identificacao = "{{ prestador.nome }}"
    if modelo.sn_exibe_conselho_assinatura:
        identificacao += " - {{ prestador.conselho }} {{ prestador.numero_conselho }} {{ prestador.uf_conselho }}"
    assinatura = (
        f'<section data-celeris-signature="true" style="display:block;width:92mm;min-width:72mm;'
        f'max-width:100%;margin:{margem_bloco};break-before:avoid;page-break-before:avoid;'
        f'break-inside:avoid;text-align:{alinhamento}">'
        f'<div style="width:100%;height:18px;border-bottom:1px solid #111;margin:0 0 3px"></div>'
        f"<strong>{identificacao}</strong>"
        "</section>"
    )
    if "</main>" in conteudo:
        return conteudo.replace("</main>", f"{assinatura}</main>", 1)
    return f"{conteudo}{assinatura}"


def _impressao_possui_grade(modelo):
    conteudo = f"{modelo.ds_html_impressao or ''}\n{modelo.ds_css_impressao or ''}"
    return "grid-template-columns" in conteudo and "grid-column" in conteudo


class _HtmlFragmentNode:
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, tag=None, attrs=None):
        self.tag = tag
        self.attrs = list(attrs or [])
        self.children = []

    def attr(self, name, default=""):
        name = name.lower()
        for key, value in self.attrs:
            if key.lower() == name:
                return value or ""
        return default

    def set_attr(self, name, value):
        for index, (key, _value) in enumerate(self.attrs):
            if key.lower() == name.lower():
                self.attrs[index] = (key, value)
                return
        self.attrs.append((name, value))

    def append(self, child):
        self.children.append(child)

    def serialize(self):
        if self.tag is None:
            return "".join(child.serialize() if isinstance(child, _HtmlFragmentNode) else child for child in self.children)
        attrs = "".join(
            f' {html_escape(str(key), quote=True)}="{html_escape(str(value or ""), quote=True)}"'
            for key, value in self.attrs
            if value is not None
        )
        if self.tag.lower() in self.VOID_TAGS:
            return f"<{self.tag}{attrs}>"
        children = "".join(child.serialize() if isinstance(child, _HtmlFragmentNode) else child for child in self.children)
        return f"<{self.tag}{attrs}>{children}</{self.tag}>"


class _HtmlFragmentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = _HtmlFragmentNode()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _HtmlFragmentNode(tag, attrs)
        self.stack[-1].append(node)
        if tag.lower() not in _HtmlFragmentNode.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].append(_HtmlFragmentNode(tag, attrs))

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag and self.stack[index].tag.lower() == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].append(data)

    def handle_entityref(self, name):
        self.stack[-1].append(f"&{name};")

    def handle_charref(self, name):
        self.stack[-1].append(f"&#{name};")


def _normalizar_grade_html_para_pdf(html, row_height=0):
    if not html or "display:grid" not in html and "display: grid" not in html:
        return html or ""

    parser = _HtmlFragmentParser()
    parser.feed(html)
    parser.close()

    def estilo(node):
        return node.attr("style") if isinstance(node, _HtmlFragmentNode) else ""

    def limpar_estilo_grade(valor):
        resultado = valor or ""
        for propriedade in (
            "grid-column",
            "grid-row",
            "grid-template-columns",
            "grid-template-rows",
            "display",
            "gap",
        ):
            resultado = re.sub(rf"{propriedade}\s*:[^;]+;?", "", resultado, flags=re.I)
        return resultado.strip()

    def posicao(valor, propriedade):
        match = re.search(rf"{propriedade}\s*:\s*(\d+)\s*(?:/\s*span\s*(\d+))?", valor or "", flags=re.I)
        return (
            max(1, int(match.group(1))) if match else 1,
            max(1, int(match.group(2) or 1)) if match else 1,
        )

    def contar_colunas(style, elementos):
        repeat = re.search(r"grid-template-columns\s*:\s*repeat\(\s*(\d+)", style or "", flags=re.I)
        if repeat:
            return max(1, int(repeat.group(1)))
        minmax = len(re.findall(r"minmax\s*\(", style or "", flags=re.I))
        if minmax:
            return max(1, minmax)
        return max(1, *(posicao(elemento[1], "grid-column")[0] + posicao(elemento[1], "grid-column")[1] - 1 for elemento in elementos))

    def contar_linhas(style, elementos):
        repeat = re.search(r"grid-template-rows\s*:\s*repeat\(\s*(\d+)", style or "", flags=re.I)
        if repeat:
            return max(1, int(repeat.group(1)))
        return max(1, *(posicao(elemento[1], "grid-row")[0] + posicao(elemento[1], "grid-row")[1] - 1 for elemento in elementos))

    def alinhamento_vertical(style):
        if re.search(r"align-self\s*:\s*(end|flex-end)\b", style or "", flags=re.I):
            return "bottom"
        if re.search(r"align-self\s*:\s*center\b", style or "", flags=re.I):
            return "middle"
        return "top"

    def converter(node):
        if not isinstance(node, _HtmlFragmentNode):
            return node
        node_style = estilo(node)
        if not re.search(r"display\s*:\s*grid\b", node_style, flags=re.I) or not re.search(r"grid-template-columns\s*:", node_style, flags=re.I):
            node.children = [converter(child) for child in node.children]
            return node
        elementos = []
        for child in node.children:
            if not isinstance(child, _HtmlFragmentNode):
                continue
            child_style = estilo(child)
            if re.search(r"grid-column\s*:", child_style, flags=re.I):
                elementos.append((child, child_style, converter(child)))
        if not elementos:
            node.children = [converter(child) for child in node.children]
            return node

        colunas = contar_colunas(node_style, elementos)
        linhas = contar_linhas(node_style, elementos)
        itens = []
        for original, child_style, elemento in elementos:
            coluna, colspan = posicao(child_style, "grid-column")
            linha, rowspan = posicao(child_style, "grid-row")
            coluna = min(coluna, colunas)
            colspan = min(colspan, max(1, colunas - coluna + 1))
            itens.append({
                "node": elemento,
                "coluna": coluna,
                "linha": linha,
                "colspan": colspan,
                "rowspan": rowspan,
                "vertical": alinhamento_vertical(child_style),
            })
        itens.sort(key=lambda item: (item["linha"], item["coluna"]))
        por_inicio = {(item["linha"], item["coluna"]): item for item in itens}
        ocupadas = set()
        linhas_nodes = []
        for linha in range(1, linhas + 1):
            tr = _HtmlFragmentNode("tr", [("style", f"height:{row_height}px;min-height:{row_height}px")])
            for coluna in range(1, colunas + 1):
                if (linha, coluna) in ocupadas:
                    continue
                item = por_inicio.get((linha, coluna))
                if item:
                    elemento = item["node"]
                    elemento.set_attr("style", limpar_estilo_grade(estilo(elemento)))
                    attrs = [
                        ("style", f'vertical-align:{item["vertical"]};padding:0;border:0;min-width:0;overflow-wrap:anywhere;word-break:break-word'),
                    ]
                    if item["colspan"] > 1:
                        attrs.append(("colspan", str(item["colspan"])))
                    if item["rowspan"] > 1:
                        attrs.append(("rowspan", str(item["rowspan"])))
                    td = _HtmlFragmentNode("td", attrs)
                    td.append(elemento)
                    for offset_linha in range(item["rowspan"]):
                        for offset_coluna in range(item["colspan"]):
                            if offset_linha or offset_coluna:
                                ocupadas.add((linha + offset_linha, coluna + offset_coluna))
                else:
                    td = _HtmlFragmentNode("td", [("style", f"vertical-align:top;padding:0;border:0;min-width:0;height:{row_height}px;overflow-wrap:anywhere;word-break:break-word")])
                    if row_height:
                        td.append("&nbsp;")
                tr.append(td)
            linhas_nodes.append(tr)

        table = _HtmlFragmentNode(
            "table",
            [
                ("class", "pdf-grid-table"),
                ("role", "presentation"),
                ("style", f"width:100%;max-width:100%;border-collapse:collapse;table-layout:fixed;{limpar_estilo_grade(node_style)}"),
            ],
        )
        colgroup = _HtmlFragmentNode("colgroup")
        for _coluna in range(colunas):
            colgroup.append(_HtmlFragmentNode("col", [("style", f"width:{100 / colunas}%")]))
        tbody = _HtmlFragmentNode("tbody")
        for tr in linhas_nodes:
            tbody.append(tr)
        table.append(colgroup)
        table.append(tbody)
        return table

    parser.root.children = [converter(child) for child in parser.root.children]
    return parser.root.serialize()


def _modelo_possui_layout_impressao(modelo):
    projeto = modelo.ds_projeto_impressao if isinstance(modelo.ds_projeto_impressao, dict) else {}
    layout = projeto.get("printLayout") if isinstance(projeto, dict) else {}
    return bool(isinstance(layout, dict) and layout.get("elements"))


def _formatar_texto_rico_documento(conteudo):
    resultado = str(conteudo or "")
    resultado = re.sub(r"<left>", '<div style="text-align:left">', resultado, flags=re.I)
    resultado = re.sub(r"</left>", "</div>", resultado, flags=re.I)
    resultado = re.sub(r"<center>", '<div style="text-align:center">', resultado, flags=re.I)
    resultado = re.sub(r"</center>", "</div>", resultado, flags=re.I)
    resultado = re.sub(r"<right>", '<div style="text-align:right">', resultado, flags=re.I)
    resultado = re.sub(r"</right>", "</div>", resultado, flags=re.I)
    resultado = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", resultado)
    resultado = re.sub(r"\*([^*\n]+)\*", r"<strong>\1</strong>", resultado)
    resultado = re.sub(r"_([^_\n]+)_", r"<u>\1</u>", resultado)
    resultado = re.sub(r"(^|[\s(>])/([^/\n<>]+?)/(?=$|[\s.,;!?<)])", r"\1<em>\2</em>", resultado)
    return resultado


def _gerar_tela_pela_grade(modelo):
    projeto = modelo.ds_projeto_tela if isinstance(modelo.ds_projeto_tela, dict) else {}
    grade = projeto.get("grid") or {}
    campos = projeto.get("formFields") or []
    if not campos:
        return modelo.ds_html_tela or ""

    colunas = max(1, min(12, int(grade.get("columns") or 1)))
    linhas = max(1, min(80, int(grade.get("rows") or 1)))
    fonte_tamanho_padrao = max(7, min(72, int(grade.get("fontSize") or 14)))
    fonte_padrao = conditional_escape(grade.get("fontFamily") or "Arial, sans-serif")

    def numero(valor, padrao=1, minimo=1, maximo=2400):
        try:
            return max(minimo, min(maximo, int(float(valor))))
        except (TypeError, ValueError):
            return padrao

    def nome_campo(campo):
        nome = campo.get("name") or campo.get("label") or "campo"
        return re.sub(r"[^a-zA-Z0-9_]+", "_", str(nome)).strip("_").lower() or "campo"

    def posicao_grade(campo):
        coluna = max(1, min(colunas, numero(campo.get("col"), 1, 1, colunas)))
        linha = max(1, min(linhas, numero(campo.get("row"), 1, 1, linhas)))
        colspan = max(1, min(colunas - coluna + 1, numero(campo.get("colSpan"), 1, 1, colunas)))
        rowspan = max(1, min(linhas - linha + 1, numero(campo.get("rowSpan"), 1, 1, linhas)))
        return coluna, linha, colspan, rowspan

    def estilo_posicao(campo):
        coluna, linha, colspan, rowspan = posicao_grade(campo)
        return f"grid-column:{coluna} / span {colspan};grid-row:{linha} / span {rowspan}"

    def estilo_campo(campo):
        fonte_tamanho = numero(campo.get("fontSize"), fonte_tamanho_padrao, 7, 72)
        fonte = conditional_escape(campo.get("fontFamily") or fonte_padrao)
        cor = conditional_escape(campo.get("textColor") or "#111111")
        extras = []
        if campo.get("margin"):
            extras.append(f"margin:{conditional_escape(campo.get('margin'))}")
        if campo.get("padding"):
            extras.append(f"padding:{conditional_escape(campo.get('padding'))}")
        extras.append(f"--field-font-size:{fonte_tamanho}px")
        extras.append(f"font-size:{fonte_tamanho + 1}px")
        extras.append(f"font-family:{fonte}")
        extras.append(f"color:{cor}")
        return f"{estilo_posicao(campo)};" + ";".join(extras)

    def estilo_texto(campo):
        fonte_tamanho = numero(campo.get("fontSize"), fonte_tamanho_padrao, 7, 72)
        fonte = conditional_escape(campo.get("fontFamily") or fonte_padrao)
        cor = conditional_escape(campo.get("textColor") or "#111111")
        extras = []
        if campo.get("margin"):
            extras.append(f"margin:{conditional_escape(campo.get('margin'))}")
        if campo.get("padding"):
            extras.append(f"padding:{conditional_escape(campo.get('padding'))}")
        extras.append(f"font-size:{fonte_tamanho}px")
        extras.append(f"font-family:{fonte}")
        extras.append(f"color:{cor}")
        return f"{estilo_posicao(campo)};" + ";".join(extras)

    def opcoes_estruturadas(texto):
        opcoes = []
        atual = []
        dentro_chaves = False
        entre_aspas = None
        for char in str(texto or ""):
            if entre_aspas:
                atual.append(char)
                if char == entre_aspas:
                    entre_aspas = None
                continue
            if char in {'"', "'"}:
                entre_aspas = char
                atual.append(char)
            elif char == "[":
                dentro_chaves = True
                atual.append(char)
            elif char == "]":
                dentro_chaves = False
                atual.append(char)
            elif char == "," and not dentro_chaves:
                valor = "".join(atual).strip()
                if valor:
                    opcoes.append(valor)
                atual = []
            else:
                atual.append(char)
        valor = "".join(atual).strip()
        if valor:
            opcoes.append(valor)
        return opcoes

    def parse_embutido(texto):
        valor = str(texto or "").strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in {'"', "'"}:
            return {"tipo": "literal", "texto": valor[1:-1]}
        match = re.match(r"^(?P<label>[^\[]*)\[(?P<body>[^\]]+)\]\s*$", valor)
        if not match:
            return {"tipo": "campo", "label": valor, "nome": nome_campo({"name": valor}), "placeholder": ""}
        partes = [parte.strip() for parte in re.split(r"[;,]", match.group("body"), maxsplit=1)]
        return {
            "tipo": "campo",
            "label": match.group("label").strip(),
            "nome": nome_campo({"name": partes[0]}),
            "placeholder": partes[1] if len(partes) > 1 else "",
        }

    elementos = []
    for campo in sorted(campos, key=lambda item: (item.get("row") or 0, item.get("col") or 0, str(item.get("id") or ""))):
        tipo = campo.get("type") or "text"
        nome = nome_campo(campo)
        estilo = estilo_campo(campo)
        rotulo = conditional_escape(campo.get("label") or "")
        obrigatorio = " required" if campo.get("required") else ""
        readonly = ' disabled tabindex="-1" aria-disabled="true"' if campo.get("readonly") else ""
        placeholder = f' placeholder="{conditional_escape(campo.get("placeholder"))}"' if campo.get("placeholder") else ""
        valor_binding = f"{{{{ {conditional_escape(campo.get('binding'))} }}}}" if campo.get("binding") else ""

        if tipo == "static-text":
            conteudo = _formatar_texto_rico_documento(campo.get("content"))
            classe = "generated-screen-title" if campo.get("displayStyle") == "title" else f"generated-screen-{campo.get('displayStyle') or 'text'}"
            tag = "h2" if campo.get("displayStyle") == "title" else "div"
            elementos.append(f'<{tag} class="{classe}" style="{estilo_texto(campo)}">{conteudo}</{tag}>')
        elif tipo == "static-variable":
            label = str(campo.get("label") or "").strip()
            conteudo = f"{f'<strong>{conditional_escape(label)}:</strong> ' if label else ''}{valor_binding}"
            elementos.append(f'<div class="generated-screen-variable" style="{estilo}">{conteudo}</div>')
        elif tipo == "line":
            largura = max(3 if campo.get("lineStyle") == "double" else 1, numero(campo.get("lineWidth"), 1, 1, 20))
            elementos.append(
                f'<div class="generated-screen-line" style="{estilo_posicao(campo)};margin-top:{numero(campo.get("marginTop"), 0, 0, 200)}px;margin-bottom:{numero(campo.get("marginBottom"), 0, 0, 200)}px"><hr style="margin:0;border:0;'
                f'border-top:{largura}px {conditional_escape(campo.get("lineStyle") or "solid")} {conditional_escape(campo.get("lineColor") or "#111")}"></div>'
            )
        elif tipo == "image":
            largura = numero(campo.get("imageWidth"), 120, 1, 2400)
            altura = numero(campo.get("imageHeight"), 80, 1, 2400)
            elementos.append(
                f'<div class="generated-image-field" style="{estilo}"><img src="{conditional_escape(campo.get("imageUrl") or "")}" '
                f'alt="{conditional_escape(campo.get("label") or "Imagem")}" style="width:{largura}px;height:{altura}px;object-fit:contain"></div>'
            )
        elif tipo == "textarea":
            elementos.append(f'<label style="{estilo}">{rotulo}<textarea data-document-field="true" name="campo_{nome}" rows="5"{placeholder}{obrigatorio}{readonly}>{valor_binding}</textarea></label>')
        elif tipo in {"select", "auxiliary"}:
            if tipo == "auxiliary":
                source = (
                    f' data-option-source="auxiliary" data-source-table="{conditional_escape(campo.get("sourceTable"))}"'
                    f' data-source-value-field="{conditional_escape(campo.get("sourceValueField") or "cd_valor")}"'
                    f' data-source-display-field="{conditional_escape(campo.get("sourceDisplayField") or "ds_valor")}"'
                )
                opcoes = ""
            else:
                source = ""
                opcoes = "".join(f'<option value="{conditional_escape(opcao.strip())}">{conditional_escape(opcao.strip())}</option>' for opcao in str(campo.get("options") or "").split(",") if opcao.strip())
            elementos.append(f'<label style="{estilo}">{rotulo}<select data-document-field="true" name="campo_{nome}"{source}{obrigatorio}{readonly}><option value=""></option>{opcoes}</select></label>')
        elif tipo == "exclusive-checkboxes":
            opcoes = []
            for opcao in opcoes_estruturadas(campo.get("options")):
                parsed = parse_embutido(opcao)
                if parsed["tipo"] == "literal":
                    opcoes.append(f'<span class="generated-exclusive-literal">{conditional_escape(parsed["texto"])}</span>')
                    continue
                tem_detalhe = "[" in str(opcao)
                detalhe = f'<input class="generated-exclusive-detail" data-auto-size-input="true" data-document-field="true" data-exclusive-detail="{conditional_escape(parsed["label"])}" name="campo_{conditional_escape(parsed["nome"])}" type="text" disabled tabindex="-1" placeholder="{conditional_escape(parsed["placeholder"])}">' if tem_detalhe else ""
                classe_opcao = "generated-exclusive-option generated-exclusive-option-with-detail" if tem_detalhe else "generated-exclusive-option"
                opcoes.append(f'<label class="{classe_opcao}"><input data-document-field="true" data-exclusive-choice="campo_{nome}" name="campo_{nome}" type="checkbox" value="{conditional_escape(parsed["label"])}"{readonly}><span>{conditional_escape(parsed["label"])}</span>{detalhe}</label>')
            elementos.append(f'<fieldset class="generated-exclusive-checkboxes" style="{estilo}" data-exclusive-group="campo_{nome}" data-exclusive-required="{str(bool(campo.get("required"))).lower()}" data-exclusive-readonly="{str(bool(campo.get("readonly"))).lower()}"><legend>{rotulo or "&nbsp;"}</legend><div>{"".join(opcoes)}</div></fieldset>')
        elif tipo == "multiple-fields":
            controles = []
            for opcao in opcoes_estruturadas(campo.get("options")):
                parsed = parse_embutido(opcao)
                if parsed["tipo"] == "literal":
                    controles.append(f'<span class="generated-multiple-literal">{conditional_escape(parsed["texto"])}</span>')
                else:
                    label = f'<span>{conditional_escape(parsed["label"])}</span>' if parsed["label"] else ""
                    controles.append(f'<label class="generated-multiple-item">{label}<input data-document-field="true" name="campo_{conditional_escape(parsed["nome"])}" type="text" placeholder="{conditional_escape(parsed["placeholder"])}"{obrigatorio}{readonly}></label>')
            elementos.append(f'<fieldset class="generated-multiple-fields" style="{estilo}"><legend>{rotulo or "&nbsp;"}</legend><div>{"".join(controles)}</div></fieldset>')
        elif tipo == "checkbox":
            if campo.get("booleanStyle") == "single":
                elementos.append(f'<fieldset class="generated-boolean-field" style="{estilo}" data-boolean-style="single"><legend>{rotulo or "&nbsp;"}</legend><label class="provider-checkbox"><input data-document-field="true" name="campo_{nome}" type="checkbox"{obrigatorio}{readonly}><span>Sim</span></label></fieldset>')
            else:
                elementos.append(f'<fieldset class="generated-exclusive-checkboxes generated-boolean-field" style="{estilo}" data-exclusive-group="campo_{nome}" data-exclusive-required="{str(bool(campo.get("required"))).lower()}" data-exclusive-readonly="{str(bool(campo.get("readonly"))).lower()}" data-boolean-style="double"><legend>{rotulo or "&nbsp;"}</legend><div><label class="generated-exclusive-option"><input data-document-field="true" data-exclusive-choice="campo_{nome}" name="campo_{nome}" type="checkbox" value="Sim"{readonly}><span>Sim</span></label><label class="generated-exclusive-option"><input data-document-field="true" data-exclusive-choice="campo_{nome}" name="campo_{nome}" type="checkbox" value="Não"{readonly}><span>Não</span></label></div></fieldset>')
        else:
            input_html = f'<input data-document-field="true" name="campo_{nome}" type="{conditional_escape(tipo)}" value="{valor_binding}"{placeholder}{obrigatorio}{readonly}>'
            if tipo in {"text", "number"} and (campo.get("prefix") or campo.get("suffix")):
                prefixo = f'<span>{conditional_escape(campo.get("prefix"))}</span>' if campo.get("prefix") else ""
                sufixo = f'<span>{conditional_escape(campo.get("suffix"))}</span>' if campo.get("suffix") else ""
                input_html = f'<span class="generated-field-affix">{prefixo}{input_html}{sufixo}</span>'
            elementos.append(f'<label style="{estilo}">{rotulo}{input_html}</label>')

    return (
        f'<section class="generated-clinical-form" style="grid-template-columns:repeat({colunas},minmax(0,1fr));'
        f'grid-template-rows:repeat({linhas},minmax(0,auto))">{"".join(elementos)}</section>'
    )


def _gerar_impressao_pela_grade(modelo):
    projeto_impressao = modelo.ds_projeto_impressao if isinstance(modelo.ds_projeto_impressao, dict) else {}
    layout = projeto_impressao.get("printLayout") if isinstance(projeto_impressao, dict) else {}
    if not isinstance(layout, dict) or not layout.get("elements"):
        return modelo.ds_html_impressao or ""

    grade = layout.get("grid") or {}
    elementos_layout = layout.get("elements") or []
    def _numero(valor, padrao=1, minimo=1, maximo=2400):
        try:
            return max(minimo, min(maximo, int(float(valor))))
        except (TypeError, ValueError):
            return padrao

    colunas = max(1, min(12, _numero(grade.get("columns"), 1, 1, 12)))
    linhas_configuradas = max(1, min(80, _numero(grade.get("rows"), 1, 1, 80)))
    linhas_ocupadas = max(
        1,
        *(
            _numero(elemento.get("row"), 1, 1, linhas_configuradas)
            + _numero(elemento.get("rowSpan"), 1, 1, linhas_configuradas)
            - 1
            for elemento in elementos_layout
        ),
    )
    linhas = max(1, min(80, linhas_ocupadas))
    fonte_tamanho = max(7, min(72, _numero(grade.get("fontSize"), 11, 7, 72)))
    fonte_familia = conditional_escape(grade.get("fontFamily") or "Arial, sans-serif")
    elemento_documento = str(getattr(modelo, "tp_elemento", "") or "").upper()
    altura_linha_fixa = 0

    def _posicao(elemento):
        coluna = max(1, min(colunas, _numero(elemento.get("col"), 1, 1, colunas)))
        linha = max(1, min(linhas, _numero(elemento.get("row"), 1, 1, linhas)))
        colspan = max(1, min(colunas - coluna + 1, _numero(elemento.get("colSpan"), 1, 1, colunas)))
        rowspan = max(1, min(linhas - linha + 1, _numero(elemento.get("rowSpan"), 1, 1, linhas)))
        return coluna, linha, colspan, rowspan

    def _estilo_base(elemento):
        estilos = [
            "min-width:0",
            "max-width:100%",
            "box-sizing:border-box",
        ]
        if elemento.get("margin"):
            estilos.append(f"margin:{conditional_escape(elemento.get('margin'))}")
        if elemento.get("padding"):
            estilos.append(f"padding:{conditional_escape(elemento.get('padding'))}")
        if elemento.get("fontSize"):
            estilos.append(f"font-size:{_numero(elemento.get('fontSize'), fonte_tamanho, 7, 72)}px")
        if elemento.get("fontFamily"):
            estilos.append(f"font-family:{conditional_escape(elemento.get('fontFamily'))}")
        return ";".join(estilos)

    def _alinhamento_vertical(elemento):
        return {
            "center": "middle",
            "end": "bottom",
        }.get(elemento.get("verticalAlign"), "top")

    def _variavel(nome):
        nome = str(nome or "").strip()
        return f"{{{{ {conditional_escape(nome)} }}}}" if nome else ""

    def _conteudo_texto(elemento):
        return _formatar_texto_rico_documento(elemento.get("content"))

    elementos = []

    def _adicionar_elemento(elemento, html):
        elementos.append({"elemento": elemento, "html": html})

    for elemento in elementos_layout:
        tipo = elemento.get("type") or "field"
        estilo = _estilo_base(elemento)
        if tipo == "image":
            largura = _numero(elemento.get("imageWidth"), 120, 1, 2400)
            altura = _numero(elemento.get("imageHeight"), 80, 1, 2400)
            _adicionar_elemento(elemento,
                f'<div class="pdf-layout-image-box" style="{estilo};position:relative;width:{largura}px;'
                f'max-width:100%;height:{altura}px;overflow:visible;line-height:0">'
                f'<img src="{conditional_escape(elemento.get("imageUrl") or "")}" alt="{conditional_escape(elemento.get("label") or "")}" '
                f'style="display:block;width:{largura}px;height:{altura}px;max-width:100%;object-fit:contain"></div>'
            )
            continue

        if tipo == "line":
            espessura = max(3 if elemento.get("lineStyle") == "double" else 1, _numero(elemento.get("lineWidth"), 1, 1, 20))
            _adicionar_elemento(elemento,
                f'<div style="{estilo};overflow:visible">'
                f'<hr style="margin:0;border:0;border-top:{espessura}px {conditional_escape(elemento.get("lineStyle") or "solid")} {conditional_escape(elemento.get("lineColor") or "#111")}"></div>'
            )
            continue

        if tipo == "vline":
            espessura = max(3 if elemento.get("lineStyle") == "double" else 1, _numero(elemento.get("lineWidth"), 1, 1, 20))
            _, _, _, rowspan = _posicao(elemento)
            altura_minima = max(24, rowspan * 24)
            _adicionar_elemento(elemento,
                f'<div style="{estilo};justify-self:center;width:0;min-height:{altura_minima}px;height:100%;'
                f'border-left:{espessura}px {conditional_escape(elemento.get("lineStyle") or "solid")} {conditional_escape(elemento.get("lineColor") or "#111")}"></div>'
            )
            continue

        if tipo == "pagebreak":
            _adicionar_elemento(elemento, f'<div style="{estilo};height:0;min-height:0;break-after:page;page-break-after:always"></div>')
            continue

        if tipo == "variable":
            fonte_valor = "700" if elemento.get("textBold") else "400"
            rotulo = str(elemento.get("label") or "").strip()
            rotulo_html = f'<strong style="color:{conditional_escape(elemento.get("labelColor") or "#111")}">{conditional_escape(rotulo)}:</strong> ' if rotulo else ""
            texto = _variavel(elemento.get("sourceField"))
            _adicionar_elemento(elemento,
                f'<div style="{estilo};width:100%;text-align:{conditional_escape(elemento.get("textAlign") or "left")};'
                'overflow-wrap:anywhere;word-break:break-word;white-space:normal">'
                f'{rotulo_html}<span style="color:{conditional_escape(elemento.get("textColor") or "#111")};font-weight:{fonte_valor}">{texto}</span></div>'
            )
            continue

        if tipo in {"text", "html"}:
            _adicionar_elemento(elemento,
                f'<div style="{estilo};width:100%;overflow-wrap:anywhere;word-break:break-word;white-space:normal">'
                f'{_conteudo_texto(elemento)}</div>'
            )
            continue

        rotulo = conditional_escape(elemento.get("label") or "")
        conteudo = _conteudo_texto(elemento) if re.search(r"</(strong|b|em|i|u|span|br|div|p)\b", str(elemento.get("content") or ""), re.I) else conditional_escape(elemento.get("content") or "")
        rotulo_html = f"<strong>{rotulo}:</strong> " if rotulo and not elemento.get("hideLabel") else ""
        borda = ";border-bottom:1px solid #d1d5db" if elemento.get("showBottomBorder") is not False else ""
        _adicionar_elemento(elemento,
            f'<div style="{estilo};width:100%;min-height:20px{borda};overflow-wrap:anywhere;word-break:break-word;white-space:normal">'
            f"{rotulo_html}{conteudo}</div>"
        )

    posicoes = []
    for item in elementos:
        coluna, linha, colspan, rowspan = _posicao(item["elemento"])
        posicoes.append({
            "coluna": coluna,
            "linha": linha,
            "colspan": colspan,
            "rowspan": rowspan,
            "html": item["html"],
            "vertical": _alinhamento_vertical(item["elemento"]),
        })
    posicoes.sort(key=lambda item: (item["linha"], item["coluna"]))
    por_inicio = {(item["linha"], item["coluna"]): item for item in posicoes}
    ocupadas = set()
    linhas_html = []
    for linha in range(1, linhas + 1):
        celulas = []
        for coluna in range(1, colunas + 1):
            if (linha, coluna) in ocupadas:
                continue
            item = por_inicio.get((linha, coluna))
            if item:
                for offset_linha in range(item["rowspan"]):
                    for offset_coluna in range(item["colspan"]):
                        if offset_linha or offset_coluna:
                            ocupadas.add((linha + offset_linha, coluna + offset_coluna))
                span_coluna = f' colspan="{item["colspan"]}"' if item["colspan"] > 1 else ""
                span_linha = f' rowspan="{item["rowspan"]}"' if item["rowspan"] > 1 else ""
                conteudo_item = item["html"]
                altura_celula = max(altura_linha_fixa, altura_linha_fixa * item["rowspan"])
                if altura_linha_fixa:
                    alinhamento_flex = {
                        "top": "flex-start",
                        "middle": "center",
                        "bottom": "flex-end",
                    }.get(item["vertical"], "flex-start")
                    conteudo_item = (
                        f'<div class="pdf-grid-fixed-cell" style="height:{altura_celula}px;min-height:{altura_celula}px;'
                        f'display:flex;flex-direction:column;justify-content:{alinhamento_flex};'
                        f'align-items:stretch;overflow:visible;min-width:0;max-width:100%;box-sizing:border-box">'
                        f'{conteudo_item}</div>'
                    )
                celulas.append(
                    f'<td{span_coluna}{span_linha} style="vertical-align:{item["vertical"]};padding:0;border:0;'
                    f'min-width:0;height:{altura_celula}px;overflow:visible;overflow-wrap:anywhere;word-break:break-word">{conteudo_item}</td>'
                )
            else:
                altura_celula = altura_linha_fixa
                conteudo_vazio = "&nbsp;" if altura_celula else ""
                celulas.append(
                    f'<td style="vertical-align:top;padding:0;border:0;min-width:0;height:{altura_celula}px;'
                    f'overflow-wrap:anywhere;word-break:break-word">{conteudo_vazio}</td>'
                )
        linhas_html.append(f'<tr style="height:{altura_linha_fixa}px;min-height:{altura_linha_fixa}px">{"".join(celulas)}</tr>')
    colunas_html = "".join(f'<col style="width:{100 / colunas}%">' for _ in range(colunas))
    conteudo = (
        '<table class="pdf-grid-table" role="presentation" '
        'style="width:100%;max-width:100%;border-collapse:collapse;table-layout:fixed">'
        f'<colgroup>{colunas_html}</colgroup>'
        f'{"".join(linhas_html)}</table>'
    )
    fit_one_page = "true" if grade.get("fitOnePage") else "false"
    html = (
        f'<main data-celeris-grid-print="true" data-fit-one-page="{fit_one_page}" style="width:100%;max-width:100%;margin:0;'
        f'padding:2px;background:transparent;color:#111;box-sizing:border-box;font-size:{fonte_tamanho}px;'
        f'font-family:{fonte_familia};line-height:1.15;overflow-wrap:anywhere;word-break:break-word">'
        f'{conteudo}</main>'
    )
    return html


def _safe_return_url(request):
    candidate = request.POST.get("return_to") or request.GET.get("return_to", "")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return ""


def _idade(data_nascimento):
    if not data_nascimento:
        return ""
    hoje = timezone.localdate()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))


def _parse_date(value, fallback=None):
    try:
        return datetime.fromisoformat(value).date() if value else fallback
    except ValueError:
        return fallback


def _feriados():
    valores = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="feriado",
        sn_ativo=True,
    )
    datas = set()
    for valor in valores:
        for raw in (valor.cd_valor, valor.ds_valor):
            texto = str(raw or "").strip()
            for formato in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    datas.add(datetime.strptime(texto[:10], formato).date())
                    break
                except ValueError:
                    continue
    return datas


def _dias_com_agenda(empresa, inicio, fim):
    return set(
        HorarioAgenda.objects.filter(
            cd_empresa=empresa,
            dh_inicio__date__gte=inicio,
            dh_inicio__date__lte=fim,
        )
        .exclude(ds_status="CANCELADO")
        .values_list("dh_inicio__date", flat=True)
    )


def _dias_com_agendamento(empresa, inicio, fim):
    return set(
        Agendamento.objects.filter(
            cd_empresa=empresa,
            dh_agendamento__date__gte=inicio,
            dh_agendamento__date__lte=fim,
        )
        .exclude(ds_status="CANCELADO")
        .values_list("dh_agendamento__date", flat=True)
    )


def _calendario_mensal(empresa, data_selecionada, data_final=None):
    primeiro = data_selecionada.replace(day=1)
    ultimo_dia = calendar.monthrange(primeiro.year, primeiro.month)[1]
    ultimo = primeiro.replace(day=ultimo_dia)
    feriados = _feriados()
    dias_com_agenda = _dias_com_agenda(empresa, primeiro, ultimo)
    dias_com_agendamento = _dias_com_agendamento(empresa, primeiro, ultimo)
    semanas = []
    for semana in calendar.Calendar(firstweekday=6).monthdatescalendar(primeiro.year, primeiro.month):
        semanas.append([
            {
                "date": dia,
                "iso": dia.isoformat(),
                "day": dia.day,
                "in_month": dia.month == primeiro.month,
                "selected": dia == data_selecionada or (data_final and data_selecionada <= dia <= data_final),
                "holiday": dia in feriados,
                "has_schedule": dia in dias_com_agenda,
                "has_appointment": dia in dias_com_agendamento,
                "today": dia == timezone.localdate(),
            }
            for dia in semana
        ])
    anterior = (primeiro - timedelta(days=1)).replace(day=1)
    proximo = (ultimo + timedelta(days=1)).replace(day=1)
    return {
        "month": primeiro,
        "weeks": semanas,
        "previous": anterior,
        "next": proximo,
        "weekdays": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
    }


def _criar_documento_clinico(atendimento, tipo, titulo, conteudo, user, status="ABERTO", origem=None):
    status_final = {
        "RASCUNHO": "ABERTO",
        "FINALIZADO": "FECHADO",
        "ASSINADO": "FECHADO",
    }.get(status, status)
    documento = DocumentoClinico.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        cd_documento_origem=origem,
        tp_documento=tipo,
        ds_titulo=titulo,
        ds_conteudo=conteudo,
        ds_status=status_final,
        dh_finalizacao=timezone.now() if status_final == "FECHADO" else None,
        dh_assinatura=timezone.now() if status_final == "FECHADO" else None,
        cd_usuario_emissor=user,
        cd_usuario_responsavel=user,
        ds_hash_conteudo=hashlib.sha256((conteudo or "").encode("utf-8")).hexdigest() if status_final == "FECHADO" else "",
        cd_usuario_criacao=user,
        cd_usuario_atualizacao=user,
        ds_campos_bloqueados={
            "paciente.codigo": atendimento.cd_paciente_id,
            "paciente.nome": (atendimento.cd_paciente.nm_social or "").strip() or atendimento.cd_paciente.nm_paciente,
            "atendimento.codigo": atendimento.pk,
            "empresa.nome": atendimento.cd_empresa.nm_empresa,
            "usuario.nome": user.display_name() if hasattr(user, "display_name") else user.get_username(),
        },
    )
    EventoDocumentoClinico.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_documento_clinico=documento,
        cd_usuario=user,
        tp_evento="FECHADO" if status_final == "FECHADO" else "CRIADO",
    )
    return documento


class ModeloDocumentoForm(forms.ModelForm):
    class Meta:
        model = ModeloDocumento
        fields = (
            "nm_modelo",
            "tp_documento",
            "tp_elemento",
            "cd_cabecalho",
            "cd_rodape",
            "ds_alteracoes_versao",
            "sn_exibe_assinatura",
            "tp_alinhamento_assinatura",
            "sn_exibe_conselho_assinatura",
            "sn_ativo",
        )

    def __init__(self, *args, empresa=None, **kwargs):
        self.original_name = kwargs.pop("original_name", "")
        super().__init__(*args, **kwargs)
        disponiveis = Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True)
        self.fields["cd_cabecalho"].queryset = ModeloDocumento.objects.filter(
            disponiveis, tp_elemento="CABECALHO", sn_versao_atual=True, sn_ativo=True
        )
        self.fields["cd_rodape"].queryset = ModeloDocumento.objects.filter(
            disponiveis, tp_elemento="RODAPE", sn_versao_atual=True, sn_ativo=True
        )
        self.fields["cd_cabecalho"].required = False
        self.fields["cd_rodape"].required = False
        self.fields["ds_alteracoes_versao"].required = True
        self.fields["tp_alinhamento_assinatura"].required = False

    def clean(self):
        cleaned_data = super().clean()
        documentos_sem_formulario = {
            "COMPROVANTE_AGENDAMENTO",
            "COMPROVANTE_CHAMADO",
            "FICHA_ATENDIMENTO",
            "ETIQUETA_ATENDIMENTO",
        }
        if cleaned_data.get("tp_documento") in documentos_sem_formulario:
            cleaned_data["sn_exibe_assinatura"] = False
            cleaned_data["sn_exibe_conselho_assinatura"] = False
            cleaned_data["tp_alinhamento_assinatura"] = "CENTRO"
            return cleaned_data
        if self.is_bound and "sn_exibe_assinatura" not in self.data:
            cleaned_data["sn_exibe_assinatura"] = True
        cleaned_data["tp_alinhamento_assinatura"] = (
            cleaned_data.get("tp_alinhamento_assinatura") or "CENTRO"
        )
        return cleaned_data

    def clean_nm_modelo(self):
        nome = (self.cleaned_data.get("nm_modelo") or "").strip()
        if nome != self.original_name and any(
            unicodedata.combining(char) for char in unicodedata.normalize("NFD", nome)
        ):
            raise forms.ValidationError("O nome pode usar letras maiúsculas e minúsculas, mas não pode conter acentuação.")
        return nome


def _pastas_documento_padrao(empresa, user=None):
    pastas = []
    for ordem, (nome, tipo, editavel) in enumerate(
        [
            ("Cabeçalhos", "CABECALHOS", False),
            ("Rodapés", "RODAPES", False),
            ("Documentos de admissão", "ADMISSAO", True),
            ("Documentos de alta", "ALTA", True),
        ]
    ):
        pasta, _ = PastaDocumento.objects.get_or_create(
            cd_empresa=empresa,
            cd_pasta_pai=None,
            nm_pasta=nome,
            defaults={
                "tp_pasta": tipo,
                "nr_ordem": ordem,
                "sn_sistema": True,
                "sn_editavel": editavel,
                "cd_usuario_criacao": user,
                "cd_usuario_atualizacao": user,
            },
        )
        if editavel and pasta.sn_sistema:
            pasta.sn_sistema = False
            pasta.save(update_fields=["sn_sistema", "dh_atualizacao"])
        pastas.append(pasta)
    return pastas


STATUS_TIMESTAMP_FIELDS = {
    "RECEPCIONADO": "dh_recepcao",
    "EM_CLASSIFICACAO": "dh_inicio_classificacao",
    "AGUARDANDO_CONSULTA": "dh_fim_classificacao",
    "EM_ATENDIMENTO": "dh_inicio_atendimento",
    "ALTA_MEDICA": "dh_alta_medica",
    "ALTA_HOSPITALAR": "dh_alta_hospitalar",
    "FINALIZADO": "dh_fim",
    "CANCELADO": "dh_cancelamento",
}


def _registrar_fluxo(atendimento, status_anterior, status_novo, user=None, *, setor=None, prestador=None, origem="", observacao=""):
    AtendimentoFluxo.objects.create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        ds_status_anterior=status_anterior or "",
        ds_status_novo=status_novo,
        cd_setor=setor or atendimento.cd_setor_atual,
        cd_prestador=prestador or atendimento.cd_prestador,
        cd_usuario=user,
        ds_origem=origem,
        ds_observacao=observacao,
    )


def _mudar_status_atendimento(atendimento, status_novo, user=None, *, setor=None, prestador=None, origem="", observacao="", save=True):
    status_anterior = atendimento.ds_status
    agora = timezone.now()
    atendimento.ds_status = status_novo
    if setor:
        atendimento.cd_setor_atual = setor
    timestamp_field = STATUS_TIMESTAMP_FIELDS.get(status_novo)
    if timestamp_field and not getattr(atendimento, timestamp_field):
        setattr(atendimento, timestamp_field, agora)
    if status_novo == "CANCELADO":
        atendimento.cd_usuario_cancelamento = user
        atendimento.sn_ativo = False
    if user:
        atendimento.cd_usuario_atualizacao = user
    if save:
        atendimento.save()
    if status_anterior != status_novo:
        _registrar_fluxo(
            atendimento,
            status_anterior,
            status_novo,
            user,
            setor=setor,
            prestador=prestador,
            origem=origem,
            observacao=observacao,
        )
    return atendimento


def _vincular_prestador_atendimento(atendimento, prestador, user=None, papel="MEDICO", principal=False):
    if not prestador:
        return
    AtendimentoPrestador.objects.update_or_create(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento=atendimento,
        cd_prestador=prestador,
        tp_papel=papel,
        defaults={
            "sn_responsavel_principal": principal,
            "sn_ativo": True,
            "cd_usuario_atualizacao": user,
            "cd_usuario_criacao": user,
        },
    )


FORM_SCREENS = {
    "agendar",
    "atender-agendamento",
    "atendimento",
    "cadastro-paciente-agendamento",
    "cadastro-paciente-atendimento",
}


def _apply_audit(instance, user):
    if not instance.pk and hasattr(instance, "cd_usuario_criacao"):
        instance.cd_usuario_criacao = user
    if hasattr(instance, "cd_usuario_atualizacao"):
        instance.cd_usuario_atualizacao = user


def _query_text(request):
    return request.GET.get("q", "").strip().replace("%", "")


def _auxiliary_code(value):
    normalized = unicodedata.normalize("NFD", value)
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    return re.sub(r"[^A-Z0-9]+", "_", normalized.upper()).strip("_")[:40]

SCREEN_TITLES = {
    "agendar": "Agendar",
    "atender-agendamento": "Atender",
    "consultar-agendamento": "Consultar",
    "agendas": "Agendas",
    "escalas": "Escalas",
    "cadastro-paciente-agendamento": "Cadastro de paciente",
    "atendimento": "Atendimento",
    "consulta-atendimento": "Consulta de atendimento",
    "cadastro-paciente-atendimento": "Cadastro de paciente",
    "convenios-agendamento": "Convênios",
    "tipos-atendimento-agendamento": "Tipos de Atendimento",
    "especialidades-agendamento": "Especialidades",
    "convenios-atendimento": "Convênios",
    "tipos-atendimento-atendimento": "Tipos de Atendimento",
    "especialidades-atendimento": "Especialidades",
    "convenios": "Convênios",
    "tipos-atendimento": "Tipos de Atendimento",
    "especialidades": "Especialidades",
    "profissionais": "Prestadores",
    "salas": "Salas",
    "relatorio-agendamentos": "Relatório de Agendamentos",
    "relatorio-atendimentos": "Relatório de Atendimentos",
    "relatorio-produtividade": "Relatório de Produtividade",
}


@login_required
def screen(request, screen):
    roles_by_screen = {
        "agendas": {"Recepcionista"},
        "atender-agendamento": {"Enfermeiro"},
        "convenios": {"TI", "Recepcionista"},
        "especialidades": {"TI"},
        "escalas": {"TI"},
        "tipos-atendimento": {"TI"},
        "salas": {"TI"},
    }
    required_roles = roles_by_screen.get(screen)
    if required_roles and not (
        request.user.is_superuser
        or request.user.groups.filter(name__in=("TI", *required_roles)).exists()
    ):
        raise PermissionDenied
    title = SCREEN_TITLES.get(screen, "Atendimento")
    if screen in {"convenios-agendamento", "convenios-atendimento", "convenios"}:
        return _editable_convenios(request, title)
    if screen in {"profissionais"}:
        return profissionais(request)
    if screen in {"escalas"}:
        return _editable_escalas(request, title)
    if screen in {"agendas"}:
        return _agenda_dashboard(request)
    if screen in {"atender-agendamento"}:
        return _fila_atendimento(request)
    auxiliary_by_screen = {
        "tipos-atendimento-agendamento": "tipo_atendimento",
        "tipos-atendimento-atendimento": "tipo_atendimento",
        "tipos-atendimento": "tipo_atendimento",
        "especialidades-agendamento": "especialidade",
        "especialidades-atendimento": "especialidade",
        "especialidades": "especialidade",
        "salas": "sala",
    }
    if screen in auxiliary_by_screen:
        return _editable_auxiliary(request, auxiliary_by_screen[screen], title)
    template = "core/form_page.html" if screen in FORM_SCREENS else "core/table_page.html"
    return render(request, template, {"title": title, "rows": []})


def _editable_convenios(request, title):
    request.current_tab_title = "Cadastros > Tabelas > Convênios"
    request.current_tab_root_title = "Convênios"
    request.current_module_title = "Cadastros"
    request.current_can_query = True
    request.current_can_remove = True
    empresa = _empresa_logada(request)
    registros = Convenio.objects.filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        filtro = Q(nm_convenio__icontains=query)
        if query.isdigit():
            filtro |= Q(cd_convenio=int(query))
        registros = registros.filter(filtro)
    registros = paginate_table(
        request,
        registros,
        {"cd_convenio", "nm_convenio", "sn_ativo"},
        "cd_convenio",
    )
    if request.method == "POST":
        for convenio in registros:
            if request.POST.get(f"delete_{convenio.pk}") == "1":
                convenio.sn_ativo = False
                _apply_audit(convenio, request.user)
                convenio.save(update_fields=["sn_ativo", "cd_usuario_atualizacao", "dh_atualizacao"])
                continue
            if f"name_{convenio.pk}" not in request.POST:
                continue
            convenio.nm_convenio = request.POST.get(f"name_{convenio.pk}", convenio.nm_convenio)
            convenio.sn_ativo = request.POST.get(f"active_{convenio.pk}") == "true"
            _apply_audit(convenio, request.user)
            convenio.save()
        for index, name in enumerate(request.POST.getlist("new_name")):
            name = name.strip()
            if not name:
                continue
            Convenio.objects.update_or_create(
                cd_empresa=empresa,
                nm_convenio=name,
                defaults={"sn_ativo": request.POST.getlist("new_active")[index] == "true" if index < len(request.POST.getlist("new_active")) else True},
            )
        messages.success(request, "Convênios salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "atendimento/editable_convenios.html", {"title": title, "registros": registros})


def _editable_prestadores(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = False
    empresa = _empresa_logada(request)
    registros = Prestador.objects.filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        filtro = Q(nm_prestador__icontains=query) | Q(ds_especialidade__icontains=query)
        if query.isdigit():
            filtro |= Q(cd_prestador=int(query))
        registros = registros.filter(filtro)
    if request.method == "POST":
        for prestador in registros:
            if f"name_{prestador.pk}" not in request.POST:
                continue
            prestador.nm_prestador = request.POST.get(f"name_{prestador.pk}", prestador.nm_prestador)
            prestador.ds_especialidade = request.POST.get(f"specialty_{prestador.pk}", prestador.ds_especialidade)
            prestador.sn_ativo = request.POST.get(f"active_{prestador.pk}") == "true"
            prestador.save()
        new_names = request.POST.getlist("new_name")
        new_specialties = request.POST.getlist("new_specialty")
        new_actives = request.POST.getlist("new_active")
        for index, name in enumerate(new_names):
            name = name.strip()
            if not name:
                continue
            Prestador.objects.create(
                cd_empresa=empresa,
                nm_prestador=name,
                ds_especialidade=new_specialties[index].strip() if index < len(new_specialties) else "",
                sn_ativo=(new_actives[index] if index < len(new_actives) else "true") == "true",
            )
        messages.success(request, "Prestadores salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(request, "atendimento/editable_prestadores.html", {"title": title, "registros": registros})


@login_required
@role_required("TI")
def profissionais(request):
    return redirect("atendimento:cadastro-profissional-novo")


@login_required
@role_required("TI")
def cadastro_profissional(request, cd_prestador=None):
    request.current_tab_title = "Cadastros > Prestadores > Cadastro"
    request.current_tab_root_title = "Cadastro de prestador"
    request.current_module_title = "Cadastros"
    request.current_can_query = True
    request.current_return_url = _safe_return_url(request)
    empresa = _empresa_logada(request)
    if request.GET.get("consultar") == "1":
        logger.info(
            "Consulta de prestadores iniciada usuario=%s empresa=%s filtros=%s",
            request.user.pk,
            empresa.pk,
            request.GET.dict(),
        )
        registros = Prestador.objects.filter(cd_empresa=empresa)
        text_fields = (
            "nm_prestador", "nm_guerra", "nr_cpf", "nr_rg", "ds_orgao_emissor", "nm_mae", "nm_pai",
            "nr_cartao_sus", "ds_grau_instrucao", "tp_genero", "ds_nacionalidade",
            "ds_naturalidade", "ds_observacao", "tp_prestador", "ds_conselho", "nr_conselho",
            "sg_conselho", "tp_sexo", "ds_cor_raca", "tp_vinculo", "nr_telefone", "nr_celular", "nr_celular_2",
            "ds_email", "nr_cep", "sg_estado", "ds_cidade", "tp_logradouro",
            "ds_endereco", "nr_endereco", "ds_complemento", "ds_bairro",
            "nr_cep_comercial", "sg_estado_comercial", "ds_cidade_comercial",
            "tp_logradouro_comercial", "ds_endereco_comercial", "nr_endereco_comercial",
            "ds_complemento_comercial", "ds_bairro_comercial", "cd_banco", "nr_agencia",
            "nr_digito_agencia", "nm_agencia", "nr_conta", "nr_digito_conta", "tp_conta",
            "nm_favorecido", "nr_documento_favorecido", "ds_chave_pix", "ds_contato_principal",
        )
        provider_code = request.GET.get("cd_prestador", "").strip()
        has_filter = False
        provider_name_alias = (
            request.GET.get("nome")
            or request.GET.get("q")
            or request.GET.get("ds_nome")
            or request.GET.get("prestador")
            or ""
        ).strip()
        if provider_name_alias and not request.GET.get("nm_prestador"):
            registros = registros.filter(nm_prestador__icontains=provider_name_alias.replace("%", ""))
            has_filter = True
        if provider_code.isdigit():
            registros = registros.filter(cd_prestador=int(provider_code))
            has_filter = True
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
            has_filter = True
        expedition_date = request.GET.get("dt_expedicao", "")
        if expedition_date:
            registros = registros.filter(dt_expedicao=expedition_date)
            has_filter = True
        birth_date = request.GET.get("dt_nascimento", "")
        if birth_date:
            registros = registros.filter(dt_nascimento=birth_date)
            has_filter = True
        for field_name in ("cd_cep", "cd_cep_comercial"):
            value = request.GET.get(field_name, "")
            if value.isdigit():
                registros = registros.filter(**{f"{field_name}_id": int(value)})
                has_filter = True
        for field_name in text_fields:
            if field_name == "tp_prestador":
                continue
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
                has_filter = True
        for field_name in (
            "sn_permite_agenda",
            "sn_permite_atendimento",
            "sn_permite_prescricao",
            "sn_permite_classificacao",
            "sn_mesmo_endereco",
        ):
            value = request.GET.get(field_name, "")
            if value in {"True", "False"}:
                registros = registros.filter(**{field_name: value == "True"})
                has_filter = True
        provider_types = [
            value for value in (
                request.GET.getlist("tipos_prestador")
                + request.GET.getlist("tp_prestador")
            )
            if value
        ]
        if provider_types:
            registros = registros.filter(
                Q(tp_prestador__in=provider_types)
                | Q(tipos_vinculados__cd_tipo_prestador__in=provider_types, tipos_vinculados__sn_ativo=True)
            ).distinct()
            has_filter = True
        specialties = [
            value for value in (
                request.GET.getlist("ds_especialidades")
                + request.GET.getlist("ds_especialidade")
                + request.GET.getlist("ds_especialidade_principal")
            )
            if value
        ]
        if specialties:
            has_filter = True
        ordered_records = registros.order_by("cd_prestador")
        if specialties:
            specialty_set = set(specialties)
            result_ids = [
                provider.cd_prestador
                for provider in ordered_records
                if specialty_set.intersection(provider.ds_especialidades or [provider.ds_especialidade])
            ][:200]
        else:
            result_ids = list(ordered_records.values_list("cd_prestador", flat=True)[:200])
        request.session["consulta_prestadores"] = result_ids
        logger.info(
            "Consulta de prestadores concluida usuario=%s empresa=%s quantidade=%s",
            request.user.pk,
            empresa.pk,
            len(result_ids),
        )
        if not result_ids:
            messages.warning(request, "Nenhum prestador encontrado para os filtros informados.")
            request.session["consulta_prestadores"] = []
            return redirect(f"{request.path}?sem_resultados=1")
        return redirect(
            f"{reverse('atendimento:cadastro-profissional', args=[result_ids[0]])}?origem=consulta"
        )
    prestador = get_object_or_404(Prestador, cd_empresa=empresa, cd_prestador=cd_prestador) if cd_prestador else None
    if request.GET.get("sem_resultados") == "1":
        request.current_start_query = True
    if prestador:
        request.current_toggle_active_url = reverse("atendimento:alternar-status-prestador", args=[prestador.pk])
        request.current_toggle_active_label = "Desativar" if prestador.sn_ativo else "Ativar"
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get("consulta_prestadores", []) if query_context else []
    if query_context:
        request.current_new_url = f"{reverse('atendimento:cadastro-profissional-novo')}?origem=consulta&novo=1"
    if not prestador and query_context and request.GET.get("novo") == "1":
        request.current_record_status = f"Item {len(result_ids) + 1} de {len(result_ids)}"
        if result_ids:
            request.current_first_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[-1]])}?origem=consulta"
    if prestador and prestador.cd_prestador in result_ids:
        current_index = result_ids.index(prestador.cd_prestador)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        if current_index > 0:
            request.current_first_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[current_index - 1]])}?origem=consulta"
        if current_index < len(result_ids) - 1:
            request.current_next_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[current_index + 1]])}?origem=consulta"
            request.current_last_url = f"{reverse('atendimento:cadastro-profissional', args=[result_ids[-1]])}?origem=consulta"
    prestador_bloqueado = False
    mensagem_trava_prestador = ""
    if prestador:
        if request.method == "POST":
            resultado_trava = usuario_tem_trava_ou_livre(empresa, request.user, "prestador", prestador.pk)
            if not resultado_trava.permitido:
                messages.error(request, resultado_trava.mensagem)
                return redirect(f"{reverse('atendimento:cadastro-profissional', args=[prestador.pk])}?origem=consulta")
        else:
            resultado_trava = usuario_tem_trava_ou_livre(
                empresa,
                request.user,
                "prestador",
                prestador.pk,
            )
            if not resultado_trava.permitido:
                prestador_bloqueado = True
                mensagem_trava_prestador = resultado_trava.mensagem
                request.current_can_save = False
                messages.warning(request, f"{resultado_trava.mensagem} O registro ficará somente para consulta.")
    form = PrestadorForm(request.POST or None, instance=prestador, empresa=empresa)
    if request.method == "POST":
        logger.info(
            "Gravacao de prestador iniciada usuario=%s empresa=%s prestador=%s campos=%s",
            request.user.pk,
            empresa.pk,
            cd_prestador or "novo",
            sorted(request.POST.keys()),
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    saved = form.save(commit=False)
                    saved.cd_empresa = empresa
                    _apply_audit(saved, request.user)
                    saved.save()
                    form.save_m2m()
                    tipos = form.cleaned_data.get("tipos_prestador") or [saved.tp_prestador]
                    saved.tipos_vinculados.update(sn_principal=False)
                    saved.tipos_vinculados.exclude(cd_tipo_prestador__in=tipos).update(
                        sn_ativo=False,
                        sn_principal=False,
                        cd_usuario_atualizacao=request.user,
                    )
                    for tipo in tipos:
                        vinculo, _ = PrestadorTipo.objects.get_or_create(
                            cd_empresa=empresa,
                            cd_prestador=saved,
                            cd_tipo_prestador=tipo,
                            defaults={
                                "sn_principal": tipo == saved.tp_prestador,
                                "sn_ativo": True,
                                "cd_usuario_criacao": request.user,
                                "cd_usuario_atualizacao": request.user,
                            },
                        )
                        vinculo.sn_ativo = True
                        vinculo.sn_principal = tipo == saved.tp_prestador
                        _apply_audit(vinculo, request.user)
                        vinculo.save()
                logger.info(
                    "Prestador gravado usuario=%s empresa=%s prestador=%s",
                    request.user.pk,
                    empresa.pk,
                    saved.cd_prestador,
                )
                liberar_trava_edicao(
                    empresa,
                    request.user,
                    "prestador",
                    saved.pk,
                    motivo="Liberada após salvar cadastro de prestador.",
                )
                messages.success(request, "Prestador salvo com sucesso.")
                if query_context and saved.pk not in result_ids:
                    result_ids.append(saved.pk)
                    request.session["consulta_prestadores"] = result_ids
                edit_url = reverse("atendimento:cadastro-profissional", args=[saved.cd_prestador])
                if request.current_return_url:
                    edit_url = f"{edit_url}?{urlencode({'return_to': request.current_return_url})}"
                elif query_context:
                    edit_url = f"{edit_url}?origem=consulta"
                return redirect(edit_url)
            except Exception:
                logger.exception(
                    "Falha inesperada ao gravar prestador usuario=%s empresa=%s prestador=%s",
                    request.user.pk,
                    empresa.pk,
                    cd_prestador or "novo",
                )
                messages.error(request, "Não foi possível gravar o prestador. Consulte o log técnico.")
        else:
            logger.warning(
                "Prestador nao gravado por validacao usuario=%s empresa=%s prestador=%s erros=%s",
                request.user.pk,
                empresa.pk,
                cd_prestador or "novo",
                form.errors.as_json(),
            )
    return render(
        request,
        "atendimento/cadastro_profissional.html",
        {
            "form": form,
            "prestador": prestador,
            "prestador_bloqueado": prestador_bloqueado,
            "mensagem_trava_prestador": mensagem_trava_prestador,
            "return_to": request.current_return_url,
        },
    )


@login_required
@role_required("TI")
def alternar_status_prestador(request, cd_prestador):
    if request.method != "POST":
        raise PermissionDenied
    empresa = _empresa_logada(request)
    provider = get_object_or_404(Prestador, cd_empresa=empresa, cd_prestador=cd_prestador)
    provider.sn_ativo = not provider.sn_ativo
    _apply_audit(provider, request.user)
    provider.save()
    messages.success(request, f"Prestador {'reativado' if provider.sn_ativo else 'desativado'} com sucesso.")
    return redirect("atendimento:cadastro-profissional", cd_prestador=provider.pk)


@login_required
@role_required("TI")
def liberar_trava_prestador(request, cd_prestador):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    prestador = Prestador.objects.filter(cd_empresa=empresa, pk=cd_prestador).first()
    if not prestador:
        return JsonResponse({"ok": False, "error": "Prestador não encontrado."}, status=404)
    liberar_trava_edicao(
        empresa,
        request.user,
        "prestador",
        prestador.pk,
        motivo="Liberada ao sair do cadastro de prestador.",
    )
    return HttpResponse(status=204)


@login_required
@role_required("TI")
def adquirir_trava_prestador(request, cd_prestador):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "MÃ©todo nÃ£o permitido."}, status=405)
    empresa = _empresa_logada(request)
    prestador = Prestador.objects.filter(cd_empresa=empresa, pk=cd_prestador).first()
    if not prestador:
        return JsonResponse({"ok": False, "error": "Prestador nÃ£o encontrado."}, status=404)
    resultado = adquirir_trava_edicao(
        empresa,
        request.user,
        "prestador",
        prestador.pk,
        f"Prestador {prestador.cd_prestador} - {prestador.nm_prestador}",
        request.session.session_key or "",
    )
    if not resultado.permitido:
        return JsonResponse({"ok": False, "error": resultado.mensagem}, status=409)
    return JsonResponse({"ok": True})


@login_required
@role_required("Enfermeiro")
def iniciar_pre_atendimento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    request.current_tab_title = "Atendimento > Pré-atendimento"
    request.current_tab_root_title = "Pré-atendimento"
    request.current_module_title = "Atendimento"
    pre_atendimento = getattr(agendamento, "pre_atendimento", None)
    form = PreAtendimentoForm(request.POST or None, instance=pre_atendimento, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_paciente = agendamento.cd_paciente
        saved.cd_agendamento = agendamento
        saved.dh_fim = timezone.now()
        _apply_audit(saved, request.user)
        saved.save()
        agendamento.ds_status = "RECEPCIONADO"
        agendamento.save(update_fields=["ds_status", "dh_atualizacao"])
        atendimento = Atendimento.objects.filter(cd_empresa=empresa, cd_agendamento=agendamento).first()
        if atendimento:
            atendimento.cd_pre_atendimento = saved
            atendimento.ds_queixa_principal = saved.ds_queixa_principal
            atendimento.save(update_fields=["cd_pre_atendimento", "ds_queixa_principal", "dh_atualizacao"])
            _mudar_status_atendimento(atendimento, "AGUARDANDO_CONSULTA", request.user, origem="pre_atendimento")
        messages.success(request, "Pré-atendimento concluído e paciente encaminhado por prioridade.")
        return redirect("atendimento:atender-agendamento")
    return render(
        request,
        "atendimento/pre_atendimento.html",
        {"form": form, "agendamento": agendamento, "paciente": agendamento.cd_paciente},
    )


@login_required
@role_required("Enfermeiro")
def iniciar_pre_atendimento_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_agendamento"),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    request.current_tab_title = "Atendimento > Pré-atendimento"
    request.current_tab_root_title = "Pré-atendimento"
    request.current_module_title = "Atendimento"
    form = PreAtendimentoForm(request.POST or None, instance=atendimento.cd_pre_atendimento, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_paciente = atendimento.cd_paciente
        saved.cd_agendamento = atendimento.cd_agendamento
        saved.dh_fim = timezone.now()
        _apply_audit(saved, request.user)
        saved.save()
        atendimento.cd_pre_atendimento = saved
        atendimento.ds_queixa_principal = saved.ds_queixa_principal
        atendimento.save(update_fields=["cd_pre_atendimento", "ds_queixa_principal", "dh_atualizacao"])
        _mudar_status_atendimento(atendimento, "AGUARDANDO_CONSULTA", request.user, origem="pre_atendimento")
        messages.success(request, "Pré-atendimento concluído e paciente encaminhado por prioridade.")
        return redirect("atendimento:fila-classificacao")
    return render(
        request,
        "atendimento/pre_atendimento.html",
        {"form": form, "agendamento": atendimento.cd_agendamento, "paciente": atendimento.cd_paciente, "atendimento": atendimento},
    )


@login_required
@role_required("Recepcionista", "Médico")
def iniciar_atendimento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    atendimento, created = Atendimento.objects.get_or_create(
        cd_empresa=empresa,
        cd_agendamento=agendamento,
        defaults={
            "cd_paciente": agendamento.cd_paciente,
            "cd_pre_atendimento": getattr(agendamento, "pre_atendimento", None),
            "cd_prestador": agendamento.cd_agenda_profissional.cd_prestador if agendamento.cd_agenda_profissional else None,
            "cd_setor_atual": agendamento.cd_agenda_profissional.cd_setor_atendimento if agendamento.cd_agenda_profissional else None,
            "cd_convenio": agendamento.cd_paciente.cd_convenio,
            "ds_origem": "AGENDADO",
            "ds_tipo_atendimento": agendamento.ds_tipo_atendimento,
            "ds_especialidade": agendamento.ds_especialidade,
            "ds_plano": agendamento.ds_plano,
            "ds_status": "AGUARDANDO_CLASSIFICACAO",
            "cd_usuario_criacao": request.user,
            "cd_usuario_atualizacao": request.user,
        },
    )
    if created:
        _registrar_fluxo(atendimento, "", atendimento.ds_status, request.user, origem="iniciar_atendimento")
    _vincular_prestador_atendimento(atendimento, atendimento.cd_prestador, request.user, principal=True)
    agendamento.ds_status = "EM_ATENDIMENTO"
    agendamento.save(update_fields=["ds_status"])
    return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.cd_atendimento)


@login_required
@role_required("Recepcionista")
def recepcao(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Recepção"
    request.current_tab_root_title = "Recepção"
    request.current_module_title = "Atendimento"
    request.current_start_query = not bool(request.GET)
    senha_selecionada = request.GET.get("senha", "")
    form = PacienteSearchForm(request.GET or None)
    pacientes = Paciente.objects.none()
    if request.GET and form.is_valid():
        pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
        dados = form.cleaned_data
        if dados.get("cd_paciente"):
            pacientes = pacientes.filter(cd_paciente=dados["cd_paciente"])
        if dados.get("termo"):
            termo = dados["termo"].replace("%", "")
            pacientes = pacientes.filter(Q(nm_paciente__icontains=termo) | Q(nm_social__icontains=termo))
        if dados.get("nr_cpf"):
            pacientes = pacientes.filter(nr_cpf__icontains=dados["nr_cpf"].replace("%", ""))
        if dados.get("nm_mae"):
            pacientes = pacientes.filter(nm_mae__icontains=dados["nm_mae"].replace("%", ""))
        if dados.get("nr_cartao_sus"):
            pacientes = pacientes.filter(nr_cartao_sus__icontains=dados["nr_cartao_sus"].replace("%", ""))
        if dados.get("dt_nascimento"):
            pacientes = pacientes.filter(dt_nascimento=dados["dt_nascimento"])
        pacientes = pacientes.order_by("nm_paciente")[:30]
    return render(
        request,
        "atendimento/recepcao.html",
        {
            "form": form,
            "pacientes": pacientes,
            "consulta_executada": bool(request.GET),
            "senha_selecionada": senha_selecionada,
            "senhas_classificadas": SenhaAtendimento.objects.select_related(
                "cd_tipo_senha", "cd_classe_senha", "cd_paciente"
            ).filter(
                cd_empresa=empresa,
                dt_senha=timezone.localdate(),
                ds_status="CLASSIFICADA",
            )[:30],
        },
    )


@login_required
@role_required("Recepcionista")
def recepcao_revisar_paciente(request, cd_paciente):
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, pk=cd_paciente)
    atendimento_aberto = (
        Atendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente)
        .exclude(ds_status__in={"FINALIZADO", "ALTA", "ALTA_HOSPITALAR", "CANCELADO", "EVADIU", "OBITO"})
        .order_by("-dh_inicio")
        .first()
    )
    if atendimento_aberto and request.GET.get("prosseguir") != "1":
        prosseguir_params = {"prosseguir": "1"}
        if request.GET.get("senha", "").isdigit():
            prosseguir_params["senha"] = request.GET["senha"]
        return render(
            request,
            "atendimento/confirmar_atendimento_aberto.html",
            {
                "paciente": paciente,
                "atendimento": atendimento_aberto,
                "prosseguir_url": f"{request.path}?{urlencode(prosseguir_params)}",
                "cancelar_url": reverse("atendimento:recepcao"),
            },
        )
    target = reverse("atendimento:revisar-paciente-agendamento", args=[paciente.pk])
    params_data = {"recepcao_direta": "1", "return_to": reverse("atendimento:recepcao")}
    if request.GET.get("senha", "").isdigit():
        params_data["senha"] = request.GET["senha"]
    params = urlencode(params_data)
    return redirect(f"{target}?{params}")


@login_required
@role_required("Recepcionista")
def agendamentos_operacionais(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Agendamentos"
    request.current_tab_root_title = "Agendamentos"
    request.current_module_title = "Atendimento"
    hoje = timezone.localdate()
    data = request.GET.get("data") or hoje.isoformat()
    data_inicio = _parse_date(data, hoje)
    mes = int(request.GET.get("mes") or data_inicio.month)
    ano = int(request.GET.get("ano") or data_inicio.year)
    data_calendario = data_inicio.replace(year=ano, month=mes, day=min(data_inicio.day, calendar.monthrange(ano, mes)[1]))
    termo = request.GET.get("q", "").strip().replace("%", "")
    especialidades_selecionadas = [value for value in request.GET.getlist("especialidades") if value]
    todos = request.GET.get("todas_especialidades") == "1" or not especialidades_selecionadas
    registros = (
        Agendamento.objects.select_related(
            "cd_paciente",
            "cd_paciente__cd_convenio",
            "cd_agenda_profissional__cd_prestador",
            "atendimento",
        )
        .filter(cd_empresa=empresa, dh_agendamento__date=data_inicio)
        .order_by("dh_agendamento")
    )
    if not todos and especialidades_selecionadas:
        registros = registros.filter(ds_especialidade__in=especialidades_selecionadas)
    if termo:
        filtros = (
            Q(cd_paciente__nm_paciente__icontains=termo)
            | Q(cd_paciente__nr_cpf__icontains=termo)
            | Q(cd_paciente__nr_cartao_sus__icontains=termo)
            | Q(cd_paciente__nr_rg__icontains=termo)
            | Q(ds_profissional__icontains=termo)
            | Q(cd_agenda_profissional__cd_prestador__nm_prestador__icontains=termo)
            | Q(ds_especialidade__icontains=termo)
            | Q(cd_paciente__nm_mae__icontains=termo)
        )
        if termo.isdigit():
            filtros |= Q(cd_paciente_id=int(termo))
        if re.match(r"^\d{1,2}:\d{2}$", termo):
            filtros |= Q(dh_agendamento__time=datetime.strptime(termo, "%H:%M").time())
        registros = registros.filter(filtros)
    especialidades_qs = ValorAuxiliarGlobal.objects.filter(cd_tabela_auxiliar_global__ds_tabela="especialidade", sn_ativo=True).order_by("ds_valor")
    especialidades = [{"codigo": item.cd_valor, "descricao": item.ds_valor} for item in especialidades_qs]
    if not especialidades:
        especialidades = [
            {"codigo": value, "descricao": value}
            for value in Agendamento.objects.filter(cd_empresa=empresa)
            .exclude(ds_especialidade="")
            .order_by("ds_especialidade")
            .values_list("ds_especialidade", flat=True)
            .distinct()
        ]
    registros = list(registros[:200])
    nomes_especialidades = {item["codigo"]: item["descricao"] for item in especialidades}
    for agendamento in registros:
        agendamento.nm_especialidade_exibicao = nomes_especialidades.get(
            agendamento.ds_especialidade,
            (agendamento.ds_especialidade or "").replace("_", " ").title(),
        )
    calendario = _calendario_mensal(empresa, data_calendario)
    return render(
        request,
        "atendimento/agendamentos_operacionais.html",
        {
            "registros": registros,
            "data": data_inicio.isoformat(),
            "termo": termo,
            "todos": todos,
            "especialidades": especialidades,
            "especialidades_selecionadas": especialidades_selecionadas,
            "calendario": calendario,
        },
    )


@login_required
@role_required("Recepcionista")
def recepcionar_agendamento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    atendimento_existente = Atendimento.objects.filter(cd_empresa=empresa, cd_agendamento=agendamento).first()
    if atendimento_existente:
        messages.warning(request, "Este agendamento já possui atendimento gerado.")
        return redirect("atendimento:cadastro-atendimento", cd_atendimento=atendimento_existente.pk)
    review_url = reverse("atendimento:revisar-paciente-agendamento", args=[agendamento.cd_paciente_id])
    query = urlencode(
        {
            "recepcionar": agendamento.pk,
            "return_to": f"{reverse('atendimento:agendamentos-operacionais')}?data={agendamento.dh_agendamento:%Y-%m-%d}",
        }
    )
    return redirect(f"{review_url}?{query}")


@login_required
@role_required("Recepcionista")
def cadastro_atendimento(request, cd_agendamento=None, cd_atendimento=None, cd_paciente=None):
    empresa = _empresa_logada(request)
    atendimento = (
        get_object_or_404(
            Atendimento.objects.select_related("cd_paciente", "cd_agendamento", "cd_prestador", "cd_convenio"),
            cd_empresa=empresa,
            pk=cd_atendimento,
        )
        if cd_atendimento else None
    )
    agendamento = (
        get_object_or_404(
            Agendamento.objects.select_related(
                "cd_paciente__cd_convenio",
                "cd_agenda_profissional__cd_prestador",
                "cd_agenda_profissional__cd_setor_atendimento",
            ),
            cd_empresa=empresa,
            pk=cd_agendamento,
        )
        if cd_agendamento else getattr(atendimento, "cd_agendamento", None)
    )
    if agendamento and atendimento is None:
        atendimento = Atendimento.objects.filter(cd_empresa=empresa, cd_agendamento=agendamento).first()
        if atendimento:
            return redirect("atendimento:cadastro-atendimento", cd_atendimento=atendimento.pk)
    paciente = (
        atendimento.cd_paciente
        if atendimento
        else agendamento.cd_paciente
        if agendamento
        else get_object_or_404(Paciente, cd_empresa=empresa, pk=cd_paciente)
    )
    if not atendimento and getattr(paciente, "sn_obito", False):
        messages.error(request, "Não é possível criar atendimento: o paciente consta como óbito no prontuário.")
        return redirect(_safe_return_url(request) or "atendimento:recepcao")
    senha_recepcao = None
    if request.GET.get("senha", "").isdigit():
        senha_recepcao = get_object_or_404(
            SenhaAtendimento,
            cd_empresa=empresa,
            pk=int(request.GET["senha"]),
            ds_status="CLASSIFICADA",
        )
    request.current_tab_title = "Atendimento > Recepção > Cadastro de atendimento"
    request.current_tab_root_title = "Cadastro de atendimento"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    request.current_return_url = _safe_return_url(request) or (
        reverse("atendimento:recepcao") if cd_paciente else reverse("atendimento:agendamentos-operacionais")
    )
    initial = {}
    if agendamento and not atendimento:
        agenda = agendamento.cd_agenda_profissional
        initial = {
            "cd_prestador": getattr(agenda, "cd_prestador_id", None),
            "ds_origem": "ENCAIXE" if agendamento.sn_encaixe else "AGENDADO",
            "cd_convenio": paciente.cd_convenio_id,
            "ds_plano": agendamento.ds_plano,
            "ds_tipo_atendimento": agendamento.ds_tipo_atendimento,
            "ds_especialidade": agendamento.ds_especialidade,
            "ds_destino": "CONSULTORIO",
        }
    elif not atendimento:
        initial = {
            "ds_origem": "DEMANDA_ESPONTANEA",
            "cd_convenio": paciente.cd_convenio_id,
        }
    form = CadastroAtendimentoForm(
        request.POST or None,
        instance=atendimento,
        initial=initial,
        empresa=empresa,
        paciente=paciente,
        agendamento=agendamento,
    )
    responsavel = getattr(atendimento, "responsavel", None) if atendimento else None
    responsavel_form = ResponsavelAtendimentoForm(
        request.POST or None,
        instance=responsavel,
        prefix="responsavel",
        empresa=empresa,
    )
    modelos_documentos_atendimento = ModeloDocumento.objects.filter(
        Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
        tp_elemento="DOCUMENTO",
        tp_documento__in={"FICHA_ATENDIMENTO", "ETIQUETA_ATENDIMENTO"},
        sn_versao_atual=True,
        sn_ativo=True,
    ).order_by("tp_documento", "nm_modelo")
    if request.method == "POST" and form.is_valid() and responsavel_form.is_valid():
        with transaction.atomic():
            saved = form.save(commit=False)
            saved.cd_empresa = empresa
            saved.cd_paciente = paciente
            saved.cd_agendamento = agendamento
            saved.cd_setor_atual = (
                agendamento.cd_agenda_profissional.cd_setor_atendimento
                if agendamento and agendamento.cd_agenda_profissional else saved.cd_setor_atual
            )
            if not saved.pk:
                saved.ds_status = "AGUARDANDO_CLASSIFICACAO"
                saved.dh_recepcao = timezone.now()
            _apply_audit(saved, request.user)
            saved.save()
            if senha_recepcao:
                senha_recepcao.cd_paciente = paciente
                senha_recepcao.ds_status = "RECEPCIONADA"
                senha_recepcao.cd_usuario_atualizacao = request.user
                senha_recepcao.save(
                    update_fields=["cd_paciente", "ds_status", "cd_usuario_atualizacao", "dh_atualizacao"]
                )
            responsible_data = [
                value for name, value in responsavel_form.cleaned_data.items()
                if name != "sn_mesmo_endereco_paciente" and value not in ("", None, False)
            ]
            if responsible_data or responsavel_form.cleaned_data.get("sn_mesmo_endereco_paciente") or responsavel:
                saved_responsavel = responsavel_form.save(commit=False)
                saved_responsavel.cd_empresa = empresa
                saved_responsavel.cd_atendimento = saved
                if saved_responsavel.sn_mesmo_endereco_paciente:
                    for field_name in (
                        "cd_cep", "sg_estado", "ds_cidade", "tp_logradouro",
                        "ds_endereco", "nr_endereco", "ds_complemento", "ds_bairro",
                    ):
                        setattr(saved_responsavel, field_name, getattr(paciente, field_name))
                _apply_audit(saved_responsavel, request.user)
                saved_responsavel.save()
            if agendamento:
                agendamento.ds_status = "RECEPCIONADO"
                _apply_audit(agendamento, request.user)
                agendamento.save(update_fields=["ds_status", "dh_atualizacao", "cd_usuario_atualizacao"])
            if not atendimento:
                _registrar_fluxo(saved, "", saved.ds_status, request.user, origem="cadastro_atendimento")
                _vincular_prestador_atendimento(saved, saved.cd_prestador, request.user, principal=True)
        messages.success(request, f"Atendimento {saved.pk} gerado com sucesso.")
        return redirect(f"{reverse('atendimento:cadastro-atendimento', args=[saved.pk])}?salvo=1")
    return render(
        request,
        "atendimento/cadastro_atendimento.html",
        {
            "form": form,
            "responsavel_form": responsavel_form,
            "atendimento": atendimento,
            "agendamento": agendamento,
            "paciente": paciente,
            "return_to": request.current_return_url,
            "modelos_documentos_atendimento": modelos_documentos_atendimento,
        },
    )


@login_required
def ficha_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related(
            "cd_paciente",
            "cd_agendamento",
            "cd_pre_atendimento",
            "cd_prestador",
        ),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    request.current_tab_title = "Atendimento > Ficha de atendimento"
    request.current_tab_root_title = f"Atendimento {atendimento.cd_atendimento}"
    request.current_module_title = "Atendimento"
    request.current_return_url = _safe_return_url(request)
    if request.method == "POST":
        raise PermissionDenied("Dados administrativos do atendimento só podem ser alterados pela recepção.")
    historico = Atendimento.objects.filter(cd_empresa=empresa, cd_paciente=atendimento.cd_paciente).exclude(pk=atendimento.pk)[:10]
    grupos = set(request.user.groups.values_list("name", flat=True))
    clinical_permissions = {
        "medico": request.user.is_superuser or bool(grupos.intersection({"TI", "Médico", "Médico"})),
        "enfermeiro": request.user.is_superuser or bool(grupos.intersection({"TI", "Enfermeiro"})),
        "laboratorio": request.user.is_superuser or bool(grupos.intersection({"TI", "Laboratório", "Laboratorio"})),
    }
    perfis_assistenciais, itens_menu_assistencial = _itens_menu_assistencial_mesclados(request.user, empresa)
    perfil_assistencial = perfis_assistenciais[0] if perfis_assistenciais else None
    if not request.user.is_superuser and not perfis_assistenciais and not any(clinical_permissions.values()):
        raise PermissionDenied("Usuário sem perfil assistencial para acessar o prontuário.")
    menu_assistencial_raizes = []
    if perfis_assistenciais:
        mapa_acoes = {
            "SINAIS_VITAIS": "#classificacao",
            "ADMISSAO": reverse("atendimento:documento-assistencial", args=[atendimento.pk, "admissao"]),
            "EVOLUIR": reverse("atendimento:evoluir", args=[atendimento.pk]),
            "PRESCREVER": reverse("atendimento:prescrever", args=[atendimento.pk]),
            "EXAMES": reverse("atendimento:solicitar-exame", args=[atendimento.pk]),
            "ALTA_MEDICA": reverse("atendimento:conceder-alta", args=[atendimento.pk]),
            "RECEITUARIO": reverse("atendimento:documento-assistencial", args=[atendimento.pk, "receituario"]),
            "AIH": reverse("atendimento:documento-assistencial", args=[atendimento.pk, "aih"]),
            "DOCUMENTOS": "#documentos",
        }
        for item in itens_menu_assistencial:
            if item.tp_item == "LINK_EXTERNO":
                item.url_renderizada = (
                    item.ds_url
                    .replace("<<cd_atendimento>>", str(atendimento.pk))
                    .replace("<<cd_paciente>>", str(atendimento.cd_paciente_id))
                    .replace("<<cd_prestador>>", str(atendimento.cd_prestador_id or ""))
                    .replace("<<atendimento.codigo>>", str(atendimento.pk))
                    .replace("<<paciente.codigo>>", str(atendimento.cd_paciente_id))
                    .replace("<<prestador.codigo>>", str(atendimento.cd_prestador_id or ""))
                )
                dominio = _url_externa_permitida(empresa, item.url_renderizada)
                item.url_externa_permitida = bool(dominio)
                item.url_externa_embutida = bool(dominio and dominio.sn_permite_iframe)
                if item.url_externa_embutida:
                    item.url_renderizada = reverse(
                        "atendimento:link-externo-assistencial",
                        args=[atendimento.pk, item.pk],
                    )
                elif not dominio:
                    item.url_renderizada = "#"
            elif item.tp_item == "DOCUMENTO" and item.cd_modelo_documento_id:
                item.url_renderizada = reverse("atendimento:abrir-modelo-assistencial", args=[atendimento.pk, item.pk])
            elif item.tp_item == "ESCALA":
                item.url_renderizada = reverse("atendimento:executar-escala-clinica", args=[atendimento.pk, item.pk])
            elif item.tp_item == "ANEXO":
                item.url_renderizada = reverse("atendimento:anexos-clinicos", args=[atendimento.pk, item.pk])
            elif item.tp_item == "HISTORICO":
                item.url_renderizada = reverse("atendimento:historico-documentos-assistencial", args=[atendimento.pk, item.pk])
            else:
                item.url_renderizada = mapa_acoes.get(item.ds_acao, item.ds_url or "#")
        itens_por_chave = {item.chave_mesclagem: item for item in itens_menu_assistencial}
        for item in itens_menu_assistencial:
            pai = itens_por_chave.get(item.chave_pai_mesclagem)
            if pai:
                pai.filhos_renderizados.append(item)
            else:
                menu_assistencial_raizes.append(item)
    documentos_visiveis = DocumentoClinico.objects.filter(
        cd_empresa=empresa,
        cd_atendimento__cd_paciente=atendimento.cd_paciente,
    ).select_related(
        "cd_atendimento",
        "cd_usuario_responsavel",
        "cd_item_menu_assistencial__cd_perfil_assistencial",
    )
    if not request.user.is_superuser:
        perfil_ids = [perfil.pk for perfil in perfis_assistenciais]
        documentos_visiveis = documentos_visiveis.filter(
            Q(cd_item_menu_assistencial__isnull=True)
            | Q(
                cd_item_menu_assistencial__cd_perfil_assistencial__sn_sigiloso=False,
                cd_item_menu_assistencial__sn_privado=False,
            )
            | Q(cd_item_menu_assistencial__cd_perfil_assistencial_id__in=perfil_ids)
        )
    return render(
        request,
        "atendimento/ficha_atendimento.html",
        {
            "atendimento": atendimento,
            "paciente": atendimento.cd_paciente,
            "idade": _idade(atendimento.cd_paciente.dt_nascimento),
            "historico": historico,
            "documentos": documentos_visiveis,
            "clinical_permissions": clinical_permissions,
            "perfil_assistencial": perfil_assistencial,
            "perfis_assistenciais": perfis_assistenciais,
            "itens_menu_assistencial": itens_menu_assistencial,
            "menu_assistencial_raizes": menu_assistencial_raizes,
        },
    )


@login_required
def abrir_modelo_assistencial(request, cd_atendimento, cd_item):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, pk=cd_atendimento)
    item = get_object_or_404(
        ItemMenuAssistencial.objects.select_related("cd_modelo_documento", "cd_perfil_assistencial"),
        cd_empresa=empresa,
        pk=cd_item,
        sn_ativo=True,
        tp_item="DOCUMENTO",
    )
    perfis_permitidos = _perfis_assistenciais_usuario(request.user, empresa)
    if not request.user.is_superuser and not perfis_permitidos.filter(pk=item.cd_perfil_assistencial_id).exists():
        raise PermissionDenied
    modelo = item.cd_modelo_documento
    documento = DocumentoClinico.objects.filter(
        cd_empresa=empresa,
        cd_atendimento=atendimento,
        cd_modelo_documento=modelo,
        ds_status__in=["ABERTO", "RASCUNHO"],
    ).first()
    if not documento:
        if not item.sn_permite_criar or item.sn_somente_historico:
            historico = DocumentoClinico.objects.filter(
                cd_empresa=empresa,
                cd_atendimento__cd_paciente=atendimento.cd_paciente,
                cd_modelo_documento=modelo,
            ).first()
            if historico:
                return redirect("atendimento:imprimir-documento-clinico", cd_documento=historico.pk)
            messages.warning(request, "Esta tela está configurada apenas para consulta e ainda não possui documentos.")
            return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
        documento = _criar_documento_clinico(
            atendimento,
            modelo.tp_documento,
            modelo.nm_modelo,
            "",
            request.user,
        )
        documento.cd_modelo_documento = modelo
        documento.cd_item_menu_assistencial = item
        documento.cd_versao_perfil = item.cd_versao_perfil
        documento.cd_usuario_responsavel = request.user
        documento.ds_status = "ABERTO"
        documento.save(update_fields=[
            "cd_modelo_documento",
            "cd_item_menu_assistencial",
            "cd_versao_perfil",
            "cd_usuario_responsavel",
            "ds_status",
        ])
    return _redirect_documento_clinico(request, documento)


def _obter_versao_edicao_perfil(perfil, empresa, usuario):
    existente = perfil.versoes.filter(ds_status="RASCUNHO").first()
    if existente:
        return existente
    publicada = perfil.versoes.filter(ds_status="PUBLICADO").first()
    numero = (perfil.versoes.aggregate(maior=Max("nr_versao"))["maior"] or 0) + 1
    nova = PerfilAssistencialVersao.objects.create(
        cd_empresa=empresa,
        cd_perfil_assistencial=perfil,
        nr_versao=numero,
        ds_status="RASCUNHO",
        ds_descricao_versao="",
        cd_usuario_criacao=usuario,
        cd_usuario_atualizacao=usuario,
    )
    origem = publicada.itens.all() if publicada else perfil.itens.filter(cd_versao_perfil__isnull=True)
    mapa = {}
    for item_origem in origem.order_by("nr_ordem", "pk"):
        pai_origem = item_origem.cd_item_pai_id
        clone = ItemMenuAssistencial.objects.create(
            cd_empresa=empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=nova,
            cd_item_pai_id=mapa.get(pai_origem),
            cd_modelo_documento=item_origem.cd_modelo_documento,
            cd_item_tecnico=item_origem.cd_item_tecnico,
            nm_item=item_origem.nm_item,
            ds_icone=item_origem.ds_icone,
            nr_ordem=item_origem.nr_ordem,
            tp_item=item_origem.tp_item,
            ds_acao=item_origem.ds_acao,
            ds_url=item_origem.ds_url,
            sn_privado=item_origem.sn_privado,
            sn_imprimivel=item_origem.sn_imprimivel,
            sn_permite_criar=item_origem.sn_permite_criar,
            sn_permite_abandonar=item_origem.sn_permite_abandonar,
            sn_permite_cancelar=item_origem.sn_permite_cancelar,
            sn_somente_historico=item_origem.sn_somente_historico,
            ds_configuracao=item_origem.ds_configuracao,
            sn_ativo=item_origem.sn_ativo,
            cd_usuario_criacao=usuario,
            cd_usuario_atualizacao=usuario,
        )
        mapa[item_origem.pk] = clone.pk
    return nova


@login_required
@role_required("TI")
def perfis_assistenciais(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Perfis assistenciais"
    request.current_tab_root_title = "Perfis assistenciais"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    perfil_id = request.POST.get("perfil") or request.GET.get("perfil")
    perfil = (
        PerfilAssistencial.objects.filter(cd_empresa=empresa, pk=perfil_id).first()
        if str(perfil_id or "").isdigit()
        else None
    )
    acao = request.POST.get("acao")

    if request.method == "POST" and acao == "salvar_dominio":
        dominio_texto = request.POST.get("ds_dominio", "").strip().lower()
        parsed = urlparse(dominio_texto if "://" in dominio_texto else f"https://{dominio_texto}")
        if parsed.scheme != "https" or not parsed.hostname:
            messages.error(request, "Informe um domínio HTTPS válido.")
        else:
            dominio, _ = DominioExternoPermitido.objects.get_or_create(
                cd_empresa=empresa,
                ds_dominio=parsed.hostname,
                defaults={
                    "cd_usuario_criacao": request.user,
                    "cd_usuario_atualizacao": request.user,
                },
            )
            dominio.sn_permite_iframe = request.POST.get("sn_permite_iframe") == "on"
            dominio.sn_ativo = True
            _apply_audit(dominio, request.user)
            dominio.save()
            messages.success(request, "Domínio externo autorizado.")
        return redirect(
            f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}"
            if perfil
            else reverse("atendimento:perfis-assistenciais")
        )

    if request.method == "POST" and acao == "salvar_escala":
        nome_escala = request.POST.get("nm_escala", "").strip()
        try:
            perguntas = json.loads(request.POST.get("ds_perguntas") or "[]")
            faixas = json.loads(request.POST.get("ds_faixas_resultado") or "[]")
        except json.JSONDecodeError:
            perguntas = faixas = None
        if not nome_escala or not isinstance(perguntas, list) or not isinstance(faixas, list):
            messages.error(request, "Informe nome, perguntas e faixas em formato válido.")
        else:
            numero = (
                EscalaClinica.objects.filter(cd_empresa=empresa, nm_escala=nome_escala)
                .aggregate(maior=Max("nr_versao"))["maior"]
                or 0
            ) + 1
            escala = EscalaClinica.objects.create(
                cd_empresa=empresa,
                nm_escala=nome_escala,
                ds_descricao=request.POST.get("ds_descricao_escala", "").strip(),
                tp_calculo=request.POST.get("tp_calculo") or "SOMA",
                ds_expressao_calculo=request.POST.get("ds_expressao_calculo", "").strip(),
                ds_perguntas=perguntas,
                ds_faixas_resultado=faixas,
                nr_versao=numero,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
            messages.success(request, f"Escala {escala.nm_escala} v{escala.nr_versao} criada.")
        return redirect(
            f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}"
            if perfil
            else reverse("atendimento:perfis-assistenciais")
        )

    def versao_edicao(perfil_atual):
        return _obter_versao_edicao_perfil(perfil_atual, empresa, request.user)

    if request.method == "POST" and acao == "copiar_perfil" and perfil:
        nome_base = f"{perfil.nm_perfil} - Cópia"
        nome_copia = nome_base
        sufixo = 2
        while PerfilAssistencial.objects.filter(cd_empresa=empresa, nm_perfil=nome_copia).exists():
            nome_copia = f"{nome_base} {sufixo}"
            sufixo += 1
        origem_versao = (
            perfil.versoes.filter(ds_status="RASCUNHO").first()
            or perfil.versoes.filter(ds_status="PUBLICADO").first()
        )
        with transaction.atomic():
            copia = PerfilAssistencial.objects.create(
                cd_empresa=empresa,
                nm_perfil=nome_copia,
                ds_descricao=perfil.ds_descricao,
                sn_ativo=True,
                sn_sigiloso=perfil.sn_sigiloso,
                tipos_prestador=[],
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
            copia_versao = PerfilAssistencialVersao.objects.create(
                cd_empresa=empresa,
                cd_perfil_assistencial=copia,
                nr_versao=1,
                ds_status="RASCUNHO",
                ds_descricao_versao=f"Cópia do perfil {perfil.nm_perfil}",
                ds_configuracao=copy.deepcopy(origem_versao.ds_configuracao) if origem_versao else {},
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
            itens_origem = list(
                (
                    origem_versao.itens.filter(sn_ativo=True)
                    if origem_versao
                    else perfil.itens.filter(sn_ativo=True, cd_versao_perfil__isnull=True)
                ).order_by("nr_ordem", "pk")
            )
            mapa = {}
            pendentes = itens_origem[:]
            while pendentes:
                inseridos = 0
                for item_origem in pendentes[:]:
                    if item_origem.cd_item_pai_id and item_origem.cd_item_pai_id not in mapa:
                        continue
                    item_copia = ItemMenuAssistencial.objects.create(
                        cd_empresa=empresa,
                        cd_perfil_assistencial=copia,
                        cd_versao_perfil=copia_versao,
                        cd_item_pai=mapa.get(item_origem.cd_item_pai_id),
                        cd_modelo_documento=item_origem.cd_modelo_documento,
                        cd_item_tecnico=item_origem.cd_item_tecnico,
                        nm_item=item_origem.nm_item,
                        ds_icone=item_origem.ds_icone,
                        nr_ordem=item_origem.nr_ordem,
                        tp_item=item_origem.tp_item,
                        ds_acao=item_origem.ds_acao,
                        ds_url=item_origem.ds_url,
                        sn_privado=item_origem.sn_privado,
                        sn_imprimivel=item_origem.sn_imprimivel,
                        sn_permite_criar=item_origem.sn_permite_criar,
                        sn_permite_abandonar=item_origem.sn_permite_abandonar,
                        sn_permite_cancelar=item_origem.sn_permite_cancelar,
                        sn_somente_historico=item_origem.sn_somente_historico,
                        ds_configuracao=copy.deepcopy(item_origem.ds_configuracao),
                        sn_ativo=True,
                        cd_usuario_criacao=request.user,
                        cd_usuario_atualizacao=request.user,
                    )
                    mapa[item_origem.pk] = item_copia
                    pendentes.remove(item_origem)
                    inseridos += 1
                if not inseridos:
                    break
        messages.success(request, "Perfil copiado com toda a estrutura e sem tipos de prestador.")
        return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={copia.pk}")

    if request.method == "POST" and acao == "salvar_perfil":
        tipos = [tipo for tipo in request.POST.getlist("tipos_prestador") if tipo]
        nome = request.POST.get("nm_perfil", "").strip()
        if not nome:
            messages.error(request, "Informe o nome do perfil.")
        else:
            conflitos = PerfilAssistencialTipo.objects.filter(
                cd_empresa=empresa,
                cd_tipo_prestador__in=tipos,
                sn_ativo=True,
            )
            if perfil:
                conflitos = conflitos.exclude(cd_perfil_assistencial=perfil)
            if conflitos.exists():
                messages.error(
                    request,
                    "Um ou mais tipos de prestador já pertencem a outro perfil assistencial.",
                )
            else:
                with transaction.atomic():
                    perfil = perfil or PerfilAssistencial(cd_empresa=empresa)
                    perfil.nm_perfil = nome
                    perfil.ds_descricao = request.POST.get("ds_descricao", "").strip()
                    perfil.sn_ativo = request.POST.get("sn_ativo") in {"on", "true", "1"}
                    perfil.sn_sigiloso = request.POST.get("sn_sigiloso") in {"on", "true", "1"}
                    perfil.tipos_prestador = tipos
                    _apply_audit(perfil, request.user)
                    perfil.save()
                    perfil.tipos_vinculados.exclude(cd_tipo_prestador__in=tipos).update(sn_ativo=False)
                    for tipo in tipos:
                        vinculo, _ = PerfilAssistencialTipo.objects.get_or_create(
                            cd_empresa=empresa,
                            cd_perfil_assistencial=perfil,
                            cd_tipo_prestador=tipo,
                            defaults={
                                "sn_ativo": True,
                                "cd_usuario_criacao": request.user,
                                "cd_usuario_atualizacao": request.user,
                            },
                        )
                        if not vinculo.sn_ativo:
                            vinculo.sn_ativo = True
                            _apply_audit(vinculo, request.user)
                            vinculo.save()
                    _obter_versao_edicao_perfil(perfil, empresa, request.user)
                messages.success(request, "Perfil assistencial salvo e aplicado.")
                return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
    if request.method == "POST" and acao == "adicionar_item" and perfil:
        versao = versao_edicao(perfil)
        item_id_edicao = str(request.POST.get("item") or "").strip()
        item_edicao = (
            versao.itens.filter(pk=int(item_id_edicao)).first()
            if item_id_edicao.isdigit()
            else None
        )
        if not item_edicao and item_id_edicao.isdigit():
            item_original = perfil.itens.filter(pk=int(item_id_edicao)).first()
            if item_original:
                item_edicao = versao.itens.filter(
                    cd_item_tecnico=item_original.cd_item_tecnico,
                    sn_ativo=True,
                ).first()
        pai_id = request.POST.get("cd_item_pai") or None
        if pai_id:
            pai_item = versao.itens.filter(pk=pai_id, tp_item="GRUPO", sn_ativo=True).first()
            if not pai_item and str(pai_id).isdigit():
                pai_original = perfil.itens.filter(pk=int(pai_id), tp_item="GRUPO").first()
                if pai_original:
                    pai_item = versao.itens.filter(
                        cd_item_tecnico=pai_original.cd_item_tecnico,
                        tp_item="GRUPO",
                        sn_ativo=True,
                    ).first()
            pai_id = pai_item.pk if pai_item else None
        if request.POST.get("cd_item_pai") and not pai_id:
            messages.error(request, "O grupo pai não pertence à versão em edição.")
            return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
        if item_edicao and pai_id:
            pai_verificacao = versao.itens.filter(pk=pai_id).first()
            while pai_verificacao:
                if pai_verificacao.pk == item_edicao.pk:
                    messages.error(request, "Um item não pode ser movido para dentro de si mesmo.")
                    return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
                pai_verificacao = pai_verificacao.cd_item_pai
        try:
            configuracao = json.loads(request.POST.get("ds_configuracao") or "{}")
        except json.JSONDecodeError:
            configuracao = {}
        escala_id = request.POST.get("cd_escala_clinica", "").strip()
        nome_nova_escala = request.POST.get("nm_nova_escala", "").strip()
        if request.POST.get("tp_item") == "ESCALA" and nome_nova_escala:
            try:
                perguntas_novas = json.loads(request.POST.get("ds_perguntas_escala") or "[]")
                faixas_novas = json.loads(request.POST.get("ds_faixas_escala") or "[]")
            except json.JSONDecodeError:
                perguntas_novas = faixas_novas = None
            if not isinstance(perguntas_novas, list) or not isinstance(faixas_novas, list):
                messages.error(request, "Revise as perguntas e faixas da nova escala.")
                return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
            numero_escala = (
                EscalaClinica.objects.filter(cd_empresa=empresa, nm_escala=nome_nova_escala)
                .aggregate(maior=Max("nr_versao"))["maior"]
                or 0
            ) + 1
            escala_criada = EscalaClinica.objects.create(
                cd_empresa=empresa,
                nm_escala=nome_nova_escala,
                ds_descricao=request.POST.get("ds_descricao_nova_escala", "").strip(),
                tp_calculo=request.POST.get("tp_calculo_nova_escala") or "SOMA",
                ds_expressao_calculo=request.POST.get("ds_expressao_nova_escala", "").strip(),
                ds_perguntas=perguntas_novas,
                ds_faixas_resultado=faixas_novas,
                nr_versao=numero_escala,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
            escala_id = str(escala_criada.pk)
        if escala_id.isdigit():
            configuracao["escala"] = int(escala_id)
        item = item_edicao or ItemMenuAssistencial(
            cd_empresa=empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
        )
        item.cd_item_pai_id = pai_id
        item.cd_modelo_documento_id = request.POST.get("cd_modelo_documento") or None
        item.cd_item_tecnico = _normalizar_chave_tecnica_assistencial(request.POST.get("cd_item_tecnico", ""))
        item.nm_item = request.POST.get("nm_item", "").strip()
        item.ds_icone = request.POST.get("ds_icone", "").strip()
        ordem_postada = request.POST.get("nr_ordem")
        if item_edicao:
            item.nr_ordem = int(ordem_postada) if str(ordem_postada or "").isdigit() else item.nr_ordem
        else:
            item.nr_ordem = (
                versao.itens.filter(cd_item_pai_id=pai_id, sn_ativo=True)
                .aggregate(maior=Max("nr_ordem"))["maior"]
                or -1
            ) + 1
        item.tp_item = request.POST.get("tp_item") or "ACAO"
        item.ds_acao = request.POST.get("ds_acao", "").strip()
        item.ds_url = request.POST.get("ds_url", "").strip()
        item.sn_privado = request.POST.get("sn_privado") == "on"
        item.sn_imprimivel = request.POST.get("sn_imprimivel") == "on"
        item.sn_permite_criar = request.POST.get("sn_permite_criar") == "on"
        item.sn_permite_abandonar = request.POST.get("sn_permite_abandonar") == "on"
        item.sn_permite_cancelar = request.POST.get("sn_permite_cancelar") == "on"
        item.sn_somente_historico = request.POST.get("sn_somente_historico") == "on"
        item.ds_configuracao = configuracao
        item.sn_ativo = True
        if item.nm_item:
            if not item.cd_item_tecnico:
                item.cd_item_tecnico = _normalizar_chave_tecnica_assistencial(item.nm_item)
            _apply_audit(item, request.user)
            item.save()
            messages.success(
                request,
                f"Item {'atualizado' if item_edicao else 'adicionado'} no perfil.",
            )
        return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}#profile-item-{item.pk}")
    if request.method == "POST" and acao == "remover_item" and perfil:
        versao = versao_edicao(perfil)
        item_id = str(request.POST.get("item") or "").strip()
        item = versao.itens.filter(pk=int(item_id)).first() if item_id.isdigit() else None
        if not item and item_id.isdigit():
            item_original = perfil.itens.filter(pk=int(item_id)).first()
            if item_original:
                item = versao.itens.filter(
                    cd_item_tecnico=item_original.cd_item_tecnico,
                    sn_ativo=True,
                ).first()
        if not item:
            messages.error(request, "Item da estrutura não encontrado no perfil atual.")
            return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
        item.sn_ativo = False
        _apply_audit(item, request.user)
        item.save()
        messages.success(request, "Item removido do perfil.")
        return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")
    if request.method == "POST" and acao == "publicar_perfil" and perfil:
        descricao = request.POST.get("ds_descricao_versao", "").strip()
        versao = perfil.versoes.filter(ds_status="RASCUNHO").first()
        if not versao:
            messages.error(request, "Não existe versão em rascunho para publicar.")
        elif not descricao:
            messages.error(request, "Descreva as alterações desta versão.")
        else:
            with transaction.atomic():
                perfil.versoes.filter(ds_status="PUBLICADO").update(ds_status="ARQUIVADO")
                versao.ds_status = "PUBLICADO"
                versao.ds_descricao_versao = descricao
                versao.dh_publicacao = timezone.now()
                versao.cd_usuario_publicacao = request.user
                _apply_audit(versao, request.user)
                versao.save()
            messages.success(request, f"Versão {versao.nr_versao} publicada.")
        return redirect(f"{reverse('atendimento:perfis-assistenciais')}?perfil={perfil.pk}")

    perfis = PerfilAssistencial.objects.filter(cd_empresa=empresa)
    if request.GET.get("consultar") == "1" or request.GET.get("abrir") == "1":
        nome = request.GET.get("nm_perfil", "").strip()
        descricao = request.GET.get("ds_descricao", "").strip()
        tipo = (request.GET.get("tipo_prestador") or request.GET.get("tipos_prestador") or "").strip()
        sigiloso = request.GET.get("sn_sigiloso", "").strip()
        ativo = request.GET.get("sn_ativo", "").strip()
        if nome:
            perfis = perfis.filter(nm_perfil__icontains=nome)
        if descricao:
            perfis = perfis.filter(ds_descricao__icontains=descricao)
        if tipo:
            perfis = perfis.filter(tipos_vinculados__cd_tipo_prestador=tipo, tipos_vinculados__sn_ativo=True)
        if sigiloso in {"true", "false"}:
            perfis = perfis.filter(sn_sigiloso=sigiloso == "true")
        if ativo in {"true", "false"}:
            perfis = perfis.filter(sn_ativo=ativo == "true")
        perfis = perfis.distinct()
        if not perfil and request.GET.get("consultar") == "1" and any(
            request.GET.get(campo, "").strip()
            for campo in ("nm_perfil", "ds_descricao", "tipo_prestador", "tipos_prestador", "sn_sigiloso", "sn_ativo")
        ):
            perfis_encontrados = list(perfis[:2])
            if len(perfis_encontrados) == 1:
                perfil = perfis_encontrados[0]

    tipos_ocupados = PerfilAssistencialTipo.objects.filter(
        cd_empresa=empresa,
        sn_ativo=True,
    )
    if perfil:
        tipos_ocupados = tipos_ocupados.exclude(cd_perfil_assistencial=perfil)
    tipos_prestador = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="tipo_prestador", sn_ativo=True,
    ).exclude(cd_valor__in=tipos_ocupados.values("cd_tipo_prestador")).order_by("ds_valor")
    versao_atual = None
    itens_versao = ItemMenuAssistencial.objects.none()
    if perfil:
        versao_atual = (
            perfil.versoes.filter(ds_status="RASCUNHO").first()
            or perfil.versoes.filter(ds_status="PUBLICADO").first()
        )
        itens_versao_queryset = (
            versao_atual.itens.filter(sn_ativo=True).select_related("cd_modelo_documento", "cd_item_pai")
            if versao_atual
            else perfil.itens.filter(sn_ativo=True, cd_versao_perfil__isnull=True)
        )
        itens_lista = list(itens_versao_queryset.order_by("nr_ordem", "pk"))
        filhos = {}
        for item_arvore in itens_lista:
            filhos.setdefault(item_arvore.cd_item_pai_id, []).append(item_arvore)
        itens_versao = []

        def adicionar_filhos(pai_id, nivel):
            for filho in filhos.get(pai_id, []):
                filho.nivel_arvore = nivel
                itens_versao.append(filho)
                adicionar_filhos(filho.pk, nivel + 1)

        adicionar_filhos(None, 0)
    return render(
        request,
        "atendimento/perfis_assistenciais.html",
        {
            "perfis": perfis,
            "perfil": perfil,
            "tipos_prestador": tipos_prestador,
            "tipos_selecionados": list(
                perfil.tipos_vinculados.filter(sn_ativo=True).values_list("cd_tipo_prestador", flat=True)
            ) if perfil else [],
            "tipos_item": ItemMenuAssistencial.TIPOS,
            "versao_atual": versao_atual,
            "itens_versao": itens_versao,
            "modelos_documento": ModeloDocumento.objects.filter(
                Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
                tp_elemento="DOCUMENTO",
                sn_versao_atual=True,
                sn_ativo=True,
            ),
            "escalas_clinicas": EscalaClinica.objects.filter(cd_empresa=empresa, sn_ativo=True),
            "dominios_externos": DominioExternoPermitido.objects.filter(cd_empresa=empresa, sn_ativo=True),
            "acoes": [
                ("SINAIS_VITAIS", "Sinais vitais"), ("ADMISSAO", "Admissão / Anamnese"),
                ("EVOLUIR", "Evoluir"), ("PRESCREVER", "Prescrever medicações"),
                ("EXAMES", "Prescrever exames"), ("ALTA_MEDICA", "Alta médica"),
                ("RECEITUARIO", "Receituário"), ("AIH", "AIH"), ("DOCUMENTOS", "Documentos"),
            ],
            "icones_assistenciais": [
                ("file-text", "Documento"),
                ("clipboard-plus", "Atendimento"),
                ("activity", "Evolução / sinais vitais"),
                ("syringe", "Medicação"),
                ("printer", "Impressão"),
                ("history", "Histórico"),
                ("settings", "Configuração"),
                ("search", "Consulta"),
                ("eye", "Visualização"),
                ("edit", "Edição"),
                ("check", "Confirmação"),
                ("ban", "Bloqueio / cancelar"),
                ("key", "Segurança"),
                ("table", "Lista / escala"),
                ("monitor", "Tela externa"),
                ("folder", "Menu / pasta"),
                ("image", "Imagem / exame"),
                ("users", "Pacientes"),
                ("user", "Profissional"),
                ("stethoscope", "Profissional de saúde"),
                ("pill", "Medicamento"),
                ("package", "Materiais / insumos"),
                ("briefcase", "Mala / serviço"),
                ("car", "Carro"),
                ("ambulance", "Ambulância"),
                ("truck", "Transporte"),
                ("heart-pulse", "Cardiologia / sinais"),
                ("flask", "Laboratório"),
                ("shield", "Segurança / sigilo"),
                ("calendar", "Agenda"),
                ("map-pin", "Local / setor"),
            ],
        },
    )


def _serializar_item_assistencial(item):
    return {
        "id": item.pk,
        "parent_id": item.cd_item_pai_id,
        "technical_key": item.cd_item_tecnico,
        "name": item.nm_item,
        "icon": item.ds_icone,
        "order": item.nr_ordem,
        "type": item.tp_item,
        "action": item.ds_acao,
        "url": item.ds_url,
        "document_model_id": item.cd_modelo_documento_id,
        "private": item.sn_privado,
        "printable": item.sn_imprimivel,
        "can_create": item.sn_permite_criar,
        "can_abandon": item.sn_permite_abandonar,
        "can_cancel": item.sn_permite_cancelar,
        "history_only": item.sn_somente_historico,
        "configuration": item.ds_configuracao,
    }


@login_required
@role_required("TI")
def perfil_assistencial_itens_api(request, cd_perfil):
    empresa = _empresa_logada(request)
    perfil = get_object_or_404(PerfilAssistencial, cd_empresa=empresa, pk=cd_perfil)
    if request.method == "GET":
        versao = (
            perfil.versoes.filter(ds_status="RASCUNHO").first()
            or perfil.versoes.filter(ds_status="PUBLICADO").first()
        )
        itens = versao.itens.filter(sn_ativo=True) if versao else perfil.itens.filter(cd_versao_perfil__isnull=True, sn_ativo=True)
        return JsonResponse({
            "ok": True,
            "version": {
                "id": versao.pk if versao else None,
                "number": versao.nr_versao if versao else None,
                "status": versao.ds_status if versao else "LEGADO",
            },
            "items": [_serializar_item_assistencial(item) for item in itens.order_by("nr_ordem", "pk")],
        })
    if request.method not in {"POST", "PATCH", "DELETE"}:
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)
    with transaction.atomic():
        versao = _obter_versao_edicao_perfil(perfil, empresa, request.user)
        if isinstance(payload.get("items"), list):
            ids_validos = set(versao.itens.filter(sn_ativo=True).values_list("pk", flat=True))
            for posicao, item_data in enumerate(payload["items"]):
                item_id_lista = item_data.get("id")
                if item_id_lista not in ids_validos:
                    continue
                versao.itens.filter(pk=item_id_lista).update(
                    nr_ordem=max(0, int(item_data.get("order", posicao))),
                    cd_usuario_atualizacao=request.user,
                )
            return JsonResponse({"ok": True, "version": versao.nr_versao})
        item_id = payload.get("id")
        item = versao.itens.filter(pk=item_id).first() if item_id else None
        if request.method == "DELETE":
            if not item:
                return JsonResponse({"ok": False, "error": "Item não encontrado no rascunho."}, status=404)
            item.sn_ativo = False
            _apply_audit(item, request.user)
            item.save()
            return JsonResponse({"ok": True})
        nome = str(payload.get("name") or "").strip()
        tipo = str(payload.get("type") or "ACAO").strip().upper()
        chave = _normalizar_chave_tecnica_assistencial(payload.get("technical_key") or "")
        if not nome or tipo not in dict(ItemMenuAssistencial.TIPOS):
            return JsonResponse({"ok": False, "error": "Nome e tipo válidos são obrigatórios."}, status=400)
        if not chave:
            chave = _normalizar_chave_tecnica_assistencial(nome)
        duplicado = versao.itens.filter(cd_item_tecnico=chave, sn_ativo=True)
        if item:
            duplicado = duplicado.exclude(pk=item.pk)
        if duplicado.exists():
            return JsonResponse({"ok": False, "error": "A chave técnica já existe nesta versão."}, status=400)
        pai_id = payload.get("parent_id")
        pai = versao.itens.filter(pk=pai_id, tp_item="GRUPO", sn_ativo=True).first() if pai_id else None
        if pai_id and not pai:
            return JsonResponse({"ok": False, "error": "Grupo pai inválido."}, status=400)
        modelo_id = payload.get("document_model_id")
        modelo = None
        if modelo_id:
            modelo = ModeloDocumento.objects.filter(
                Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
                pk=modelo_id,
                tp_elemento="DOCUMENTO",
                sn_ativo=True,
            ).first()
            if not modelo:
                return JsonResponse({"ok": False, "error": "Modelo de documento inválido."}, status=400)
        item = item or ItemMenuAssistencial(
            cd_empresa=empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
        )
        item.cd_item_pai = pai
        item.cd_modelo_documento = modelo
        item.cd_item_tecnico = chave
        item.nm_item = nome
        item.ds_icone = str(payload.get("icon") or "").strip()
        item.nr_ordem = max(0, int(payload.get("order") or 0))
        item.tp_item = tipo
        item.ds_acao = str(payload.get("action") or "").strip()
        item.ds_url = str(payload.get("url") or "").strip()
        item.sn_privado = bool(payload.get("private"))
        item.sn_imprimivel = payload.get("printable", True) is not False
        item.sn_permite_criar = payload.get("can_create", True) is not False
        item.sn_permite_abandonar = payload.get("can_abandon", True) is not False
        item.sn_permite_cancelar = bool(payload.get("can_cancel"))
        item.sn_somente_historico = bool(payload.get("history_only"))
        item.ds_configuracao = payload.get("configuration") if isinstance(payload.get("configuration"), dict) else {}
        item.sn_ativo = True
        _apply_audit(item, request.user)
        item.save()
    return JsonResponse({"ok": True, "item": _serializar_item_assistencial(item), "version": versao.nr_versao})


@login_required
@role_required("TI")
def publicar_perfil_assistencial_api(request, cd_perfil):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    perfil = get_object_or_404(PerfilAssistencial, cd_empresa=empresa, pk=cd_perfil)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)
    descricao = str(payload.get("description") or "").strip()
    if not descricao:
        return JsonResponse({"ok": False, "error": "A descrição da versão é obrigatória."}, status=400)
    with transaction.atomic():
        versao = get_object_or_404(perfil.versoes.select_for_update(), ds_status="RASCUNHO")
        perfil.versoes.filter(ds_status="PUBLICADO").update(ds_status="ARQUIVADO")
        versao.ds_status = "PUBLICADO"
        versao.ds_descricao_versao = descricao
        versao.dh_publicacao = timezone.now()
        versao.cd_usuario_publicacao = request.user
        _apply_audit(versao, request.user)
        versao.save()
    return JsonResponse({"ok": True, "version": versao.nr_versao})


@login_required
@role_required("Médico")
def solicitar_exame(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    form = SolicitacaoExameForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "SOLICITACAO_EXAME",
            f"Solicitação de exame {saved.cd_solicitacao_exame}",
            f"Exame: {saved.ds_exame}\nPrioridade: {saved.get_ds_prioridade_display()}\nJustificativa: {saved.ds_justificativa}",
            request.user,
            status="FECHADO",
        )
        _mudar_status_atendimento(atendimento, "AGUARDANDO_EXAMES", request.user, origem="solicitacao_exame")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/solicitar_exame.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("TI")
def resultado_exame(request, cd_solicitacao):
    empresa = _empresa_logada(request)
    solicitacao = get_object_or_404(SolicitacaoExame, cd_empresa=empresa, cd_solicitacao_exame=cd_solicitacao)
    resultado = getattr(solicitacao, "resultado", None)
    form = ResultadoExameForm(request.POST or None, request.FILES or None, instance=resultado)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_solicitacao_exame = solicitacao
        if saved.sn_liberado:
            saved.dh_liberacao = timezone.now()
            solicitacao.ds_status = "LIBERADO"
            solicitacao.save(update_fields=["ds_status", "dh_atualizacao"])
        _apply_audit(saved, request.user)
        saved.save()
        if saved.sn_liberado:
            _mudar_status_atendimento(solicitacao.cd_atendimento, "RETORNO_EXAMES", request.user, origem="resultado_exame")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=solicitacao.cd_atendimento_id)
    return render(request, "atendimento/resultado_exame.html", {"form": form, "solicitacao": solicitacao})


@login_required
@role_required("Médico")
def prescrever(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    form = PrescricaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "PRESCRICAO",
            f"Prescrição {saved.cd_prescricao}",
            f"{saved.ds_prescricao}\n\nOrientações: {saved.ds_orientacoes}",
            request.user,
            status="FECHADO",
        )
        messages.success(request, "Prescrição registrada.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/prescricao.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("Médico")
def evoluir(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    if not atendimento.cd_prestador:
        messages.error(request, "Informe o prestador na consulta antes de evoluir.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    form = EvolucaoAtendimentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        saved.cd_atendimento = atendimento
        saved.cd_prestador = atendimento.cd_prestador
        _apply_audit(saved, request.user)
        saved.save()
        _criar_documento_clinico(
            atendimento,
            "EVOLUCAO",
            f"Evolução {saved.cd_evolucao_atendimento}",
            saved.ds_evolucao,
            request.user,
            status="FECHADO",
        )
        messages.success(request, "Evolução registrada.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    return render(request, "atendimento/evolucao.html", {"form": form, "atendimento": atendimento})


@login_required
@role_required("Médico")
@xframe_options_sameorigin
def conceder_alta(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    pendencias = []
    pendencias_detalhadas = []
    opcoes_cid = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela__in=["cid", "cids"],
        sn_ativo=True,
    ).select_related("cd_tabela_auxiliar_global").order_by("cd_valor", "ds_valor")
    opcoes_motivo_alta = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela__in=["motivo_alta", "motivos_alta"],
        sn_ativo=True,
    ).select_related("cd_tabela_auxiliar_global").order_by("ds_valor", "cd_valor")
    dh_alta_inicial = atendimento.dh_alta_medica or timezone.now()
    dh_alta_get = request.GET.get("dh_alta_medica", "").strip()
    if dh_alta_get:
        try:
            dh_alta_inicial = datetime.fromisoformat(dh_alta_get)
            if timezone.is_naive(dh_alta_inicial):
                dh_alta_inicial = timezone.make_aware(dh_alta_inicial)
        except (TypeError, ValueError):
            dh_alta_inicial = atendimento.dh_alta_medica or timezone.now()

    def _contexto_alta():
        return {
            "atendimento": atendimento,
            "pendencias": pendencias,
            "pendencias_detalhadas": pendencias_detalhadas,
            "opcoes_cid": opcoes_cid,
            "opcoes_motivo_alta": opcoes_motivo_alta,
            "dh_alta_medica_input": timezone.localtime(dh_alta_inicial).strftime("%Y-%m-%dT%H:%M"),
            "embed": request.GET.get("embed") == "1",
            "alta_base_template": "base/document_embed.html" if request.GET.get("embed") == "1" else "base/layout.html",
        }

    perfis, itens = _itens_menu_assistencial_mesclados(request.user, atendimento.cd_empresa)
    itens_por_modelo = {
        item.cd_modelo_documento_id: item
        for item in itens
        if item.cd_modelo_documento_id and item.tp_item != "GRUPO"
    }
    documentos_abertos = atendimento.documentos.filter(ds_status__in=["ABERTO", "RASCUNHO"])
    if documentos_abertos.exists():
        pendencias.append(f"{documentos_abertos.count()} documento(s) em aberto")
        for documento in documentos_abertos.select_related("cd_modelo_documento", "cd_usuario_emissor", "cd_usuario_responsavel").order_by("dh_emissao", "pk"):
            item = itens_por_modelo.get(documento.cd_modelo_documento_id)
            url = ""
            if item:
                url = (
                    f"{reverse('pep_prontuario_standalone', args=[atendimento.cd_paciente_id])}?"
                    f"{urlencode({'modo': 'atendimento', 'atendimento': atendimento.pk, 'item': item.pk, 'documento': documento.pk, 'return_to': reverse('pep_standalone')})}"
                )
            pendencias_detalhadas.append({
                "tipo": "documento",
                "texto": f"{documento.ds_titulo} — {documento.get_ds_status_display()}",
                "detalhe": f"Emitido em {timezone.localtime(documento.dh_emissao):%d/%m/%Y %H:%M}" if documento.dh_emissao else "",
                "responsavel": documento.cd_usuario_responsavel or documento.cd_usuario_emissor,
                "url": url,
            })
    exames_pendentes = atendimento.solicitacoes_exames.exclude(ds_status__in=["LIBERADO", "CANCELADO"])
    if exames_pendentes.exists():
        pendencias.append(f"{exames_pendentes.count()} exame(s) pendente(s)")
        for exame in exames_pendentes.order_by("pk"):
            pendencias_detalhadas.append({
                "tipo": "exame",
                "texto": f"{exame.ds_exame} — {exame.get_ds_status_display()}",
                "detalhe": "",
                "responsavel": "",
                "url": "",
            })
    itens_obrigatorios = [
        item
        for item in itens
        if (item.ds_configuracao or {}).get("obrigatorio_alta")
        and item.cd_modelo_documento_id
    ]
    for item in itens_obrigatorios:
        if not atendimento.documentos.filter(
            cd_modelo_documento=item.cd_modelo_documento,
            ds_status="FECHADO",
        ).exists():
            pendencias.append(f"documento obrigatório: {item.nm_item}")
            pendencias_detalhadas.append({
                "tipo": "documento_obrigatorio",
                "texto": f"Documento obrigatório não finalizado: {item.nm_item}",
                "detalhe": "Feche o documento obrigatório antes de registrar a alta.",
                "responsavel": "",
                "url": "",
            })
    if request.method == "POST":
        if pendencias:
            messages.error(request, f"Alta bloqueada: {', '.join(pendencias)}.")
            return render(request, "atendimento/alta.html", _contexto_alta())
        atendimento.ds_cid = request.POST.get("ds_cid", "").strip()
        atendimento.ds_diagnostico = request.POST.get("ds_diagnostico", "").strip()
        atendimento.ds_conduta = request.POST.get("ds_observacao_alta", "").strip()
        if not atendimento.ds_destino:
            atendimento.ds_destino = "ALTA"
        atendimento.ds_motivo_alta = request.POST.get("ds_motivo_alta", "").strip()
        dh_alta_texto = request.POST.get("dh_alta_medica", "").strip()
        try:
            dh_alta_medica = datetime.fromisoformat(dh_alta_texto)
            if timezone.is_naive(dh_alta_medica):
                dh_alta_medica = timezone.make_aware(dh_alta_medica)
        except (TypeError, ValueError):
            dh_alta_medica = None
        if not atendimento.cd_prestador or not atendimento.ds_diagnostico or not atendimento.ds_motivo_alta or not dh_alta_medica:
            messages.error(request, "Informe data/hora da alta, diagnóstico/CID e motivo da alta.")
            return render(request, "atendimento/alta.html", _contexto_alta())

        with transaction.atomic():
            motivo_normalizado = unicodedata.normalize("NFKD", atendimento.ds_motivo_alta).encode("ascii", "ignore").decode("ascii").lower()
            alta_por_obito = "obito" in motivo_normalizado
            atendimento.dh_alta_medica = dh_alta_medica
            _apply_audit(atendimento, request.user)
            atendimento.save(update_fields=[
                "ds_cid", "ds_diagnostico", "ds_conduta", "ds_destino", "ds_motivo_alta",
                "dh_alta_medica", "dh_atualizacao", "cd_usuario_atualizacao",
            ])
            if alta_por_obito:
                paciente = atendimento.cd_paciente
                paciente.sn_obito = True
                paciente.dh_obito = dh_alta_medica
                _apply_audit(paciente, request.user)
                paciente.save(update_fields=["sn_obito", "dh_obito", "dh_atualizacao", "cd_usuario_atualizacao"])
            documento = _criar_documento_clinico(
                atendimento,
                "RESUMO_ALTA",
                f"Resumo de alta {atendimento.pk}",
                (
                    f"CID: {atendimento.ds_cid or '-'}\n"
                    f"Diagnóstico: {atendimento.ds_diagnostico}\n"
                    f"Observações: {atendimento.ds_conduta or '-'}\n"
                    f"Motivo da alta: {atendimento.ds_motivo_alta}\n"
                    f"Data e hora: {timezone.localtime(atendimento.dh_alta_medica):%d/%m/%Y %H:%M}"
                ),
                request.user,
                status="FECHADO",
            )
            _mudar_status_atendimento(atendimento, "OBITO" if alta_por_obito else "ALTA_MEDICA", request.user, origem="alta_medica")
        messages.success(request, "Alta médica registrada. O resumo está disponível para impressão.")
        return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)
    return render(request, "atendimento/alta.html", _contexto_alta())


@login_required
@role_required("Médico")
def documento_assistencial(request, cd_atendimento, tipo):
    tipos = {
        "admissao": ("ADMISSAO_ANAMNESE", "Admissão / Anamnese"),
        "receituario": ("RECEITUARIO", "Receituário"),
        "aih": ("AIH", "AIH"),
    }
    if tipo not in tipos:
        raise PermissionDenied
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_prestador"),
        cd_empresa=_empresa_logada(request),
        pk=cd_atendimento,
    )
    codigo, titulo = tipos[tipo]
    if request.method == "POST":
        conteudo = request.POST.get("ds_conteudo", "").strip()
        if not conteudo:
            messages.error(request, "Preencha o conteúdo do documento.")
        else:
            documento = _criar_documento_clinico(
                atendimento,
                codigo,
                f"{titulo} - atendimento {atendimento.pk}",
                conteudo,
                request.user,
                status="FINALIZADO" if request.POST.get("finalizar") == "1" else "RASCUNHO",
            )
            messages.success(request, f"{titulo} registrado.")
            return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)
    return render(
        request,
        "atendimento/documento_assistencial.html",
        {"atendimento": atendimento, "tipo": tipo, "titulo": titulo},
    )


@login_required
@role_required("Médico")
def finalizar_atendimento(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    if request.method != "POST":
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    if atendimento.ds_status not in {"ALTA", "ALTA_MEDICA"}:
        messages.error(request, "Conceda a alta antes de finalizar o atendimento.")
        return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)
    _mudar_status_atendimento(atendimento, "FINALIZADO", request.user, origem="finalizar_atendimento")
    if atendimento.cd_agendamento:
        atendimento.cd_agendamento.ds_status = "FINALIZADO"
        atendimento.cd_agendamento.save(update_fields=["ds_status", "dh_atualizacao"])
    messages.success(request, "Atendimento finalizado com sucesso.")
    return redirect("atendimento:pep")


@login_required
@xframe_options_sameorigin
def imprimir_atendimento(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_pre_atendimento", "cd_agendamento"),
        cd_empresa=empresa,
        cd_atendimento=cd_atendimento,
    )
    modelo_id = request.GET.get("modelo", "").strip()
    if modelo_id.isdigit():
        modelo = get_object_or_404(
            ModeloDocumento,
            Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
            pk=int(modelo_id),
            tp_elemento="DOCUMENTO",
            tp_documento__in={"FICHA_ATENDIMENTO", "ETIQUETA_ATENDIMENTO"},
            sn_versao_atual=True,
            sn_ativo=True,
        )
        agora = timezone.now()
        documento = DocumentoClinico(
            cd_documento_clinico=0,
            cd_empresa=empresa,
            cd_atendimento=atendimento,
            cd_modelo_documento=modelo,
            tp_documento=modelo.tp_documento,
            ds_titulo=modelo.nm_modelo,
            ds_status="FECHADO",
            dh_criacao=agora,
            dh_emissao=agora,
            cd_usuario_emissor=request.user,
            cd_usuario_criacao=request.user,
        )
        return render(
            request,
            "atendimento/imprimir_modelo_atendimento.html",
            {
                "atendimento": atendimento,
                "empresa": empresa,
                "modelo": modelo,
                "apresentacao": _renderizar_documento(documento, True),
            },
        )
    return render(request, "atendimento/imprimir_atendimento.html", {"atendimento": atendimento, "empresa": empresa})


@login_required
@role_required("TI")
def modelos_documento(request, cd_modelo=None):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Editor de documentos"
    request.current_tab_root_title = "Editor de documentos"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    _pastas_documento_padrao(empresa, request.user)
    modelo = (
        ModeloDocumento.objects.filter(Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True), pk=cd_modelo).first()
        if cd_modelo
        else None
    )
    return _resposta_modelos_documento(request, empresa, modelo)


@login_required
@role_required("TI")
def testar_variavel_documento(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    atendimento_id = str(request.POST.get("atendimento") or "").strip()
    atendimento = (
        Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_convenio", "cd_setor_atual")
        .filter(cd_empresa=empresa, pk=int(atendimento_id))
        .first()
        if atendimento_id.isdigit()
        else None
    )
    if not atendimento and atendimento_id != "demonstrativo":
        return JsonResponse({"ok": False, "error": "Selecione um atendimento de teste válido."}, status=400)
    contexto = (
        _variaveis_atendimento_documento(atendimento, empresa)
        if atendimento
        else {
            "paciente.nome": "PACIENTE DE TESTE",
            "paciente.sexo": "F",
            "paciente.codigo": "000001",
            "atendimento.codigo": "000001",
            "atendimento.data_hora": timezone.localtime().strftime("%d/%m/%Y %H:%M:%S"),
            "empresa.nome": empresa.nm_empresa,
        }
    )
    try:
        resultado = _avaliar_expressao_variavel(
            request.POST.get("expressao", ""),
            contexto,
            strict=True,
        )
    except ValueError as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)
    return JsonResponse({"ok": True, "result": resultado})


@login_required
@role_required("TI")
def rascunho_editor_documento(request):
    empresa = _empresa_logada(request)
    RascunhoEditorDocumento.objects.filter(
        cd_empresa=empresa,
        cd_usuario=request.user,
        dh_atualizacao__lt=timezone.now() - timedelta(days=2),
    ).delete()
    modelo_id = str(request.GET.get("modelo") or request.POST.get("modelo") or "").strip()
    chave_guia = (
        request.GET.get("guia")
        or request.POST.get("guia")
        or "editor-documentos"
    ).strip()[:180]
    modelo = (
        ModeloDocumento.objects.filter(
            Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
            pk=int(modelo_id),
        ).first()
        if modelo_id.isdigit()
        else None
    )
    filtros = {
        "cd_empresa": empresa,
        "cd_usuario": request.user,
        "cd_modelo_documento": modelo,
        "ds_chave_guia": chave_guia,
    }
    if request.method == "GET":
        rascunho = RascunhoEditorDocumento.objects.filter(**filtros).first()
        return JsonResponse({
            "ok": True,
            "state": rascunho.ds_estado if rascunho else None,
            "updated_at": rascunho.dh_atualizacao.isoformat() if rascunho else None,
        })
    if request.method == "POST":
        if request.POST.get("acao") == "descartar":
            RascunhoEditorDocumento.objects.filter(**filtros).delete()
            return JsonResponse({"ok": True})
        try:
            content_length = int(request.META.get("CONTENT_LENGTH") or 0)
            is_gzip = request.headers.get("X-Celeris-Draft-Encoding") == "gzip"
            max_upload_size = 15_000_000 if is_gzip else 3_000_000
            if content_length > max_upload_size:
                return JsonResponse({"ok": False, "error": "Rascunho excede o limite de envio."}, status=413)
            raw_body = request.body or b"{}"
            if is_gzip:
                raw_body = gzip.decompress(raw_body)
                if len(raw_body) > 20_000_000:
                    return JsonResponse({"ok": False, "error": "Rascunho descompactado excede o limite permitido."}, status=413)
            payload = json.loads(raw_body.decode("utf-8"))
        except RequestDataTooBig:
            return JsonResponse({"ok": False, "error": "Rascunho excede o limite permitido."}, status=413)
        except (OSError, EOFError):
            return JsonResponse({"ok": False, "error": "Rascunho compactado inválido."}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "Estado inválido."}, status=400)
        estado = payload.get("state")
        if not isinstance(estado, dict):
            return JsonResponse({"ok": False, "error": "Estado inválido."}, status=400)
        if not is_gzip and len(request.body or b"") > 3_000_000:
            return JsonResponse({"ok": False, "error": "Rascunho excede o limite de 3 MB."}, status=413)
        rascunho = RascunhoEditorDocumento.objects.filter(**filtros).first()
        if not rascunho:
            rascunho = RascunhoEditorDocumento(**filtros)
        rascunho.ds_estado = estado
        rascunho.save()
        return JsonResponse({"ok": True, "updated_at": rascunho.dh_atualizacao.isoformat()})
    if request.method == "DELETE":
        RascunhoEditorDocumento.objects.filter(**filtros).delete()
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)


def _ids_familia_modelo_documento(modelo):
    raiz = modelo
    while raiz.cd_versao_anterior_id:
        raiz = raiz.cd_versao_anterior
    candidatos = list(
        ModeloDocumento.objects.filter(cd_empresa=modelo.cd_empresa)
        .only("pk", "cd_versao_anterior_id")
    )
    filhos = {}
    for candidato in candidatos:
        filhos.setdefault(candidato.cd_versao_anterior_id, []).append(candidato.pk)
    encontrados = []
    pendentes = [raiz.pk]
    while pendentes:
        atual = pendentes.pop()
        if atual in encontrados:
            continue
        encontrados.append(atual)
        pendentes.extend(filhos.get(atual, []))
    return encontrados


def _versao_atual_modelo_documento(modelo):
    if not modelo:
        return None
    if modelo.sn_versao_atual and modelo.sn_ativo:
        return modelo
    atual = (
        ModeloDocumento.objects.filter(
            pk__in=_ids_familia_modelo_documento(modelo),
            sn_versao_atual=True,
            sn_ativo=True,
        )
        .order_by("-nr_versao", "-pk")
        .first()
    )
    return atual or modelo


def _propagar_referencia_modelo_documento(modelo_anterior, modelo_atual, usuario):
    if not modelo_anterior or not modelo_atual or modelo_anterior.pk == modelo_atual.pk:
        return
    if modelo_atual.tp_elemento not in {"CABECALHO", "RODAPE"}:
        return
    campo = "cd_cabecalho" if modelo_atual.tp_elemento == "CABECALHO" else "cd_rodape"
    ids_familia = _ids_familia_modelo_documento(modelo_anterior)
    atualizacoes = {
        f"{campo}_id": modelo_atual.pk,
        "cd_usuario_atualizacao_id": usuario.pk,
    }
    ModeloDocumento.objects.filter(
        cd_empresa=modelo_atual.cd_empresa,
        **{f"{campo}_id__in": ids_familia},
    ).exclude(pk=modelo_atual.pk).update(**atualizacoes)


def _resposta_modelos_documento(request, empresa, modelo):
    pasta_id = request.POST.get("pasta_selecionada") or request.GET.get("pasta") or getattr(modelo, "cd_pasta_id", None)
    pasta_id = int(pasta_id) if str(pasta_id or "").isdigit() else None
    pasta_selecionada = PastaDocumento.objects.filter(
        Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
        pk=pasta_id,
        sn_ativo=True,
    ).first()
    pasta_gravacao = pasta_selecionada if pasta_selecionada and pasta_selecionada.cd_empresa_id == empresa.pk else None
    redirect_url = reverse("atendimento:modelos-documento")
    if pasta_gravacao:
        redirect_url = f"{redirect_url}?{urlencode({'pasta': pasta_gravacao.pk})}"
    initial_html_tela = getattr(modelo, "ds_html_tela", "") if modelo else ""
    initial_css_tela = getattr(modelo, "ds_css_tela", "") if modelo else ""
    initial_project_tela = getattr(modelo, "ds_projeto_tela", {}) if modelo else {}
    initial_html_impressao = getattr(modelo, "ds_html_impressao", "") if modelo else ""
    initial_css_impressao = getattr(modelo, "ds_css_impressao", "") if modelo else ""
    initial_project_impressao = getattr(modelo, "ds_projeto_impressao", {}) if modelo else {}
    modelo_protegido = bool(modelo and (modelo.sn_sistema or not modelo.sn_editavel))
    if modelo:
        modelo.cd_cabecalho = _versao_atual_modelo_documento(modelo.cd_cabecalho)
        modelo.cd_rodape = _versao_atual_modelo_documento(modelo.cd_rodape)
    acao = request.POST.get("acao")
    if request.method == "POST" and acao == "criar_pasta":
        nome = request.POST.get("nm_pasta", "").strip()
        if any(unicodedata.combining(char) for char in unicodedata.normalize("NFD", nome)):
            messages.error(request, "O nome da pasta não pode conter acentuação.")
        elif nome:
            pasta = PastaDocumento(cd_empresa=empresa, cd_pasta_pai=pasta_gravacao, nm_pasta=nome)
            _apply_audit(pasta, request.user)
            pasta.save()
            messages.success(request, "Pasta criada com sucesso.")
        return redirect(redirect_url)
    if request.method == "POST" and acao in {"renomear", "mover", "excluir", "copiar"}:
        tipo_item = request.POST.get("tipo_item")
        item_id = request.POST.get("item_id")
        if tipo_item == "pasta":
            item = get_object_or_404(PastaDocumento, cd_empresa=empresa, pk=item_id)
            if item.sn_sistema or not item.sn_editavel:
                raise PermissionDenied
            if acao == "renomear":
                novo_nome = request.POST.get("novo_nome", "").strip() or item.nm_pasta
                if any(unicodedata.combining(char) for char in unicodedata.normalize("NFD", novo_nome)):
                    messages.error(request, "O nome da pasta não pode conter acentuação.")
                    return redirect(redirect_url)
                item.nm_pasta = novo_nome
                _apply_audit(item, request.user)
                item.save()
            elif acao == "mover":
                destino_id = request.POST.get("destino_id", "").strip()
                destino = (
                    PastaDocumento.objects.filter(cd_empresa=empresa, pk=int(destino_id), sn_ativo=True).first()
                    if destino_id.isdigit() else None
                )
                ancestral = destino
                destino_invalido = destino == item
                while ancestral and not destino_invalido:
                    destino_invalido = ancestral.cd_pasta_pai_id == item.pk
                    ancestral = ancestral.cd_pasta_pai
                if destino_invalido:
                    messages.error(request, "Não é possível mover uma pasta para dentro dela mesma.")
                    return redirect(redirect_url)
                item.cd_pasta_pai = destino
                _apply_audit(item, request.user)
                item.save()
            elif item.subpastas.exists() or ModeloDocumento.objects.filter(cd_pasta=item).exists():
                messages.error(request, "A pasta não pode ser excluída porque contém itens.")
            else:
                item.delete()
        elif tipo_item == "documento":
            item = get_object_or_404(
                ModeloDocumento.objects.filter(Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True)),
                pk=item_id,
            )
            if acao != "copiar" and (item.cd_empresa_id != empresa.pk or item.sn_sistema or not item.sn_editavel):
                raise PermissionDenied
            if acao == "copiar":
                destino_id = request.POST.get("destino_id", "").strip()
                destino = (
                    PastaDocumento.objects.filter(cd_empresa=empresa, pk=int(destino_id), sn_ativo=True).first()
                    if destino_id.isdigit() else None
                )
                nome_base = request.POST.get("novo_nome", "").strip() or item.nm_modelo
                nome = nome_base
                sufixo = 2
                while ModeloDocumento.objects.filter(
                    cd_empresa=empresa,
                    tp_documento=item.tp_documento,
                    nm_modelo=nome,
                    sn_versao_atual=True,
                ).exists():
                    nome = f"{nome_base} ({sufixo})"
                    sufixo += 1
                copia = ModeloDocumento(
                    cd_empresa=empresa,
                    cd_pasta=destino,
                    cd_cabecalho=item.cd_cabecalho,
                    cd_rodape=item.cd_rodape,
                    nm_modelo=nome,
                    tp_documento=item.tp_documento,
                    tp_elemento=item.tp_elemento,
                    nr_versao=1,
                    ds_alteracoes_versao="Cópia criada a partir de um modelo padrão Celeris.",
                    ds_html_tela=item.ds_html_tela,
                    ds_css_tela=item.ds_css_tela,
                    ds_projeto_tela=item.ds_projeto_tela,
                    ds_html_impressao=item.ds_html_impressao,
                    ds_css_impressao=item.ds_css_impressao,
                    ds_projeto_impressao=item.ds_projeto_impressao,
                    ds_cabecalho=item.ds_cabecalho,
                    ds_corpo=item.ds_corpo,
                    ds_rodape=item.ds_rodape,
                    ds_variaveis=item.ds_variaveis,
                    ds_campos_bloqueados=item.ds_campos_bloqueados,
                    sn_exibe_assinatura=item.sn_exibe_assinatura,
                    tp_alinhamento_assinatura=item.tp_alinhamento_assinatura,
                    sn_exibe_conselho_assinatura=item.sn_exibe_conselho_assinatura,
                    sn_versao_atual=True,
                    sn_sistema=False,
                    sn_editavel=True,
                    sn_ativo=item.sn_ativo,
                )
                _apply_audit(copia, request.user)
                copia.save()
                messages.success(request, f'Documento "{copia.nm_modelo}" copiado para a empresa.')
                return redirect("atendimento:editar-modelo-documento", cd_modelo=copia.pk)
            if acao == "renomear":
                novo_nome = request.POST.get("novo_nome", "").strip() or item.nm_modelo
                if any(unicodedata.combining(char) for char in unicodedata.normalize("NFD", novo_nome)):
                    messages.error(request, "O nome não pode conter acentuação.")
                    return redirect(redirect_url)
                item.nm_modelo = novo_nome
                _apply_audit(item, request.user)
                item.save()
            elif acao == "mover":
                destino_id = request.POST.get("destino_id", "").strip()
                item.cd_pasta = (
                    PastaDocumento.objects.filter(cd_empresa=empresa, pk=int(destino_id), sn_ativo=True).first()
                    if destino_id.isdigit() else None
                )
                _apply_audit(item, request.user)
                item.save()
            else:
                try:
                    item.delete()
                except ProtectedError:
                    messages.error(request, "O documento possui versões ou utilizações e não pode ser excluído.")
        return redirect(redirect_url)
    form = ModeloDocumentoForm(
        request.POST or None,
        instance=None if request.method == "POST" else modelo,
        empresa=empresa,
        original_name=modelo.nm_modelo if modelo else "",
    )
    novo_tipo = request.GET.get("novo")
    if not modelo and not novo_tipo:
        request.current_can_save = False
    if not modelo and novo_tipo == "campo":
        form.initial["tp_elemento"] = "CAMPO"
        form.initial["tp_documento"] = "ADMINISTRATIVO"
    elif not modelo and novo_tipo == "variavel":
        form.initial["tp_elemento"] = "VARIAVEL"
        form.initial["tp_documento"] = "ADMINISTRATIVO"
    elif not modelo and novo_tipo == "bloco":
        form.initial["tp_elemento"] = "BLOCO"
        form.initial["tp_documento"] = "ADMINISTRATIVO"
    elif not modelo and novo_tipo == "documento":
        form.initial["tp_elemento"] = "DOCUMENTO"
    elif not modelo and novo_tipo == "cabecalho":
        form.initial["tp_elemento"] = "CABECALHO"
        form.initial["tp_documento"] = "ADMINISTRATIVO"
    elif not modelo and novo_tipo == "rodape":
        form.initial["tp_elemento"] = "RODAPE"
        form.initial["tp_documento"] = "ADMINISTRATIVO"
    elemento_editor = getattr(modelo, "tp_elemento", None) or form.initial.get("tp_elemento") or "DOCUMENTO"
    if modelo and request.method != "POST":
        form.initial["ds_alteracoes_versao"] = ""
        if not modelo.sn_versao_atual:
            form.initial["sn_ativo"] = False
    if request.method == "POST" and form.is_valid():
        salvar_como_empresa = (
            modelo_protegido
            and not request.user.is_superuser
            and request.POST.get("salvar_como_empresa") == "1"
        )
        if modelo_protegido and not request.user.is_superuser and not salvar_como_empresa:
            form.add_error(None, "Modelos padrão do Celeris não podem ser sobrescritos. Salve uma cópia para a empresa.")
        saved = form.save(commit=False)
        saved.cd_empresa = empresa if salvar_como_empresa else (modelo.cd_empresa if modelo else empresa)
        saved.cd_pasta = pasta_gravacao if salvar_como_empresa else (pasta_selecionada if modelo else pasta_gravacao)
        if modelo and not salvar_como_empresa:
            saved.sn_sistema = modelo.sn_sistema
            saved.sn_editavel = modelo.sn_editavel
        elif salvar_como_empresa:
            saved.sn_sistema = False
            saved.sn_editavel = True
            saved.nr_versao = 1
            saved.cd_versao_anterior = None
            nome_base = saved.nm_modelo
            sufixo = 2
            while ModeloDocumento.objects.filter(
                cd_empresa=empresa,
                tp_documento=saved.tp_documento,
                nm_modelo=saved.nm_modelo,
                sn_versao_atual=True,
            ).exists():
                saved.nm_modelo = f"{nome_base} ({sufixo})"
                sufixo += 1
        saved.ds_html_tela = request.POST.get("ds_html_tela", "")
        saved.ds_css_tela = request.POST.get("ds_css_tela", "")
        saved.ds_html_impressao = request.POST.get("ds_html_impressao", "")
        saved.ds_css_impressao = request.POST.get("ds_css_impressao", "")
        if saved.tp_elemento == "CABECALHO":
            saved.ds_css_impressao += "\n.reusable-document-header{max-height:55mm;overflow:hidden}"
        elif saved.tp_elemento == "RODAPE":
            saved.ds_css_impressao += "\n.reusable-document-footer{max-height:35mm;overflow:hidden}"
        elif saved.tp_elemento == "DOCUMENTO":
            saved.ds_html_impressao = _configurar_assinatura_prestador(saved.ds_html_impressao, saved)
        for field_name in ("ds_projeto_tela", "ds_projeto_impressao"):
            try:
                setattr(saved, field_name, json.loads(request.POST.get(field_name) or "{}"))
            except json.JSONDecodeError:
                form.add_error(None, f"Não foi possível interpretar o projeto do editor ({field_name}).")
        if saved.tp_elemento == "VARIAVEL":
            projeto_tela = saved.ds_projeto_tela if isinstance(saved.ds_projeto_tela, dict) else {}
            projeto_tela["customVariable"] = {
                "name": request.POST.get("custom_variable_name", "").strip(),
                "expression": request.POST.get("custom_variable_expression", ""),
            }
            saved.ds_projeto_tela = projeto_tela
        if saved.tp_elemento == "DOCUMENTO" and not _impressao_possui_grade(saved):
            saved.ds_html_impressao = _gerar_impressao_pela_grade(saved)
        if modelo and not salvar_como_empresa and not form.errors:
            campos = (
                "nm_modelo", "tp_documento", "tp_elemento", "cd_cabecalho_id", "cd_rodape_id",
                "sn_ativo", "sn_exibe_assinatura", "tp_alinhamento_assinatura",
                "sn_exibe_conselho_assinatura", "ds_html_tela", "ds_css_tela", "ds_projeto_tela",
                "ds_html_impressao", "ds_css_impressao", "ds_projeto_impressao",
            )
            if all(getattr(saved, campo) == getattr(modelo, campo) for campo in campos) and saved.cd_pasta_id == modelo.cd_pasta_id:
                form.add_error(None, "Nenhuma alteração real foi identificada. Modifique o conteúdo ou a configuração antes de salvar uma nova versão.")
        if not form.errors:
            if modelo and not salvar_como_empresa:
                familia = ModeloDocumento.objects.filter(pk__in=_ids_familia_modelo_documento(modelo))
                saved.nr_versao = (familia.aggregate(maior=Max("nr_versao"))["maior"] or 0) + 1
                saved.cd_versao_anterior = modelo
                familia.update(sn_versao_atual=False, sn_ativo=False, cd_usuario_atualizacao=request.user)
                saved.sn_ativo = True
            _apply_audit(saved, request.user)
            saved.save()
            if modelo and not salvar_como_empresa:
                _propagar_referencia_modelo_documento(modelo, saved, request.user)
            RascunhoEditorDocumento.objects.filter(
                cd_empresa=empresa,
                cd_usuario=request.user,
                cd_modelo_documento=modelo,
            ).delete()
            if salvar_como_empresa:
                messages.success(request, "Cópia do modelo padrão salva para a empresa.")
                return redirect("atendimento:editar-modelo-documento", cd_modelo=saved.pk)
            messages.success(request, f"Versão {saved.nr_versao} do modelo salva com sucesso.")
            return redirect(_safe_return_url(request) or redirect_url)
    if request.method == "POST":
        initial_html_tela = request.POST.get("ds_html_tela", initial_html_tela)
        initial_css_tela = request.POST.get("ds_css_tela", initial_css_tela)
        initial_html_impressao = request.POST.get("ds_html_impressao", initial_html_impressao)
        initial_css_impressao = request.POST.get("ds_css_impressao", initial_css_impressao)
        try:
            initial_project_tela = json.loads(request.POST.get("ds_projeto_tela") or "{}")
        except json.JSONDecodeError:
            initial_project_tela = {}
        try:
            initial_project_impressao = json.loads(request.POST.get("ds_projeto_impressao") or "{}")
        except json.JSONDecodeError:
            initial_project_impressao = {}
        if elemento_editor == "VARIAVEL":
            if not isinstance(initial_project_tela, dict):
                initial_project_tela = {}
            initial_project_tela["customVariable"] = {
                "name": request.POST.get("custom_variable_name", "").strip(),
                "expression": request.POST.get("custom_variable_expression", ""),
            }
    modelos = ModeloDocumento.objects.filter(
        Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
        sn_versao_atual=True,
    ).select_related("cd_pasta")
    versoes = (
        ModeloDocumento.objects.filter(pk__in=_ids_familia_modelo_documento(modelo)).order_by("-nr_versao")
        if modelo
        else ModeloDocumento.objects.none()
    )
    atendimentos_teste = list(
        Atendimento.objects.filter(cd_empresa=empresa, sn_ativo=True)
        .select_related("cd_paciente", "cd_prestador")
        .order_by("-dh_inicio")[:20]
    )
    contextos_teste = [
        {
            "id": atendimento.pk,
            "label": f"Atendimento {atendimento.pk} · {atendimento.cd_paciente.nm_paciente}",
            "variables": _variaveis_atendimento_documento(atendimento, empresa),
        }
        for atendimento in atendimentos_teste
    ]
    usuario_teste = request.user.get_username()
    documento_teste = {
        "documento.codigo": modelo.pk if modelo else "NOVO",
        "documento.titulo": modelo.nm_modelo if modelo else "Documento em edição",
        "documento.status": "Rascunho",
        "documento.data_hora_criacao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        "documento.datahoracriacao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        "documento.data_hora_atual": timezone.localtime().strftime("%d/%m/%Y %H:%M:%S"),
        "documento.datahoraatual": timezone.localtime().strftime("%d/%m/%Y %H:%M:%S"),
        "documento.usuario_criacao": usuario_teste,
        "documento.usuariocriacao": usuario_teste,
        "documento.pagina": "1",
    }
    agendamento_teste = Agendamento.objects.filter(cd_empresa=empresa).select_related(
        "cd_paciente", "cd_agenda_profissional__cd_prestador", "cd_usuario_criacao",
    ).order_by("-dh_agendamento").first()
    variaveis_agendamento_teste = {}
    if agendamento_teste:
        agenda_teste = agendamento_teste.cd_agenda_profissional
        usuario_agendamento = agendamento_teste.cd_usuario_criacao
        variaveis_agendamento_teste = {
            "agendamento.codigo": agendamento_teste.pk,
            "agendamento.data": timezone.localtime(agendamento_teste.dh_agendamento).strftime("%d/%m/%Y"),
            "agendamento.hora": timezone.localtime(agendamento_teste.dh_agendamento).strftime("%H:%M"),
            "agendamento.data_hora": timezone.localtime(agendamento_teste.dh_agendamento).strftime("%d/%m/%Y %H:%M"),
            "agendamento.dia_semana": timezone.localtime(agendamento_teste.dh_agendamento).strftime("%A"),
            "agendamento.prestador": agendamento_teste.ds_profissional,
            "agendamento.nome_guerra_prestador": getattr(getattr(agenda_teste, "cd_prestador", None), "nm_guerra", "") or agendamento_teste.ds_profissional,
            "agendamento.especialidade": agendamento_teste.ds_especialidade,
            "agendamento.tipo": agendamento_teste.ds_tipo_atendimento,
            "agendamento.plano": agendamento_teste.ds_plano,
            "agendamento.observacao": agendamento_teste.ds_observacao,
            "agendamento.usuario": (
                usuario_agendamento.display_name()
                if usuario_agendamento and hasattr(usuario_agendamento, "display_name")
                else getattr(usuario_agendamento, "username", "")
            ),
        }
    for contexto in contextos_teste:
        contexto["variables"].update(documento_teste)
        contexto["variables"].update(variaveis_agendamento_teste)
        contexto["variables"].update({
            "chamado.codigo": "000001",
            "chamado.titulo": "Solicitação de suporte demonstrativa",
            "chamado.descricao": "Descrição do chamado para pré-visualização.",
            "chamado.modulo": "Suporte",
            "chamado.status": "Aberto",
            "chamado.setor": "Recepção",
            "chamado.prioridade": "Normal",
            "chamado.motivo": "Manutenção",
            "chamado.oficina": "Informática",
            "chamado.solicitante": usuario_teste,
            "chamado.usuario_solicitante": usuario_teste,
            "chamado.responsavel": "",
            "chamado.usuario_responsavel": "",
            "chamado.data_hora_solicitacao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
            "chamado.data_hora_recebimento": "",
            "chamado.data_hora_realizacao": "",
            "chamado.data_hora_conclusao": "",
            "chamado.motivo_conclusao": "",
            "chamado.conclusao": "",
            "chamado.executores": "",
            "chamado.usuario_emissao": usuario_teste,
            "chamado.data_hora_emissao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
        })
    if not contextos_teste:
        contextos_teste.append(
            {
                "id": "demonstrativo",
                "label": "Atendimento demonstrativo · Paciente de Teste",
                "variables": {
                    "paciente.nome": "PACIENTE DE TESTE",
                    "paciente.codigo": "000001",
                    "paciente.nascimento": "01/01/1990",
                    "paciente.mae": "MARIA DA SILVA",
                    "paciente.cpf": "529.982.247-25",
                    "paciente.cns": "Não informado",
                    "paciente.sexo": "Feminino",
                    "atendimento.codigo": "000001",
                    "atendimento.data_hora": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
                    "atendimento.status": "Em atendimento",
                    "atendimento.especialidade": "Clínica Geral",
                    "prestador.nome": "MÉDICO DE TESTE",
                    "prestador.conselho": "CRM",
                    "prestador.numero_conselho": "000000",
                    "empresa.nome": empresa.nm_empresa,
                    "agendamento.codigo": "000001",
                    "agendamento.data": timezone.localtime().strftime("%d/%m/%Y"),
                    "agendamento.hora": timezone.localtime().strftime("%H:%M"),
                    "agendamento.data_hora": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
                    "agendamento.dia_semana": timezone.localtime().strftime("%A"),
                    "agendamento.prestador": "MÉDICO DE TESTE",
                    "agendamento.nome_guerra_prestador": "MÉDICO TESTE",
                    "agendamento.especialidade": "Clínica Geral",
                    "agendamento.tipo": "Primeira consulta",
                    "agendamento.plano": "Plano demonstrativo",
                    "agendamento.observacao": "Sem observações",
                    "agendamento.usuario": usuario_teste,
                    "chamado.codigo": "000001",
                    "chamado.titulo": "Solicitação de suporte demonstrativa",
                    "chamado.descricao": "Descrição do chamado para pré-visualização.",
                    "chamado.modulo": "Suporte",
                    "chamado.status": "Aberto",
                    "chamado.setor": "Recepção",
                    "chamado.prioridade": "Normal",
                    "chamado.motivo": "Manutenção",
                    "chamado.oficina": "Informática",
                    "chamado.solicitante": usuario_teste,
                    "chamado.usuario_solicitante": usuario_teste,
                    "chamado.responsavel": "",
                    "chamado.usuario_responsavel": "",
                    "chamado.data_hora_solicitacao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
                    "chamado.data_hora_recebimento": "",
                    "chamado.data_hora_realizacao": "",
                    "chamado.data_hora_conclusao": "",
                    "chamado.motivo_conclusao": "",
                    "chamado.conclusao": "",
                    "chamado.executores": "",
                    "chamado.usuario_emissao": usuario_teste,
                    "chamado.data_hora_emissao": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
                    **documento_teste,
                },
            }
        )
    documentos_sem_formulario = {"COMPROVANTE_AGENDAMENTO", "COMPROVANTE_CHAMADO", "FICHA_ATENDIMENTO", "ETIQUETA_ATENDIMENTO"}
    layout_apenas = elemento_editor == "DOCUMENTO" and (form["tp_documento"].value() or "") in documentos_sem_formulario
    return render(
        request,
        "atendimento/modelos_documento.html",
        {
            "form": form,
            "modelos": modelos,
            "modelo": modelo,
            "versoes": versoes,
            "pastas_empresa": PastaDocumento.objects.filter(cd_empresa=empresa, sn_ativo=True),
            "pastas_sistema": PastaDocumento.objects.filter(cd_empresa__isnull=True, sn_ativo=True),
            "pastas_destino": PastaDocumento.objects.filter(cd_empresa=empresa, sn_ativo=True),
            "pasta_selecionada": pasta_selecionada,
            "campos_reutilizaveis": list(
                modelos.filter(tp_elemento__in=("CAMPO", "BLOCO", "VARIAVEL")).values(
                    "cd_modelo_documento",
                    "nm_modelo",
                    "tp_elemento",
                    "ds_html_tela",
                    "ds_html_impressao",
                    "ds_projeto_tela",
                    "ds_projeto_impressao",
                )
            ),
            "variaveis_personalizadas": list(
                modelos.filter(tp_elemento="VARIAVEL").values(
                    "cd_modelo_documento", "nm_modelo", "ds_projeto_tela",
                )
            ),
            "elementos_impressao": list(
                modelos.filter(tp_elemento__in=("CABECALHO", "RODAPE")).values(
                    "cd_modelo_documento",
                    "tp_elemento",
                    "ds_html_impressao",
                    "ds_css_impressao",
                    "ds_projeto_impressao",
                )
            ),
            "tabelas_auxiliares": [
                {
                    "ds_tabela": tabela.ds_tabela,
                    "ds_descricao": tabela.ds_descricao,
                    "valores": list(
                        tabela.valores.filter(sn_ativo=True).order_by("ds_valor").values(
                            "cd_valor_auxiliar_global",
                            "cd_valor",
                            "ds_valor",
                            "ds_grupo",
                        )
                    ),
                }
                for tabela in TabelaAuxiliarGlobal.objects.filter(sn_ativo=True)
                .prefetch_related("valores")
                .order_by("ds_descricao", "ds_tabela")
            ],
            "elemento_editor": elemento_editor,
            "layout_apenas": layout_apenas,
            "modo_criacao": novo_tipo,
            "contextos_teste": contextos_teste,
            "empresa": empresa,
            "initial_html_tela": initial_html_tela,
            "initial_css_tela": initial_css_tela,
            "initial_project_tela": initial_project_tela,
            "initial_html_impressao": initial_html_impressao,
            "initial_css_impressao": initial_css_impressao,
            "initial_project_impressao": initial_project_impressao,
        },
    )


def _sanitizador_css_documento():
    return CSSSanitizer(
        allowed_css_properties=[
            "background",
            "background-color",
            "border",
            "border-bottom",
            "border-radius",
            "bottom",
            "break-after",
            "break-inside",
            "box-sizing",
            "color",
            "column-gap",
            "display",
            "flex",
            "flex-direction",
            "flex-wrap",
            "flex-grow",
            "flex-shrink",
            "flex-basis",
            "font-family",
            "font-size",
            "font-style",
            "font-weight",
            "gap",
            "grid-column",
            "grid-column-end",
            "grid-column-start",
            "grid-row",
            "grid-row-end",
            "grid-row-start",
            "grid-template-columns",
            "grid-template-rows",
            "height",
            "left",
            "letter-spacing",
            "line-height",
            "margin",
            "margin-top",
            "margin-right",
            "margin-bottom",
            "margin-left",
            "max-width",
            "max-height",
            "min-width",
            "min-height",
            "object-fit",
            "overflow",
            "overflow-wrap",
            "padding",
            "padding-top",
            "padding-right",
            "padding-bottom",
            "padding-left",
            "position",
            "right",
            "row-gap",
            "text-align",
            "text-decoration",
            "top",
            "width",
            "word-break",
            "align-items",
            "align-self",
            "border-left",
            "border-top",
            "border-collapse",
            "justify-self",
            "white-space",
            "table-layout",
            "vertical-align",
        ]
    )


def _conteudo_documento_seguro(conteudo):
    css = _sanitizador_css_documento()
    return bleach.clean(
        conteudo or "",
        tags={
            "a", "article", "aside", "b", "blockquote", "br", "div", "em", "fieldset",
            "col", "colgroup", "footer", "h1", "h2", "h3", "header", "hr", "i", "img", "input", "label",
            "legend", "li", "main", "ol", "option", "p", "section", "select", "small",
            "span", "strong", "table", "tbody", "td", "textarea", "th", "thead", "tr",
            "u", "ul",
        },
        attributes={
            "*": [
                "class", "style", "data-variable", "data-document-field", "data-option-source",
                "data-source-table", "data-source-query", "data-source-value-field",
                "data-source-display-field", "data-binding", "data-celeris-signature",
                "data-celeris-grid-print", "data-fit-one-page", "data-exclusive-choice",
                "data-exclusive-detail", "data-exclusive-group", "data-exclusive-required",
                "data-exclusive-readonly", "data-boolean-style",
                "role", "colspan", "rowspan",
            ],
            "a": ["href", "target"],
            "img": ["src", "alt", "width", "height"],
            "input": ["type", "name", "value", "placeholder", "required", "checked", "readonly", "disabled", "tabindex", "aria-disabled"],
            "textarea": ["name", "placeholder", "required", "rows", "readonly", "disabled", "tabindex", "aria-disabled"],
            "select": ["name", "required", "disabled", "tabindex", "aria-disabled"],
            "option": ["value", "selected"],
        },
        protocols={"http", "https", "data"},
        css_sanitizer=css,
        strip=True,
    )


def _preencher_opcoes_documento(conteudo, documento):
    def valor_auxiliar(valor, campo):
        aliases = {
            "id": "cd_valor_auxiliar_global",
            "pk": "cd_valor_auxiliar_global",
            "codigo": "cd_valor",
            "descricao": "ds_valor",
            "grupo": "ds_grupo",
        }
        return getattr(valor, aliases.get(campo, campo), "")

    def preencher(match):
        atributos = match.group("attributes")
        origem = re.search(r'data-option-source="([^"]+)"', atributos)
        if not origem:
            return match.group(0)
        opcoes = []
        if origem.group(1) == "auxiliary":
            tabela_match = re.search(r'data-source-table="([^"]*)"', atributos)
            tabela = tabela_match.group(1) if tabela_match else ""
            value_match = re.search(r'data-source-value-field="([^"]*)"', atributos)
            display_match = re.search(r'data-source-display-field="([^"]*)"', atributos)
            campos_permitidos = {"cd_valor_auxiliar_global", "id", "pk", "cd_valor", "ds_valor", "ds_grupo", "codigo", "descricao", "grupo"}
            value_field = value_match.group(1) if value_match and value_match.group(1) in campos_permitidos else "cd_valor"
            display_field = display_match.group(1) if display_match and display_match.group(1) in campos_permitidos else "ds_valor"
            opcoes = [
                (valor_auxiliar(valor, value_field), valor_auxiliar(valor, display_field))
                for valor in ValorAuxiliarGlobal.objects.filter(
                    cd_tabela_auxiliar_global__ds_tabela=tabela,
                    sn_ativo=True,
                ).order_by("ds_valor")
            ]
        elif origem.group(1) == "query":
            query_match = re.search(r'data-source-query="([^"]*)"', atributos)
            consulta = query_match.group(1) if query_match else ""
            if consulta == "convenios":
                opcoes = list(
                    Convenio.objects.filter(cd_empresa=documento.cd_empresa, sn_ativo=True)
                    .order_by("nm_convenio").values_list("pk", "nm_convenio")
                )
            elif consulta == "prestadores":
                opcoes = list(
                    Prestador.objects.filter(cd_empresa=documento.cd_empresa, sn_ativo=True)
                    .order_by("nm_prestador").values_list("pk", "nm_prestador")
                )
            elif consulta == "setores":
                opcoes = list(
                    Setor.objects.filter(cd_empresa=documento.cd_empresa, sn_ativo=True)
                    .order_by("nm_setor").values_list("pk", "nm_setor")
                )
        html_opcoes = '<option value=""></option>' + "".join(
            f'<option value="{conditional_escape(codigo)}">{conditional_escape(descricao)}</option>'
            for codigo, descricao in opcoes
        )
        return f"<select{atributos}>{html_opcoes}</select>"

    return re.sub(
        r"<select(?P<attributes>[^>]*)>.*?</select>",
        preencher,
        conteudo or "",
        flags=re.IGNORECASE | re.DOTALL,
    )


def _css_documento_seguro(conteudo):
    seguro = re.sub(r"@import[^;]*;", "", conteudo or "", flags=re.IGNORECASE)
    seguro = re.sub(r"expression\s*\([^)]*\)", "", seguro, flags=re.IGNORECASE)
    seguro = re.sub(r"url\s*\(\s*['\"]\s*javascript:[^)]*\)", "", seguro, flags=re.IGNORECASE)
    seguro = seguro.replace("</style", "")
    return mark_safe(seguro)


def _avaliar_expressao_variavel(expressao, contexto, strict=False):
    operadores = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Mod: lambda a, b: a % b,
        ast.Eq: lambda a, b: a == b,
        ast.NotEq: lambda a, b: a != b,
        ast.Lt: lambda a, b: a < b,
        ast.LtE: lambda a, b: a <= b,
        ast.Gt: lambda a, b: a > b,
        ast.GtE: lambda a, b: a >= b,
    }
    formatos_data_hora = (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )

    def converter_data_hora(valor):
        if isinstance(valor, datetime):
            return valor
        texto = str(valor or "").strip().replace("T", " ")
        for formato in formatos_data_hora:
            try:
                return datetime.strptime(texto, formato)
            except ValueError:
                continue
        return None

    def calcular_idade(nascimento, referencia=None):
        data_nascimento = converter_data_hora(nascimento)
        if not data_nascimento:
            return ""
        data_referencia = converter_data_hora(referencia) if referencia is not None else None
        data_referencia = data_referencia.date() if data_referencia else timezone.localdate()
        data_nascimento = data_nascimento.date()
        return data_referencia.year - data_nascimento.year - (
            (data_referencia.month, data_referencia.day) < (data_nascimento.month, data_nascimento.day)
        )

    funcoes = {
        "data": lambda valor: converter_data_hora(valor).strftime("%d/%m/%Y") if converter_data_hora(valor) else "",
        "hora": lambda valor: converter_data_hora(valor).strftime("%H:%M:%S") if converter_data_hora(valor) else "",
        "idade": calcular_idade,
        "maiusculo": lambda valor: str(valor or "").upper(),
        "minusculo": lambda valor: str(valor or "").lower(),
        "titulo": lambda valor: str(valor or "").title(),
        "juntar": lambda *valores: "".join(str(valor) for valor in valores),
        "substituir": lambda valor, antigo, novo: str(valor or "").replace(str(antigo), str(novo)),
        "arredondar": lambda valor, casas=0: round(float(valor), int(casas)),
    }

    def avaliar(no):
        if isinstance(no, ast.Expression):
            return avaliar(no.body)
        if isinstance(no, ast.Constant):
            return no.value
        if isinstance(no, ast.Name):
            return contexto.get(no.id, "")
        if isinstance(no, ast.Attribute):
            partes = []
            atual = no
            while isinstance(atual, ast.Attribute):
                partes.insert(0, atual.attr)
                atual = atual.value
            if not isinstance(atual, ast.Name):
                raise ValueError
            partes.insert(0, atual.id)
            return contexto.get(".".join(partes), "")
        if isinstance(no, ast.IfExp):
            return avaliar(no.body) if avaliar(no.test) else avaliar(no.orelse)
        if isinstance(no, ast.BoolOp):
            valores = [avaliar(item) for item in no.values]
            return all(valores) if isinstance(no.op, ast.And) else any(valores)
        if isinstance(no, ast.UnaryOp) and isinstance(no.op, ast.Not):
            return not avaliar(no.operand)
        if isinstance(no, ast.UnaryOp) and isinstance(no.op, (ast.USub, ast.UAdd)):
            valor = avaliar(no.operand)
            return -valor if isinstance(no.op, ast.USub) else +valor
        if isinstance(no, ast.BinOp) and type(no.op) in operadores:
            return operadores[type(no.op)](avaliar(no.left), avaliar(no.right))
        if isinstance(no, ast.Compare):
            esquerda = avaliar(no.left)
            for operador, comparador in zip(no.ops, no.comparators):
                direita = avaliar(comparador)
                if type(operador) not in operadores or not operadores[type(operador)](esquerda, direita):
                    return False
                esquerda = direita
            return True
        if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id in funcoes and not no.keywords:
            return funcoes[no.func.id](*(avaliar(argumento) for argumento in no.args))
        raise ValueError

    try:
        arvore = ast.parse(expressao or '""', mode="eval")
        return avaliar(arvore)
    except SyntaxError as error:
        if strict:
            detalhe = f"linha {error.lineno}, coluna {error.offset}" if error.lineno and error.offset else "sintaxe inválida"
            raise ValueError(f"Erro de sintaxe na expressão ({detalhe}). Verifique parênteses, aspas e operadores.") from error
        return ""
    except ZeroDivisionError as error:
        if strict:
            raise ValueError("Erro na expressão: divisão por zero.") from error
        return ""
    except (TypeError, ValueError, OverflowError) as error:
        if strict:
            raise ValueError("Erro na expressão: variável inexistente, função não permitida ou tipo de dado incompatível.") from error
        return ""


def _adicionar_variaveis_personalizadas(variaveis, empresa):
    modelos = list(ModeloDocumento.objects.filter(
        Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
        tp_elemento="VARIAVEL",
        sn_versao_atual=True,
        sn_ativo=True,
    ))
    for _ in range(max(1, min(5, len(modelos)))):
        for modelo in modelos:
            projeto = modelo.ds_projeto_tela if isinstance(modelo.ds_projeto_tela, dict) else {}
            configuracao = projeto.get("customVariable") or {}
            nome = re.sub(r"[^a-zA-Z0-9_]+", "_", configuracao.get("name") or modelo.nm_modelo).strip("_").lower()
            if nome:
                variaveis[f"variavel.{nome}"] = _avaliar_expressao_variavel(configuracao.get("expression"), variaveis)
    return variaveis


def _variaveis_atendimento_documento(atendimento, empresa):
    paciente = atendimento.cd_paciente
    nascimento = paciente.dt_nascimento.strftime("%d/%m/%Y") if paciente.dt_nascimento else ""
    data_hora = timezone.localtime(atendimento.dh_inicio).strftime("%d/%m/%Y %H:%M") if atendimento.dh_inicio else ""
    especialidade = (
        ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela="especialidade",
            cd_valor=atendimento.ds_especialidade,
            sn_ativo=True,
        )
        .values_list("ds_valor", flat=True)
        .first()
        or {"CLINICA_GERAL": "Clínica Geral"}.get(atendimento.ds_especialidade)
        or atendimento.ds_especialidade.replace("_", " ").title()
    )
    especialidade = especialidade.title()
    prestador = atendimento.cd_prestador
    criador = getattr(atendimento, "cd_usuario_criacao", None)
    variaveis = {
        "paciente.nome": (paciente.nm_social or "").strip() or paciente.nm_paciente,
        "paciente.codigo": paciente.pk,
        "paciente.nascimento": nascimento,
        "paciente.mae": paciente.nm_mae,
        "paciente.pai": paciente.nm_pai,
        "paciente.cpf": paciente.nr_cpf,
        "paciente.rg": paciente.nr_rg,
        "paciente.cns": paciente.nr_cartao_sus,
        "paciente.sexo": paciente.tp_sexo,
        "paciente.genero": paciente.tp_genero,
        "paciente.estado_civil": paciente.tp_estado_civil,
        "paciente.telefone": paciente.nr_telefone,
        "paciente.celular": paciente.nr_celular,
        "paciente.email": paciente.ds_email,
        "paciente.endereco": paciente.ds_endereco,
        "paciente.numero": paciente.nr_endereco,
        "paciente.bairro": paciente.ds_bairro,
        "paciente.cidade": paciente.ds_cidade,
        "paciente.uf": paciente.sg_estado,
        "paciente.cep": paciente.nr_cep,
        "atendimento.codigo": atendimento.pk,
        "atendimento.data_hora": data_hora,
        "atendimento.status": atendimento.get_ds_status_display(),
        "atendimento.especialidade": especialidade,
        "atendimento.tipo": atendimento.ds_tipo_atendimento,
        "atendimento.origem": atendimento.get_ds_origem_display(),
        "atendimento.convenio": getattr(atendimento.cd_convenio, "nm_convenio", "") or "",
        "atendimento.plano": atendimento.ds_plano,
        "atendimento.subplano": atendimento.ds_subplano,
        "atendimento.setor": getattr(atendimento.cd_setor_atual, "nm_setor", "") or "",
        "atendimento.cid": atendimento.ds_cid,
        "atendimento.usuario_criacao": (
            criador.display_name() if criador and hasattr(criador, "display_name") else getattr(criador, "username", "")
        ),
        "prestador.nome": getattr(prestador, "nm_prestador", "") or "",
        "prestador.conselho": getattr(prestador, "ds_conselho", "") or "",
        "prestador.numero_conselho": getattr(prestador, "nr_conselho", "") or "",
        "prestador.uf_conselho": getattr(prestador, "sg_conselho", "") or "",
        "empresa.nome": empresa.nm_empresa,
        "documento.data_hora_atual": timezone.localtime().strftime("%d/%m/%Y %H:%M:%S"),
    }
    return _adicionar_variaveis_personalizadas(variaveis, empresa)


def _variaveis_documento_administrativo(empresa):
    variaveis = {
        "paciente.nome": "",
        "paciente.codigo": "",
        "paciente.nascimento": "",
        "paciente.mae": "",
        "paciente.pai": "",
        "paciente.cpf": "",
        "paciente.rg": "",
        "paciente.cns": "",
        "paciente.sexo": "",
        "paciente.genero": "",
        "paciente.estado_civil": "",
        "paciente.telefone": "",
        "paciente.celular": "",
        "paciente.email": "",
        "paciente.endereco": "",
        "paciente.numero": "",
        "paciente.bairro": "",
        "paciente.cidade": "",
        "paciente.uf": "",
        "paciente.cep": "",
        "atendimento.codigo": "",
        "atendimento.data_hora": "",
        "atendimento.status": "",
        "atendimento.especialidade": "",
        "atendimento.tipo": "",
        "atendimento.origem": "",
        "atendimento.convenio": "",
        "atendimento.plano": "",
        "atendimento.subplano": "",
        "atendimento.setor": "",
        "atendimento.cid": "",
        "atendimento.usuario_criacao": "",
        "prestador.nome": "",
        "prestador.conselho": "",
        "prestador.numero_conselho": "",
        "prestador.uf_conselho": "",
        "empresa.nome": empresa.nm_empresa,
        "documento.data_hora_atual": timezone.localtime().strftime("%d/%m/%Y %H:%M:%S"),
    }
    return _adicionar_variaveis_personalizadas(variaveis, empresa)


def _css_formulario_clinico_tela_editor():
    return (
        ".document-content .generated-clinical-form{display:grid!important;column-gap:18px!important;row-gap:14px!important;color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form label{display:grid!important;align-self:end!important;gap:5px!important;font-weight:700!important;min-width:0!important;color:inherit!important}"
        ".document-content .generated-clinical-form input,.document-content .generated-clinical-form select,.document-content .generated-clinical-form textarea{box-sizing:border-box!important;width:100%!important;padding:8px!important;border:1px solid var(--line,#cbd5e1)!important;border-radius:7px!important;background:var(--field-bg,#fff)!important;color:var(--text,#111)!important;font-size:var(--field-font-size,14px)!important;font-family:inherit!important}"
        ".document-content .generated-clinical-form textarea{width:100%!important;min-width:100%!important;max-width:100%!important;min-height:96px!important;max-height:192px!important;resize:vertical!important}"
        ".document-content .generated-clinical-form input:not([type=checkbox]),.document-content .generated-clinical-form select{height:40px!important;min-height:40px!important}"
        ".document-content .generated-clinical-form select:hover{border-color:var(--primary,#2563eb)!important;background:var(--primary-soft,#eff6ff)!important}"
        ".document-content .generated-clinical-form select:focus{border-color:var(--primary,#2563eb)!important;outline:0!important;box-shadow:0 0 0 3px color-mix(in srgb,var(--primary,#2563eb),transparent 76%)!important}"
        ".document-content .generated-clinical-form select option,.document-content .generated-clinical-form select optgroup{background:var(--field-bg,#fff)!important;color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form select option:checked{background:var(--primary,#2563eb)!important;color:#fff!important}"
        ".dark .document-content .generated-clinical-form select{color-scheme:dark}"
        ".light .document-content .generated-clinical-form select{color-scheme:light}"
        ".document-content .generated-clinical-form :disabled{cursor:not-allowed!important;background:var(--panel-soft,#e9eef5)!important;color:var(--muted,#475569)!important;opacity:1!important}"
        ".document-content .generated-clinical-form .provider-checkbox{display:flex!important;align-self:end!important;align-items:center!important;box-sizing:border-box!important;width:100%!important;height:40px!important;min-height:40px!important;padding:0 8px!important;border:1px solid var(--line,#cbd5e1)!important;background:var(--field-bg,#fff)!important;color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form .provider-checkbox input{appearance:none!important;display:grid!important;place-content:center!important;flex:0 0 32px!important;width:32px!important;height:32px!important;min-height:32px!important;margin:0!important;border:1px solid var(--line,#cbd5e1)!important;border-radius:5px!important;background:var(--field-bg,#fff)!important}"
        ".document-content .generated-clinical-form .provider-checkbox input:checked{border-color:var(--primary,#2563eb)!important;background-color:var(--primary,#2563eb)!important}"
        ".document-content .generated-clinical-form .provider-checkbox>span{font-size:var(--field-font-size,14px)!important}"
        ".document-content .generated-field-affix{display:flex!important;align-items:center!important;gap:6px!important;width:100%!important;min-width:0!important;min-height:40px!important}"
        ".document-content .generated-field-affix>input{flex:1 1 auto!important;width:auto!important;min-width:0!important;max-width:none!important}"
        ".document-content .generated-field-affix>span{flex:0 0 auto!important;white-space:nowrap!important}"
        ".document-content .generated-screen-title{margin:0!important;align-self:center!important;font-size:20px!important;line-height:1.2!important}"
        ".document-content .generated-screen-description,.document-content .generated-screen-text,.document-content .generated-screen-variable{align-self:center!important;color:var(--text,#111)!important}"
        ".document-content .generated-screen-help{align-self:stretch!important;padding:8px 10px!important;border-left:3px solid var(--primary,#2563eb)!important;border-radius:5px!important;background:var(--primary-soft,#eff6ff)!important;color:var(--text,#111)!important}"
        ".document-content .generated-screen-line{align-self:center!important;width:100%!important}"
        ".document-content .generated-clinical-form label,.document-content .generated-exclusive-checkboxes legend,.document-content .generated-multiple-fields legend,.document-content .generated-boolean-field legend{font-size:calc(var(--field-font-size,14px) + 1px)!important;font-weight:700!important}"
        ".document-content .generated-exclusive-checkboxes{display:flex!important;align-items:end!important;align-self:end!important;flex-wrap:wrap!important;gap:7px 9px!important;box-sizing:border-box!important;width:100%!important;max-width:100%!important;min-width:0!important;margin:0 0 4px!important;padding:0!important;border:0!important}"
        ".document-content .generated-exclusive-checkboxes legend{flex:0 0 auto!important;min-height:18px!important;margin:0!important;padding:0!important;font-weight:700!important;color:inherit!important}"
        ".document-content .generated-exclusive-checkboxes>div{display:flex!important;flex-wrap:wrap!important;align-items:stretch!important;flex:1 1 240px!important;gap:7px!important;width:100%!important;min-width:0!important}"
        ".document-content .generated-boolean-field .generated-exclusive-option{flex-basis:96px!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-option{display:flex!important;align-items:center!important;flex:1 1 88px!important;gap:7px!important;box-sizing:border-box!important;width:100%!important;max-width:min(180px,100%)!important;min-height:40px!important;min-width:0!important;overflow:visible!important;padding:3px 7px!important;border:1px solid var(--line,#cbd5e1)!important;border-radius:7px!important;background:var(--field-bg,#fff)!important;font-size:var(--field-font-size,14px)!important;font-weight:600!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-option-with-detail,.document-content .generated-exclusive-checkboxes .generated-exclusive-option:has(.generated-exclusive-detail){grid-column:auto!important;display:grid!important;grid-template-columns:auto minmax(0,max-content) minmax(54px,1fr)!important;align-items:center!important;flex:2 1 260px!important;min-width:min(220px,100%)!important;width:100%!important;max-width:min(520px,100%)!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-option>span{flex:0 1 auto!important;min-width:0!important;max-width:100%!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;overflow-wrap:normal!important;word-break:normal!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-literal{align-self:center!important;flex:0 0 auto!important;margin:0 4px!important;white-space:nowrap!important;font-weight:700!important;color:var(--text,#111)!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-option>input[type=checkbox]{appearance:none!important;flex:0 0 32px!important;width:32px!important;height:32px!important;min-height:32px!important;padding:0!important;border-radius:5px!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-option>input[type=checkbox]:checked{border-color:var(--primary,#2563eb)!important;background-color:var(--primary,#2563eb)!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-detail{display:block!important;justify-self:stretch!important;flex:0 1 auto!important;width:auto!important;min-width:54px!important;max-width:100%!important;height:30px!important;min-height:30px!important;box-sizing:border-box!important;padding:4px 6px!important;border:1px solid var(--line,#cbd5e1)!important;border-radius:6px!important;background:var(--field-bg,#fff)!important;color:var(--text,#111)!important;transition:width .12s ease!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-detail:disabled{border-color:var(--line,#cbd5e1)!important;background:color-mix(in srgb,var(--field-bg,#fff) 78%,var(--panel-soft,#e9eef5) 22%)!important;color:var(--muted,#475569)!important;opacity:1!important}"
        ".document-content .generated-exclusive-checkboxes .generated-exclusive-detail::placeholder{color:var(--muted,#475569)!important;opacity:.9!important}"
        ".document-content .generated-exclusive-checkboxes input[data-exclusive-choice]:checked~.generated-exclusive-detail:not(:disabled){border-color:var(--line,#cbd5e1)!important;background:var(--field-bg,#fff)!important;color:var(--text,#111)!important}"
        ".document-content .generated-multiple-fields,.document-content .generated-boolean-field{box-sizing:border-box!important;min-width:0!important;margin:0!important;padding:0!important;border:0!important}"
        ".document-content .generated-multiple-fields>div{display:flex!important;align-items:end!important;flex-wrap:wrap!important;gap:8px!important;min-width:0!important}"
        ".document-content .generated-multiple-item{flex:0 1 140px!important;min-width:90px!important;max-width:min(220px,100%)!important}"
        ".document-content .generated-multiple-item>span{font-size:calc(var(--field-font-size,14px) + 1px)!important;font-weight:700!important}"
        ".document-content .generated-multiple-literal{align-self:center!important;padding:0 2px!important;font-size:var(--field-font-size,14px)!important}"
        ".document-content .generated-boolean-field .provider-checkbox{margin-top:5px!important}"
    )


def _renderizar_documento(documento, modo_impressao):
    modelo = _versao_atual_modelo_documento(documento.cd_modelo_documento)
    variaveis = (
        _variaveis_atendimento_documento(documento.cd_atendimento, documento.cd_empresa)
        if getattr(documento, "cd_atendimento_id", None)
        else _variaveis_documento_administrativo(documento.cd_empresa)
    )
    variaveis_html = set()
    variaveis["documento.conteudo"] = documento.ds_conteudo
    variaveis["documento.codigo"] = documento.pk
    variaveis["documento.titulo"] = documento.ds_titulo
    variaveis["documento.status"] = documento.get_ds_status_display()
    variaveis["documento.data_hora_criacao"] = timezone.localtime(documento.dh_criacao).strftime("%d/%m/%Y %H:%M")
    variaveis["documento.datahoracriacao"] = variaveis["documento.data_hora_criacao"]
    variaveis["documento.data_hora_atual"] = timezone.localtime().strftime("%d/%m/%Y %H:%M:%S")
    variaveis["documento.datahoraatual"] = variaveis["documento.data_hora_atual"]
    variaveis["documento.usuario_criacao"] = (
        documento.cd_usuario_criacao.get_username()
        if documento.cd_usuario_criacao
        else ""
    )
    variaveis["documento.usuariocriacao"] = variaveis["documento.usuario_criacao"]
    variaveis.update(getattr(documento, "_variaveis_adicionais", {}) or {})
    for chave, valor in list(variaveis.items()):
        chave_sem_separador = re.sub(r"[_\-\s]+", "", str(chave))
        if chave_sem_separador and chave_sem_separador not in variaveis:
            variaveis[chave_sem_separador] = valor
    projeto_tela = modelo.ds_projeto_tela if modelo and isinstance(modelo.ds_projeto_tela, dict) else {}
    campos_por_nome = {
        campo.get("name"): campo
        for campo in (projeto_tela.get("formFields") or [])
        if campo.get("name")
    }

    def opcoes_estruturadas(texto):
        opcoes = []
        atual = []
        dentro_chaves = False
        entre_aspas = None
        for char in str(texto or ""):
            if entre_aspas:
                atual.append(char)
                if char == entre_aspas:
                    entre_aspas = None
                continue
            if char in {'"', "'"}:
                entre_aspas = char
                atual.append(char)
            elif char == "[":
                dentro_chaves = True
                atual.append(char)
            elif char == "]":
                dentro_chaves = False
                atual.append(char)
            elif char == "," and not dentro_chaves:
                valor = "".join(atual).strip()
                if valor:
                    opcoes.append(valor)
                atual = []
            else:
                atual.append(char)
        valor = "".join(atual).strip()
        if valor:
            opcoes.append(valor)
        return opcoes

    def rotulo_opcao(texto):
        return re.sub(r"\[.*$", "", str(texto or "")).strip()

    def opcao_literal(texto):
        valor = str(texto or "").strip()
        return len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in {"'", '"'}

    def texto_literal(texto):
        valor = str(texto or "").strip()
        return valor[1:-1] if opcao_literal(valor) else valor

    def checkbox_impresso(marcado):
        classe = "print-check-box checked" if marcado else "print-check-box"
        return f'<span class="{classe}"></span>'

    def texto_multilinha_impresso(valor):
        texto = str(conditional_escape(valor or "")).replace("\r\n", "\n").replace("\r", "\n")
        return mark_safe(
            '<span class="document-preserve-text" '
            'style="white-space:pre-wrap;tab-size:4;overflow-wrap:anywhere;word-break:break-word">'
            f"{texto}</span>"
        )

    def formatar_valor_campo(nome, valor):
        campo = campos_por_nome.get(nome) or {}
        tipo = campo.get("type")
        if modo_impressao and tipo == "textarea":
            variaveis_html.add(f"campo.{nome}")
            variaveis_html.add(nome)
            return texto_multilinha_impresso(valor)
        if modo_impressao and tipo == "exclusive-checkboxes":
            selecionado = str(valor or "")
            variaveis_html.add(f"campo.{nome}")
            variaveis_html.add(nome)
            return mark_safe(" ".join(
                str(conditional_escape(texto_literal(opcao))) if opcao_literal(opcao)
                else f"{checkbox_impresso(rotulo_opcao(opcao) == selecionado)}{conditional_escape(rotulo_opcao(opcao))}"
                for opcao in opcoes_estruturadas(campo.get("options"))
            ))
        if modo_impressao and tipo == "checkbox":
            variaveis_html.add(f"campo.{nome}")
            variaveis_html.add(nome)
            if campo.get("booleanStyle") == "single":
                return mark_safe(f"{checkbox_impresso(bool(valor))}Sim")
            selecionado = str(valor or "")
            return mark_safe(
                f"{checkbox_impresso(selecionado == 'Sim')}Sim "
                f"{checkbox_impresso(selecionado == 'Não')}Não"
            )
        return valor

    for nome, valor in (documento.ds_dados_formulario or {}).items():
        valor = formatar_valor_campo(nome, valor)
        variaveis[f"campo.{nome}"] = valor
        variaveis[nome] = valor
    if modo_impressao:
        for nome, campo in campos_por_nome.items():
            if f"campo.{nome}" not in variaveis and campo.get("type") in {"exclusive-checkboxes", "checkbox"}:
                valor = formatar_valor_campo(nome, "")
                variaveis[f"campo.{nome}"] = valor
                variaveis[nome] = valor
    for nome in campos_por_nome:
        variaveis.setdefault(f"campo.{nome}", "")
        variaveis.setdefault(nome, "")

    def renderizar(html):
        resultado = _preencher_opcoes_documento(html or "", documento)
        resultado = re.sub(
            r"{{\s*([^{}]+?)\s*}}",
            lambda match: "{{ "
            + re.sub(r"\s+", "", html_unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip())
            + " }}",
            resultado,
        )
        resultado = re.sub(
            r"{{\s*documento\.pagina\s*}}",
            '<span class="document-page-variable"></span>',
            resultado,
        )
        for chave, valor in variaveis.items():
            substituicao = str(valor) if chave == "documento.conteudo" or chave in variaveis_html else str(conditional_escape(valor))
            resultado = resultado.replace(f"{{{{ {chave} }}}}", substituicao)
            resultado = resultado.replace(f"{{{{{chave}}}}}", substituicao)
        resultado = re.sub(r"{{\s*campo(?:\.[a-zA-Z0-9_]*)?\s*}}", "", resultado)
        if not modo_impressao:
            resultado = re.sub(
                r"\sreadonly(=[\s>])",
                ' disabled tabindex="-1" aria-disabled="true"',
                resultado,
                flags=re.IGNORECASE,
            )
        return mark_safe(_conteudo_documento_seguro(resultado))

    if not modelo:
        conteudo = str(conditional_escape(documento.ds_conteudo)).replace("\n", "<br>")
        return {"cabecalho": "", "conteudo": mark_safe(conteudo), "rodape": "", "css": ""}
    campo_html = "ds_html_impressao" if modo_impressao else "ds_html_tela"
    campo_css = "ds_css_impressao" if modo_impressao else "ds_css_tela"
    cabecalho = _versao_atual_modelo_documento(modelo.cd_cabecalho)
    rodape = _versao_atual_modelo_documento(modelo.cd_rodape)
    css_base = getattr(modelo, campo_css, "")
    css_layout = (
        ".document-content .generated-clinical-form{column-gap:18px!important;row-gap:14px!important;"
        "color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form label,"
        ".document-content .generated-clinical-form fieldset{font-family:inherit!important;"
        "color:inherit!important}"
        ".document-content .generated-clinical-form label,"
        ".document-content .generated-clinical-form .generated-exclusive-checkboxes legend,"
        ".document-content .generated-clinical-form .generated-multiple-fields legend,"
        ".document-content .generated-clinical-form .generated-boolean-field legend{"
        "font-size:calc(var(--field-font-size,14px) + 1px)!important;font-weight:700!important}"
        ".document-content .generated-clinical-form input,.document-content .generated-clinical-form select,"
        ".document-content .generated-clinical-form textarea{border-color:var(--line,#cbd5e1)!important;"
        "background:var(--field-bg,#fff)!important;color:var(--text,#111)!important;"
        "font-size:var(--field-font-size,14px)!important;font-family:inherit!important}"
        ".document-content .generated-clinical-form :disabled{cursor:not-allowed;"
        "background:var(--panel-soft,#e9eef5)!important;color:var(--muted,#475569)!important;opacity:1}"
        ".document-content .generated-clinical-form input:not([type=checkbox]),"
        ".document-content .generated-clinical-form select{height:38px!important;min-height:38px!important}"
        ".document-content .generated-clinical-form textarea{width:100%!important;min-width:100%!important;max-width:100%!important;"
        "min-height:96px!important;max-height:192px!important;resize:vertical!important}"
        ".document-content .generated-clinical-form select{border-radius:6px!important}"
        ".document-content .generated-clinical-form select:hover{border-color:var(--primary,#2563eb)!important;"
        "background:var(--primary-soft,#eff6ff)!important}"
        ".document-content .generated-clinical-form select option,"
        ".document-content .generated-clinical-form select optgroup{background:var(--field-bg,#fff)!important;"
        "color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form select option:checked{"
        "background:var(--primary,#2563eb)!important;color:#fff!important}"
        ".dark .document-content .generated-clinical-form select{color-scheme:dark}"
        ".light .document-content .generated-clinical-form select{color-scheme:light}"
        ".document-content .generated-clinical-form .provider-checkbox{display:flex!important;align-self:end!important;"
        "box-sizing:border-box!important;width:100%!important;height:38px!important;min-height:38px!important;"
        "border-color:var(--line,#cbd5e1)!important;background:var(--field-bg,#fff)!important;"
        "color:var(--text,#111)!important}"
        ".document-content .generated-clinical-form .provider-checkbox input{width:32px!important;height:32px!important;"
        "min-height:32px!important;flex:0 0 32px!important;margin:0!important;"
        "border-color:var(--line,#cbd5e1)!important;background-color:var(--field-bg,#fff)!important}"
        ".document-content .generated-clinical-form .provider-checkbox input:checked{"
        "border-color:var(--primary,#2563eb)!important;background-color:var(--primary,#2563eb)!important}"
        ".document-content .generated-clinical-form .provider-checkbox>span{"
        "font-size:var(--field-font-size,14px)!important}"
        ".document-content .generated-clinical-form .generated-exclusive-checkboxes{"
        "display:flex!important;align-items:end!important;align-self:end!important;flex-wrap:wrap!important;"
        "gap:7px 9px!important;box-sizing:border-box!important;width:100%!important;max-width:100%!important;"
        "min-width:0!important;margin:0 0 4px!important;padding:0!important;border:0!important}"
        ".document-content .generated-clinical-form .generated-exclusive-checkboxes>div{"
        "display:grid!important;grid-template-columns:repeat(auto-fill,minmax(min(135px,100%),1fr))!important;"
        "align-items:stretch!important;flex:1 1 240px!important;gap:7px!important;width:100%!important;min-width:0!important}"
        ".document-content .generated-clinical-form .generated-boolean-field>div{"
        "grid-template-columns:repeat(auto-fill,minmax(min(112px,100%),1fr))!important}"
        ".document-content .generated-clinical-form .generated-exclusive-option{"
        "display:flex!important;align-items:center!important;flex:1 1 auto!important;gap:7px!important;"
        "box-sizing:border-box!important;width:100%!important;max-width:100%!important;min-height:38px!important;min-width:0!important;"
        "padding:3px 7px!important;border:1px solid var(--line,#cbd5e1)!important;border-radius:7px!important;"
        "background:var(--field-bg,#fff)!important;font-size:var(--field-font-size,14px)!important;font-weight:600!important}"
        ".document-content .generated-clinical-form .generated-exclusive-option-with-detail,"
        ".document-content .generated-clinical-form .generated-exclusive-option:has(.generated-exclusive-detail){"
        "display:grid!important;grid-template-columns:auto minmax(0,max-content) minmax(54px,auto)!important;"
        "flex:1 1 auto!important;min-width:0!important;width:100%!important}"
        ".document-content .generated-clinical-form .generated-exclusive-option>span{"
        "flex:0 1 auto!important;min-width:0!important;max-width:100%!important;white-space:nowrap!important;overflow-wrap:normal!important;word-break:normal!important}"
        ".document-content .generated-clinical-form .generated-exclusive-option>input[type=checkbox]{"
        "appearance:none!important;flex:0 0 32px!important;width:32px!important;height:32px!important;"
        "min-height:32px!important;padding:0!important;border-radius:5px!important}"
        ".document-content .generated-clinical-form .generated-exclusive-detail{"
        "flex:0 1 auto!important;width:54px!important;min-width:54px!important;max-width:100%!important;"
        "height:30px!important;min-height:30px!important;box-sizing:border-box!important;transition:width .12s ease!important}"
        ".document-content .generated-clinical-form .generated-multiple-item{"
        "flex:0 1 140px!important;min-width:90px!important;max-width:min(220px,100%)!important}"
        ".document-content .generated-field-affix{display:flex!important;align-items:center;gap:6px;"
        "width:100%;min-width:0;min-height:38px}"
        ".document-content .generated-field-affix>input{flex:1 1 auto;width:auto!important;min-width:0;max-width:none}"
        ".document-content .generated-field-affix>span{flex:0 0 auto;white-space:nowrap}"
        if not modo_impressao
        else ".document-content main>section{column-gap:0!important;row-gap:0!important}"
    )
    if not modo_impressao:
        css_layout = f"{css_layout}{_css_formulario_clinico_tela_editor()}"
    projeto_impressao = modelo.ds_projeto_impressao if isinstance(modelo.ds_projeto_impressao, dict) else {}
    limitar_uma_pagina = bool((projeto_impressao.get("printLayout") or {}).get("grid", {}).get("fitOnePage"))
    conteudo_modelo = getattr(modelo, campo_html, "") or documento.ds_conteudo
    if not modo_impressao and projeto_tela.get("formFields"):
        conteudo_modelo = _gerar_tela_pela_grade(modelo)
    if modo_impressao and _modelo_possui_layout_impressao(modelo):
        conteudo_modelo = _gerar_impressao_pela_grade(modelo)
    elif modo_impressao and not getattr(modelo, campo_html, "") and not _impressao_possui_grade(modelo):
        conteudo_modelo = _gerar_impressao_pela_grade(modelo)
    if modo_impressao and modelo.tp_elemento == "DOCUMENTO":
        conteudo_modelo = _configurar_assinatura_prestador(conteudo_modelo, modelo)
    cabecalho_html = getattr(cabecalho, campo_html, "") if modo_impressao and cabecalho else ""
    rodape_html = getattr(rodape, campo_html, "") if modo_impressao and rodape else ""
    if modo_impressao and cabecalho and _modelo_possui_layout_impressao(cabecalho):
        cabecalho_html = _gerar_impressao_pela_grade(cabecalho)
    if modo_impressao and rodape and _modelo_possui_layout_impressao(rodape):
        rodape_html = _gerar_impressao_pela_grade(rodape)
    return {
        "cabecalho": renderizar(cabecalho_html),
        "conteudo": renderizar(conteudo_modelo),
        "rodape": renderizar(rodape_html),
        "css": _css_documento_seguro(f"{css_base}\n{css_layout}"),
        "limitar_uma_pagina": limitar_uma_pagina,
    }


def _nome_arquivo_pdf_documento(documento):
    titulo = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(documento.ds_titulo or "documento")).strip("_").lower()
    return f"{titulo or 'documento'}_{documento.pk or 'preview'}.pdf"


def _marca_dagua_rascunho_png_data_uri():
    try:
        from PIL import Image, ImageDraw, ImageFont
        largura, altura = 1400, 2000
        imagem = Image.new("RGBA", (largura, altura), (255, 255, 255, 0))
        try:
            fonte = ImageFont.truetype("arialbd.ttf", 260)
        except Exception:
            try:
                fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", 260)
            except Exception:
                fonte = ImageFont.load_default()

        texto = "RASCUNHO"
        medidor = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 0)))
        bbox = medidor.textbbox((0, 0), texto, font=fonte, stroke_width=2)
        texto_largura = bbox[2] - bbox[0]
        texto_altura = bbox[3] - bbox[1]
        margem = 160
        texto_base = Image.new("RGBA", (texto_largura + margem * 2, texto_altura + margem * 2), (255, 255, 255, 0))
        desenho_texto = ImageDraw.Draw(texto_base)
        desenho_texto.text(
            (margem - bbox[0], margem - bbox[1]),
            texto,
            font=fonte,
            fill=(148, 163, 184, 64),
            stroke_width=2,
            stroke_fill=(148, 163, 184, 64),
        )
        texto_rotacionado = texto_base.rotate(-28, resample=Image.Resampling.BICUBIC, expand=True)

        for centro_y in (170, altura // 2, altura - 170):
            posicao = ((largura - texto_rotacionado.width) // 2, int(centro_y - texto_rotacionado.height / 2))
            imagem.alpha_composite(texto_rotacionado, posicao)

        buffer = BytesIO()
        imagem.save(buffer, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception:
        return (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1400 2000'%3E"
            "%3Cg font-family='Arial,sans-serif' font-size='260' font-weight='900' fill='%2394a3b8' "
            "fill-opacity='.25' text-anchor='middle'%3E%3Ctext x='700' y='170' transform='rotate(-28 700 170)'%3E"
            "RASCUNHO%3C/text%3E%3Ctext x='700' y='1000' transform='rotate(-28 700 1000)'%3ERASCUNHO%3C/text%3E"
            "%3Ctext x='700' y='1830' transform='rotate(-28 700 1830)'%3ERASCUNHO%3C/text%3E%3C/g%3E%3C/svg%3E"
        )


def _resposta_pdf_documento(request, documento, empresa, apresentacao=None, apenas_layout=False, tipo_layout="DOCUMENTO"):
    tipo_layout = str(tipo_layout or "DOCUMENTO").upper()
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - depende de biblioteca externa/ambiente nativo
        logger.exception("WeasyPrint indisponível para renderizar PDF: %s", exc)
        detalhe = str(exc)
        return HttpResponse(
            (
                "Renderização PDF indisponível.\n\n"
                "O pacote Python do WeasyPrint pode estar instalado, mas no Windows ele também precisa "
                "das bibliotecas nativas GTK/Pango disponíveis no PATH do processo do Django.\n\n"
                "1. Instale/garanta o GTK runtime para Windows.\n"
                "2. Reinicie o terminal/servidor Django após ajustar o PATH.\n"
                "3. Use o Python do venv para dependências Python: "
                r".\.venv\Scripts\python.exe -m pip install -r requirements.txt"
                "\n4. Para runtime embutido, copie as DLLs para runtime\\weasyprint\\bin\\."
                "\n\n"
                f"Detalhe técnico: {detalhe}"
            ),
            status=501,
            content_type="text/plain; charset=utf-8",
        )

    def remover_marcador_pagina_fragmento(html):
        resultado = str(html or "")
        resultado = re.sub(
            r"(?is)<div\b([^>]*)>\s*(?:(?!</div>).)*document-page-variable(?:(?!</div>).)*</div>",
            r"<div\1>&nbsp;</div>",
            resultado,
        )
        resultado = re.sub(
            r"(?is)(?:<strong[^>]*>\s*)?p[áa]gina\s*:?\s*(?:</strong>)?\s*"
            r"<span[^>]*class=[\"'][^\"']*document-page-variable[^\"']*[\"'][^>]*>\s*</span>",
            "",
            resultado,
        )
        resultado = re.sub(
            r"(?is)<strong\b[^>]*>\s*p(?:[áa]|á)gina\s*:?\s*</strong>\s*"
            r"(?:<span\b(?![^>]*document-page-variable)[^>]*>\s*)*"
            r"<span\b[^>]*class=[\"'][^\"']*document-page-variable[^\"']*[\"'][^>]*>.*?</span>"
            r"(?:\s*</span>)*",
            "",
            resultado,
        )
        resultado = re.sub(
            r"(?is)<span\b[^>]*class=[\"'][^\"']*document-page-variable[^\"']*[\"'][^>]*>.*?</span>",
            "",
            resultado,
        )
        return re.sub(
            r"(?is)<span[^>]*class=[\"'][^\"']*document-page-variable[^\"']*[\"'][^>]*>\s*</span>",
            "",
            resultado,
        )

    apresentacao = dict(apresentacao or _renderizar_documento(documento, True))
    for chave_html in ("cabecalho", "conteudo", "rodape"):
        altura_linha = 0
        html_normalizado = _normalizar_grade_html_para_pdf(str(apresentacao.get(chave_html) or ""), row_height=altura_linha)
        apresentacao[chave_html] = mark_safe(_conteudo_documento_seguro(html_normalizado))
    cabecalho_html = str(apresentacao.get("cabecalho") or "")
    rodape_html = str(apresentacao.get("rodape") or "")
    linhas_cabecalho = max(1, cabecalho_html.count("<tr"))
    cabecalho_padding_superior_mm = 0
    margem_superior_pdf_mm = max(
        34,
        min(52, int(linhas_cabecalho * 2.4 + cabecalho_padding_superior_mm + 12)),
    )
    pagina_no_cabecalho = False
    pagina_no_rodape = False
    if pagina_no_cabecalho or pagina_no_rodape:
        apresentacao = dict(apresentacao)
        if pagina_no_cabecalho:
            apresentacao["cabecalho"] = mark_safe(remover_marcador_pagina_fragmento(cabecalho_html))
        if pagina_no_rodape:
            apresentacao["rodape"] = mark_safe(remover_marcador_pagina_fragmento(rodape_html))
    possui_assinatura = "data-celeris-signature" in str(apresentacao.get("conteudo") or "")

    def montar_html(assinatura_compacta=False):
        atendimento_documento = documento.cd_atendimento if getattr(documento, "cd_atendimento_id", None) else None
        return render_to_string(
            "atendimento/documento_clinico_pdf.html",
            {
                "documento": documento,
                "atendimento": atendimento_documento,
                "empresa": empresa,
                "apresentacao": apresentacao,
                "pagina_no_cabecalho": pagina_no_cabecalho,
                "pagina_no_rodape": pagina_no_rodape,
                "apenas_layout": apenas_layout,
                "tipo_layout": tipo_layout,
                "rascunho": documento.ds_status not in {"FECHADO", "FINALIZADO", "CANCELADO", "ABANDONADO"},
                "cancelado": documento.ds_status == "CANCELADO",
                "marca_dagua_rascunho": _marca_dagua_rascunho_png_data_uri(),
                "margem_superior_pdf_mm": margem_superior_pdf_mm,
                "cabecalho_padding_superior_mm": cabecalho_padding_superior_mm,
                "assinatura_compacta": assinatura_compacta,
            },
            request=request,
        )

    base_url = request.build_absolute_uri("/")
    documento_pdf = HTML(string=montar_html(False), base_url=base_url).render()
    if possui_assinatura and len(documento_pdf.pages) > 1:
        documento_pdf_compacto = HTML(string=montar_html(True), base_url=base_url).render()
        if len(documento_pdf_compacto.pages) < len(documento_pdf.pages):
            documento_pdf = documento_pdf_compacto
    pdf = documento_pdf.write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{_nome_arquivo_pdf_documento(documento)}"'
    response["X-Frame-Options"] = "SAMEORIGIN"
    response["X-Celeris-Pdf-Pages"] = str(len(documento_pdf.pages))
    return response


@login_required
@xframe_options_sameorigin
def preview_pdf_modelo_documento(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"erro": "Payload inválido."}, status=400)

    empresa = _empresa_logada(request)
    tipo_layout = str(payload.get("elemento") or "DOCUMENTO").upper()
    apresentacao = {
        "cabecalho": payload.get("cabecalho") or "",
        "conteudo": payload.get("conteudo") or "",
        "rodape": payload.get("rodape") or "",
        "css": payload.get("css") or "",
        "modo_impressao": True,
        "limitar_uma_pagina": bool(payload.get("limitar_uma_pagina")),
    }
    projeto_impressao = payload.get("projeto_impressao") if isinstance(payload.get("projeto_impressao"), dict) else {}
    projeto_cabecalho = payload.get("cabecalho_projeto") if isinstance(payload.get("cabecalho_projeto"), dict) else {}
    projeto_rodape = payload.get("rodape_projeto") if isinstance(payload.get("rodape_projeto"), dict) else {}

    def substituir_variaveis_preview(conteudo):
        variaveis_preview = {}
        variaveis_preview.update(payload.get("variaveis_teste") if isinstance(payload.get("variaveis_teste"), dict) else {})
        for nome, valor in (payload.get("valores_campos") if isinstance(payload.get("valores_campos"), dict) else {}).items():
            if isinstance(valor, str) and ("\n" in valor or "\r" in valor or "\t" in valor):
                valor = (
                    '<span class="document-preserve-text" '
                    'style="white-space:pre-wrap;tab-size:4;overflow-wrap:anywhere;word-break:break-word">'
                    f'{conditional_escape(valor).replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))}'
                    '</span>'
                )
            variaveis_preview[f"campo.{nome}"] = valor
            variaveis_preview[nome] = valor
        for chave, valor in list(variaveis_preview.items()):
            chave_sem_separador = re.sub(r"[_\-\s]+", "", str(chave))
            if chave_sem_separador and chave_sem_separador not in variaveis_preview:
                variaveis_preview[chave_sem_separador] = valor
        resultado = re.sub(
            r"{{\s*([^{}]+?)\s*}}",
            lambda match: "{{ "
            + re.sub(r"\s+", "", html_unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip())
            + " }}",
            str(conteudo or ""),
        )
        for chave, valor in variaveis_preview.items():
            resultado = re.sub(
                rf"{{{{\s*{re.escape(str(chave))}\s*}}}}",
                str(valor or ""),
                resultado,
            )
        return re.sub(r"{{\s*campo(?:\.[a-zA-Z0-9_]*)?\s*}}", "", resultado)

    if tipo_layout == "DOCUMENTO" and isinstance(projeto_impressao.get("printLayout"), dict):
        assinatura = payload.get("assinatura") if isinstance(payload.get("assinatura"), dict) else {}
        modelo_temporario = SimpleNamespace(
            ds_projeto_impressao=projeto_impressao,
            tp_elemento="DOCUMENTO",
            sn_exibe_assinatura=assinatura.get("exibe", True),
            tp_alinhamento_assinatura=assinatura.get("alinhamento") or "CENTRO",
            sn_exibe_conselho_assinatura=bool(assinatura.get("conselho")),
        )
        conteudo_gerado = _gerar_impressao_pela_grade(modelo_temporario)
        if modelo_temporario.sn_exibe_assinatura:
            conteudo_gerado = _configurar_assinatura_prestador(conteudo_gerado, modelo_temporario)
        apresentacao["conteudo"] = substituir_variaveis_preview(conteudo_gerado)
        if isinstance(projeto_cabecalho.get("printLayout"), dict):
            apresentacao["cabecalho"] = substituir_variaveis_preview(
                _gerar_impressao_pela_grade(SimpleNamespace(
                    ds_projeto_impressao=projeto_cabecalho,
                    tp_elemento="CABECALHO",
                ))
            )
        if isinstance(projeto_rodape.get("printLayout"), dict):
            apresentacao["rodape"] = substituir_variaveis_preview(
                _gerar_impressao_pela_grade(SimpleNamespace(
                    ds_projeto_impressao=projeto_rodape,
                    tp_elemento="RODAPE",
                ))
            )
    if tipo_layout == "CABECALHO":
        conteudo_cabecalho = payload.get("conteudo") or ""
        if isinstance(projeto_impressao.get("printLayout"), dict):
            modelo_temporario = SimpleNamespace(
                ds_projeto_impressao=projeto_impressao,
                tp_elemento="CABECALHO",
            )
            conteudo_cabecalho = _gerar_impressao_pela_grade(modelo_temporario)
        apresentacao["cabecalho"] = substituir_variaveis_preview(conteudo_cabecalho)
        apresentacao["conteudo"] = ""
        apresentacao["rodape"] = ""
    elif tipo_layout == "RODAPE":
        conteudo_rodape = payload.get("conteudo") or ""
        if isinstance(projeto_impressao.get("printLayout"), dict):
            modelo_temporario = SimpleNamespace(
                ds_projeto_impressao=projeto_impressao,
                tp_elemento="RODAPE",
            )
            conteudo_rodape = _gerar_impressao_pela_grade(modelo_temporario)
        apresentacao["cabecalho"] = ""
        apresentacao["conteudo"] = ""
        apresentacao["rodape"] = substituir_variaveis_preview(conteudo_rodape)
    documento = SimpleNamespace(
        pk=payload.get("codigo") or "preview",
        ds_titulo=payload.get("titulo") or "Pré-visualização",
        ds_status=payload.get("status") or "RASCUNHO",
        cd_atendimento=None,
    )
    return _resposta_pdf_documento(
        request,
        documento,
        empresa,
        apresentacao,
        apenas_layout=tipo_layout in {"CABECALHO", "RODAPE"},
        tipo_layout=tipo_layout,
    )


@login_required
@xframe_options_sameorigin
def imprimir_documento_clinico(request, cd_documento):
    empresa = _empresa_logada(request)
    documento = get_object_or_404(
        DocumentoClinico.objects.select_related(
            "cd_atendimento__cd_paciente",
            "cd_atendimento__cd_prestador",
            "cd_usuario_emissor",
            "cd_modelo_documento__cd_cabecalho",
            "cd_modelo_documento__cd_rodape",
            "cd_item_menu_assistencial__cd_perfil_assistencial",
        ),
        cd_empresa=empresa,
        cd_documento_clinico=cd_documento,
    )
    somente_consulta = request.GET.get("somente_consulta") == "1"
    chave_excepcional = f"acesso_documento_excepcional_{documento.pk}"
    if not _usuario_pode_visualizar_documento(request.user, documento) and not request.session.get(chave_excepcional):
        raise PermissionDenied("Usuário sem perfil assistencial para este documento.")
    perfil_documento = getattr(getattr(documento, "cd_item_menu_assistencial", None), "cd_perfil_assistencial", None)
    perfis_usuario = _perfis_assistenciais_usuario(request.user, empresa)
    acesso_regular = (
        request.user.is_superuser
        or not perfil_documento
        or not perfil_documento.sn_sigiloso
        or perfis_usuario.filter(pk=perfil_documento.pk).exists()
    )
    if not acesso_regular and not request.session.get(chave_excepcional):
        raise PermissionDenied("Documento sigiloso para outro perfil assistencial.")
    if request.method == "POST" and somente_consulta:
        raise PermissionDenied("O prontuário foi aberto em modo de consulta.")
    if request.method == "POST" and documento.ds_status in {"ABERTO", "RASCUNHO"}:
        if documento.cd_usuario_responsavel_id and documento.cd_usuario_responsavel_id != request.user.pk:
            raise PermissionDenied("Assuma o documento antes de alterá-lo.")
        mensagem_trava = _bloqueio_trava_documento(request, documento)
        if mensagem_trava:
            messages.warning(request, mensagem_trava)
            return _redirect_documento_clinico(request, documento)
        documento.ds_conteudo = _conteudo_documento_seguro(request.POST.get("ds_conteudo", ""))
        try:
            documento.ds_dados_formulario = json.loads(request.POST.get("ds_dados_formulario") or "{}")
        except json.JSONDecodeError:
            messages.error(request, "Não foi possível interpretar os campos preenchidos.")
            return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)
        _apply_audit(documento, request.user)
        documento.save(update_fields=["ds_conteudo", "ds_dados_formulario", "dh_atualizacao", "cd_usuario_atualizacao"])
        EventoDocumentoClinico.objects.create(
            cd_empresa=empresa,
            cd_documento_clinico=documento,
            cd_usuario=request.user,
            tp_evento="ATUALIZADO",
        )
        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)
    AcessoClinicoAuditado.objects.create(
        cd_empresa=empresa,
        cd_usuario=request.user,
        cd_documento_clinico=documento,
        tp_acesso="VISUALIZACAO",
        ds_ip=request.META.get("REMOTE_ADDR") or None,
    )
    modo_impressao = request.GET.get("modo") == "impressao"
    embed = request.GET.get("embed") == "1"
    if modo_impressao and documento.cd_item_menu_assistencial and not documento.cd_item_menu_assistencial.sn_imprimivel:
        raise PermissionDenied("A impressão foi desativada na configuração desta tela.")
    apresentacao = _renderizar_documento(documento, modo_impressao)
    if modo_impressao and request.GET.get("pdf") == "1":
        return _resposta_pdf_documento(request, documento, empresa, apresentacao)
    return render(
        request,
        "atendimento/documento_clinico.html",
        {
            "documento": documento,
            "atendimento": documento.cd_atendimento,
            "empresa": empresa,
            "modo_impressao": modo_impressao,
            "embed": embed,
            "documento_base_template": "base/document_embed.html" if embed else "base/layout.html",
            "somente_consulta": somente_consulta,
            "pode_imprimir": not documento.cd_item_menu_assistencial or documento.cd_item_menu_assistencial.sn_imprimivel,
            "apresentacao": apresentacao,
            "historico_mesmo_tipo": DocumentoClinico.objects.filter(
                cd_empresa=empresa,
                cd_atendimento__cd_paciente=documento.cd_atendimento.cd_paciente,
                cd_modelo_documento=documento.cd_modelo_documento,
            ).exclude(pk=documento.pk).exclude(ds_status="ABANDONADO").select_related("cd_atendimento", "cd_usuario_responsavel")[:30],
            "pode_assumir": not somente_consulta and documento.ds_status in {"ABERTO", "RASCUNHO"} and documento.cd_usuario_responsavel_id != request.user.pk,
            "pode_fechar": not somente_consulta and documento.ds_status in {"ABERTO", "RASCUNHO"} and documento.cd_usuario_responsavel_id in {None, request.user.pk},
            "pode_abandonar": not somente_consulta and documento.ds_status in {"ABERTO", "RASCUNHO"} and (
                not documento.cd_item_menu_assistencial
                or documento.cd_item_menu_assistencial.sn_permite_abandonar
            ),
            "pode_cancelar": not somente_consulta and documento.ds_status == "FECHADO" and bool(
                documento.cd_item_menu_assistencial
                and documento.cd_item_menu_assistencial.sn_permite_cancelar
            ),
        },
    )


def _redirect_documento_clinico(request, documento):
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)


def _titulo_trava_documento(documento):
    return f"Documento {documento.pk} - {documento.ds_titulo or documento.tp_documento}"


def _mensagem_documento_nao_editavel(documento):
    usuario = documento.cd_usuario_responsavel
    usuario_texto = f" por {nome_usuario_trava(usuario)}" if usuario else ""
    if documento.ds_status in {"FECHADO", "FINALIZADO", "ASSINADO"}:
        return f"Este documento já foi finalizado{usuario_texto}."
    if documento.ds_status == "CANCELADO":
        return f"Este documento já foi cancelado{usuario_texto}."
    if documento.ds_status == "ABANDONADO":
        return f"Este documento já foi excluído{usuario_texto}."
    return "Este documento não está mais disponível para edição."


def _bloqueio_trava_documento(request, documento):
    resultado = usuario_tem_trava_ou_livre(documento.cd_empresa, request.user, "documento_clinico", documento.pk)
    if resultado.permitido:
        return ""
    return f"{resultado.mensagem} Aguarde a liberação ou solicite ao TI em Sessões e travas."


def _liberar_trava_documento(documento, usuario, motivo):
    liberar_trava_edicao(documento.cd_empresa, usuario, "documento_clinico", documento.pk, motivo=motivo)


def _registrar_evento_documento(documento, usuario, tipo, motivo="", dados=None):
    return EventoDocumentoClinico.objects.create(
        cd_empresa=documento.cd_empresa,
        cd_documento_clinico=documento,
        cd_usuario=usuario,
        tp_evento=tipo,
        ds_motivo=motivo,
        ds_dados=dados or {},
    )


def _campos_obrigatorios_documento_preenchidos(documento):
    projeto = documento.cd_modelo_documento.ds_projeto_tela if documento.cd_modelo_documento else {}
    campos = projeto.get("formFields", []) if isinstance(projeto, dict) else []
    ausentes = []
    for campo in campos:
        if not campo.get("required"):
            continue
        nome = campo.get("name", "")
        valor = documento.ds_dados_formulario.get(nome)
        if valor in (None, "", False, []):
            ausentes.append(campo.get("label") or nome)
    return ausentes


@login_required
def assumir_documento_clinico(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    motivo = request.POST.get("motivo", "").strip()
    if not motivo:
        return JsonResponse({"ok": False, "error": "Informe o motivo da assunção."}, status=400)
    with transaction.atomic():
        documento = DocumentoClinico.objects.select_for_update().filter(cd_empresa=empresa, pk=cd_documento).first()
        if not documento:
            messages.error(request, "Documento não encontrado ou não pertence à empresa atual.")
            return redirect(_safe_return_url(request) or "atendimento:pep")
        if documento.ds_status not in {"ABERTO", "RASCUNHO"}:
            messages.warning(request, _mensagem_documento_nao_editavel(documento))
            return _redirect_documento_clinico(request, documento)
        mensagem_trava = _bloqueio_trava_documento(request, documento)
        if mensagem_trava:
            messages.warning(request, mensagem_trava)
            return _redirect_documento_clinico(request, documento)
        if not _usuario_pode_operar_documento(request.user, documento):
            raise PermissionDenied
        anterior = documento.cd_usuario_responsavel_id
        documento.cd_usuario_responsavel = request.user
        documento.ds_status = "ABERTO"
        _apply_audit(documento, request.user)
        documento.save(update_fields=[
            "cd_usuario_responsavel",
            "ds_status",
            "dh_atualizacao",
            "cd_usuario_atualizacao",
        ])
        _registrar_evento_documento(
            documento,
            request.user,
            "ASSUMIDO",
            motivo,
            {"usuario_anterior": anterior},
        )
        adquirir_trava_edicao(
            documento.cd_empresa,
            request.user,
            "documento_clinico",
            documento.pk,
            _titulo_trava_documento(documento),
        )
    messages.success(request, "Documento assumido com sucesso.")
    return _redirect_documento_clinico(request, documento)


@login_required
def fechar_documento_clinico(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    with transaction.atomic():
        documento = (
            DocumentoClinico.objects.select_for_update()
            .select_related("cd_modelo_documento", "cd_usuario_responsavel")
            .filter(cd_empresa=empresa, pk=cd_documento)
            .first()
        )
        if not documento:
            messages.error(request, "Documento não encontrado ou não pertence à empresa atual.")
            return redirect(_safe_return_url(request) or "atendimento:pep")
        if documento.ds_status not in {"ABERTO", "RASCUNHO"}:
            messages.warning(request, _mensagem_documento_nao_editavel(documento))
            return _redirect_documento_clinico(request, documento)
        mensagem_trava = _bloqueio_trava_documento(request, documento)
        if mensagem_trava:
            messages.warning(request, mensagem_trava)
            return _redirect_documento_clinico(request, documento)
        if not _usuario_pode_operar_documento(request.user, documento):
            raise PermissionDenied
        if documento.cd_usuario_responsavel_id not in {None, request.user.pk}:
            raise PermissionDenied("Assuma o documento antes de fechá-lo.")
        if "ds_dados_formulario" in request.POST:
            documento.ds_conteudo = _conteudo_documento_seguro(request.POST.get("ds_conteudo", ""))
            try:
                documento.ds_dados_formulario = json.loads(request.POST.get("ds_dados_formulario") or "{}")
            except json.JSONDecodeError:
                messages.error(request, "Nao foi possivel interpretar os campos preenchidos.")
                return _redirect_documento_clinico(request, documento)
        ausentes = _campos_obrigatorios_documento_preenchidos(documento)
        if ausentes:
            messages.error(request, f"Preencha os campos obrigatórios: {', '.join(ausentes)}.")
            return _redirect_documento_clinico(request, documento)
        conteudo_hash = json.dumps(
            {
                "conteudo": documento.ds_conteudo,
                "dados": documento.ds_dados_formulario,
                "modelo": documento.cd_modelo_documento_id,
                "atendimento": documento.cd_atendimento_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        agora = timezone.now()
        prestador_assinante = getattr(request.user, "cd_prestador", None)
        assinatura = {
            "usuario_id": request.user.pk,
            "usuario_nome": request.user.display_name() if hasattr(request.user, "display_name") else request.user.get_username(),
            "prestador_id": getattr(prestador_assinante, "pk", None),
            "prestador_nome": getattr(prestador_assinante, "nm_prestador", ""),
            "conselho": getattr(prestador_assinante, "ds_conselho", ""),
            "numero_conselho": getattr(prestador_assinante, "nr_conselho", ""),
            "uf_conselho": getattr(prestador_assinante, "sg_conselho", ""),
            "data_hora": agora.isoformat(),
        }
        conteudo_hash = json.dumps(
            {"documento": json.loads(conteudo_hash), "assinatura": assinatura},
            ensure_ascii=False,
            sort_keys=True,
        )
        documento.ds_status = "FECHADO"
        documento.cd_usuario_responsavel = request.user
        documento.dh_finalizacao = agora
        documento.dh_assinatura = agora
        documento.ds_hash_conteudo = hashlib.sha256(conteudo_hash.encode("utf-8")).hexdigest()
        documento.ds_campos_bloqueados = {
            **(documento.ds_campos_bloqueados or {}),
            "assinatura": assinatura,
        }
        _apply_audit(documento, request.user)
        documento.save(update_fields=[
            "ds_status",
            "cd_usuario_responsavel",
            "dh_finalizacao",
            "dh_assinatura",
            "ds_conteudo",
            "ds_dados_formulario",
            "ds_hash_conteudo",
            "ds_campos_bloqueados",
            "dh_atualizacao",
            "cd_usuario_atualizacao",
        ])
        _registrar_evento_documento(
            documento,
            request.user,
            "FECHADO",
            dados={"hash": documento.ds_hash_conteudo, "assinatura": assinatura},
        )
        _liberar_trava_documento(documento, request.user, "Liberada ao fechar documento.")
    messages.success(request, "Documento fechado e assinado eletronicamente.")
    return _redirect_documento_clinico(request, documento)


@login_required
def abandonar_documento_clinico(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    motivo = request.POST.get("motivo", "").strip() or "Exclusão de documento aberto confirmada pelo usuário."
    empresa = _empresa_logada(request)
    with transaction.atomic():
        documento = DocumentoClinico.objects.select_for_update().filter(cd_empresa=empresa, pk=cd_documento).first()
        if not documento:
            messages.error(request, "Documento não encontrado ou não pertence à empresa atual.")
            return redirect(_safe_return_url(request) or "atendimento:pep")
        if documento.ds_status not in {"ABERTO", "RASCUNHO"}:
            messages.warning(request, _mensagem_documento_nao_editavel(documento))
            return _redirect_documento_clinico(request, documento)
        mensagem_trava = _bloqueio_trava_documento(request, documento)
        if mensagem_trava:
            messages.warning(request, mensagem_trava)
            return _redirect_documento_clinico(request, documento)
        if not _usuario_pode_operar_documento(request.user, documento):
            raise PermissionDenied
        if documento.cd_item_menu_assistencial and not documento.cd_item_menu_assistencial.sn_permite_abandonar:
            raise PermissionDenied("Este item não permite abandonar documentos.")
        documento.ds_status = "ABANDONADO"
        _apply_audit(documento, request.user)
        documento.save(update_fields=["ds_status", "dh_atualizacao", "cd_usuario_atualizacao"])
        _registrar_evento_documento(documento, request.user, "ABANDONADO", motivo)
        _liberar_trava_documento(documento, request.user, "Liberada ao excluir documento aberto.")
    messages.success(request, "Documento excluído.")
    return _redirect_documento_clinico(request, documento)


@login_required
def cancelar_documento_clinico(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    motivo = request.POST.get("motivo", "").strip()
    if not motivo:
        messages.error(request, "Informe o motivo do cancelamento.")
        return redirect("atendimento:imprimir-documento-clinico", cd_documento=cd_documento)
    empresa = _empresa_logada(request)
    with transaction.atomic():
        documento = get_object_or_404(
            DocumentoClinico.objects.select_for_update(),
            cd_empresa=empresa,
            pk=cd_documento,
            ds_status="FECHADO",
        )
        if not _usuario_pode_operar_documento(request.user, documento):
            raise PermissionDenied
        if not documento.cd_item_menu_assistencial or not documento.cd_item_menu_assistencial.sn_permite_cancelar:
            raise PermissionDenied("Este tipo de documento não permite cancelamento.")
        documento.ds_status = "CANCELADO"
        documento.ds_motivo_cancelamento = motivo
        documento.dh_cancelamento = timezone.now()
        documento.cd_usuario_cancelamento = request.user
        _apply_audit(documento, request.user)
        documento.save(update_fields=[
            "ds_status",
            "ds_motivo_cancelamento",
            "dh_cancelamento",
            "cd_usuario_cancelamento",
            "dh_atualizacao",
            "cd_usuario_atualizacao",
        ])
        _registrar_evento_documento(documento, request.user, "CANCELADO", motivo)
    messages.success(request, "Documento cancelado sem exclusão do histórico.")
    return _redirect_documento_clinico(request, documento)


@login_required
def liberar_trava_documento_clinico(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    empresa = _empresa_logada(request)
    documento = DocumentoClinico.objects.filter(cd_empresa=empresa, pk=cd_documento).first()
    if not documento:
        return JsonResponse({"ok": False, "error": "Documento não encontrado."}, status=404)
    liberar_trava_edicao(
        empresa,
        request.user,
        "documento_clinico",
        documento.pk,
        motivo="Liberada ao sair do prontuário.",
    )
    return HttpResponse(status=204)


@login_required
def liberar_acesso_excepcional_documento(request, cd_documento):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    grupos = set(request.user.groups.values_list("name", flat=True))
    if not request.user.is_superuser and "Auditor Clínico" not in grupos:
        raise PermissionDenied
    motivo = request.POST.get("motivo", "").strip()
    if not motivo:
        return JsonResponse({"ok": False, "error": "Informe o motivo do acesso."}, status=400)
    documento = get_object_or_404(
        DocumentoClinico,
        cd_empresa=_empresa_logada(request),
        pk=cd_documento,
    )
    request.session[f"acesso_documento_excepcional_{documento.pk}"] = True
    _registrar_evento_documento(documento, request.user, "ACESSO_EXCEPCIONAL", motivo)
    AcessoClinicoAuditado.objects.create(
        cd_empresa=documento.cd_empresa,
        cd_usuario=request.user,
        cd_documento_clinico=documento,
        tp_acesso="ACESSO_EXCEPCIONAL",
        ds_motivo=motivo,
        ds_ip=request.META.get("REMOTE_ADDR") or None,
    )
    return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)


def _item_assistencial_permitido(request, atendimento, cd_item, tipo=None):
    item = get_object_or_404(
        ItemMenuAssistencial.objects.select_related(
            "cd_perfil_assistencial",
            "cd_versao_perfil",
            "cd_modelo_documento",
        ),
        cd_empresa=atendimento.cd_empresa,
        pk=cd_item,
        sn_ativo=True,
    )
    if tipo and item.tp_item != tipo:
        raise PermissionDenied
    if not request.user.is_superuser:
        perfis = _perfis_assistenciais_usuario(request.user, atendimento.cd_empresa)
        if not perfis.filter(pk=item.cd_perfil_assistencial_id).exists():
            raise PermissionDenied
    return item


@login_required
def link_externo_assistencial(request, cd_atendimento, cd_item):
    atendimento = get_object_or_404(
        Atendimento,
        cd_empresa=_empresa_logada(request),
        pk=cd_atendimento,
    )
    item = _item_assistencial_permitido(request, atendimento, cd_item, "LINK_EXTERNO")
    url = (
        item.ds_url
        .replace("<<cd_atendimento>>", str(atendimento.pk))
        .replace("<<cd_paciente>>", str(atendimento.cd_paciente_id))
        .replace("<<cd_prestador>>", str(atendimento.cd_prestador_id or ""))
        .replace("<<atendimento.codigo>>", str(atendimento.pk))
        .replace("<<paciente.codigo>>", str(atendimento.cd_paciente_id))
        .replace("<<prestador.codigo>>", str(atendimento.cd_prestador_id or ""))
    )
    dominio = _url_externa_permitida(atendimento.cd_empresa, url)
    if not dominio:
        raise PermissionDenied("Domínio externo não autorizado.")
    if not dominio.sn_permite_iframe:
        return redirect(url)
    return render(
        request,
        "atendimento/link_externo_assistencial.html",
        {"atendimento": atendimento, "item": item, "url_externa": url},
    )


@login_required
def executar_escala_clinica(request, cd_atendimento, cd_item):
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_prestador"),
        cd_empresa=_empresa_logada(request),
        pk=cd_atendimento,
    )
    item = _item_assistencial_permitido(request, atendimento, cd_item, "ESCALA")
    escala_id = str((item.ds_configuracao or {}).get("escala") or "")
    escala = get_object_or_404(
        EscalaClinica,
        cd_empresa=atendimento.cd_empresa,
        pk=int(escala_id) if escala_id.isdigit() else 0,
        sn_ativo=True,
    )
    perguntas = escala.ds_perguntas if isinstance(escala.ds_perguntas, list) else []
    if request.method == "POST":
        if not request.user.check_password(request.POST.get("senha", "")):
            messages.error(request, "Senha inválida. A escala não foi assinada.")
            return render(
                request,
                "atendimento/executar_escala_clinica.html",
                {"atendimento": atendimento, "item": item, "escala": escala, "perguntas": perguntas},
            )
        respostas = {}
        for pergunta in perguntas:
            chave = str(pergunta.get("chave") or "").strip()
            opcoes = pergunta.get("opcoes") or []
            valor = request.POST.get(f"pergunta_{chave}", "")
            opcao = next((opcao for opcao in opcoes if str(opcao.get("valor")) == valor), None)
            if not chave or not opcao:
                messages.error(request, f"Responda: {pergunta.get('texto') or chave}.")
                return render(
                    request,
                    "atendimento/executar_escala_clinica.html",
                    {"atendimento": atendimento, "item": item, "escala": escala, "perguntas": perguntas},
                )
            pontuacao = float(opcao.get("pontos") or 0)
            respostas[chave] = {
                "pergunta": pergunta.get("texto"),
                "valor": valor,
                "descricao": opcao.get("descricao"),
                "pontos": pontuacao,
            }
        try:
            resultado = _calcular_resultado_escala(
                escala,
                {chave: resposta["pontos"] for chave, resposta in respostas.items()},
            )
        except (SyntaxError, ValueError, ZeroDivisionError) as error:
            messages.error(request, f"Não foi possível calcular a escala: {error}")
            return render(
                request,
                "atendimento/executar_escala_clinica.html",
                {"atendimento": atendimento, "item": item, "escala": escala, "perguntas": perguntas},
            )
        faixa = _faixa_resultado_escala(escala.ds_faixas_resultado, resultado)
        with transaction.atomic():
            documento = _criar_documento_clinico(
                atendimento,
                f"ESCALA_{escala.pk}",
                f"{escala.nm_escala} - atendimento {atendimento.pk}",
                json.dumps(
                    {
                        "escala": escala.nm_escala,
                        "respostas": respostas,
                        "resultado": resultado,
                        "classificacao": faixa.get("descricao", "Sem classificação"),
                        "cor_classificacao": faixa.get("cor", ""),
                        "classificacao_negrito": bool(faixa.get("negrito")),
                    },
                    ensure_ascii=False,
                ),
                request.user,
                status="FECHADO",
            )
            documento.cd_item_menu_assistencial = item
            documento.cd_versao_perfil = item.cd_versao_perfil
            documento.save(update_fields=["cd_item_menu_assistencial", "cd_versao_perfil"])
            ResultadoEscalaClinica.objects.create(
                cd_empresa=atendimento.cd_empresa,
                cd_atendimento=atendimento,
                cd_escala_clinica=escala,
                cd_documento_clinico=documento,
                ds_respostas=respostas,
                nr_resultado=resultado,
                ds_classificacao=faixa.get("descricao", "Sem classificação"),
                ds_cor=faixa.get("cor", ""),
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
        messages.success(request, f"Escala concluída: {resultado:g} · {faixa.get('descricao', 'Sem classificação')}.")
        return redirect("atendimento:imprimir-documento-clinico", cd_documento=documento.pk)
    return render(
        request,
        "atendimento/executar_escala_clinica.html",
        {"atendimento": atendimento, "item": item, "escala": escala, "perguntas": perguntas},
    )


@login_required
@role_required("TI")
def testar_escala_clinica(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método não permitido."}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido."}, status=400)
    escala = get_object_or_404(
        EscalaClinica,
        cd_empresa=_empresa_logada(request),
        pk=payload.get("escala"),
        sn_ativo=True,
    )
    respostas = payload.get("respostas") or {}
    pontos = {}
    for pergunta in escala.ds_perguntas or []:
        chave = str(pergunta.get("chave") or "")
        opcao = next(
            (
                opcao
                for opcao in pergunta.get("opcoes") or []
                if str(opcao.get("valor")) == str(respostas.get(chave))
            ),
            None,
        )
        if not opcao:
            return JsonResponse({"ok": False, "error": f"Resposta inválida para {chave}."}, status=400)
        pontos[chave] = float(opcao.get("pontos") or 0)
    try:
        resultado = _calcular_resultado_escala(escala, pontos)
    except (SyntaxError, ValueError, ZeroDivisionError) as error:
        return JsonResponse({"ok": False, "error": str(error)}, status=400)
    faixa = _faixa_resultado_escala(escala.ds_faixas_resultado, resultado)
    return JsonResponse({
        "ok": True,
        "resultado": resultado,
        "classificacao": faixa.get("descricao", "Sem classificação"),
        "cor": faixa.get("cor", ""),
        "negrito": bool(faixa.get("negrito")),
    })


@login_required
def anexos_clinicos(request, cd_atendimento, cd_item):
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente"),
        cd_empresa=_empresa_logada(request),
        pk=cd_atendimento,
    )
    item = _item_assistencial_permitido(request, atendimento, cd_item, "ANEXO")
    configuracao = item.ds_configuracao or {}
    tipos_permitidos = set(configuracao.get("tipos_mime") or [
        "application/pdf",
        "image/jpeg",
        "image/png",
    ])
    limite = int(configuracao.get("tamanho_maximo_mb") or 10) * 1024 * 1024
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            messages.error(request, "Selecione um arquivo.")
        elif arquivo.content_type not in tipos_permitidos:
            messages.error(request, "Tipo de arquivo não permitido.")
        elif arquivo.size > limite:
            messages.error(request, f"O arquivo excede o limite de {limite // 1024 // 1024} MB.")
        else:
            digest = hashlib.sha256()
            for chunk in arquivo.chunks():
                digest.update(chunk)
            arquivo.seek(0)
            anexo = AnexoClinico(
                cd_empresa=atendimento.cd_empresa,
                cd_atendimento=atendimento,
                cd_item_menu_assistencial=item,
                nm_arquivo=arquivo.name,
                ds_tipo_mime=arquivo.content_type,
                nr_tamanho=arquivo.size,
                ds_checksum_sha256=digest.hexdigest(),
                ds_arquivo=arquivo,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
            anexo.save()
            messages.success(request, "Anexo armazenado e enviado para validação de segurança.")
            return redirect(
                "atendimento:anexos-clinicos",
                cd_atendimento=atendimento.pk,
                cd_item=item.pk,
            )
    anexos = atendimento.anexos_clinicos.filter(sn_ativo=True)
    return render(
        request,
        "atendimento/anexos_clinicos.html",
        {
            "atendimento": atendimento,
            "item": item,
            "anexos": anexos,
            "tipos_permitidos": ", ".join(sorted(tipos_permitidos)),
            "limite_mb": limite // 1024 // 1024,
        },
    )


@login_required
def baixar_anexo_clinico(request, cd_anexo):
    empresa = _empresa_logada(request)
    anexo = get_object_or_404(
        AnexoClinico.objects.select_related(
            "cd_atendimento",
            "cd_documento_clinico",
            "cd_item_menu_assistencial__cd_perfil_assistencial",
        ),
        cd_empresa=empresa,
        pk=cd_anexo,
        sn_ativo=True,
    )
    if anexo.cd_documento_clinico and not _usuario_pode_operar_documento(request.user, anexo.cd_documento_clinico):
        raise PermissionDenied
    if anexo.cd_item_menu_assistencial and not request.user.is_superuser:
        if not _perfis_assistenciais_usuario(request.user, empresa).filter(
            pk=anexo.cd_item_menu_assistencial.cd_perfil_assistencial_id
        ).exists():
            raise PermissionDenied
    AcessoClinicoAuditado.objects.create(
        cd_empresa=empresa,
        cd_usuario=request.user,
        cd_anexo_clinico=anexo,
        tp_acesso="DOWNLOAD",
        ds_ip=request.META.get("REMOTE_ADDR") or None,
    )
    anexo.ds_arquivo.open("rb")
    return FileResponse(
        anexo.ds_arquivo,
        as_attachment=True,
        filename=anexo.nm_arquivo,
        content_type=anexo.ds_tipo_mime,
    )


@login_required
def historico_documentos_assistencial(request, cd_atendimento, cd_item):
    atendimento = get_object_or_404(
        Atendimento.objects.select_related("cd_paciente"),
        cd_empresa=_empresa_logada(request),
        pk=cd_atendimento,
    )
    item = _item_assistencial_permitido(request, atendimento, cd_item, "HISTORICO")
    configuracao = item.ds_configuracao or {}
    documentos = DocumentoClinico.objects.filter(
        cd_empresa=atendimento.cd_empresa,
        cd_atendimento__cd_paciente=atendimento.cd_paciente,
    ).select_related(
        "cd_atendimento",
        "cd_usuario_responsavel",
        "cd_item_menu_assistencial__cd_perfil_assistencial",
    )
    tipos = configuracao.get("tipos_documento") or []
    if tipos:
        documentos = documentos.filter(tp_documento__in=tipos)
    modelo_id = configuracao.get("modelo_documento")
    if modelo_id:
        documentos = documentos.filter(cd_modelo_documento_id=modelo_id)
    if not request.user.is_superuser:
        perfil_ids = list(
            _perfis_assistenciais_usuario(request.user, atendimento.cd_empresa).values_list("pk", flat=True)
        )
        documentos = documentos.filter(
            Q(cd_item_menu_assistencial__isnull=True)
            | Q(
                cd_item_menu_assistencial__cd_perfil_assistencial__sn_sigiloso=False,
                cd_item_menu_assistencial__sn_privado=False,
            )
            | Q(cd_item_menu_assistencial__cd_perfil_assistencial_id__in=perfil_ids)
        )
    return render(
        request,
        "atendimento/historico_documentos_assistencial.html",
        {
            "atendimento": atendimento,
            "paciente": atendimento.cd_paciente,
            "item": item,
            "documentos": documentos.order_by("-dh_emissao")[:200],
        },
    )


@login_required
def copiar_documento_clinico(request, cd_documento):
    empresa = _empresa_logada(request)
    origem = get_object_or_404(DocumentoClinico, cd_empresa=empresa, cd_documento_clinico=cd_documento)
    if origem.ds_status not in {"FECHADO", "CANCELADO"}:
        raise PermissionDenied("Somente documentos fechados ou cancelados podem ser copiados.")
    if not _usuario_pode_visualizar_documento(request.user, origem):
        raise PermissionDenied
    copia = _criar_documento_clinico(
        origem.cd_atendimento,
        origem.tp_documento,
        origem.ds_titulo,
        origem.ds_conteudo,
        request.user,
        origem=origem,
    )
    copia.cd_modelo_documento = origem.cd_modelo_documento
    copia.cd_item_menu_assistencial = origem.cd_item_menu_assistencial
    copia.cd_versao_perfil = origem.cd_versao_perfil
    copia.cd_usuario_responsavel = request.user
    copia.ds_dados_formulario = copy.deepcopy(origem.ds_dados_formulario or {})
    copia.ds_campos_bloqueados = {}
    copia.save(update_fields=[
        "cd_modelo_documento",
        "cd_item_menu_assistencial",
        "cd_versao_perfil",
        "cd_usuario_responsavel",
        "ds_dados_formulario",
        "ds_campos_bloqueados",
    ])
    messages.success(request, "Documento copiado como rascunho.")
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        parsed = urlparse(next_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["documento"] = str(copia.pk)
        return redirect(urlunparse(parsed._replace(query=urlencode(query))))
    return _redirect_documento_clinico(request, copia)


def _editable_auxiliary(request, table_name, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
    tabela, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela=table_name,
        defaults={"ds_descricao": title, "sn_ativo": True},
    )
    query = _query_text(request)
    if request.method == "POST":
        for valor in tabela.valores.all():
            if request.POST.get(f"delete_{valor.pk}") == "1":
                try:
                    valor.delete()
                except ProtectedError:
                    messages.error(
                        request,
                        f"{valor.ds_valor} está em uso e não pode ser excluído.",
                    )
                continue
            if f"description_{valor.pk}" not in request.POST:
                continue
            valor.ds_valor = request.POST.get(f"description_{valor.pk}", valor.ds_valor)
            valor.sn_ativo = request.POST.get(f"active_{valor.pk}") == "true"
            valor.save()
        new_descriptions = request.POST.getlist("new_description")
        new_actives = request.POST.getlist("new_active")
        created = 0
        for index, description in enumerate(new_descriptions):
            description = description.strip()
            if not description:
                continue
            code = _auxiliary_code(description)
            ValorAuxiliarGlobal.objects.update_or_create(
                cd_tabela_auxiliar_global=tabela,
                cd_valor=code,
                defaults={"ds_valor": description, "sn_ativo": (new_actives[index] if index < len(new_actives) else "true") == "true"},
            )
            created += 1
        if new_descriptions and not created and not any(
            request.POST.get(f"description_{valor.pk}", "").strip()
            for valor in tabela.valores.all()
        ):
            messages.error(request, "Informe a descrição obrigatória antes de salvar.")
        else:
            messages.success(request, f"{title} salvo com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    valores = tabela.valores.all()
    if query:
        value_filter = Q(cd_valor__icontains=query) | Q(ds_valor__icontains=query)
        if query.isdigit():
            value_filter |= Q(cd_valor_auxiliar_global=int(query))
        valores = valores.filter(value_filter)
    valores = paginate_table(
        request,
        valores,
        {"cd_valor_auxiliar_global", "cd_valor", "ds_valor", "sn_ativo"},
        "cd_valor_auxiliar_global",
    )
    return render(request, "atendimento/editable_auxiliary.html", {"title": title, "tabela": tabela, "valores": valores})


def _editable_escalas(request, title):
    request.current_tab_title = title
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = True
    empresa = _empresa_logada(request)
    registros = AgendaProfissional.objects.select_related("cd_prestador").filter(cd_empresa=empresa)
    query = _query_text(request)
    if query:
        registros = registros.filter(Q(ds_agenda__icontains=query) | Q(cd_prestador__nm_prestador__icontains=query) | Q(cd_prestador__ds_especialidade__icontains=query))
    registros = paginate_table(
        request,
        registros,
        {
            "cd_agenda_profissional",
            "cd_prestador__nm_prestador",
            "ds_agenda",
            "nr_dia_semana",
            "hr_inicio",
            "hr_fim",
            "nr_tempo_atendimento",
            "nr_intervalo",
            "sn_atende_feriado",
            "sn_ativo",
        },
        "cd_agenda_profissional",
    )
    prestadores = Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_agenda=True)
    if request.method == "POST":
        for escala in registros:
            if request.POST.get(f"delete_{escala.pk}") == "1":
                try:
                    escala.delete()
                except ProtectedError:
                    messages.error(request, "A escala possui agendas geradas e não pode ser excluída. Desative-a.")
                continue
            if f"name_{escala.pk}" not in request.POST:
                continue
            escala.cd_prestador_id = request.POST.get(f"provider_{escala.pk}") or escala.cd_prestador_id
            escala.ds_agenda = request.POST.get(f"name_{escala.pk}", escala.ds_agenda)
            dias_semana = request.POST.getlist(f"weekdays_{escala.pk}")
            escala.ds_dias_semana = [int(dia) for dia in dias_semana]
            escala.nr_dia_semana = escala.ds_dias_semana[0] if escala.ds_dias_semana else escala.nr_dia_semana
            escala.hr_inicio = request.POST.get(f"start_{escala.pk}", escala.hr_inicio)
            escala.hr_fim = request.POST.get(f"end_{escala.pk}", escala.hr_fim)
            escala.nr_tempo_atendimento = request.POST.get(f"duration_{escala.pk}", escala.nr_tempo_atendimento)
            escala.nr_intervalo = request.POST.get(f"interval_{escala.pk}", escala.nr_intervalo)
            escala.sn_atende_feriado = request.POST.get(f"holiday_{escala.pk}") == "true"
            escala.sn_ativo = request.POST.get(f"active_{escala.pk}") == "true"
            _apply_audit(escala, request.user)
            escala.save()
        new_providers = request.POST.getlist("new_provider")
        for index, provider_id in enumerate(new_providers):
            if not provider_id:
                continue
            escala = AgendaProfissional(
                cd_empresa=empresa,
                cd_prestador_id=provider_id,
                ds_agenda=request.POST.getlist("new_name")[index].strip() if index < len(request.POST.getlist("new_name")) else "ESCALA",
                nr_dia_semana=request.POST.getlist("new_weekday")[index] if index < len(request.POST.getlist("new_weekday")) else 0,
                ds_dias_semana=[int(dia) for dia in request.POST.getlist("new_weekdays")],
                hr_inicio=request.POST.getlist("new_start")[index] if index < len(request.POST.getlist("new_start")) else "08:00",
                hr_fim=request.POST.getlist("new_end")[index] if index < len(request.POST.getlist("new_end")) else "12:00",
                nr_tempo_atendimento=request.POST.getlist("new_duration")[index] if index < len(request.POST.getlist("new_duration")) else 30,
                nr_intervalo=request.POST.getlist("new_interval")[index] if index < len(request.POST.getlist("new_interval")) else 0,
                sn_atende_feriado=(request.POST.getlist("new_holiday")[index] if index < len(request.POST.getlist("new_holiday")) else "false") == "true",
                sn_ativo=(request.POST.getlist("new_active")[index] if index < len(request.POST.getlist("new_active")) else "true") == "true",
            )
            if escala.ds_dias_semana:
                escala.nr_dia_semana = escala.ds_dias_semana[0]
            _apply_audit(escala, request.user)
            escala.save()
        messages.success(request, "Escalas salvas com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    return render(
        request,
        "atendimento/editable_escalas.html",
        {"title": title, "registros": registros, "prestadores": prestadores, "dias_semana": AgendaProfissional.DIAS_SEMANA},
    )


@login_required
@role_required("TI")
def cadastro_escala(request, cd_escala=None):
    request.current_tab_title = "Atendimento > Agendamento > Cadastro de escala"
    request.current_tab_root_title = "Cadastro de escala"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = bool(cd_escala)
    empresa = _empresa_logada(request)
    if request.GET.get("consultar") == "1":
        registros = AgendaProfissional.objects.filter(cd_empresa=empresa).prefetch_related("convenios")
        codigo = request.GET.get("cd_agenda_profissional", "").strip()
        if codigo.isdigit():
            registros = registros.filter(pk=int(codigo))
        text_fields = ("ds_agenda",)
        exact_fields = (
            "tp_escala",
            "tp_horario",
            "ds_tipo_agendamento",
            "ds_especialidade",
            "cd_prestador",
            "cd_setor_atendimento",
            "hr_inicio",
            "hr_fim",
            "nr_tempo_atendimento",
            "nr_intervalo",
            "qt_horarios_dia",
            "qt_encaixes",
        )
        for field_name in text_fields:
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
        for field_name in exact_fields:
            value = request.GET.get(field_name, "").strip()
            if value:
                registros = registros.filter(**{field_name: value})
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
        feriado = request.GET.get("sn_atende_feriado", "")
        if feriado in {"True", "False", "on"}:
            registros = registros.filter(sn_atende_feriado=feriado in {"True", "on"})
        convenios = [value for value in request.GET.getlist("convenios") if value.isdigit()]
        if convenios:
            registros = registros.filter(convenios__in=convenios).distinct()
        dias = {int(value) for value in request.GET.getlist("ds_dias_semana") if value.isdigit()}
        result_ids = [
            escala.pk
            for escala in registros.order_by("cd_agenda_profissional")[:200]
            if not dias or dias.issubset(set(escala.dias_semana))
        ]
        request.session["consulta_escalas"] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhuma escala encontrada para os filtros informados.")
            return redirect("atendimento:escalas")
        return redirect(
            f"{reverse('atendimento:cadastro-escala', args=[result_ids[0]])}?origem=consulta"
        )

    escala = (
        get_object_or_404(AgendaProfissional.objects.prefetch_related("convenios"), cd_empresa=empresa, pk=cd_escala)
        if cd_escala
        else None
    )
    if escala:
        request.current_toggle_active_url = reverse("atendimento:alternar-status-escala", args=[escala.pk])
        request.current_toggle_active_label = "Desativar" if escala.sn_ativo else "Ativar"
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get("consulta_escalas", []) if query_context else []
    if query_context:
        request.current_new_url = f"{reverse('atendimento:escalas')}?origem=consulta&novo=1"
    if not escala and query_context and request.GET.get("novo") == "1":
        request.current_record_status = f"Item {len(result_ids) + 1} de {len(result_ids)}"
        if result_ids:
            request.current_first_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[-1]])}?origem=consulta"
    elif not escala and query_context and request.GET.get("exclusao_concluida") == "1":
        request.current_record_status = f"{len(result_ids)} encontrado(s)"
        if result_ids:
            request.current_next_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[0]])}?origem=consulta"
            request.current_last_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[-1]])}?origem=consulta"
    if escala and escala.pk in result_ids:
        index = result_ids.index(escala.pk)
        request.current_record_status = f"Item {index + 1} de {len(result_ids)}"
        if index > 0:
            request.current_first_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[index - 1]])}?origem=consulta"
        if index < len(result_ids) - 1:
            request.current_next_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[index + 1]])}?origem=consulta"
            request.current_last_url = f"{reverse('atendimento:cadastro-escala', args=[result_ids[-1]])}?origem=consulta"
    form = EscalaForm(request.POST or None, instance=escala, empresa=empresa)
    if request.method == "POST" and request.POST.get("_excluir_atual") == "1" and escala:
        ordem_original = request.session.get("consulta_escalas", [])
        if not ordem_original and escala:
            ordem_original = [escala.pk]
        removido = False
        try:
            escala.delete()
            removido = True
        except ProtectedError:
            messages.error(request, "A escala possui agendas geradas e não pode ser excluída. Desative-a.")
        restantes = [
            item_id
            for item_id in ordem_original
            if AgendaProfissional.objects.filter(cd_empresa=empresa, pk=item_id).exists()
        ]
        request.session["consulta_escalas"] = restantes
        if removido:
            messages.success(request, "Escala excluída e alteração salva com sucesso.")
            parametros = "origem=consulta&exclusao_concluida=1" if query_context else "exclusao_concluida=1"
            return redirect(f"{reverse('atendimento:escalas')}{parametros}")
        destino = reverse("atendimento:cadastro-escala", args=[escala.pk])
        return redirect(f"{destino}?origem=consulta" if query_context else destino)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        _apply_audit(saved, request.user)
        saved.save()
        form.save_m2m()
        if query_context and saved.pk not in result_ids:
            result_ids.append(saved.pk)
            request.session["consulta_escalas"] = result_ids
        messages.success(request, "Escala salva com sucesso.")
        destino = reverse("atendimento:cadastro-escala", args=[saved.pk])
        return redirect(f"{destino}?origem=consulta" if query_context else destino)
    dias_selecionados = (
        [int(value) for value in request.POST.getlist("ds_dias_semana") if value.isdigit()]
        if request.method == "POST"
        else (escala.dias_semana if escala else [0, 1, 2, 3, 4])
    )
    return render(
        request,
        "atendimento/cadastro_escala.html",
        {
            "form": form,
            "escala": escala,
            "dias_semana": AgendaProfissional.DIAS_SEMANA,
            "dias_selecionados": dias_selecionados,
        },
    )


@login_required
@role_required("TI")
def alternar_status_escala(request, cd_escala):
    if request.method != "POST":
        raise PermissionDenied
    escala = get_object_or_404(AgendaProfissional, cd_empresa=_empresa_logada(request), pk=cd_escala)
    escala.sn_ativo = not escala.sn_ativo
    _apply_audit(escala, request.user)
    escala.save(update_fields=["sn_ativo", "dh_atualizacao", "cd_usuario_atualizacao"])
    messages.success(request, f"Escala {'ativada' if escala.sn_ativo else 'desativada'} com sucesso.")
    return redirect("atendimento:cadastro-escala", cd_escala=escala.pk)


def _agenda_dashboard(request):
    request.current_tab_title = "Agendas"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    request.current_can_remove = False
    empresa = _empresa_logada(request)
    hoje = timezone.localdate()
    agendamentos_hoje = Agendamento.objects.filter(cd_empresa=empresa, dh_agendamento__date=hoje)
    total_agendado = agendamentos_hoje.count()
    total_confirmado = agendamentos_hoje.filter(sn_confirmado=True).count()
    especialidade_totais = {}
    for item in agendamentos_hoje.values("ds_especialidade"):
        chave = item["ds_especialidade"] or "Não informada"
        especialidade_totais[chave] = especialidade_totais.get(chave, 0) + 1
    return render(
        request,
        "atendimento/agendas_dashboard.html",
        {
            "total_agendado": total_agendado,
            "total_confirmado": total_confirmado,
            "total_pendente": max(total_agendado - total_confirmado, 0),
            "especialidade_totais": especialidade_totais.items(),
            "horarios": _horarios_disponiveis(empresa),
            "agendamentos": agendamentos_hoje.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador"),
        },
    )


def _fila_atendimento(request):
    request.current_tab_title = "Atendimento > Fila de atendimento"
    request.current_tab_root_title = "Atender"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    fila = (
        Agendamento.objects.select_related("cd_paciente", "cd_agenda_profissional__cd_prestador", "pre_atendimento")
        .filter(
            cd_empresa=empresa,
            ds_status__in=["AGENDADO", "AGUARDANDO_PRE_ATENDIMENTO", "AGUARDANDO_ATENDIMENTO"],
        )
        .order_by("pre_atendimento__nr_prioridade", "dh_agendamento", "dh_criacao")
    )
    return render(request, "atendimento/fila_atendimento.html", {"fila": fila})


@login_required
@role_required("Recepcionista", "Enfermeiro", "Médico")
def atendimentos(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Atendimentos"
    request.current_tab_root_title = "Atendimentos"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_prestador").filter(cd_empresa=empresa).order_by("-dh_inicio")[:100]
    return render(request, "atendimento/atendimentos.html", {"registros": registros})


@login_required
@role_required("TI", "Médico", "Enfermeiro")
def pep(request):
    empresa = _empresa_logada(request)
    pep_standalone = getattr(request, "pep_standalone", False)
    request.current_tab_title = "Atendimento > PEP"
    request.current_tab_root_title = "PEP"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    setores = Setor.objects.filter(cd_empresa=empresa, tp_setor=Setor.TipoSetor.ATENDIMENTO, sn_ativo=True)
    if not request.user.groups.filter(name="TI").exists():
        setores = setores.filter(usuarios=request.user)
    setores = setores.distinct().order_by("nm_setor")
    aba = request.GET.get("aba", "atendimentos")
    setor_ids = [value for value in request.GET.getlist("setores") if value.isdigit()]
    usar_todos_setores = request.GET.get("todos_setores", "1") == "1" and not setor_ids
    setores_filtrados = setores if usar_todos_setores else setores.filter(pk__in=setor_ids)
    prestador_logado = getattr(request.user, "cd_prestador", None)
    codigos_especialidades_permitidas = []
    if prestador_logado:
        codigos_especialidades_permitidas = [
            str(codigo).strip().upper()
            for codigo in list(prestador_logado.ds_especialidades or []) + [prestador_logado.ds_especialidade]
            if str(codigo or "").strip()
        ]
    elif request.user.groups.filter(name="TI").exists():
        codigos_especialidades_permitidas = [
            str(codigo).strip().upper()
            for codigo in Atendimento.objects.filter(cd_empresa=empresa)
            .exclude(ds_especialidade="")
            .values_list("ds_especialidade", flat=True)
            .distinct()
            if str(codigo or "").strip()
        ]
    codigos_especialidades_permitidas = list(dict.fromkeys(codigos_especialidades_permitidas))
    nomes_especialidades = {
        str(item.cd_valor).strip().upper(): item.ds_valor
        for item in ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela="especialidade",
            sn_ativo=True,
        )
    }
    especialidades_permitidas = []
    descricoes_adicionadas = set()
    for codigo in codigos_especialidades_permitidas:
        descricao = (
            nomes_especialidades.get(codigo)
            or {"CLINICA_GERAL": "Clínica Geral"}.get(codigo)
            or codigo.replace("_", " ").title()
        )
        chave_descricao = unicodedata.normalize("NFKD", descricao).encode("ascii", "ignore").decode().strip().casefold()
        if chave_descricao in descricoes_adicionadas:
            continue
        descricoes_adicionadas.add(chave_descricao)
        especialidades_permitidas.append({"codigo": codigo, "descricao": descricao})
    especialidades_selecionadas = [
        str(codigo).strip().upper()
        for codigo in request.GET.getlist("especialidades_atendimento")
        if str(codigo).strip().upper() in codigos_especialidades_permitidas
    ]
    atendimentos_setor = (
        Atendimento.objects.select_related("cd_paciente", "cd_paciente__cd_convenio", "cd_convenio", "cd_prestador", "cd_pre_atendimento", "cd_setor_atual")
        .prefetch_related("solicitacoes_exames", "prescricoes")
        .filter(cd_empresa=empresa, sn_ativo=True)
        .filter(ds_status__in=[
            "RECEPCIONADO",
            "ABERTO",
            "AGUARDANDO_CLASSIFICACAO",
            "EM_CLASSIFICACAO",
            "AGUARDANDO_CONSULTA",
            "EM_ATENDIMENTO",
            "AGUARDANDO_EXAMES",
            "RETORNO_EXAMES",
            "EM_OBSERVACAO",
        ])
        .order_by("cd_pre_atendimento__nr_prioridade", "dh_inicio")
    )
    if setores_filtrados.exists():
        atendimentos_setor = atendimentos_setor.filter(Q(cd_setor_atual__in=setores_filtrados) | Q(cd_setor_atual__isnull=True))
    elif setores.exists():
        atendimentos_setor = atendimentos_setor.none()
    if prestador_logado and not request.user.groups.filter(name="TI").exists():
        atendimentos_setor = atendimentos_setor.filter(
            Q(cd_prestador=prestador_logado)
            | Q(cd_prestador__isnull=True, ds_especialidade__in=codigos_especialidades_permitidas)
        )
    if especialidades_selecionadas:
        atendimentos_setor = atendimentos_setor.filter(ds_especialidade__in=especialidades_selecionadas)
    busca_atendimento = request.GET.get("q_atendimento", "").strip().replace("%", "")
    nr_atendimento = request.GET.get("nr_atendimento", "").strip()
    if nr_atendimento.isdigit():
        atendimentos_setor = atendimentos_setor.filter(cd_atendimento=int(nr_atendimento))
        busca_atendimento = ""
    elif busca_atendimento:
        filtros_atendimento = (
            Q(cd_paciente__nm_paciente__icontains=busca_atendimento)
            | Q(cd_paciente__nr_cpf__icontains=busca_atendimento)
            | Q(cd_paciente__nr_cartao_sus__icontains=busca_atendimento)
            | Q(cd_paciente__nr_rg__icontains=busca_atendimento)
        )
        if busca_atendimento.isdigit():
            filtros_atendimento |= Q(cd_paciente_id=int(busca_atendimento))
        atendimentos_setor = atendimentos_setor.filter(filtros_atendimento)

    pacientes_geral = Paciente.objects.none()
    paciente_selecionado = None
    atendimentos_paciente = Atendimento.objects.none()
    atendimento_selecionado = None
    busca = request.GET.get("q", "").strip().replace("%", "")
    nr_atendimento_geral = request.GET.get("nr_atendimento_geral", "").strip()
    data_inicio = request.GET.get("data_inicio", "")
    data_fim = request.GET.get("data_fim", "")
    paciente_id = request.GET.get("paciente")
    atendimento_id = request.GET.get("atendimento")
    if aba == "todos":
        pacientes_geral = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if nr_atendimento_geral.isdigit():
            pacientes_geral = pacientes_geral.filter(atendimento__cd_atendimento=int(nr_atendimento_geral))
            busca = ""
            data_inicio = ""
            data_fim = ""
        elif busca:
            filtros = (
                Q(nm_paciente__icontains=busca)
                | Q(nr_cpf__icontains=busca)
                | Q(nr_cartao_sus__icontains=busca)
                | Q(nr_rg__icontains=busca)
                | Q(atendimento__cd_atendimento__icontains=busca)
            )
            if busca.isdigit():
                filtros |= Q(cd_paciente=int(busca))
            pacientes_geral = pacientes_geral.filter(filtros)
        elif not data_inicio and not data_fim:
            pacientes_geral = pacientes_geral.none()
        if data_inicio:
            pacientes_geral = pacientes_geral.filter(atendimento__dh_inicio__date__gte=data_inicio)
        if data_fim:
            pacientes_geral = pacientes_geral.filter(atendimento__dh_inicio__date__lte=data_fim)
        pacientes_geral = pacientes_geral.distinct().order_by("nm_paciente")[:50]
        if paciente_id:
            paciente_selecionado = get_object_or_404(Paciente, cd_empresa=empresa, pk=paciente_id)
            atendimentos_paciente = (
                Atendimento.objects.select_related("cd_prestador", "cd_pre_atendimento", "cd_convenio")
                .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes")
                .filter(cd_empresa=empresa, cd_paciente=paciente_selecionado)
                .order_by("-dh_inicio")
            )
        if atendimento_id:
            atendimento_selecionado = get_object_or_404(
                Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_pre_atendimento", "cd_convenio")
                .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes"),
                cd_empresa=empresa,
                pk=atendimento_id,
            )
            paciente_selecionado = atendimento_selecionado.cd_paciente
            atendimentos_paciente = Atendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente_selecionado).order_by("-dh_inicio")
    return render(
        request,
        "atendimento/pep.html",
        {
            "pep_standalone": pep_standalone,
            "pep_base_template": "base/pep_layout.html" if pep_standalone else "base/layout.html",
            "pep_list_url": reverse("pep_standalone") if pep_standalone else reverse("atendimento:pep"),
            "setores": setores,
            "setores_filtrados": setores_filtrados,
            "setor_ids": [str(value) for value in setores_filtrados.values_list("pk", flat=True)],
            "setor_chamada_padrao": setores_filtrados.first(),
            "usar_todos_setores": usar_todos_setores,
            "especialidades_permitidas": especialidades_permitidas,
            "especialidades_selecionadas": especialidades_selecionadas,
            "atendimentos": atendimentos_setor[:80],
            "aba": aba,
            "busca_atendimento": busca_atendimento,
            "nr_atendimento": nr_atendimento,
            "busca": busca,
            "nr_atendimento_geral": nr_atendimento_geral,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "pacientes_geral": pacientes_geral,
            "paciente_selecionado": paciente_selecionado,
            "atendimentos_paciente": atendimentos_paciente,
            "atendimento_selecionado": atendimento_selecionado,
            "agora": timezone.now(),
        },
    )


@login_required
@role_required("TI", "Médico", "Enfermeiro")
def pep_prontuario_paciente(request, cd_paciente):
    empresa = _empresa_logada(request)
    pep_standalone = getattr(request, "pep_standalone", False)
    pep_list_route = "pep_standalone" if pep_standalone else "atendimento:pep"
    pep_patient_route = "pep_prontuario_standalone" if pep_standalone else "atendimento:pep-prontuario-paciente"
    paciente = get_object_or_404(
        Paciente.objects.select_related("cd_convenio"),
        cd_empresa=empresa,
        pk=cd_paciente,
    )
    somente_consulta = request.GET.get("modo") == "consulta"
    atendimentos = (
        Atendimento.objects.select_related(
            "cd_prestador", "cd_pre_atendimento", "cd_convenio", "cd_setor_atual",
        )
        .prefetch_related(
            "solicitacoes_exames__resultado", "prescricoes", "evolucoes", "documentos",
        )
        .filter(cd_empresa=empresa, cd_paciente=paciente)
        .order_by("-dh_inicio")
    )
    atendimento_id = request.GET.get("atendimento", "").strip()
    if atendimento_id.isdigit():
        atendimento_selecionado = get_object_or_404(atendimentos, pk=int(atendimento_id))
    else:
        status_abertos = [
            "AGUARDANDO_CONSULTA", "EM_ATENDIMENTO", "AGUARDANDO_EXAMES",
            "RETORNO_EXAMES", "EM_OBSERVACAO",
        ]
        atendimento_selecionado = atendimentos.filter(ds_status__in=status_abertos).first() or atendimentos.first()
    ultimos_sinais_vitais = (
        atendimento_selecionado.cd_pre_atendimento
        if atendimento_selecionado and atendimento_selecionado.cd_pre_atendimento_id
        else PreAtendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente)
        .order_by("-dh_classificacao")
        .first()
    )
    historico_sinais_vitais = (
        PreAtendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente)
        .select_related("cd_prestador_responsavel")
        .order_by("-dh_classificacao")[:30]
    )
    return_to = _safe_return_url(request) or f"{reverse(pep_list_route)}?aba=todos"
    request.current_return_url = return_to
    request.current_tab_title = "Atendimento > PEP > Prontuário"
    request.current_tab_root_title = "PEP"
    request.current_module_title = "Atendimento"
    request.current_can_query = False
    grupos = set(request.user.groups.values_list("name", flat=True))
    can_clinical_actions = request.user.is_superuser or bool(grupos.intersection({"TI", "Médico", "Médico"}))
    perfis_assistenciais, itens_assistenciais = _itens_menu_assistencial_mesclados(request.user, empresa)
    menu_assistencial_raizes = []
    if atendimento_selecionado:
        mapa_acoes = {
            "SINAIS_VITAIS": f"{reverse('atendimento:ficha-atendimento', args=[atendimento_selecionado.pk])}#classificacao",
            "ADMISSAO": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "admissao"]),
            "EVOLUIR": reverse("atendimento:evoluir", args=[atendimento_selecionado.pk]),
            "PRESCREVER": reverse("atendimento:prescrever", args=[atendimento_selecionado.pk]),
            "EXAMES": reverse("atendimento:solicitar-exame", args=[atendimento_selecionado.pk]),
            "ALTA_MEDICA": reverse("atendimento:conceder-alta", args=[atendimento_selecionado.pk]),
            "RECEITUARIO": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "receituario"]),
            "AIH": reverse("atendimento:documento-assistencial", args=[atendimento_selecionado.pk, "aih"]),
            "DOCUMENTOS": f"{reverse('atendimento:ficha-atendimento', args=[atendimento_selecionado.pk])}#documentos",
        }
        for item in itens_assistenciais:
            item.somente_consulta = somente_consulta and item.tp_item not in {"DOCUMENTO", "HISTORICO", "GRUPO"}
            if item.tp_item == "GRUPO":
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'grupo': item.pk, 'return_to': return_to})}"
                )
                item.url_inicio_renderizada = item.url_renderizada
            elif item.tp_item == "DOCUMENTO" and item.cd_modelo_documento_id:
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                )
            elif item.tp_item in {"ESCALA", "ANEXO", "HISTORICO", "LINK_EXTERNO"}:
                item.url_renderizada = (
                    f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                    f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                )
            else:
                if pep_standalone and item.ds_acao:
                    item.url_renderizada = (
                        f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                        f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item.pk, 'return_to': return_to})}"
                    )
                else:
                    item.url_renderizada = mapa_acoes.get(item.ds_acao, item.ds_url or "#")
        itens_por_chave = {item.chave_mesclagem: item for item in itens_assistenciais}
        for item in itens_assistenciais:
            pai = itens_por_chave.get(item.chave_pai_mesclagem)
            if pai:
                pai.filhos_renderizados.append(item)
            else:
                menu_assistencial_raizes.append(item)
    item_selecionado = None
    ultimo_documento_item = None
    documento_aberto_item = None
    apresentacao_documento_item = None
    documento_editavel_item = False
    documento_modo_impressao_item = False
    pode_assumir_documento_item = False
    pode_cancelar_documento_item = False
    pode_copiar_documento_item = False
    documento_bloqueio_item = ""
    pep_documento_next_url = ""
    historico_documentos_item = DocumentoClinico.objects.none()
    item_id = (request.POST.get("item") or request.GET.get("item") or "").strip()
    if atendimento_selecionado and item_id.isdigit():
        item_selecionado = next(
            (
                item for item in itens_assistenciais
                if item.pk == int(item_id) and item.tp_item != "GRUPO"
            ),
            None,
        )
    if item_selecionado and item_selecionado.tp_item == "DOCUMENTO" and item_selecionado.cd_modelo_documento_id:
        modelo_documento_item = _versao_atual_modelo_documento(item_selecionado.cd_modelo_documento)
        if modelo_documento_item and modelo_documento_item.pk != item_selecionado.cd_modelo_documento_id:
            item_selecionado.cd_modelo_documento = modelo_documento_item
            item_selecionado.cd_modelo_documento_id = modelo_documento_item.pk
        modelos_familia_item = _ids_familia_modelo_documento(modelo_documento_item) if modelo_documento_item else [item_selecionado.cd_modelo_documento_id]
        historico_documentos_item = DocumentoClinico.objects.filter(
            cd_empresa=empresa,
            cd_atendimento__cd_paciente=paciente,
            cd_modelo_documento_id__in=modelos_familia_item,
        ).exclude(ds_status="ABANDONADO").select_related(
            "cd_atendimento",
            "cd_usuario_responsavel",
            "cd_usuario_cancelamento",
        ).prefetch_related(
            Prefetch(
                "eventos",
                queryset=EventoDocumentoClinico.objects.select_related("cd_usuario").order_by("-dh_evento"),
            )
        ).order_by("-dh_emissao")
        documento_id = (request.GET.get("documento") or "").strip()
        if documento_id.isdigit():
            ultimo_documento_item = historico_documentos_item.filter(pk=int(documento_id)).first()
        documento_aberto_item = historico_documentos_item.filter(ds_status__in=["ABERTO", "RASCUNHO"]).first()
        if not ultimo_documento_item:
            ultimo_documento_item = documento_aberto_item or historico_documentos_item.first()
        if request.method == "POST" and request.POST.get("acao") == "novo_documento":
            if somente_consulta:
                raise PermissionDenied("O prontuário foi aberto em modo de consulta.")
            if not item_selecionado.sn_permite_criar or item_selecionado.sn_somente_historico:
                raise PermissionDenied("Esta tela não permite criar documentos.")
            if not atendimento_selecionado or atendimento_selecionado.ds_status in {
                "FINALIZADO", "ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "CANCELADO",
            }:
                raise PermissionDenied("Não é possível criar documentos em um atendimento encerrado.")
            data_hora_texto = request.POST.get("dh_documento", "").strip()
            try:
                data_hora_documento = datetime.fromisoformat(data_hora_texto)
                if timezone.is_naive(data_hora_documento):
                    data_hora_documento = timezone.make_aware(data_hora_documento)
            except (TypeError, ValueError):
                messages.error(request, "Informe uma data e hora válida para o documento.")
            else:
                documento = _criar_documento_clinico(
                    atendimento_selecionado,
                    modelo_documento_item.tp_documento,
                    modelo_documento_item.nm_modelo,
                    "",
                    request.user,
                )
                documento.cd_modelo_documento = modelo_documento_item
                documento.cd_item_menu_assistencial = item_selecionado
                documento.cd_versao_perfil = item_selecionado.cd_versao_perfil
                documento.cd_usuario_responsavel = request.user
                documento.ds_status = "ABERTO"
                documento.dh_emissao = data_hora_documento
                documento.save(update_fields=[
                    "cd_modelo_documento",
                    "cd_item_menu_assistencial",
                    "cd_versao_perfil",
                    "cd_usuario_responsavel",
                    "ds_status",
                    "dh_emissao",
                ])
                params = urlencode({
                    "modo": "atendimento",
                    "atendimento": atendimento_selecionado.pk,
                    "item": item_selecionado.pk,
                    "documento": documento.pk,
                    "return_to": return_to,
                })
                return redirect(f"{reverse(pep_patient_route, args=[paciente.pk])}?{params}")
        if ultimo_documento_item:
            documento_editavel_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}
                and ultimo_documento_item.cd_usuario_responsavel_id in {None, request.user.pk}
            )
            pode_assumir_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}
                and ultimo_documento_item.cd_usuario_responsavel_id not in {None, request.user.pk}
                and _usuario_pode_operar_documento(request.user, ultimo_documento_item)
            )
            pode_cancelar_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status == "FECHADO"
                and item_selecionado.sn_permite_cancelar
                and _usuario_pode_operar_documento(request.user, ultimo_documento_item)
            )
            pode_copiar_documento_item = bool(
                not somente_consulta
                and ultimo_documento_item.ds_status in {"FECHADO", "CANCELADO"}
                and _usuario_pode_visualizar_documento(request.user, ultimo_documento_item)
            )
            if ultimo_documento_item.ds_status in {"ABERTO", "RASCUNHO"}:
                if documento_editavel_item:
                    resultado_trava = adquirir_trava_edicao(
                        empresa,
                        request.user,
                        "documento_clinico",
                        ultimo_documento_item.pk,
                        _titulo_trava_documento(ultimo_documento_item),
                    )
                    if not resultado_trava.permitido:
                        documento_editavel_item = False
                        pode_assumir_documento_item = False
                        documento_bloqueio_item = (
                            f"{resultado_trava.mensagem} O documento ficará somente para consulta até a liberação."
                        )
                elif pode_assumir_documento_item:
                    trava_ativa = consultar_trava_ativa(empresa, "documento_clinico", ultimo_documento_item.pk)
                    if trava_ativa and trava_ativa.cd_usuario_id != request.user.pk:
                        pode_assumir_documento_item = False
                        documento_bloqueio_item = (
                            f"Este documento está em edição por {nome_usuario_trava(trava_ativa.cd_usuario)}. "
                            "Não é possível assumir enquanto a trava estiver ativa."
                        )
            documento_modo_impressao_item = not documento_editavel_item
            apresentacao_documento_item = _renderizar_documento(ultimo_documento_item, documento_modo_impressao_item)
            pep_documento_next_url = (
                f"{reverse(pep_patient_route, args=[paciente.pk])}?"
                f"{urlencode({'modo': 'consulta' if somente_consulta else 'atendimento', 'atendimento': atendimento_selecionado.pk, 'item': item_selecionado.pk, 'documento': ultimo_documento_item.pk, 'return_to': return_to})}"
            )
    _marcar_ramo_menu_assistencial(menu_assistencial_raizes, item_selecionado)
    itens_por_id = {item.pk: item for item in itens_assistenciais}
    grupo_id = (request.GET.get("grupo") or "").strip()
    grupo_requisitado = itens_por_id.get(int(grupo_id)) if grupo_id.isdigit() else None
    if item_selecionado:
        grupo_telas = itens_por_id.get(item_selecionado.cd_item_pai_id)
        pep_telas_barra = [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO"
            and item.cd_item_pai_id == getattr(grupo_telas, "pk", None)
        ] if grupo_telas else [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO" and not item.cd_item_pai_id
        ]
        pep_grupo_tela_atual = grupo_telas
    else:
        pep_grupo_tela_atual = grupo_requisitado if getattr(grupo_requisitado, "tp_item", "") == "GRUPO" else None
        pep_telas_barra = [
            item for item in itens_assistenciais
            if item.tp_item != "GRUPO"
            and item.cd_item_pai_id == getattr(pep_grupo_tela_atual, "pk", None)
        ] if pep_grupo_tela_atual else []
        if pep_grupo_tela_atual:
            pep_grupo_tela_atual.tem_item_ativo = True
    _preparar_arvore_menu_assistencial(menu_assistencial_raizes, pep_grupo_tela_atual)
    historico_documentos_lista = list(historico_documentos_item[:30])
    travas_por_documento = {
        int(trava.ds_recurso_id): trava
        for trava in (
            consultar_trava_ativa(empresa, "documento_clinico", documento.pk)
            for documento in historico_documentos_lista
            if documento.ds_status in {"ABERTO", "RASCUNHO"}
        )
        if trava and str(trava.ds_recurso_id).isdigit()
    }
    for documento_historico in historico_documentos_lista:
        eventos_status = [
            evento for evento in documento_historico.eventos.all()
            if evento.tp_evento in {"ABANDONADO", "CANCELADO"}
        ]
        documento_historico.pep_evento_status = eventos_status[0] if eventos_status else None
        documento_historico.pep_status_inativo = documento_historico.ds_status in {"ABANDONADO", "CANCELADO"}
        trava_documento = travas_por_documento.get(documento_historico.pk)
        documento_historico.pep_travado_por_outro = bool(
            trava_documento and trava_documento.cd_usuario_id != request.user.pk
        )
        documento_historico.pep_trava_usuario = (
            nome_usuario_trava(trava_documento.cd_usuario)
            if documento_historico.pep_travado_por_outro
            else ""
        )
    if documento_bloqueio_item:
        messages.warning(request, documento_bloqueio_item)
    return render(
        request,
        "atendimento/pep_prontuario_paciente.html",
        {
            "pep_standalone": pep_standalone,
            "pep_base_template": "base/pep_layout.html" if pep_standalone else "base/layout.html",
            "pep_list_url": reverse(pep_list_route),
            "pep_patient_url": reverse(pep_patient_route, args=[paciente.pk]),
            "paciente": paciente,
            "idade": _idade(paciente.dt_nascimento),
            "atendimentos": atendimentos,
            "atendimento": atendimento_selecionado,
            "ultimos_sinais_vitais": ultimos_sinais_vitais,
            "historico_sinais_vitais": historico_sinais_vitais,
            "return_to": return_to,
            "can_clinical_actions": can_clinical_actions,
            "perfis_assistenciais": perfis_assistenciais,
            "menu_assistencial_raizes": menu_assistencial_raizes,
            "pep_telas_barra": pep_telas_barra,
            "pep_grupo_tela_atual": pep_grupo_tela_atual,
            "item_selecionado": item_selecionado,
            "ultimo_documento_item": ultimo_documento_item,
            "documento_aberto_item": documento_aberto_item,
            "documento_editavel_item": documento_editavel_item,
            "documento_modo_impressao_item": documento_modo_impressao_item,
            "pode_assumir_documento_item": pode_assumir_documento_item,
            "pode_cancelar_documento_item": pode_cancelar_documento_item,
            "pode_copiar_documento_item": pode_copiar_documento_item,
            "documento_bloqueio_item": documento_bloqueio_item,
            "apresentacao_documento_item": apresentacao_documento_item,
            "pep_documento_next_url": pep_documento_next_url,
            "historico_documentos_item": historico_documentos_lista,
            "agora_documento": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "atendimento_aberto": atendimento_selecionado and atendimento_selecionado.ds_status not in {
                "FINALIZADO", "ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "CANCELADO",
            },
            "somente_consulta": somente_consulta,
        },
    )


def _validar_prestador_pep_standalone(request):
    if getattr(request.user, "cd_prestador_id", None):
        return True
    messages.error(request, "O PEP exige um prestador vinculado ao usuário.")
    return False


def _view_sem_decoradores(view):
    while getattr(view, "__wrapped__", None):
        view = view.__wrapped__
    return view


@login_required
def pep_standalone(request):
    if not _validar_prestador_pep_standalone(request):
        return redirect("core:home")
    request.pep_standalone = True
    return _view_sem_decoradores(pep)(request)


@login_required
def pep_prontuario_paciente_standalone(request, cd_paciente):
    if not _validar_prestador_pep_standalone(request):
        return redirect("core:home")
    request.pep_standalone = True
    return _view_sem_decoradores(pep_prontuario_paciente)(request, cd_paciente)


@login_required
@role_required("TI", "Médico", "Enfermeiro")
def pep_chamar(request, cd_atendimento):
    empresa = _empresa_logada(request)
    atendimento = get_object_or_404(Atendimento, cd_empresa=empresa, cd_atendimento=cd_atendimento)
    setor = get_object_or_404(Setor, cd_empresa=empresa, pk=request.POST.get("setor"))
    maquina_nome = (
        request.POST.get("maquina")
        or request.COOKIES.get("celeris_maquina_chamada")
        or request.META.get("COMPUTERNAME")
        or ""
    ).strip()
    maquina = (
        MaquinaChamada.objects.select_related("cd_setor")
        .filter(cd_empresa=empresa, nm_maquina__iexact=maquina_nome, sn_ativo=True)
        .first()
        if maquina_nome
        else None
    )
    if maquina and maquina.cd_setor_id:
        setor = maquina.cd_setor
    destino = ""
    if maquina:
        tipo = maquina.get_tp_sala_display()
        destino = f"{tipo} {maquina.nr_sala}".strip() or maquina.nm_sala
    ChamadaPainel.objects.create(
        cd_empresa=empresa,
        cd_atendimento=atendimento,
        cd_setor=setor,
        ds_local=destino or f"{setor.nm_setor}",
        cd_usuario_criacao=request.user,
        cd_usuario_atualizacao=request.user,
    )
    messages.success(request, "Paciente enviado para o painel de chamada.")
    return redirect(f"{reverse('atendimento:pep')}?aba=atendimentos&todos_setores=0&setores={setor.pk}")


@login_required
@role_required("TI")
def paineis_chamada(request, cd_painel=None):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Painéis de chamada"
    request.current_tab_root_title = "Painéis de chamada"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    if request.GET.get("consultar") == "1":
        registros = PainelChamada.objects.filter(cd_empresa=empresa).prefetch_related("setores")
        codigo = request.GET.get("cd_painel_chamada", "").strip()
        if codigo.isdigit():
            registros = registros.filter(pk=int(codigo))
        for field_name in (
            "nm_painel", "ds_descricao", "nm_maquina", "nr_referencia",
            "ds_local_exibicao", "ds_mensagem_padrao", "ds_layout", "ds_tamanho",
            "ds_cor", "ds_prioridade_visual", "ds_midia_url", "ds_observacao",
        ):
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
        for field_name in ("tp_painel", "nr_tempo_exibicao"):
            value = request.GET.get(field_name, "").strip()
            if value:
                registros = registros.filter(**{field_name: value})
        for field_name in ("sn_ativo", "sn_voz"):
            value = request.GET.get(field_name, "")
            if value in {"True", "False", "on"}:
                registros = registros.filter(**{field_name: value in {"True", "on"}})
        setores = [value for value in request.GET.getlist("setores") if value.isdigit()]
        if setores:
            registros = registros.filter(setores__in=setores).distinct()
        result_ids = list(registros.order_by("cd_painel_chamada").values_list("pk", flat=True)[:200])
        request.session["consulta_paineis_chamada"] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum painel encontrado para os filtros informados.")
            return redirect("atendimento:paineis-chamada")
        return redirect("atendimento:cadastro-painel-chamada", cd_painel=result_ids[0])

    painel = (
        get_object_or_404(PainelChamada.objects.prefetch_related("setores"), cd_empresa=empresa, pk=cd_painel)
        if cd_painel
        else None
    )
    if painel:
        request.current_toggle_active_url = reverse("atendimento:alternar-status-painel-chamada", args=[painel.pk])
        request.current_toggle_active_label = "Desativar" if painel.sn_ativo else "Ativar"
    result_ids = request.session.get("consulta_paineis_chamada", [])
    if painel and painel.pk in result_ids:
        index = result_ids.index(painel.pk)
        request.current_record_status = f"Item {index + 1} de {len(result_ids)}"
        if index > 0:
            request.current_first_url = reverse("atendimento:cadastro-painel-chamada", args=[result_ids[0]])
            request.current_previous_url = reverse("atendimento:cadastro-painel-chamada", args=[result_ids[index - 1]])
        if index < len(result_ids) - 1:
            request.current_next_url = reverse("atendimento:cadastro-painel-chamada", args=[result_ids[index + 1]])
            request.current_last_url = reverse("atendimento:cadastro-painel-chamada", args=[result_ids[-1]])
    form = PainelChamadaForm(request.POST or None, instance=painel, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.cd_empresa = empresa
        _apply_audit(saved, request.user)
        saved.save()
        form.save_m2m()
        messages.success(request, "Painel de chamada salvo com sucesso.")
        return redirect("atendimento:cadastro-painel-chamada", cd_painel=saved.pk)
    return render(request, "atendimento/paineis_chamada.html", {"form": form, "painel": painel})


@login_required
@role_required("TI")
def alternar_status_painel_chamada(request, cd_painel):
    if request.method != "POST":
        raise PermissionDenied
    painel = get_object_or_404(PainelChamada, cd_empresa=_empresa_logada(request), pk=cd_painel)
    painel.sn_ativo = not painel.sn_ativo
    _apply_audit(painel, request.user)
    painel.save(update_fields=["sn_ativo", "dh_atualizacao", "cd_usuario_atualizacao"])
    messages.success(request, f"Painel {'ativado' if painel.sn_ativo else 'desativado'} com sucesso.")
    return redirect("atendimento:cadastro-painel-chamada", cd_painel=painel.pk)


def painel_chamada_publico(request):
    painel = None
    painel_id = request.GET.get("painel") or request.COOKIES.get("celeris_painel_chamada")
    if painel_id:
        painel = PainelChamada.objects.prefetch_related("setores").filter(pk=painel_id, sn_ativo=True).first()
    paineis = PainelChamada.objects.filter(sn_ativo=True).order_by("nm_painel")
    chamadas = ChamadaPainel.objects.none()
    if painel:
        chamadas = (
            ChamadaPainel.objects.select_related("cd_atendimento__cd_paciente", "cd_senha_atendimento", "cd_setor")
            .filter(cd_setor__in=painel.setores.all(), ds_status="CHAMADO")
            .order_by("-dh_chamada")[:8]
        )
    response = render(request, "atendimento/painel_chamada_publico.html", {"painel": painel, "paineis": paineis, "chamadas": chamadas})
    if painel:
        response.set_cookie("celeris_painel_chamada", str(painel.pk), max_age=60 * 60 * 24 * 365)
    return response


@login_required
@role_required("TI")
def configurar_senhas(request, cd_tipo=None):
    empresa = _empresa_logada(request)
    tipo = (
        get_object_or_404(TipoSenhaAtendimento, cd_empresa=empresa, pk=cd_tipo)
        if cd_tipo
        else None
    )
    request.current_tab_title = "Painéis de Chamada > Configurar"
    request.current_tab_root_title = "Configurar senhas"
    request.current_module_title = "Painéis de Chamada"
    request.current_can_query = True
    request.current_can_remove = False
    request.current_start_query = not bool(tipo or request.GET.get("consultar"))
    if tipo:
        request.current_toggle_active_url = reverse("atendimento:alternar-status-configuracao-senha", args=[tipo.pk])
        request.current_toggle_active_label = "Desativar" if tipo.sn_ativo else "Ativar"
    if request.GET.get("consultar") == "1":
        registros = TipoSenhaAtendimento.objects.filter(cd_empresa=empresa)
        filtros = {
            "nm_tipo_senha": "nm_tipo_senha__icontains",
            "sg_tipo_senha": "sg_tipo_senha__icontains",
            "cd_protocolo": "cd_protocolo_id",
            "cd_setor_atendimento": "cd_setor_atendimento_id",
            "nr_tempo_minimo": "nr_tempo_minimo",
            "nr_prioridade": "nr_prioridade",
        }
        for campo, lookup in filtros.items():
            valor = request.GET.get(campo, "").strip()
            if valor:
                registros = registros.filter(**{lookup: valor.replace("%", "")})
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
        ids = list(registros.order_by("cd_tipo_senha").values_list("pk", flat=True)[:200])
        request.session["consulta_tipos_senha"] = ids
        if not ids:
            messages.warning(request, "Nenhum tipo de senha encontrado.")
            return redirect("atendimento:configurar-senhas")
        return redirect("atendimento:editar-configuracao-senha", cd_tipo=ids[0])
    ids = request.session.get("consulta_tipos_senha", [])
    if tipo and tipo.pk in ids:
        indice = ids.index(tipo.pk)
        request.current_record_status = f"Item {indice + 1} de {len(ids)}"
        if indice:
            request.current_first_url = reverse("atendimento:editar-configuracao-senha", args=[ids[0]])
            request.current_previous_url = reverse("atendimento:editar-configuracao-senha", args=[ids[indice - 1]])
        if indice < len(ids) - 1:
            request.current_next_url = reverse("atendimento:editar-configuracao-senha", args=[ids[indice + 1]])
            request.current_last_url = reverse("atendimento:editar-configuracao-senha", args=[ids[-1]])
    dados_form = request.POST.copy() if request.method == "POST" else None
    if dados_form is not None and not dados_form.get("nr_prioridade") and dados_form.get("nr_prioridade_tipo"):
        dados_form["nr_prioridade"] = dados_form["nr_prioridade_tipo"]
    form = TipoSenhaAtendimentoForm(dados_form, instance=tipo, empresa=empresa)
    regra_form = RegraSubdivisaoSenhaForm(dados_form, empresa=empresa, prefix="regra")
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            saved = form.save(commit=False)
            saved.cd_empresa = empresa
            if saved.cd_protocolo_id:
                saved.ds_protocolo = saved.cd_protocolo.ds_protocolo
            elif request.POST.get("ds_protocolo"):
                saved.ds_protocolo = request.POST["ds_protocolo"].strip()
            _apply_audit(saved, request.user)
            saved.save()
            for regra in list(saved.regras_subdivisao.all()):
                if request.POST.get(f"excluir_regra_{regra.pk}") == "1":
                    regra.delete()
            if regra_form.is_valid() and regra_form.cleaned_data.get("cd_classe_senha"):
                regra, _ = RegraSubdivisaoSenha.objects.update_or_create(
                    cd_tipo_senha=saved,
                    cd_classe_senha=regra_form.cleaned_data["cd_classe_senha"],
                    defaults={
                        "cd_empresa": empresa,
                        "nr_prioridade": regra_form.cleaned_data["nr_prioridade"],
                        "nr_idade_minima": regra_form.cleaned_data["nr_idade_minima"],
                        "nr_idade_maxima": regra_form.cleaned_data["nr_idade_maxima"],
                        "ds_icone": regra_form.cleaned_data["ds_icone"],
                        "sn_ativo": True,
                        "cd_usuario_atualizacao": request.user,
                    },
                )
                if not regra.cd_usuario_criacao_id:
                    regra.cd_usuario_criacao = request.user
                    regra.save(update_fields=["cd_usuario_criacao"])
            elif request.POST.get("nm_classe_senha", "").strip():
                classe, _ = ClasseSenhaAtendimento.objects.update_or_create(
                    cd_empresa=empresa,
                    cd_tipo_senha=saved,
                    sg_classe_senha=re.sub(
                        r"[^A-Z0-9]",
                        "",
                        request.POST.get("sg_classe_senha", "").upper(),
                    )[:4],
                    defaults={
                        "nm_classe_senha": request.POST["nm_classe_senha"].strip(),
                        "nr_prioridade": max(int(request.POST.get("nr_prioridade_classe") or saved.nr_prioridade), 1),
                        "nr_idade_minima": request.POST.get("nr_idade_minima") or None,
                        "nr_idade_maxima": request.POST.get("nr_idade_maxima") or None,
                        "sn_ativo": True,
                        "cd_usuario_atualizacao": request.user,
                    },
                )
                RegraSubdivisaoSenha.objects.update_or_create(
                    cd_empresa=empresa,
                    cd_tipo_senha=saved,
                    cd_classe_senha=classe,
                    defaults={
                        "nr_prioridade": classe.nr_prioridade,
                        "nr_idade_minima": classe.nr_idade_minima,
                        "nr_idade_maxima": classe.nr_idade_maxima,
                        "sn_ativo": True,
                        "cd_usuario_atualizacao": request.user,
                    },
                )
        messages.success(request, "Configuração da senha salva.")
        return redirect("atendimento:editar-configuracao-senha", cd_tipo=saved.pk)
    return render(
        request,
        "atendimento/configurar_senhas.html",
        {
            "form": form,
            "regra_form": regra_form,
            "tipo": tipo,
            "regras": tipo.regras_subdivisao.select_related("cd_classe_senha").all() if tipo else [],
        },
    )


@login_required
@role_required("TI")
def alternar_status_configuracao_senha(request, cd_tipo):
    if request.method != "POST":
        raise PermissionDenied
    tipo = get_object_or_404(
        TipoSenhaAtendimento,
        cd_empresa=_empresa_logada(request),
        pk=cd_tipo,
    )
    tipo.sn_ativo = not tipo.sn_ativo
    _apply_audit(tipo, request.user)
    tipo.save(update_fields=["sn_ativo", "cd_usuario_atualizacao", "dh_atualizacao"])
    messages.success(request, f"Tipo de senha {'ativado' if tipo.sn_ativo else 'desativado'}.")
    return redirect("atendimento:editar-configuracao-senha", cd_tipo=tipo.pk)


def _tabela_totem(request, *, modelo, titulo, template):
    empresa = _empresa_logada(request)
    request.current_tab_title = f"Painéis de Chamada > Tabelas > {titulo}"
    request.current_tab_root_title = titulo
    request.current_module_title = "Painéis de Chamada"
    request.current_can_query = True
    request.current_can_remove = True
    request.current_start_query = request.GET.get("consultar") != "1"
    if request.method == "POST":
        with transaction.atomic():
            for item in modelo.objects.filter(cd_empresa=empresa):
                if request.POST.get(f"delete_{item.pk}") == "1":
                    try:
                        item.delete()
                    except ProtectedError:
                        messages.error(request, f"{item} está em uso e não pode ser excluído.")
                    continue
                if f"name_{item.pk}" not in request.POST:
                    continue
                if modelo is ClasseSenhaAtendimento:
                    item.nm_classe_senha = request.POST.get(f"name_{item.pk}", "").strip()
                    item.sg_classe_senha = request.POST.get(f"acronym_{item.pk}", "").strip().upper()
                    item.nr_prioridade = max(1, int(request.POST.get(f"priority_{item.pk}") or 5))
                    icon_id = request.POST.get(f"icon_{item.pk}", "").strip()
                    item.cd_icone_chamada_id = int(icon_id) if icon_id.isdigit() else None
                else:
                    item.nm_protocolo = request.POST.get(f"name_{item.pk}", "").strip()
                    item.ds_protocolo = request.POST.get(f"description_{item.pk}", "").strip()
                item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
                _apply_audit(item, request.user)
                item.save()

            new_names = request.POST.getlist("new_name")
            new_active = request.POST.getlist("new_active")
            if modelo is ClasseSenhaAtendimento:
                new_acronyms = request.POST.getlist("new_acronym")
                new_priorities = request.POST.getlist("new_priority")
                new_icons = request.POST.getlist("new_icon")
                for index, name in enumerate(new_names):
                    if not name.strip():
                        continue
                    icon_id = (new_icons[index] if index < len(new_icons) else "").strip()
                    item = modelo(
                        cd_empresa=empresa,
                        nm_classe_senha=name.strip(),
                        sg_classe_senha=(new_acronyms[index] if index < len(new_acronyms) else "").strip().upper(),
                        nr_prioridade=max(1, int(new_priorities[index] or 5)) if index < len(new_priorities) else 5,
                        cd_icone_chamada_id=int(icon_id) if icon_id.isdigit() else None,
                        sn_ativo=index >= len(new_active) or new_active[index] == "true",
                    )
                    _apply_audit(item, request.user)
                    item.save()
            else:
                new_descriptions = request.POST.getlist("new_description")
                for index, name in enumerate(new_names):
                    if not name.strip():
                        continue
                    item = modelo(
                        cd_empresa=empresa,
                        nm_protocolo=name.strip(),
                        ds_protocolo=(new_descriptions[index] if index < len(new_descriptions) else "").strip(),
                        sn_ativo=index >= len(new_active) or new_active[index] == "true",
                    )
                    _apply_audit(item, request.user)
                    item.save()
        messages.success(request, f"{titulo} salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")

    registros = modelo.objects.filter(cd_empresa=empresa)
    query = request.GET.get("q", "").strip().replace("%", "")
    if query:
        if modelo is ClasseSenhaAtendimento:
            registros = registros.filter(
                Q(nm_classe_senha__icontains=query)
                | Q(sg_classe_senha__icontains=query)
                | Q(ds_icone__icontains=query)
                | Q(cd_icone_chamada__nm_icone__icontains=query)
            )
        else:
            registros = registros.filter(Q(nm_protocolo__icontains=query) | Q(ds_protocolo__icontains=query))
    if modelo is ClasseSenhaAtendimento:
        registros = registros.select_related("cd_icone_chamada")
        allowed_ordering = {
            "cd_classe_senha",
            "nm_classe_senha",
            "sg_classe_senha",
            "nr_prioridade",
            "ds_icone",
            "cd_icone_chamada",
            "sn_ativo",
        }
        default_ordering = "cd_classe_senha"
    else:
        allowed_ordering = {"cd_protocolo_senha", "nm_protocolo", "ds_protocolo", "sn_ativo"}
        default_ordering = "cd_protocolo_senha"
    registros = paginate_table(request, registros, allowed_ordering, default_ordering)
    contexto = {"registros": registros, "titulo": titulo}
    if modelo is ClasseSenhaAtendimento:
        contexto["icones"] = IconeChamada.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_icone")
    return render(request, template, contexto)


@login_required
@role_required("TI")
def classes_senha(request):
    return _tabela_totem(
        request,
        modelo=ClasseSenhaAtendimento,
        titulo="Classes",
        template="atendimento/tabela_classes_senha.html",
    )


@login_required
@role_required("TI")
def protocolos_senha(request):
    return _tabela_totem(
        request,
        modelo=ProtocoloSenhaAtendimento,
        titulo="Protocolos",
        template="atendimento/tabela_protocolos_senha.html",
    )


@login_required
@role_required("TI")
def icones_chamada(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Painéis de Chamada > Tabelas > Ícones"
    request.current_tab_root_title = "Ícones"
    request.current_module_title = "Painéis de Chamada"
    request.current_can_query = True
    request.current_can_remove = True
    request.current_start_query = request.GET.get("consultar") != "1"
    if request.method == "POST":
        with transaction.atomic():
            for item in IconeChamada.objects.filter(cd_empresa=empresa):
                if request.POST.get(f"delete_{item.pk}") == "1":
                    item.delete()
                    continue
                if f"name_{item.pk}" not in request.POST:
                    continue
                item.nm_icone = request.POST.get(f"name_{item.pk}", "").strip()
                item.ds_svg = request.POST.get(f"svg_{item.pk}", "").strip()
                item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
                _apply_audit(item, request.user)
                item.save()
            new_names = request.POST.getlist("new_name")
            new_svgs = request.POST.getlist("new_svg")
            new_active = request.POST.getlist("new_active")
            for index, name in enumerate(new_names):
                if not name.strip():
                    continue
                item = IconeChamada(
                    cd_empresa=empresa,
                    nm_icone=name.strip(),
                    ds_svg=(new_svgs[index] if index < len(new_svgs) else "").strip(),
                    sn_ativo=index >= len(new_active) or new_active[index] == "true",
                )
                _apply_audit(item, request.user)
                item.save()
        messages.success(request, "Ícones salvos com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    registros = IconeChamada.objects.filter(cd_empresa=empresa)
    query = request.GET.get("q", "").strip().replace("%", "")
    if query:
        registros = registros.filter(Q(nm_icone__icontains=query) | Q(ds_svg__icontains=query))
    registros = paginate_table(
        request,
        registros,
        {"cd_icone_chamada", "nm_icone", "sn_ativo"},
        "cd_icone_chamada",
    )
    return render(request, "atendimento/tabela_icones_chamada.html", {"registros": registros})


@login_required
@role_required("TI")
def maquinas_chamada(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Painéis de Chamada > Tabelas > Máquinas"
    request.current_tab_root_title = "Máquinas"
    request.current_module_title = "Painéis de Chamada"
    request.current_can_query = True
    request.current_can_remove = True
    request.current_start_query = request.GET.get("consultar") != "1"
    if request.method == "POST":
        with transaction.atomic():
            for item in MaquinaChamada.objects.filter(cd_empresa=empresa):
                if request.POST.get(f"delete_{item.pk}") == "1":
                    item.delete()
                    continue
                if f"machine_{item.pk}" not in request.POST:
                    continue
                setor_id = request.POST.get(f"sector_{item.pk}", "").strip()
                item.nm_maquina = request.POST.get(f"machine_{item.pk}", "").strip().upper()
                item.cd_setor_id = int(setor_id) if setor_id.isdigit() else None
                item.nm_sala = request.POST.get(f"room_name_{item.pk}", "").strip()
                item.tp_sala = request.POST.get(f"room_type_{item.pk}", "CONSULTORIO")
                item.nr_sala = request.POST.get(f"room_number_{item.pk}", "").strip()
                item.sn_ativo = request.POST.get(f"active_{item.pk}") == "true"
                _apply_audit(item, request.user)
                item.save()
            new_machines = request.POST.getlist("new_machine")
            new_sectors = request.POST.getlist("new_sector")
            new_room_names = request.POST.getlist("new_room_name")
            new_room_types = request.POST.getlist("new_room_type")
            new_room_numbers = request.POST.getlist("new_room_number")
            new_active = request.POST.getlist("new_active")
            for index, machine in enumerate(new_machines):
                if not machine.strip():
                    continue
                setor_id = (new_sectors[index] if index < len(new_sectors) else "").strip()
                item = MaquinaChamada(
                    cd_empresa=empresa,
                    nm_maquina=machine.strip().upper(),
                    cd_setor_id=int(setor_id) if setor_id.isdigit() else None,
                    nm_sala=(new_room_names[index] if index < len(new_room_names) else "").strip(),
                    tp_sala=(new_room_types[index] if index < len(new_room_types) else "CONSULTORIO") or "CONSULTORIO",
                    nr_sala=(new_room_numbers[index] if index < len(new_room_numbers) else "").strip(),
                    sn_ativo=index >= len(new_active) or new_active[index] == "true",
                )
                _apply_audit(item, request.user)
                item.save()
        messages.success(request, "Máquinas salvas com sucesso.")
        return redirect(f"{request.path}?consultar=1")
    registros = MaquinaChamada.objects.select_related("cd_setor").filter(cd_empresa=empresa)
    query = request.GET.get("q", "").strip().replace("%", "")
    if query:
        registros = registros.filter(
            Q(nm_maquina__icontains=query)
            | Q(nm_sala__icontains=query)
            | Q(nr_sala__icontains=query)
            | Q(cd_setor__nm_setor__icontains=query)
        )
    registros = paginate_table(
        request,
        registros,
        {"cd_maquina_chamada", "nm_maquina", "nm_sala", "tp_sala", "nr_sala", "sn_ativo"},
        "cd_maquina_chamada",
    )
    setores = Setor.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_setor")
    return render(
        request,
        "atendimento/tabela_maquinas_chamada.html",
        {"registros": registros, "setores": setores, "tipos_sala": MaquinaChamada.TIPOS_SALA},
    )


@login_required
@role_required("TI", "Recepcionista")
def gerar_senha_totem(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Totem > Gerar senha"
    request.current_tab_root_title = "Gerar senha"
    request.current_module_title = "Totem"
    senha_gerada = None
    if request.method == "POST":
        regra = None
        if request.POST.get("regra", "").isdigit():
            regra = get_object_or_404(
                RegraSubdivisaoSenha.objects.select_related("cd_tipo_senha", "cd_classe_senha"),
                cd_empresa=empresa,
                sn_ativo=True,
                cd_tipo_senha__sn_ativo=True,
                cd_classe_senha__sn_ativo=True,
                pk=request.POST["regra"],
            )
            classe = regra.cd_classe_senha
            tipo = regra.cd_tipo_senha
            prioridade = regra.nr_prioridade
        else:
            classe = get_object_or_404(
                ClasseSenhaAtendimento.objects.select_related("cd_tipo_senha"),
                cd_empresa=empresa,
                sn_ativo=True,
                cd_tipo_senha__sn_ativo=True,
                pk=request.POST.get("classe"),
            )
            tipo = classe.cd_tipo_senha
            prioridade = classe.nr_prioridade
        hoje = timezone.localdate()
        prefixo = f"{tipo.sg_tipo_senha}{classe.sg_classe_senha}"
        with transaction.atomic():
            usados = set(
                SenhaAtendimento.objects.select_for_update()
                .filter(cd_empresa=empresa, dt_senha=hoje, ds_senha__startswith=prefixo)
                .values_list("nr_senha", flat=True)
            )
            disponiveis = [numero for numero in range(1, 100) if numero not in usados]
            numero = random.SystemRandom().choice(disponiveis) if disponiveis else (max(usados, default=99) + 1)
            senha_gerada = SenhaAtendimento.objects.create(
                cd_empresa=empresa,
                cd_tipo_senha=tipo,
                cd_classe_senha=classe,
                nr_senha=numero,
                ds_senha=f"{prefixo} {numero:02d}",
                nr_prioridade=prioridade,
                nr_tempo_limite=tipo.nr_tempo_minimo,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
    classes = ClasseSenhaAtendimento.objects.select_related("cd_tipo_senha", "cd_icone_chamada").filter(
        cd_empresa=empresa,
        sn_ativo=True,
        cd_tipo_senha__sn_ativo=True,
        regras_subdivisao__isnull=True,
    )
    regras = RegraSubdivisaoSenha.objects.select_related("cd_tipo_senha", "cd_classe_senha", "cd_classe_senha__cd_icone_chamada").filter(
        cd_empresa=empresa,
        sn_ativo=True,
        cd_tipo_senha__sn_ativo=True,
        cd_classe_senha__sn_ativo=True,
    )
    historico = SenhaAtendimento.objects.filter(cd_empresa=empresa, dt_senha=timezone.localdate()).order_by("-dh_criacao")[:10]
    return render(
        request,
        "atendimento/gerar_senha_totem.html",
        {
            "classes": classes,
            "regras": regras,
            "historico": historico,
            "senha_gerada": senha_gerada,
            "empresa": empresa,
        },
    )


@login_required
@role_required("TI", "Recepcionista", "Enfermeiro")
@xframe_options_sameorigin
def imprimir_senha_totem(request, cd_senha):
    senha = get_object_or_404(
        SenhaAtendimento.objects.select_related("cd_empresa", "cd_tipo_senha", "cd_classe_senha"),
        cd_empresa=_empresa_logada(request),
        pk=cd_senha,
    )
    return render(request, "atendimento/imprimir_senha_totem.html", {"senha": senha})


@login_required
@role_required("Enfermeiro")
def acao_senha_classificacao(request, cd_senha, acao):
    if request.method != "POST":
        raise PermissionDenied
    senha = get_object_or_404(SenhaAtendimento, cd_empresa=_empresa_logada(request), pk=cd_senha)
    agora = timezone.now()
    if acao == "chamar":
        senha.ds_status = "CHAMADA"
        senha.dh_chamada = agora
        setor = senha.cd_tipo_senha.cd_setor_atendimento
        if setor:
            ChamadaPainel.objects.create(
                cd_empresa=senha.cd_empresa,
                cd_senha_atendimento=senha,
                cd_setor=setor,
                ds_local=setor.nm_setor,
                cd_usuario_criacao=request.user,
                cd_usuario_atualizacao=request.user,
            )
    elif acao == "receber":
        senha.ds_status = "EM_CLASSIFICACAO"
        senha.dh_recepcao = agora
    elif acao == "classificar":
        senha.ds_status = "CLASSIFICADA"
        senha.dh_classificacao = agora
    else:
        raise PermissionDenied
    _apply_audit(senha, request.user)
    senha.save()
    return redirect("atendimento:fila-classificacao")


@login_required
@role_required("Enfermeiro")
def fila_classificacao(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Classificação de Risco"
    request.current_tab_root_title = "Classificação de Risco"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_agendamento").filter(
        cd_empresa=empresa,
        ds_status="AGUARDANDO_CLASSIFICACAO",
    ).order_by("dh_inicio")
    senhas = SenhaAtendimento.objects.select_related("cd_tipo_senha", "cd_classe_senha").filter(
        cd_empresa=empresa,
        dt_senha=timezone.localdate(),
        ds_status__in={"AGUARDANDO", "CHAMADA", "EM_CLASSIFICACAO"},
    )
    return render(request, "atendimento/fila_classificacao.html", {"registros": registros, "senhas": senhas})


@login_required
@role_required("Médico")
def fila_medica(request):
    empresa = _empresa_logada(request)
    request.current_tab_title = "Atendimento > Consultas Médicas"
    request.current_tab_root_title = "Consultas Médicas"
    request.current_module_title = "Atendimento"
    registros = Atendimento.objects.select_related("cd_paciente", "cd_pre_atendimento", "cd_prestador").filter(
        cd_empresa=empresa,
        ds_status__in=["AGUARDANDO_CONSULTA", "EM_ATENDIMENTO", "ALTA"],
    ).order_by("cd_pre_atendimento__nr_prioridade", "dh_inicio")
    return render(request, "atendimento/fila_medica.html", {"registros": registros})


@login_required
@role_required("Médico")
def abrir_consulta(request, cd_atendimento):
    atendimento = get_object_or_404(Atendimento, cd_empresa=_empresa_logada(request), cd_atendimento=cd_atendimento)
    if atendimento.ds_status == "AGUARDANDO_CONSULTA":
        _mudar_status_atendimento(atendimento, "EM_ATENDIMENTO", request.user, origem="consulta_medica")
        _vincular_prestador_atendimento(atendimento, atendimento.cd_prestador, request.user, principal=True)
    return redirect("atendimento:ficha-atendimento", cd_atendimento=atendimento.pk)


@login_required
@role_required("TI", "Recepcionista")
def gerar_agenda(request):
    request.current_tab_title = "Atendimento > Agendamento > Geração de agendas"
    request.current_tab_root_title = "Geração de agendas"
    request.current_module_title = "Atendimento"
    request.current_can_query = True
    empresa = _empresa_logada(request)
    data_inicio = request.POST.get("data_inicio") or request.GET.get("data_inicio") or timezone.localdate().isoformat()
    data_fim = request.POST.get("data_fim") or request.GET.get("data_fim") or ""
    try:
        inicio = datetime.fromisoformat(data_inicio).date()
        fim = datetime.fromisoformat(data_fim).date() if data_fim else None
    except ValueError:
        inicio = timezone.localdate()
        fim = None
    if request.method == "POST":
        acao = request.POST.get("acao", "gerar")
        if acao in {"cancelar", "excluir"}:
            agenda_gerada = get_object_or_404(AgendaGerada, cd_empresa=empresa, pk=request.POST.get("agenda_gerada"))
            agendamentos_ativos = Agendamento.objects.filter(
                cd_empresa=empresa,
                cd_horario_agenda__cd_agenda_gerada=agenda_gerada,
            ).exclude(ds_status="CANCELADO")
            if acao == "excluir":
                if Agendamento.objects.filter(cd_horario_agenda__cd_agenda_gerada=agenda_gerada).exists():
                    messages.error(request, "A agenda possui histórico de agendamento e não pode ser excluída. Cancele os horários disponíveis.")
                else:
                    agenda_gerada.delete()
                    messages.success(request, "Agenda gerada excluída.")
            else:
                horarios_ocupados = set(agendamentos_ativos.values_list("cd_horario_agenda_id", flat=True))
                cancelados = agenda_gerada.horarios.exclude(pk__in=horarios_ocupados).exclude(ds_status="CANCELADO")
                total_cancelado = cancelados.update(ds_status="CANCELADO", ds_motivo_cancelamento="Cancelamento da agenda")
                restantes = agenda_gerada.horarios.exclude(ds_status="CANCELADO").exists()
                agenda_gerada.ds_status = "PARCIAL" if restantes else "CANCELADA"
                _apply_audit(agenda_gerada, request.user)
                agenda_gerada.save(update_fields=["ds_status", "dh_atualizacao", "cd_usuario_atualizacao"])
                if restantes:
                    messages.warning(request, f"{total_cancelado} horário(s) cancelado(s). Horários com pacientes agendados foram preservados.")
                else:
                    messages.success(request, "Agenda e horários cancelados.")
            return redirect("atendimento:gerar-agenda")

        escala = get_object_or_404(
            AgendaProfissional.objects.select_related("cd_prestador"),
            cd_empresa=empresa,
            sn_ativo=True,
            pk=request.POST.get("escala"),
        )
        if not fim:
            messages.error(request, "Informe a data final do período.")
            return redirect("atendimento:gerar-agenda")
        if fim < inicio:
            messages.error(request, "A data final deve ser igual ou posterior à data inicial.")
            return redirect("atendimento:gerar-agenda")
        conflito = HorarioAgenda.objects.filter(
            cd_empresa=empresa,
            cd_prestador=escala.cd_prestador,
            dh_inicio__date__gte=inicio,
            dh_inicio__date__lte=fim,
        ).exclude(ds_status="CANCELADO")
        if conflito.exists():
            primeiro = conflito.order_by("dh_inicio").first()
            messages.error(
                request,
                f"Já existem horários gerados para {escala.cd_prestador.nm_prestador} no período. Primeiro conflito: {timezone.localtime(primeiro.dh_inicio):%d/%m/%Y %H:%M}.",
            )
            return redirect("atendimento:gerar-agenda")

        feriados = _feriados()
        datas_ignoradas = []
        horarios_criar = []
        data_atual = inicio
        while data_atual <= fim:
            if data_atual.weekday() in escala.dias_semana:
                if data_atual in feriados and not escala.sn_atende_feriado:
                    datas_ignoradas.append(data_atual)
                else:
                    atual = datetime.combine(data_atual, escala.hr_inicio)
                    fim_horario = datetime.combine(data_atual, escala.hr_fim)
                    duracao = timedelta(minutes=escala.nr_tempo_atendimento)
                    passo = timedelta(minutes=escala.nr_tempo_atendimento + escala.nr_intervalo)
                    quantidade_dia = 0
                    while atual + duracao <= fim_horario and quantidade_dia < escala.qt_horarios_dia:
                        horarios_criar.append((timezone.make_aware(atual), timezone.make_aware(atual + duracao)))
                        quantidade_dia += 1
                        atual += passo
            data_atual += timedelta(days=1)
        for feriado in datas_ignoradas:
            messages.warning(request, f"{feriado:%d/%m/%Y} não teve horários gerados porque é feriado e a escala não atende feriados.")
        if not horarios_criar:
            messages.error(request, "Nenhum horário foi gerado. Revise os dias da semana, horários e feriados da escala.")
            return redirect("atendimento:gerar-agenda")
        with transaction.atomic():
            agenda_gerada = AgendaGerada(
                cd_empresa=empresa,
                cd_escala=escala,
                dt_inicio=inicio,
                dt_fim=fim,
                ds_observacao=request.POST.get("observacao", ""),
            )
            _apply_audit(agenda_gerada, request.user)
            agenda_gerada.save()
            HorarioAgenda.objects.bulk_create(
                [
                    HorarioAgenda(
                        cd_empresa=empresa,
                        cd_agenda_gerada=agenda_gerada,
                        cd_escala=escala,
                        cd_prestador=escala.cd_prestador,
                        dh_inicio=dh_inicio,
                        dh_fim=dh_fim,
                        cd_usuario_criacao=request.user,
                        cd_usuario_atualizacao=request.user,
                    )
                    for dh_inicio, dh_fim in horarios_criar
                ]
            )
        messages.success(request, f"Agenda gerada com {len(horarios_criar)} horário(s).")
        return redirect("atendimento:gerar-agenda")

    escalas = AgendaProfissional.objects.select_related("cd_prestador").filter(cd_empresa=empresa, sn_ativo=True).order_by("cd_prestador__nm_prestador", "ds_agenda")
    agendas_geradas = (
        AgendaGerada.objects.select_related("cd_escala__cd_prestador")
        .filter(cd_empresa=empresa)
        .prefetch_related(
            "horarios",
            Prefetch("horarios__agendamentos", queryset=Agendamento.objects.select_related("cd_paciente")),
        )[:100]
    )
    return render(
        request,
        "atendimento/gerar_agenda.html",
        {
            "data_inicio": inicio,
            "data_fim": fim,
            "escalas": escalas,
            "agendas_geradas": agendas_geradas,
        },
    )

def _empresa_logada(request):
    cd_empresa = request.session.get("cd_empresa") or 1
    return get_object_or_404(Empresa, cd_empresa=cd_empresa, sn_ativo=True)


@login_required
@role_required("Recepcionista")
def agendar_consultar_paciente(request):
    request.current_tab_title = "Atendimento > Agendamento > Agendar"
    request.current_module_title = "Atendimento"
    request.current_start_query = not bool(request.GET)
    empresa = _empresa_logada(request)
    form = PacienteSearchForm(request.GET or None)
    pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True).none()
    if request.GET and form.is_valid():
        cd_paciente = form.cleaned_data.get("cd_paciente")
        termo = form.cleaned_data.get("termo") or ""
        nr_cpf = form.cleaned_data.get("nr_cpf") or ""
        nr_cartao_sus = form.cleaned_data.get("nr_cartao_sus") or ""
        dt_nascimento = form.cleaned_data.get("dt_nascimento")
        nm_mae = form.cleaned_data.get("nm_mae") or ""
        pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
        if cd_paciente:
            pacientes = pacientes.filter(cd_paciente=cd_paciente)
        if termo:
            termo_like = termo.replace("%", "")
            pacientes = pacientes.filter(
                Q(nm_paciente__icontains=termo_like)
                | Q(nm_social__icontains=termo_like)
                | Q(nm_mae__icontains=termo_like)
                | Q(nr_celular__icontains=termo_like)
            )
        if nr_cpf:
            pacientes = pacientes.filter(nr_cpf__icontains=nr_cpf.replace("%", ""))
        if nr_cartao_sus:
            pacientes = pacientes.filter(nr_cartao_sus__icontains=nr_cartao_sus.replace("%", ""))
        if dt_nascimento:
            pacientes = pacientes.filter(dt_nascimento=dt_nascimento)
        if nm_mae:
            pacientes = pacientes.filter(nm_mae__icontains=nm_mae.replace("%", ""))
        if pacientes.count() > 30:
            messages.warning(request, "Muitos pacientes encontrados. Refine a busca com CPF, prontuário ou mais dados do paciente.")
    return render(request, "atendimento/agendar_consulta_paciente.html", {"form": form, "pacientes": pacientes})


@login_required
@role_required("Recepcionista")
def cadastro_paciente(request, cd_paciente=None, fluxo_agendamento=True):
    request.current_tab_title = (
        "Atendimento > Agendamento > Agendar > Cadastro de paciente"
        if fluxo_agendamento
        else "Pacientes > Cadastro de paciente"
    )
    request.current_module_title = "Atendimento" if fluxo_agendamento else "Pacientes"
    request.current_tab_root_title = "Cadastro de paciente"
    empresa = _empresa_logada(request)
    recepcao_direta = request.GET.get("recepcao_direta") == "1"
    senha_recepcao_id = request.GET.get("senha", "")
    if recepcao_direta:
        request.current_tab_title = "Atendimento > Recepção > Validar paciente"
        request.current_module_title = "Atendimento"
        request.current_return_url = _safe_return_url(request) or reverse("atendimento:recepcao")
    agendamento_recepcao = None
    agendamento_recepcao_id = request.GET.get("recepcionar", "").strip()
    if agendamento_recepcao_id.isdigit():
        agendamento_recepcao = get_object_or_404(
            Agendamento,
            cd_empresa=empresa,
            cd_paciente_id=cd_paciente,
            pk=int(agendamento_recepcao_id),
        )
        request.current_tab_title = "Atendimento > Agendamentos > Revisar paciente"
        request.current_return_url = _safe_return_url(request)
    if request.GET.get("consultar") == "1":
        registros = Paciente.objects.filter(cd_empresa=empresa)
        has_filter = False
        patient_code = request.GET.get("cd_paciente", "").strip()
        if patient_code.isdigit():
            registros = registros.filter(cd_paciente=int(patient_code))
            has_filter = True
        text_fields = (
            "nm_paciente", "nm_social", "nr_cpf", "nr_rg", "ds_orgao_emissor",
            "nr_cartao_sus", "nr_convenio", "nm_mae", "nm_pai", "nm_conjuge",
            "nr_telefone", "nr_celular", "nr_celular_2", "ds_email",
            "ds_endereco", "nr_endereco", "ds_complemento", "ds_bairro",
        )
        exact_fields = (
            "tp_sexo", "tp_genero", "ds_cor_raca", "tp_estado_civil", "tp_sanguineo",
            "ds_nacionalidade", "ds_naturalidade", "ds_profissao", "sg_estado",
            "ds_cidade", "tp_logradouro",
        )
        for field_name in text_fields:
            value = request.GET.get(field_name, "").strip().replace("%", "")
            if value:
                registros = registros.filter(**{f"{field_name}__icontains": value})
                has_filter = True
        for field_name in exact_fields:
            value = request.GET.get(field_name, "").strip()
            if value:
                registros = registros.filter(**{field_name: value})
                has_filter = True
        convenio = request.GET.get("cd_convenio", "")
        if convenio.isdigit():
            registros = registros.filter(cd_convenio_id=int(convenio))
            has_filter = True
        if request.GET.get("dt_nascimento"):
            registros = registros.filter(dt_nascimento=request.GET["dt_nascimento"])
            has_filter = True
        status = request.GET.get("sn_ativo", "")
        if status in {"True", "False"}:
            registros = registros.filter(sn_ativo=status == "True")
            has_filter = True
        if request.GET.get("cd_cep", "").isdigit():
            registros = registros.filter(cd_cep_id=int(request.GET["cd_cep"]))
            has_filter = True
        result_ids = list(registros.order_by("cd_paciente").values_list("cd_paciente", flat=True)[:200])
        request.session["consulta_pacientes"] = result_ids
        if not result_ids:
            messages.warning(request, "Nenhum paciente encontrado para os filtros informados.")
            return redirect(request.path)
        target = "atendimento:revisar-paciente-agendamento" if fluxo_agendamento else "atendimento:cadastro-paciente"
        return redirect(f"{reverse(target, args=[result_ids[0]])}?origem=consulta")
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente) if cd_paciente else None
    if paciente and getattr(paciente, "sn_obito", False) and request.method == "GET":
        messages.warning(request, "Paciente consta como óbito no prontuário. A edição cadastral é permitida apenas para correção/atualização dos dados.")
    if paciente and not fluxo_agendamento and request.user.groups.filter(name="TI").exists():
        request.current_toggle_active_url = reverse("atendimento:alternar-status-paciente", args=[paciente.pk])
        request.current_toggle_active_label = "Desativar" if paciente.sn_ativo else "Ativar"
    query_context = request.GET.get("origem") == "consulta"
    result_ids = request.session.get("consulta_pacientes", []) if query_context else []
    if query_context and not fluxo_agendamento:
        request.current_new_url = f"{reverse('atendimento:cadastro-paciente-novo')}?origem=consulta&novo=1"
    if not paciente and query_context and request.GET.get("novo") == "1":
        request.current_record_status = f"Item {len(result_ids) + 1} de {len(result_ids)}"
        route = "atendimento:cadastro-paciente-novo" if not fluxo_agendamento else "atendimento:cadastro-paciente-agendamento"
        if result_ids:
            result_route = "atendimento:cadastro-paciente" if not fluxo_agendamento else "atendimento:revisar-paciente-agendamento"
            request.current_first_url = f"{reverse(result_route, args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse(result_route, args=[result_ids[-1]])}?origem=consulta"
    if paciente and paciente.cd_paciente in result_ids:
        current_index = result_ids.index(paciente.cd_paciente)
        request.current_record_status = f"Item {current_index + 1} de {len(result_ids)}"
        route = "atendimento:revisar-paciente-agendamento" if fluxo_agendamento else "atendimento:cadastro-paciente"
        if current_index > 0:
            request.current_first_url = f"{reverse(route, args=[result_ids[0]])}?origem=consulta"
            request.current_previous_url = f"{reverse(route, args=[result_ids[current_index - 1]])}?origem=consulta"
        if current_index < len(result_ids) - 1:
            request.current_next_url = f"{reverse(route, args=[result_ids[current_index + 1]])}?origem=consulta"
            request.current_last_url = f"{reverse(route, args=[result_ids[-1]])}?origem=consulta"
    if fluxo_agendamento and paciente:
        if recepcao_direta:
            continue_url = reverse("atendimento:novo-atendimento-direto", args=[paciente.pk])
            request.current_continue_url = (
                f"{continue_url}{urlencode({'senha': senha_recepcao_id})}"
                if senha_recepcao_id.isdigit()
                else continue_url
            )
        elif agendamento_recepcao:
            continue_url = reverse("atendimento:novo-atendimento-agendado", args=[agendamento_recepcao.pk])
            query = urlencode({"return_to": request.current_return_url}) if request.current_return_url else ""
            request.current_continue_url = f"{continue_url}{query}" if query else continue_url
        else:
            request.current_continue_url = reverse("atendimento:selecionar-agenda", kwargs={"cd_paciente": paciente.cd_paciente})
    form = PacienteForm(request.POST or None, instance=paciente, empresa=empresa)
    if request.method == "POST" and form.is_valid():
        changed_data = [
            field
            for field in form.changed_data
            if field not in {"observacao_alteracao", "motivo_alteracao"}
        ]
        if paciente and changed_data and not form.cleaned_data.get("motivo_alteracao"):
            form.add_error("motivo_alteracao", "Informe o motivo da alteração.")
            messages.error(request, "Informe o motivo da alteração para salvar o paciente.")
        elif paciente and changed_data and not form.cleaned_data.get("observacao_alteracao"):
            form.add_error("observacao_alteracao", "Informe uma observação para registrar a alteração do paciente.")
            messages.error(request, "Informe uma observação para registrar a alteração do paciente.")
        else:
            before = {field: getattr(paciente, field) for field in changed_data} if paciente else {}
            saved = form.save(commit=False)
            saved.cd_empresa = empresa
            _apply_audit(saved, request.user)
            if saved.cd_convenio:
                saved.nm_convenio = saved.cd_convenio.nm_convenio
            saved.save()
            if query_context and saved.pk not in result_ids:
                result_ids.append(saved.pk)
                request.session["consulta_pacientes"] = result_ids
            if paciente and changed_data:
                after = {field: getattr(saved, field) for field in changed_data}
                HistoricoAlteracaoPaciente.objects.create(
                    cd_empresa=empresa,
                    cd_paciente=saved,
                    cd_usuario=request.user,
                    cd_motivo_alteracao=form.cleaned_data.get("motivo_alteracao"),
                    ds_observacao=form.cleaned_data["observacao_alteracao"],
                    ds_alteracoes={field: {"antes": str(before[field]), "depois": str(after[field])} for field in changed_data},
                    ds_antes={field: str(before[field]) for field in changed_data},
                    ds_depois={field: str(after[field]) for field in changed_data},
                )
            if agendamento_recepcao:
                messages.success(request, "Dados do paciente confirmados. Continue para cadastrar o atendimento.")
                target = reverse("atendimento:revisar-paciente-agendamento", args=[saved.pk])
                query = {"recepcionar": agendamento_recepcao.pk}
                if request.current_return_url:
                    query["return_to"] = request.current_return_url
                response = redirect(f"{target}{urlencode(query)}")
            elif recepcao_direta:
                messages.success(request, "Dados do paciente confirmados. Continue para cadastrar o atendimento.")
                target = reverse("atendimento:novo-atendimento-direto", args=[saved.pk])
                response = redirect(
                    f"{target}{urlencode({'senha': senha_recepcao_id})}"
                    if senha_recepcao_id.isdigit()
                    else target
                )
            elif fluxo_agendamento:
                messages.success(request, "Paciente salvo. Revise os dados e confirme o agendamento.")
                response = redirect("atendimento:selecionar-agenda", cd_paciente=saved.cd_paciente)
            else:
                messages.success(request, "Paciente salvo com sucesso.")
                destino = reverse("atendimento:cadastro-paciente", args=[saved.cd_paciente])
                response = redirect(f"{destino}?origem=consulta" if query_context else destino)
            response["HX-Replace-Url"] = response["Location"]
            return response
    return render(
        request,
        "atendimento/cadastro_paciente.html",
        {
            "form": form,
            "paciente": paciente,
            "fluxo_agendamento": fluxo_agendamento,
            "agendamento_recepcao": agendamento_recepcao,
            "recepcao_direta": recepcao_direta,
        },
    )


@login_required
@role_required("Recepcionista")
def cadastro_paciente_geral(request, cd_paciente=None):
    return cadastro_paciente(request, cd_paciente=cd_paciente, fluxo_agendamento=False)


@login_required
@role_required("TI")
def alternar_status_paciente(request, cd_paciente):
    if request.method != "POST":
        raise PermissionDenied
    empresa = _empresa_logada(request)
    patient = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    patient.sn_ativo = not patient.sn_ativo
    _apply_audit(patient, request.user)
    patient.save()
    messages.success(request, f"Paciente {'reativado' if patient.sn_ativo else 'desativado'} com sucesso.")
    return redirect("atendimento:cadastro-paciente", cd_paciente=patient.pk)


@login_required
@role_required("Recepcionista")
def selecionar_agenda(request, cd_paciente):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Selecionar agenda"
    request.current_tab_root_title = "Selecionar agenda"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    comprovante_id = request.GET.get("comprovante", "").strip()
    comprovante = (
        Agendamento.objects.select_related(
            "cd_paciente",
            "cd_paciente__cd_convenio",
            "cd_agenda_profissional__cd_prestador",
        ).filter(cd_empresa=empresa, cd_paciente=paciente, pk=int(comprovante_id)).first()
        if comprovante_id.isdigit()
        else None
    )
    hoje = timezone.localdate()
    data_filtro = _parse_date(request.GET.get("data"), hoje)
    horarios = _horarios_disponiveis(empresa, inicio=data_filtro, fim=data_filtro)
    horarios = [
        horario
        for horario in horarios
        if not list(horario["agenda"].convenios.all())
        or paciente.cd_convenio_id in {convenio.pk for convenio in horario["agenda"].convenios.all()}
    ]
    especialidades_selecionadas = [value for value in request.GET.getlist("especialidades") if value]
    todas_especialidades = (not request.GET) or request.GET.get("todas_especialidades") == "1"
    termo = request.GET.get("q", "").strip().replace("%", "")
    if especialidades_selecionadas and not todas_especialidades:
        horarios = [
            horario
            for horario in horarios
            if horario["agenda"].ds_especialidade in especialidades_selecionadas
            or horario["agenda"].cd_prestador.ds_especialidade in especialidades_selecionadas
            or set(especialidades_selecionadas).intersection(horario["agenda"].cd_prestador.ds_especialidades or [])
        ]
    if termo:
        termo_lower = termo.lower()
        horarios = [
            horario
            for horario in horarios
            if termo_lower in horario["agenda"].cd_prestador.nm_prestador.lower()
            or termo_lower in (horario["agenda"].cd_prestador.nm_guerra or "").lower()
            or termo_lower in horario["agenda"].nm_especialidade.lower()
            or termo_lower in horario["dh_agendamento"].strftime("%H:%M")
        ]
    especialidades = ValorAuxiliarGlobal.objects.filter(
        cd_tabela_auxiliar_global__ds_tabela="especialidade",
        sn_ativo=True,
    ).order_by("ds_valor")
    mes = int(request.GET.get("mes") or data_filtro.month)
    ano = int(request.GET.get("ano") or data_filtro.year)
    data_calendario = data_filtro.replace(year=ano, month=mes, day=min(data_filtro.day, calendar.monthrange(ano, mes)[1]))
    return render(
        request,
        "atendimento/selecionar_agenda.html",
        {
            "paciente": paciente,
            "idade": _idade(paciente.dt_nascimento),
            "horarios": horarios,
            "especialidades": especialidades,
            "data_filtro": data_filtro.isoformat(),
            "especialidades_selecionadas": especialidades_selecionadas,
            "todas_especialidades": todas_especialidades,
            "termo": termo,
            "calendario": _calendario_mensal(empresa, data_calendario),
            "comprovante": comprovante,
            "empresa": empresa,
            "emitido_em": timezone.now(),
        },
    )


def _validar_horario_para_paciente(slot, paciente):
    agenda = slot.cd_escala
    if not agenda.sn_ativo or not agenda.cd_prestador.sn_ativo:
        return "A escala ou o prestador deste horário está inativo."
    convenios = set(agenda.convenios.values_list("pk", flat=True))
    if convenios and paciente.cd_convenio_id not in convenios:
        return "O convênio do paciente não é aceito por esta escala."
    return ""


@login_required
@role_required("Recepcionista")
def confirmar_horario_agenda(request, cd_paciente, cd_horario):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Confirmar horário"
    request.current_tab_root_title = "Agendar"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    return_to = _safe_return_url(request) or reverse(
        "atendimento:selecionar-agenda",
        kwargs={"cd_paciente": paciente.pk},
    )
    request.current_return_url = return_to
    slot_queryset = HorarioAgenda.objects.select_related(
        "cd_escala__cd_prestador",
        "cd_agenda_gerada",
    ).prefetch_related("cd_escala__convenios")
    slot = get_object_or_404(
        slot_queryset,
        cd_empresa=empresa,
        cd_horario_agenda=cd_horario,
    )
    erro = _validar_horario_para_paciente(slot, paciente)
    if slot.ds_status != "DISPONIVEL":
        erro = "Este horário não está mais disponível."
    if erro:
        messages.error(request, erro)
        return redirect(return_to)
    if request.method == "POST":
        with transaction.atomic():
            slot = get_object_or_404(
                slot_queryset.select_for_update(),
                cd_empresa=empresa,
                cd_horario_agenda=cd_horario,
            )
            erro = _validar_horario_para_paciente(slot, paciente)
            if slot.ds_status != "DISPONIVEL":
                erro = "Este horário não está mais disponível."
            if erro:
                messages.error(request, erro)
                return redirect(return_to)
            agenda = slot.cd_escala
            agendamento = Agendamento(
                cd_empresa=empresa,
                cd_paciente=paciente,
                cd_agenda_profissional=agenda,
                cd_horario_agenda=slot,
                dh_agendamento=slot.dh_inicio,
                ds_profissional=agenda.cd_prestador.nm_prestador,
                ds_especialidade=agenda.ds_especialidade or agenda.cd_prestador.ds_especialidade,
                ds_tipo_atendimento=request.POST.get("ds_tipo_atendimento", "") or agenda.ds_tipo_agendamento,
                ds_plano=request.POST.get("ds_plano", ""),
                sn_particular=request.POST.get("sn_particular") == "1",
                sn_encaixe=request.POST.get("sn_encaixe") == "1",
                ds_observacao=request.POST.get("ds_observacao", ""),
                sn_confirmado=True,
            )
            _apply_audit(agendamento, request.user)
            agendamento.save()
            slot.ds_status = "AGENDADO"
            _apply_audit(slot, request.user)
            slot.save(update_fields=["ds_status", "dh_atualizacao", "cd_usuario_atualizacao"])
        messages.success(request, "Agendamento confirmado.")
        separador = "&" if "" in return_to else ""
        return redirect(f"{return_to}{separador}{urlencode({'comprovante': agendamento.pk})}")
    return render(
        request,
        "atendimento/confirmar_horario_agenda.html",
        {
            "paciente": paciente,
            "idade": _idade(paciente.dt_nascimento),
            "horario": slot,
            "agenda": slot.cd_escala,
            "return_to": return_to,
            "tipos_atendimento": ValorAuxiliarGlobal.objects.filter(
                cd_tabela_auxiliar_global__ds_tabela="tipo_atendimento",
                sn_ativo=True,
            ).order_by("ds_valor"),
        },
    )


@login_required
@role_required("Recepcionista")
@xframe_options_sameorigin
def comprovante_agendamento(request, cd_agendamento):
    empresa = _empresa_logada(request)
    agendamento = get_object_or_404(
        Agendamento.objects.select_related("cd_paciente", "cd_paciente__cd_convenio", "cd_agenda_profissional__cd_prestador"),
        cd_empresa=empresa,
        cd_agendamento=cd_agendamento,
    )
    request.current_tab_title = "Atendimento > Agendamento > Comprovante"
    request.current_tab_root_title = "Comprovante"
    request.current_module_title = "Atendimento"
    modelo = ModeloDocumento.objects.filter(
        Q(cd_empresa=empresa) | Q(cd_empresa__isnull=True),
        tp_elemento="DOCUMENTO",
        tp_documento="COMPROVANTE_AGENDAMENTO",
        sn_versao_atual=True,
        sn_ativo=True,
    ).order_by("-cd_empresa_id", "nm_modelo").first()
    apresentacao = None
    if modelo:
        paciente = agendamento.cd_paciente
        agenda = agendamento.cd_agenda_profissional
        atendimento_virtual = Atendimento(
            cd_atendimento=agendamento.pk,
            cd_empresa=empresa,
            cd_paciente=paciente,
            cd_prestador=agenda.cd_prestador if agenda else None,
            cd_convenio=paciente.cd_convenio,
            cd_setor_atual=getattr(agenda, "cd_setor_atendimento", None),
            ds_status="AGENDADO",
            ds_origem="AGENDADO",
            ds_especialidade=agendamento.ds_especialidade,
            ds_tipo_atendimento=agendamento.ds_tipo_atendimento,
            ds_plano=agendamento.ds_plano,
            dh_inicio=agendamento.dh_agendamento,
            cd_usuario_criacao=agendamento.cd_usuario_criacao,
        )
        agora = timezone.now()
        documento = DocumentoClinico(
            cd_documento_clinico=0,
            cd_empresa=empresa,
            cd_atendimento=atendimento_virtual,
            cd_modelo_documento=modelo,
            tp_documento=modelo.tp_documento,
            ds_titulo=modelo.nm_modelo,
            ds_status="FECHADO",
            dh_criacao=agendamento.dh_criacao or agora,
            dh_emissao=agendamento.dh_agendamento,
            cd_usuario_emissor=request.user,
            cd_usuario_criacao=request.user,
        )
        documento._variaveis_adicionais = {
            "agendamento.codigo": agendamento.pk,
            "agendamento.data": timezone.localtime(agendamento.dh_agendamento).strftime("%d/%m/%Y"),
            "agendamento.hora": timezone.localtime(agendamento.dh_agendamento).strftime("%H:%M"),
            "agendamento.data_hora": timezone.localtime(agendamento.dh_agendamento).strftime("%d/%m/%Y %H:%M"),
            "agendamento.dia_semana": timezone.localtime(agendamento.dh_agendamento).strftime("%A"),
            "agendamento.prestador": agendamento.ds_profissional,
            "agendamento.nome_guerra_prestador": getattr(agenda.cd_prestador, "nm_guerra", "") if agenda and agenda.cd_prestador else "",
            "agendamento.especialidade": agendamento.ds_especialidade,
            "agendamento.tipo": agendamento.ds_tipo_atendimento,
            "agendamento.plano": agendamento.ds_plano,
            "agendamento.observacao": agendamento.ds_observacao,
            "agendamento.usuario": str(agendamento.cd_usuario_criacao or request.user),
        }
        apresentacao = _renderizar_documento(documento, True)
        if request.GET.get("pdf") == "1":
            return _resposta_pdf_documento(request, documento, empresa, apresentacao)
    return render(
        request,
        "atendimento/comprovante_agendamento_embed.html"
        if request.GET.get("embed") == "1"
        else "atendimento/comprovante_agendamento.html",
        {
            "agendamento": agendamento,
            "paciente": agendamento.cd_paciente,
            "empresa": empresa,
            "idade": _idade(agendamento.cd_paciente.dt_nascimento),
            "emitido_em": timezone.now(),
            "modelo": modelo,
            "apresentacao": apresentacao,
        },
    )


@login_required
@role_required("TI", "Recepcionista")
def cancelar_agendamento(request, cd_agendamento):
    if request.method != "POST":
        raise PermissionDenied
    empresa = _empresa_logada(request)
    return_to = _safe_return_url(request)
    with transaction.atomic():
        agendamento = get_object_or_404(
            Agendamento.objects.select_for_update().select_related("cd_horario_agenda__cd_agenda_gerada"),
            cd_empresa=empresa,
            cd_agendamento=cd_agendamento,
        )
        if hasattr(agendamento, "atendimento"):
            messages.error(request, "O agendamento já gerou atendimento e não pode ser cancelado por esta tela.")
            return redirect(return_to or reverse("atendimento:agendamentos-operacionais"))
        agendamento.ds_status = "CANCELADO"
        _apply_audit(agendamento, request.user)
        agendamento.save(update_fields=["ds_status", "dh_atualizacao", "cd_usuario_atualizacao"])
        if agendamento.cd_horario_agenda:
            slot = agendamento.cd_horario_agenda
            slot.ds_status = "CANCELADO" if slot.cd_agenda_gerada.ds_status == "CANCELADA" else "DISPONIVEL"
            slot.ds_motivo_cancelamento = "" if slot.ds_status == "DISPONIVEL" else "Agenda cancelada"
            _apply_audit(slot, request.user)
            slot.save(update_fields=["ds_status", "ds_motivo_cancelamento", "dh_atualizacao", "cd_usuario_atualizacao"])
    messages.success(request, "Agendamento cancelado. O horário voltou a ficar disponível quando permitido pela agenda.")
    return redirect(return_to or reverse("atendimento:agendamentos-operacionais"))


def _horarios_disponiveis(empresa, dias=21, inicio=None, fim=None):
    inicio = inicio or timezone.localdate()
    fim = fim or (inicio + timedelta(days=max(dias - 1, 0)))
    slots = HorarioAgenda.objects.select_related("cd_escala__cd_prestador", "cd_agenda_gerada").prefetch_related("cd_escala__convenios").filter(
        cd_empresa=empresa,
        ds_status="DISPONIVEL",
        cd_escala__sn_ativo=True,
        cd_prestador__sn_ativo=True,
        dh_inicio__date__gte=inicio,
        dh_inicio__date__lte=fim,
    ).order_by("dh_inicio", "cd_prestador__nm_prestador")
    return [
        {
            "agenda": slot.cd_escala,
            "dh_agendamento": slot.dh_inicio,
            "horario": slot,
        }
        for slot in slots
    ]


@login_required
@role_required("Recepcionista")
def confirmar_agendamento(request, cd_paciente):
    request.current_tab_title = "Atendimento > Agendamento > Agendar > Confirmar agendamento"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=cd_paciente)
    form = AgendamentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        agendamento = form.save(commit=False)
        agendamento.cd_empresa = empresa
        agendamento.cd_paciente = paciente
        agendamento.sn_confirmado = True
        _apply_audit(agendamento, request.user)
        agendamento.save()
        messages.success(request, "Agendamento confirmado.")
        return redirect("atendimento:agendas")
    return render(request, "atendimento/confirmar_agendamento.html", {"form": form, "paciente": paciente})


@login_required
@role_required("Recepcionista")
def demanda_espontanea(request):
    request.current_tab_title = "Atendimento > Demanda espontânea"
    request.current_tab_root_title = "Demanda espontânea"
    request.current_module_title = "Atendimento"
    empresa = _empresa_logada(request)
    form = PacienteSearchForm(request.GET or None)
    pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
    if request.GET and form.is_valid():
        data = form.cleaned_data
        if data.get("cd_paciente"):
            pacientes = pacientes.filter(cd_paciente=data["cd_paciente"])
        if data.get("termo"):
            pacientes = pacientes.filter(nm_paciente__icontains=data["termo"].replace("%", ""))
        if data.get("nr_cpf"):
            pacientes = pacientes.filter(nr_cpf__icontains=data["nr_cpf"].replace("%", ""))
        if data.get("nm_mae"):
            pacientes = pacientes.filter(nm_mae__icontains=data["nm_mae"].replace("%", ""))
        if data.get("nr_cartao_sus"):
            pacientes = pacientes.filter(nr_cartao_sus__icontains=data["nr_cartao_sus"].replace("%", ""))
        if data.get("dt_nascimento"):
            pacientes = pacientes.filter(dt_nascimento=data["dt_nascimento"])
    else:
        pacientes = pacientes.none()
    if request.method == "POST":
        paciente = get_object_or_404(Paciente, cd_empresa=empresa, cd_paciente=request.POST.get("cd_paciente"))
        atendimento = Atendimento(
            cd_empresa=empresa,
            cd_paciente=paciente,
            cd_convenio=paciente.cd_convenio,
            ds_origem="DEMANDA_ESPONTANEA",
            ds_tipo_atendimento="DEMANDA_ESPONTANEA",
            ds_status="AGUARDANDO_CLASSIFICACAO",
            cd_usuario_criacao=request.user,
            cd_usuario_atualizacao=request.user,
        )
        atendimento.save()
        _registrar_fluxo(atendimento, "", atendimento.ds_status, request.user, origem="demanda_espontanea")
        messages.success(request, "Atendimento de demanda espontânea criado e encaminhado para classificação.")
        return redirect("atendimento:recepcao")
    return render(request, "atendimento/demanda_espontanea.html", {"form": form, "pacientes": pacientes})


@login_required
def verificar_paciente_unico(request):
    empresa = _empresa_logada(request)
    field = request.GET.get("field")
    value = request.GET.get("value")
    paciente_atual = request.GET.get("paciente")
    allowed_fields = {"nr_cpf": "CPF", "nr_cartao_sus": "Cartão SUS", "nr_rg": "RG"}
    if field not in allowed_fields or not value:
        return JsonResponse({"exists": False})
    if field == "nr_cpf":
        digits = "".join(character for character in value if character.isdigit())
        formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}" if len(digits) == 11 else value
        pacientes = Paciente.objects.filter(cd_empresa=empresa).filter(Q(nr_cpf=value) | Q(nr_cpf=digits) | Q(nr_cpf=formatted))
    else:
        pacientes = Paciente.objects.filter(cd_empresa=empresa, **{field: value})
    if paciente_atual:
        pacientes = pacientes.exclude(cd_paciente=paciente_atual)
    paciente = pacientes.first()
    return JsonResponse(
        {
            "exists": bool(paciente),
            "message": f"{allowed_fields[field]} já cadastrado para {paciente.nm_paciente}." if paciente else "",
        }
    )
