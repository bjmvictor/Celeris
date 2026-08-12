from django.core.exceptions import ImproperlyConfigured

from .models import MODELOS_CATALOGO_POR_TEMA


ALIASES_CATALOGO = {
    "cid": "cids",
    "motivo_alta": "motivos_alta",
}


ROTULOS_CATALOGO = {
    "bairro": "Bairros",
    "banco": "Bancos",
    "cbo": "Classificação Brasileira de Ocupações (CBO)",
    "cidade": "Cidades",
    "cids": "CIDs",
    "conselho_profissional": "Conselhos profissionais",
    "cor_raca": "Cor/Raça",
    "destino_atendimento": "Destinos de atendimento",
    "especialidade": "Especialidades",
    "estado": "Estados",
    "estado_civil": "Estados civis",
    "feriado": "Feriados",
    "genero": "Gêneros",
    "grau_instrucao": "Graus de instrução",
    "identidade_genero": "Identidades de gênero",
    "idioma": "Idiomas",
    "local_procedencia": "Locais de procedência",
    "meio_comunicacao": "Meios de comunicação",
    "meio_transporte": "Meios de transporte",
    "motivo_alteracao": "Motivos de alteração",
    "motivos_alta": "Motivos de alta",
    "nacionalidade": "Nacionalidades",
    "naturalidade": "Naturalidades",
    "orgao_emissor": "Órgãos emissores",
    "orientacao_sexual": "Orientações sexuais",
    "origem": "Origens",
    "origem_recepcao": "Origens da recepção",
    "pais": "Países",
    "parentesco": "Parentescos",
    "plano": "Planos",
    "procedimento": "Procedimentos",
    "profissao": "Profissões",
    "raca_cor": "Raças/Cores",
    "religiao": "Religiões",
    "sala": "Salas",
    "setor_exame": "Setores de exame",
    "sexo": "Sexos",
    "tipo_atendimento": "Tipos de atendimento",
    "tipo_escala": "Tipos de escala",
    "tipo_identificador_pessoa": "Tipos de identificador da pessoa",
    "tipo_logradouro": "Tipos de logradouro",
    "tipo_moradia": "Tipos de moradia",
    "tipo_ocorrencia": "Tipos de ocorrência",
    "tipo_prestador": "Tipos de prestador",
    "tipo_sanguineo": "Tipos sanguíneos",
    "tipo_vinculo": "Tipos de vínculo",
    "vulnerabilidade_social": "Vulnerabilidades sociais",
}


def normalizar_tema_catalogo(tema: str) -> str:
    tema_normalizado = (tema or "").strip().lower()
    return ALIASES_CATALOGO.get(tema_normalizado, tema_normalizado)


def modelo_catalogo(tema: str):
    tema_normalizado = normalizar_tema_catalogo(tema)
    modelo = MODELOS_CATALOGO_POR_TEMA.get(tema_normalizado)
    if modelo is None:
        raise ImproperlyConfigured(f"Catálogo temático não configurado: {tema}")
    return modelo


def catalogo_queryset(tema: str, *, ativos: bool | None = None, grupo: str | None = None):
    queryset = modelo_catalogo(tema).objects.all()
    if ativos is not None:
        queryset = queryset.filter(sn_ativo=ativos)
    if grupo is not None:
        queryset = queryset.filter(ds_grupo=grupo)
    return queryset


def opcoes_catalogo(tema: str, *, grupo: str | None = None, incluir_vazio: bool = True):
    valores = catalogo_queryset(tema, ativos=True, grupo=grupo).order_by("ds_valor")
    opcoes = [(valor.cd_valor, valor.ds_valor) for valor in valores]
    return ([('', '')] if incluir_vazio else []) + opcoes


def atualizar_item_catalogo(tema: str, codigo: str, **dados):
    return modelo_catalogo(tema).objects.update_or_create(cd_valor=codigo, defaults=dados)


def catalogos_configurados():
    return [
        {
            "tema": tema,
            "descricao": ROTULOS_CATALOGO.get(tema, tema.replace("_", " ").title()),
            "modelo": modelo,
        }
        for tema, modelo in sorted(MODELOS_CATALOGO_POR_TEMA.items())
    ]
