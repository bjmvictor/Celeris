# Homologação do fluxo assistencial

## Usuários

| Papel | Usuário | Senha |
|---|---|---|
| TI | `admin` | `123456` |
| Recepcionista | `recepcao` | `123456` |
| Enfermeiro | `enfermagem` | `123456` |
| Médico | `medico` | `123456` |

Os nomes podem ser digitados em letras minúsculas. O sistema normaliza o identificador no login.

## Roteiro

### 1. Recepcionista

1. Entrar como `recepcao`.
2. Abrir **Cadastros > Pacientes** e cadastrar ou localizar o paciente.
3. Abrir **Atendimento > Agendar**.
4. Selecionar paciente, data, especialidade, profissional e horário.
5. Abrir **Atendimento > Recepção**.
6. Clicar em **Recepcionar**.
7. Confirmar que o atendimento ficou em **Aguardando classificação**.
8. Sair.

### 2. Enfermeiro

1. Entrar como `enfermagem`.
2. Abrir **Atendimento > Classificação de Risco**.
3. Selecionar o paciente.
4. Registrar queixa, sintomas, sinais vitais, prioridade e responsável.
5. Concluir a classificação.
6. Confirmar o estado **Aguardando consulta**.
7. Sair.

### 3. Médico

1. Entrar como `medico`.
2. Abrir **Atendimento > Consultas Médicas**.
3. Abrir a consulta.
4. Registrar anamnese, diagnóstico e conduta.
5. Salvar.
6. Abrir **Prescrever** e registrar a prescrição.
7. Abrir **Evoluir** e registrar a evolução.
8. Abrir **Conceder alta** e informar o destino.
9. Clicar em **Finalizar atendimento**.
10. Confirmar o estado **Finalizado**.

## Estados do fluxo

```text
AGENDADO
  -> RECEPCIONADO
  -> AGUARDANDO CLASSIFICAÇÃO
  -> AGUARDANDO CONSULTA
  -> EM ATENDIMENTO
  -> ALTA MÉDICA
  -> FINALIZADO
```

O histórico de cada transição é gravado em `atendimento_fluxo`. A tela **Atendimento > Agendamentos** é a lista operacional por data/especialidade para recepcionar pacientes já agendados.

## Dados mínimos

A migração de homologação cria:

- empresa de homologação;
- convênio particular;
- especialidade Clínica Geral;
- médico de homologação;
- agenda de segunda a sexta, das 08:00 às 18:00.
## Homologação — agenda, PEP e documentos

- Validar calendário mensal abrindo na data atual, troca de mês, feriados em vermelho e dias com agenda em destaque.
- Validar filtro por intervalo, múltiplas especialidades e opção Todas em `Atendimento > Agendamentos` e seleção de agenda.
- Validar comprovante após confirmar agendamento e reimpressão por protocolo.
- Validar PEP pesquisando por número de atendimento e por busca geral, garantindo que agendamentos sem atendimento não aparecem.
- Validar ficha abrindo por `cd_atendimento`, botão Voltar retornando para a lista anterior e ações clínicas por permissão.
- Validar geração de `documento_clinico` ao solicitar exame, prescrever, evoluir e conceder alta.
- Validar marca d'água de rascunho/cancelado e cópia de documento como novo rascunho.
- Validar isolamento por empresa em agenda, atendimento, documento e modelo.
