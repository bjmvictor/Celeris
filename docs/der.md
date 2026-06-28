# DER

```mermaid
erDiagram
    EMPRESA ||--o{ USUARIO_EMPRESA : possui
    USUARIO ||--o{ USUARIO_EMPRESA : acessa
    EMPRESA ||--o{ PACIENTE : cadastra
    EMPRESA ||--o{ PRESTADOR : cadastra
    EMPRESA ||--o{ CONVENIO : cadastra
    CONVENIO o|--o{ PACIENTE : atende
    PRESTADOR ||--o{ AGENDA_PROFISSIONAL : possui
    PACIENTE ||--o{ AGENDAMENTO : realiza
    AGENDA_PROFISSIONAL o|--o{ AGENDAMENTO : oferece
    AGENDAMENTO o|--o| PRE_ATENDIMENTO : origina
    PACIENTE ||--o{ PRE_ATENDIMENTO : recebe
    AGENDAMENTO o|--o| ATENDIMENTO : origina
    PRE_ATENDIMENTO o|--o| ATENDIMENTO : classifica
    PACIENTE ||--o{ ATENDIMENTO : recebe
    PRESTADOR o|--o{ ATENDIMENTO : executa
    EMPRESA ||--o{ SETOR : possui
    SETOR o|--o{ ATENDIMENTO : localiza
    ATENDIMENTO ||--o{ ATENDIMENTO_FLUXO : registra
    ATENDIMENTO ||--o{ ATENDIMENTO_PRESTADOR : vincula
    PRESTADOR ||--o{ ATENDIMENTO_PRESTADOR : participa
    ATENDIMENTO ||--o{ ATENDIMENTO_PROCEDIMENTO : possui
    PAINEL_CHAMADA ||--o{ PAINEL_CHAMADA_SETOR : atende
    SETOR ||--o{ PAINEL_CHAMADA_SETOR : chama
    ATENDIMENTO ||--o{ CHAMADA_PAINEL : gera
    ATENDIMENTO ||--o{ PRESCRICAO : possui
    ATENDIMENTO ||--o{ EVOLUCAO_ATENDIMENTO : possui
    PRESTADOR ||--o{ EVOLUCAO_ATENDIMENTO : registra
    ATENDIMENTO ||--o{ SOLICITACAO_EXAME : possui
    SOLICITACAO_EXAME ||--o| RESULTADO_EXAME : produz
    PACIENTE ||--o{ HISTORICO_ALTERACAO_PACIENTE : audita
    TABELA_AUXILIAR ||--o{ VALOR_AUXILIAR : possui
    MODULO ||--o{ DEFINICAO_TELA : possui
    DEFINICAO_TELA ||--o{ CAMPO_TELA : possui
```

## Observações

- Campos auxiliares em paciente e prestador ainda são armazenados como códigos textuais; a evolução recomendada é usar chaves estrangeiras para valores auxiliares estáveis.
- Agendamento sem agenda profissional representa demanda espontânea.
- Atendimento pode nascer de um agendamento ou diretamente da recepção.
## Adendo DER — documentos clínicos

```text
empresa 1--N modelo_documento
empresa 1--N documento_clinico
atendimento 1--N documento_clinico
modelo_documento 0--N documento_clinico
documento_clinico 0--N documento_clinico (cópia/origem)
usuario 0--N documento_clinico (emissor/auditoria)
```

`documento_clinico` sempre pertence à empresa ativa e a um atendimento. Dados oficiais do paciente, atendimento, empresa e usuário ficam em `ds_campos_bloqueados` para impedir edição manual dentro do documento.
