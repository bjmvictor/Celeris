# Fluxos do sistema

Para o roteiro simplificado por usuários, consulte `docs/homologacao.md`.

## Agendamento

```text
Agendar
  -> consultar paciente
  -> revisar ou cadastrar prontuário
  -> selecionar data e especialidade
  -> selecionar horário e profissional
  -> confirmar agendamento
  -> fila/agendas
```

Dependências: paciente, convênio, profissional, especialidade, escala e horário disponível.

## Atendimento agendado

```text
Agendas/Fila
  -> selecionar agendamento
  -> confirmar dados
  -> pré-atendimento quando aplicável
  -> abrir ficha de atendimento
  -> preencher dados
  -> salvar/gerar atendimento
  -> impressão da ficha
```

Para homologação, o fluxo médico obrigatório é: abrir consulta, salvar registro clínico, prescrever, evoluir, conceder alta e finalizar.

Na recepção, o agendamento muda para `RECEPCIONADO` e o atendimento nasce como `AGUARDANDO_CLASSIFICACAO`. A triagem o encaminha para `AGUARDANDO_CONSULTA`; a consulta pode alterar para `AGUARDANDO_EXAMES`, `EM_ATENDIMENTO` ou um estado final.

Toda transição operacional do atendimento registra um evento em `atendimento_fluxo`, com empresa, atendimento, status anterior, status novo, setor, prestador, usuário, origem e data/hora. O PEP e a ficha clínica sempre operam pelo `cd_atendimento`, nunca apenas por paciente ou agendamento.

## Exames

```text
Consulta
  -> solicitar exame
  -> Solicitado
  -> Coletado
  -> Em análise
  -> resultado/anexo
  -> Liberado
  -> visualização dentro da consulta
```

## Atendimento sem agendamento

```text
Demanda espontânea
  -> selecionar paciente
  -> criar atendimento sem agendamento
  -> pré-atendimento e classificação
  -> fila por prioridade
  -> abrir ficha de atendimento
  -> preencher e salvar
  -> impressão da ficha
```

## Cadastro padrão

```text
Abrir cadastro vazio
  -> consultar OU incluir
  -> navegar nos resultados
  -> editar
  -> validar
  -> salvar
  -> registrar auditoria
```

## Tabela editável padrão

```text
Abrir tabela vazia
  -> consultar ou adicionar
  -> carregar até 20 itens
  -> ordenar por qualquer coluna
  -> navegar entre páginas
  -> salvar alterações
```

## Melhorias futuras

- Busca pesquisável com cadastro rápido em modal para entidades relacionadas.
- Importação oficial de CEP, CID e tipos de logradouro.
- Autorização granular por tela e ação.
- Impressão configurável por empresa.

## Bugs corrigidos nesta revisão

- Dropdown flutuante fechando imediatamente ao clique.
- Botão Limpar sem limpar seleções, datas, estados e validações.
- Consulta parcial de paciente com `%`.
- Consulta travada após recusar salvamento.
- Retorno fictício ao abrir cadastro de paciente diretamente.
- Guias antigas sendo descartadas automaticamente.
- Ausência de ficha real antes da impressão do atendimento.

## Melhorias implementadas

- Tela inicial reduzida a boas-vindas e contexto da sessão.
- Validação de CPF, e-mail e CNES com bloqueio e destaque visual.
- Cadastros principais organizados em seções.
- Auditoria exibida como somente leitura.
- Tabelas inicialmente vazias, paginadas em 20 itens e ordenáveis.
- Barra inferior com item/página e totais.
- Seleção de agenda filtrável por data e especialidade.
- Ficha de atendimento com impressão.

## Próximas versões

- Cadastro rápido em modal para todos os relacionamentos.
- Importadores oficiais de CEP, CID e logradouros.
- Auditoria automática via middleware para operações administrativas e importações.
- Regras clínicas configuráveis de classificação de risco.
- Modelagem de faturamento, estoque, compras e prontuário eletrônico.
## Agendamento com calendário

```text
Agendar paciente
  -> revisar/cadastrar paciente
  -> selecionar agenda com calendário mensal
  -> filtrar por data, intervalo, especialidades e pesquisa
  -> escolher horário vago
  -> exibir confirmação
  -> salvar agendamento
  -> abrir comprovante para impressão/reimpressão
```

## PEP e documentos

```text
PEP
  -> consultar por atendimento OU busca geral
  -> listar apenas atendimentos sem alta
  -> abrir ficha pelo cd_atendimento mantendo return_to
  -> registrar prescrição/exame/evolução/alta
  -> gerar documento clínico em rascunho
  -> imprimir com marca d'água se rascunho/cancelado
  -> copiar documento criando novo rascunho
```
