# Inventário de tabelas editáveis

| Tabela | Local de edição | Chave | Campos editáveis | Relacionamentos |
|---|---|---|---|---|
| `empresa` | Configuração > Empresas | `cd_empresa` | nome, CNPJ, razão social, fantasia, contato, endereço, ativo | usuários por `usuario_empresa` |
| `usuario_empresa` | Administração Django; tela ERP prevista | `id` | usuário, empresa, padrão, ativo | `usuario`, `empresa` |
| `paciente` | Pacientes/Cadastro e Agendamento/Cadastro | `cd_paciente` | dados pessoais, documentos, convênio, família, contato e endereço | `empresa`, `convenio` |
| `historico_alteracao_paciente` | Gerado automaticamente | `cd_historico_alteracao_paciente` | não editável | paciente, usuário, motivo auxiliar |
| `prestador` | Cadastros > Prestadores | `cd_prestador` | dados do prestador, documentos, contato principal, endereços residencial/comercial, multiespecialidades com principal, permissões assistenciais e dados bancários | empresa; tipo de prestador/conselho; valores auxiliares |
| `cep` | Global > CEPs | `cd_cep` | número imutável do CEP, UF, cidade, tipo/logradouro, bairro e status | paciente; prestador residencial; prestador comercial |
| `tipo_prestador_conselho` | Global > Tabelas | `id` | tipo de prestador, conselho, ativo | tipo de prestador lógico |
| `convenio` | Atendimento > Tabelas > Convênios | `cd_convenio` | nome, ativo | empresa |
| `agenda_profissional` | Atendimento > Tabelas > Escalas | `cd_agenda_profissional` | profissional, descrição, dia, início, fim, duração, intervalo, ativo | empresa, prestador |
| `agendamento` | Fluxo de agendamento | `cd_agendamento` | horário, tipo, especialidade, profissional, observação, confirmação, status | empresa, paciente, agenda |
| `pre_atendimento` | Fila > Pré-atendimento | `cd_pre_atendimento` | prioridade, queixa, sinais vitais, antropometria, observação | empresa, paciente, agendamento |
| `atendimento` | Atendimento | `cd_atendimento` | prestador, anamnese, conduta, status | empresa, paciente, agendamento, pré-atendimento |
| `atendimento_fluxo` | Gerado automaticamente nas transições assistenciais | `cd_atendimento_fluxo` | não editável | empresa, atendimento, setor, prestador, usuário |
| `atendimento_prestador` | Ficha/fluxo assistencial | `cd_atendimento_prestador` | papel, início, fim, responsável principal e ativo | empresa, atendimento, prestador |
| `atendimento_procedimento` | Ficha/fluxo assistencial | `cd_atendimento_procedimento` | procedimento, quantidade, valor, executante, principal e ativo | empresa, atendimento, prestador |
| `setor` | Global > Empresa > Setores | `cd_setor` | nome, tipo, observação e ativo | empresa, usuários |
| `painel_chamada` | Global > Empresa > Painel de Chamada | `cd_painel_chamada` | nome, descrição, máquina, tipo, local, mensagem, tempo, layout, mídia, som e ativo | empresa, setores |
| `painel_chamada_setor` | Global > Empresa > Painel de Chamada | `cd_painel_chamada_setor` | setores que enviam chamadas | painel, setor |
| `chamada_painel` | PEP/Painel público | `cd_chamada_painel` | status, local e data/hora da chamada | empresa, atendimento, setor, painel |
| `tabela_auxiliar` | Global > Tabelas auxiliares | `cd_tabela_auxiliar_global` | nome, descrição, ativo | valores auxiliares |
| `valor_auxiliar` | Global e tabelas do Atendimento | `cd_valor_auxiliar_global` | código, descrição, grupo, ativo | tabela auxiliar |
| `definicao_tela` | Configuração > Telas | `id` | módulo, título, rota, tipo, tabela, capacidades e ordem | módulo |
| `campo_tela` | Configuração > Campos | `id` | tela, campo, tipo, regras, lookup e ordem | definição de tela |
| `chamado` | TI > Chamados | `id` | módulo, título, descrição, setor, prioridade, status, responsáveis | usuários |
| `consulta_relatorio` | Relatórios | `id` | identificação, SQL, binds, exibição e ativo | usuário criador |
| `versao_consulta_relatorio` | Histórico de relatórios | `id` | gerado ao versionar | relatório, usuário |
| `periodo_social` | Social | `id` | mês, ano, ativo | atendimentos sociais |
| `atendimento_social` | Social | `id` | paciente, período e indicadores | período, usuário |
| `maquina_agente` | TI > Agentes | `id` | identificação, estado e recursos | eventos |
| `evento_agente` | Eventos do agente | `id` | normalmente automático | máquina |
| `status_painel` | Enfermagem > Painel | `id` | quantidade, estado, nível | usuário |
| `configuracao_automatica_painel` | Configuração do painel | `id` | banco, SQL, intervalo e ativo | — |
| `solicitacao_exame` | Ficha de atendimento > Solicitar exame | `cd_solicitacao_exame` | exame, justificativa, prioridade e status | atendimento, empresa, auditoria |
| `resultado_exame` | Laboratório > Resultado | `cd_resultado_exame` | texto do resultado, anexo e liberação | solicitação, empresa, auditoria |
| `prescricao` | Consulta Médica > Prescrever | `cd_prescricao` | prescrição, orientações e ativo | atendimento, empresa, auditoria |
| `evolucao_atendimento` | Consulta Médica > Evoluir | `cd_evolucao_atendimento` | evolução clínica | atendimento, prestador, empresa, auditoria |

## Matriz de edição, validação e permissão

| Tabela | Obrigatórios | Dropdowns/relacionamentos | Validações | Papel mínimo |
|---|---|---|---|---|
| `usuario` | usuário, senha e empresa na criação | empresas, grupos | usuário único; novo usuário sempre ativo | Administração |
| `prestador` | nome e nome de guerra | órgão emissor, instrução, identidade de gênero, nacionalidade, naturalidade, tipo, UF do conselho, especialidades, vínculo, contato principal, CEP, estado, cidade, logradouro, permissões e banco | código automático; nome de guerra obrigatório com sugestão do primeiro e último nome; ativo bloqueado na inclusão; CPF válido e único; conselho derivado do tipo; especialidade principal pertence à lista; cidades vinculadas ao estado; endereço comercial pode acompanhar o residencial | TI |
| `paciente` | nome, CPF e nascimento | sexo, gênero, raça/cor, estado civil, sangue, nacionalidade, naturalidade, profissão, convênio, estado e cidade | CPF válido e único; RG/CNS sem duplicidade | Recepção |
| `agendamento` | paciente, agenda, data e horário | profissional, especialidade, convênio/plano | horário único por profissional; status controlado | Recepção |
| `atendimento` | paciente, origem e status | prestador, convênio, especialidade, setor | finalização exige profissional, diagnóstico/hipótese, conduta e destino | Médico/Profissional |
| `pre_atendimento` | paciente, prioridade, queixa e responsável | profissional responsável | sinais vitais numéricos; início/fim automáticos | Triagem |
| `solicitacao_exame` | atendimento, exame e prioridade | atendimento | transição de status controlada | Médico/Profissional |
| `resultado_exame` | solicitação | solicitação | liberação registra data e altera solicitação | Laboratório |
| `prescricao` | atendimento e texto da prescrição | atendimento | somente médico ou TI | Médico |
| `evolucao_atendimento` | atendimento, prestador e evolução | atendimento, prestador | prestador deve estar definido na consulta | Médico |
| tabelas auxiliares | código e descrição | tabela auxiliar | código único por tabela | Administração |

## Tabelas auxiliares atuais

`tipo_sanguineo`, `sexo`, `genero`, `cor_raca`, `estado_civil`, `pais`, `estado`, `cidade`, `motivo_alteracao`, `tipo_prestador`, `especialidade`, `tipo_atendimento` e `sala`.

O módulo **Global** disponibiliza `cep` em tabela própria, com PK independente e vínculos por FK em paciente e prestador. Bairro permanece como texto no endereço. As demais classificações continuam em tabelas auxiliares compartilhadas.

## Tabelas auxiliares planejadas

`profissao`, `religiao`, `tipo_moradia`, `parentesco`, `distrito_sanitario`, `meio_comunicacao`, `feriado`, `tipo_pendencia`, `tipo_logradouro`, `resposta_pergunta`, `cbo_s`, `orgao_emissor`, `situacao_familiar`, `tipo_registro`, `meio_transporte`, `lingua_indigena`, `condicao_especial`, `local_trabalho`, `orientacao_sexual`, `vulnerabilidade_social`, `tipo_identificador_pessoa`, `tipo_vinculo`, `origem`, `setor_exame`, `banco`, `cid`, `motivo`, `grupo_pergunta`, `pergunta`, `tipo_ocorrencia` e `centro_custo`.

## Importação

CEP, CID e tipos de logradouro podem ser importados de bases oficiais previamente baixadas e normalizadas:

```powershell
python manage.py importar_tabela_auxiliar cid arquivo.csv
python manage.py importar_tabela_auxiliar cep arquivo.csv
python manage.py importar_tabela_auxiliar tipo_logradouro arquivo.csv
```

Formato: `codigo;descricao;grupo`. A coluna `grupo` é opcional.

Para CEP, use `grupo` no formato `UF|CODIGO_CIDADE`, permitindo preencher Estado e Cidade automaticamente no cadastro do prestador.
## Documentos clínicos

| Tabela | Tela | PK | Campos editáveis | Relacionamentos |
|---|---|---|---|---|
| `modelo_documento` | Atendimento > Modelos de documentos | `cd_modelo_documento` | nome, tipo, cabeçalho, corpo, rodapé, variáveis, campos bloqueados e ativo | empresa, auditoria |
| `documento_clinico` | Ficha de atendimento > Documentos | `cd_documento_clinico` | título, conteúdo, status e referência de cópia | empresa, atendimento, modelo, documento origem, emissor |

Estados de `documento_clinico`: `RASCUNHO`, `FINALIZADO`, `ASSINADO` e `CANCELADO`. Impressões de rascunho e cancelado exibem marca d'água visual. Cópias sempre geram novo rascunho e mantêm vínculo com `cd_documento_origem`.
