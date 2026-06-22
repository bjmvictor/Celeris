# Mapa de telas

Durante a homologação, o menu expõe somente Atendimento, Cadastros e Administração.

## Atendimento

| Tela | Rota | Tipo | Tabelas principais | Situação |
|---|---|---|---|---|
| Agendar | `/atendimento/agendamento/agendar/` | Consulta | `paciente` | Funcional; inicia revisão e seleção da agenda |
| Cadastro de paciente no agendamento | `/atendimento/agendamento/pacientes/novo/` | Cadastro | `paciente`, `convenio` | Funcional; deve fechar quando aberta diretamente |
| Revisão do paciente | `/atendimento/agendamento/pacientes/<id>/` | Cadastro | `paciente`, `historico_alteracao_paciente` | Funcional |
| Seleção de agenda | `/atendimento/agendamento/pacientes/<id>/agenda/` | Seleção | `agenda_profissional`, `agendamento` | Funcional; filtros por data/especialidade previstos |
| Agendas | `/atendimento/agendamento/agendas/` | Painel operacional | `agendamento`, `agenda_profissional` | Funcional |
| Gerar agenda | `/atendimento/agendamento/gerar-agenda/` | Processo | `agenda_profissional`, `agendamento` | Gera horários calculados |
| Fila de atendimento | `/atendimento/agendamento/atender/` | Fila | `agendamento`, `pre_atendimento` | Funcional |
| Demanda espontânea | `/atendimento/atendimento/demanda-espontanea/` | Consulta/processo | `paciente`, `agendamento` | Funcional |
| Pré-atendimento | `/atendimento/agendamento/<id>/pre-atendimento/` | Cadastro clínico | `pre_atendimento`, `agendamento` | Funcional |
| Atendimento | `/atendimento/atendimento/` | Cadastro clínico | `atendimento` | Parcial; será substituído pelo formulário real |
| Recepção | `/atendimento/recepcao/` | Fila operacional | `agendamento`, `atendimento` | Localiza agenda do dia e recepciona |
| Ficha de atendimento | `/atendimento/atendimento/ficha/<id>/` | Consulta clínica | `atendimento`, `pre_atendimento`, `solicitacao_exame`, `resultado_exame` | Anamnese, diagnóstico, conduta, exames e finalização |
| Solicitação de exame | `/atendimento/atendimento/ficha/<id>/exames/novo/` | Cadastro | `solicitacao_exame` | Vinculada ao atendimento |
| Resultado de exame | `/atendimento/exames/<id>/resultado/` | Cadastro laboratorial | `resultado_exame` | Texto, anexo e liberação |
| Prescrição | `/atendimento/atendimento/ficha/<id>/prescrever/` | Cadastro clínico | `prescricao` | Exclusiva do médico |
| Evolução | `/atendimento/atendimento/ficha/<id>/evoluir/` | Cadastro clínico | `evolucao_atendimento` | Exclusiva do médico |
| Alta | `/atendimento/atendimento/ficha/<id>/alta/` | Transição assistencial | `atendimento` | Exige destino e dados clínicos |
| Prestadores | `/atendimento/cadastros/profissionais/` | Consulta | `prestador` | Funcional |
| Cadastro de prestador | `/atendimento/cadastros/profissionais/<id>/` | Cadastro | `prestador` | Funcional |
| Escalas | `/atendimento/tabelas/escalas/` | Tabela | `agenda_profissional` | Funcional |
| Convênios | rotas `/tabelas/convenios/` | Tabela | `convenio` | Funcional |
| Especialidades, tipos e salas | rotas `/tabelas/.../` | Tabela auxiliar | `tabela_auxiliar`, `valor_auxiliar` | Funcional |

## Global e configuração

| Tela | Rota | Tabelas |
|---|---|---|
| Tabelas auxiliares | `/global/tabelas/auxiliares/.../` | `tabela_auxiliar`, `valor_auxiliar` |
| Tipo de prestador x conselho | `/global/tabelas/tipo-prestador-conselho/` | `tipo_prestador_conselho` |
| Empresas | `/configuracao/empresas/` | `empresa` |
| Usuários | `/accounts/usuarios/` | `usuario`, `usuario_empresa`, grupos e permissões |
| Configuração de telas | `/configuracao/telas/` | `definicao_tela` |
| Configuração de campos | `/configuracao/campos/` | `campo_tela` |

## Outros módulos

| Módulo | Telas | Tabelas |
|---|---|---|
| TI | Chamados, inventário de agentes | `chamado`, `maquina_agente`, `evento_agente` |
| Relatórios | Lista e execução | `consulta_relatorio`, `versao_consulta_relatorio` |
| Social | Acompanhamento | `periodo_social`, `atendimento_social` |
| Enfermagem | Painel | `status_painel`, `configuracao_automatica_painel` |

## Padrão de cadastro

Cadastros de entidades devem usar seções expansíveis por contexto, consulta no mesmo formulário, campos relacionados em seleção pesquisável e auditoria somente leitura. Tabelas simples permanecem em grade editável, inicialmente vazia e carregada somente após consulta.
