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
| Agendamentos operacional | empresa logada e agenda do dia | agendamento, atendimento, paciente | especialidade, prestador, convênio |
| PEP | atendimento gerado | atendimento, setor, chamada_painel | setor de atendimento, permissão assistencial |
| Solicitação de exame | atendimento aberto | solicitação de exame, atendimento | prioridade, catálogo de exames |
| Resultado de exame | solicitação existente | resultado de exame, solicitação | status de solicitação |
| Convênio | empresa ativa | convenio | — |
| Empresas | usuário autorizado | empresa | cidade, estado |
| Setores | empresa logada | setor | tipo de setor, ativo/inativo |
| Painel de chamada | empresa logada e setores de atendimento | painel_chamada, painel_chamada_setor, chamada_painel | tipo de painel, setores |

## Isolamento multiempresa

- A empresa escolhida no login define `request.session["cd_empresa"]`.
- Paciente, prestador, convênio, agenda, agendamento, pré-atendimento, atendimento, exames, prescrições, evoluções, setores e painéis são consultados e alterados com filtro backend por `cd_empresa`.
- Dados sem `cd_empresa` não devem entrar no fluxo operacional assistencial.

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
## Dependências novas — agenda, PEP e documentos

- `Atendimento > Agendamentos`: depende de `agendamento`, `atendimento`, `paciente`, `prestador`, `agenda_profissional`, `convenio`, `valor_auxiliar(especialidade)` e `valor_auxiliar(feriado)`.
- `Selecionar agenda`: depende de paciente revisado, escalas ativas em `agenda_profissional`, prestador ativo com agenda permitida e especialidades ativas.
- `PEP`: depende de atendimento gerado; não lista apenas agendamentos. Filtros por atendimento e busca geral são mutuamente exclusivos na interface.
- `Ficha de atendimento`: depende de `cd_atendimento` e concentra pré-atendimento, exames, prescrições, evoluções, documentos e alta.
- `Modelos de documentos`: depende de empresa ativa e perfil `TI`.
- `Documento clínico`: depende de atendimento, empresa ativa e permissões assistenciais; cópia cria rascunho novo.
