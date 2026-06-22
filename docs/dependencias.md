# Matriz de dependências

| Tela/processo | Pré-requisitos | Tabelas principais | Auxiliares |
|---|---|---|---|
| Cadastro de paciente | empresa ativa | paciente, convênio | sexo, gênero, raça/cor, estado civil, tipo sanguíneo, país, estado, cidade, profissão |
| Cadastro de prestador | empresa ativa | prestador | tipo de prestador, multiespecialidades e principal, permissões assistenciais, órgão emissor, grau de instrução, identidade de gênero, nacionalidade, naturalidade, CEP, tipo de logradouro, cidade, estado, banco, tipo de vínculo; vínculo prestador x conselho |
| Global > Integrações | perfil TI e arquivo CSV/XLSX | CEP ou tabela/valor auxiliar | CEP, estado, cidade e tipo de logradouro; XLSX requer `openpyxl` |
| Cadastro de paciente/prestador | CEP ativo selecionado | paciente.cd_cep; prestador.cd_cep; prestador.cd_cep_comercial | CEP possui PK própria; alteração descritiva não exige atualização dos cadastros vinculados |
| Cadastro de prestador | tipo de prestador | prestador.ds_conselho | conselho é preenchido pelo vínculo tipo x conselho; ausência do vínculo gera alerta não bloqueante |
| Cadastro de escala | profissional ativo | agenda profissional | especialidade indireta, dia da semana |
| Geração da agenda | escala ativa | agenda profissional | — |
| Agendamento | paciente revisado, profissional e escala ativos | paciente, agenda profissional, agendamento | especialidade, tipo de atendimento |
| Demanda espontânea | paciente cadastrado | paciente, agendamento | tipo de atendimento |
| Pré-atendimento | agendamento ou demanda espontânea | pré-atendimento, paciente, agendamento | prioridade clínica |
| Atendimento | paciente; opcionalmente agendamento e pré-atendimento | atendimento | prestador, especialidade, tipo de atendimento |
| Impressão da ficha | atendimento salvo | atendimento, paciente, prestador | — |
| Recepção | agendamento do dia | agendamento, atendimento, paciente | origem, tipo de atendimento |
| Solicitação de exame | atendimento aberto | solicitação de exame, atendimento | prioridade, catálogo de exames |
| Resultado de exame | solicitação existente | resultado de exame, solicitação | status de solicitação |
| Convênio | empresa ativa | convenio | — |
| Empresas | usuário autorizado | empresa | cidade, estado |

## Regras de origem

- Tela aberta diretamente pelo menu: ação de fechamento encerra somente a guia.
- Tela aberta por um fluxo: ação de retorno usa uma origem explícita.
- Não se deve inferir retorno apenas pelo nome da rota.

## Papéis

| Papel | Responsabilidades |
|---|---|
| Recepção | pacientes, agendamentos, recepção e abertura de atendimento |
| Triagem | classificação, sinais vitais e prioridade |
| Médico/Profissional | consulta, histórico, solicitações e finalização |
| Laboratório | andamento da solicitação, resultado e liberação |
| Administração | usuários, permissões, empresas e tabelas auxiliares |
