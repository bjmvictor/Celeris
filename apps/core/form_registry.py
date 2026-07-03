from django.db import OperationalError, ProgrammingError
from django.utils.module_loading import import_string

from .models import ConfiguracaoCampoFormulario


FORMULARIOS_CONFIGURAVEIS = {
    "cadastro_paciente": {
        "nome": "Cadastro de paciente",
        "classe": "apps.atendimento.forms.PacienteForm",
        "usa_empresa": True,
    },
    "cadastro_prestador": {
        "nome": "Cadastro de prestador",
        "classe": "apps.atendimento.forms.PrestadorForm",
        "usa_empresa": True,
    },
    "cadastro_atendimento": {
        "nome": "Cadastro de atendimento",
        "classe": "apps.atendimento.forms.CadastroAtendimentoForm",
        "usa_empresa": True,
    },
    "responsavel_atendimento": {
        "nome": "Responsável pelo atendimento",
        "classe": "apps.atendimento.forms.ResponsavelAtendimentoForm",
        "usa_empresa": True,
    },
    "cadastro_escala": {
        "nome": "Cadastro de escala",
        "classe": "apps.atendimento.forms.EscalaForm",
        "usa_empresa": True,
    },
    "cadastro_painel_chamada": {
        "nome": "Cadastro de painel de chamada",
        "classe": "apps.atendimento.forms.PainelChamadaForm",
        "usa_empresa": True,
    },
    "pre_atendimento": {
        "nome": "Pré-atendimento",
        "classe": "apps.atendimento.forms.PreAtendimentoForm",
        "usa_empresa": True,
    },
}

ROTULOS_CAMPOS = {
    "cadastro_paciente": {
        "nm_paciente": "Nome",
        "nm_social": "Nome social",
        "dt_nascimento": "Data de nascimento",
        "nr_cpf": "CPF",
        "nr_rg": "RG",
        "nr_cartao_sus": "Cartão Nacional de Saúde",
        "nm_mae": "Nome da mãe",
        "nm_pai": "Nome do pai",
    },
    "cadastro_prestador": {
        "nm_prestador": "Nome",
        "nm_guerra": "Nome de guerra",
        "dt_nascimento": "Data de nascimento",
        "nr_cpf": "CPF",
        "nr_rg": "RG",
        "nr_cartao_sus": "Cartão Nacional de Saúde",
        "nm_mae": "Nome da mãe",
        "nm_pai": "Nome do pai",
        "tp_prestador": "Tipo de prestador",
        "nr_conselho": "Número do conselho",
        "sg_conselho": "UF do conselho",
        "tp_vinculo": "Tipo de vínculo",
        "nr_telefone": "Telefone",
        "nr_celular": "Celular",
        "nr_celular_2": "Celular 2",
        "ds_email": "E-mail",
    },
    "cadastro_atendimento": {
        "cd_atendimento": "Código",
        "cd_paciente_exibicao": "Prontuário",
        "nm_paciente_exibicao": "Paciente",
        "dh_atendimento_exibicao": "Data e hora",
        "cd_prestador": "Médico/Prestador",
        "ds_tipo_atendimento": "Tipo de atendimento",
        "ds_local_procedencia": "Local de procedência",
        "ds_meio_transporte": "Meio de transporte",
    },
    "cadastro_escala": {
        "ds_agenda": "Nome da escala",
        "tp_escala": "Tipo de escala",
        "cd_prestador": "Prestador",
        "ds_especialidade": "Especialidade",
        "cd_setor_atendimento": "Setor de atendimento",
        "tp_horario": "Tipo de horário",
        "ds_dias_semana": "Dias da semana",
        "qt_horarios_dia": "Quantidade de horários",
        "qt_encaixes": "Quantidade de encaixes",
    },
}


def opcoes_formularios():
    return [(codigo, dados["nome"]) for codigo, dados in FORMULARIOS_CONFIGURAVEIS.items()]


def construir_formulario_referencia(codigo, empresa):
    configuracao = FORMULARIOS_CONFIGURAVEIS.get(codigo)
    if not configuracao:
        return None
    form_class = import_string(configuracao["classe"])
    kwargs = {"empresa": empresa} if configuracao.get("usa_empresa") else {}
    return form_class(**kwargs)


def listar_campos_formulario(codigo, empresa):
    formulario = construir_formulario_referencia(codigo, empresa)
    if formulario is None:
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
                "nome_formulario": FORMULARIOS_CONFIGURAVEIS[codigo]["nome"],
                "chave": f"{codigo}::{nome}",
                "codigo": nome,
                "nome": ROTULOS_CAMPOS.get(codigo, {}).get(
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
    codigos = [codigo_formulario] if codigo_formulario in FORMULARIOS_CONFIGURAVEIS else list(FORMULARIOS_CONFIGURAVEIS)
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
