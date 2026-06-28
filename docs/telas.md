# Mapa de telas

Durante a homologação, o menu expõe somente Atendimento, Cadastros e Administração.

## Atendimento

| Tela | Rota | Tipo | Tabelas principais | Situação |
|---|---|---|---|---|
| Agendar | `/atendimento/agendamento/agendar/` | Consulta | `paciente` | Funcional; inicia revisão e seleção da agenda |
| Agendamentos | `/atendimento/agendamento/agendamentos/` | Lista operacional | `agendamento`, `atendimento` | Lista pacientes agendados por data, especialidade e pesquisa; permite recepcionar sem duplicar atendimento |
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
| PEP | `/atendimento/pep/` | Fila clínica | `atendimento`, `setor`, `chamada_painel` | Exibe somente atendimentos gerados e permite abrir ficha pelo `cd_atendimento` |
| Solicitação de exame | `/atendimento/atendimento/ficha/<id>/exames/novo/` | Cadastro | `solicitacao_exame` | Vinculada ao atendimento |
| Resultado de exame | `/atendimento/exames/<id>/resultado/` | Cadastro laboratorial | `resultado_exame` | Texto, anexo e liberação |
| Prescrição | `/atendimento/atendimento/ficha/<id>/prescrever/` | Cadastro clínico | `prescricao` | Exclusiva do médico |
| Evolução | `/atendimento/atendimento/ficha/<id>/evoluir/` | Cadastro clínico | `evolucao_atendimento` | Exclusiva do médico |
| Alta | `/atendimento/atendimento/ficha/<id>/alta/` | Transição assistencial | `atendimento` | Exige destino e dados clínicos |
| Prestadores | `/atendimento/cadastros/profissionais/novo/` | Cadastro e consulta integrados | `prestador` | Funcional |
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
| Setores | `/global/empresa/setores/` | `setor` |
| Setores de Atendimento | `/global/empresa/setores-atendimento/` | `setor` |
| Painel de Chamada | `/atendimento/paineis-chamada/` | `painel_chamada`, `painel_chamada_setor`, `chamada_painel` |
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
 
## Atualização assistencial avançada

| Tela | Rota | Tipo | Tabelas principais | Situação |
|---|---|---|---|---|
| Comprovante de agendamento | `/atendimento/agendamento/<id>/comprovante/` | Impressão | `agendamento`, `paciente`, `empresa` | Reimpressão com protocolo do agendamento |
| Modelos de documentos | `/atendimento/documentos/modelos/` | Administração | `modelo_documento` | Cadastro de cabeçalho, corpo, rodapé, variáveis e campos bloqueados |
| Documento clínico | `/atendimento/documentos/<id>/imprimir/` | Impressão | `documento_clinico`, `atendimento` | Exibe marca d'água para rascunho/cancelado |
| Cópia de documento | `/atendimento/documentos/<id>/copiar/` | Processo | `documento_clinico` | Cria novo rascunho vinculado ao documento origem |

Regras novas: agendamentos e seleção de agenda usam calendário mensal com feriados, dias com agenda, intervalo de datas, múltiplas especialidades e busca contextual. A ficha/PEP abre por `cd_atendimento` e preserva retorno para a lista anterior via `return_to`.
