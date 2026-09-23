"""Atendimento-owned declarations for the global configurable-form mechanism."""
from apps.platform.form_registry import ConfigurableForm, form_registry


def register_forms() -> None:
    definitions = (
        ConfigurableForm(
            "cadastro_paciente", "Cadastro de paciente", "apps.atendimento.forms.PacienteForm",
            {"nm_paciente": "Nome", "nm_social": "Nome social", "dt_nascimento": "Data de nascimento", "nr_cpf": "CPF", "nr_rg": "RG", "nr_cartao_sus": "Cartão Nacional de Saúde", "nm_mae": "Nome da mãe", "nm_pai": "Nome do pai"},
        ),
        ConfigurableForm(
            "cadastro_prestador", "Cadastro de prestador", "apps.atendimento.forms.PrestadorForm",
            {"nm_prestador": "Nome", "nm_guerra": "Nome de guerra", "dt_nascimento": "Data de nascimento", "nr_cpf": "CPF", "nr_rg": "RG", "nr_cartao_sus": "Cartão Nacional de Saúde", "nm_mae": "Nome da mãe", "nm_pai": "Nome do pai", "tp_prestador": "Tipo de prestador", "nr_conselho": "Número do conselho", "sg_conselho": "UF do conselho", "tp_vinculo": "Tipo de vínculo", "nr_telefone": "Telefone", "nr_celular": "Celular", "nr_celular_2": "Celular 2", "ds_email": "E-mail"},
        ),
        ConfigurableForm(
            "cadastro_atendimento", "Cadastro de atendimento", "apps.atendimento.forms.CadastroAtendimentoForm",
            {"cd_atendimento": "Código", "cd_paciente_exibicao": "Prontuário", "nm_paciente_exibicao": "Paciente", "dh_atendimento_exibicao": "Data e hora", "cd_prestador": "Médico/Prestador", "ds_tipo_atendimento": "Tipo de atendimento", "ds_local_procedencia": "Local de procedência", "ds_meio_transporte": "Meio de transporte"},
        ),
        ConfigurableForm(
            "responsavel_atendimento", "Responsável pelo atendimento", "apps.atendimento.forms.ResponsavelAtendimentoForm",
        ),
        ConfigurableForm(
            "cadastro_escala", "Cadastro de escala", "apps.atendimento.forms.EscalaForm",
            {"ds_agenda": "Nome da escala", "tp_escala": "Tipo de escala", "cd_prestador": "Prestador", "ds_especialidade": "Especialidade", "cd_setor_atendimento": "Setor de atendimento", "tp_horario": "Tipo de horário", "ds_dias_semana": "Dias da semana", "qt_horarios_dia": "Quantidade de horários", "qt_encaixes": "Quantidade de encaixes"},
        ),
        ConfigurableForm("cadastro_painel_chamada", "Cadastro de painel de chamada", "apps.atendimento.forms.PainelChamadaForm"),
        ConfigurableForm("pre_atendimento", "Pré-atendimento", "apps.atendimento.forms.PreAtendimentoForm"),
    )
    for definition in definitions:
        form_registry.register(definition)
