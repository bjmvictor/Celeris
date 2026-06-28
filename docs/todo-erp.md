# TODO ERP Celeris

## 1. Base técnica e governança
- [x] Definir padrões iniciais de navegação, subguias, barra de ações, permissões e auditoria.
- [ ] Padronizar todos os cadastros com consulta, inclusão, alteração, exclusão lógica e histórico.
- [ ] Garantir que todos os campos persistentes exibam `TABELA.COLUNA` na barra inferior.
- [ ] Criar catálogo de tabelas editáveis, relacionamentos, donos funcionais e regras de validação.
- [ ] Implantar trilha de auditoria por usuário, data/hora, empresa, IP e origem da operação.
- [ ] Criar suite E2E para fluxos críticos: cadastro, agendamento, atendimento, exame, prescrição e faturamento.

## 2. Assistencial — cadastros essenciais
- [ ] Paciente: dados pessoais, documentos, endereço, convênio, contato, responsável e alertas.
- [ ] Prestador: dados pessoais, profissionais, conselho, especialidades, agenda, vínculo e permissões assistenciais.
- [x] Empresa/unidade: CNES, endereço, contatos, setores, salas, recursos e parâmetros operacionais iniciais.
- [ ] Convênios, planos, procedimentos, especialidades, conselhos, medicamentos, exames e materiais.
- [ ] Tabelas auxiliares com carga mínima, importação, exportação, ordenação e inativação lógica.

## 3. Assistencial — agendamento e recepção
- [ ] Escalas de prestadores por unidade, sala, especialidade, dias, horários, intervalo e bloqueios.
- [ ] Geração de agenda baseada nas escalas, feriados, ausências, encaixes e indisponibilidades.
- [ ] Agendamento por paciente, especialidade, data, prestador, convênio, plano e procedimento.
- [x] Recepção de paciente agendado com revisão cadastral, confirmação de convênio e geração de atendimento.
- [x] Recepção de demanda espontânea com abertura direta de atendimento e encaminhamento para pré-atendimento.
- [ ] Reagendamento, cancelamento, faltas, confirmação e histórico de alterações do agendamento.

## 4. Assistencial — pré-atendimento e atendimento
- [ ] Classificação de risco com prioridade, queixa principal, sinais vitais e observações.
- [x] Fila assistencial/PEP baseada em atendimentos gerados, com abertura da ficha por `cd_atendimento`.
- [ ] Atendimento médico/enfermagem com anamnese, evolução, hipótese diagnóstica, CID e conduta.
- [ ] Prescrição assistencial com medicamentos, vias, frequência, duração e orientações.
- [ ] Solicitação de exames, procedimentos e encaminhamentos a partir do atendimento.
- [ ] Impressão/geração da ficha de atendimento, prescrição, pedidos e comprovantes.

## 5. Exames, medicações e apoio diagnóstico
- [ ] Cadastro de exames por setor, material, preparo, prazo, método e integração.
- [ ] Solicitação, coleta, execução, laudo, liberação e impressão de resultados.
- [ ] Cadastro de medicamentos, apresentações, estoque mínimo, vias, unidades e restrições.
- [ ] Administração de medicamentos com checagem, aprazamento, suspensão e histórico.
- [ ] Integração futura com laboratório, imagem, PACS/RIS, balanças, equipamentos e APIs externas.

## 6. Estoque e suprimentos
- [ ] Cadastro de produtos, materiais, lotes, validade, fornecedores e centros de custo.
- [ ] Entrada, saída, transferência, inventário, consumo assistencial e rastreabilidade.
- [ ] Baixa automática por atendimento, procedimento, exame e administração medicamentosa.
- [ ] Alertas de validade, estoque mínimo, divergência e necessidade de compra.

## 7. Faturamento e convênios
- [ ] Parametrizar contratos, planos, tabelas de preço, pacotes, regras e glosas.
- [ ] Gerar conta do atendimento a partir de consultas, exames, procedimentos, materiais e medicamentos.
- [ ] Conferência de conta, auditoria, fechamento, XML/arquivo de cobrança e envio.
- [ ] Controle de guias, autorizações, elegibilidade, retorno, recurso de glosa e demonstrativos.

## 8. Financeiro
- [ ] Contas a receber por particular, convênio, pacote, coparticipação e faturamento.
- [ ] Contas a pagar, fornecedores, compras, contratos, impostos e retenções.
- [ ] Caixa, bancos, conciliação bancária, formas de pagamento e repasses.
- [ ] Fluxo de caixa, inadimplência, baixa manual/automática e relatórios gerenciais.

## 9. Contábil e fiscal
- [ ] Plano de contas, centros de custo, natureza financeira e rateios.
- [ ] Integração financeiro-contábil por eventos: recebimento, pagamento, faturamento e estoque.
- [ ] Documentos fiscais, notas, impostos, retenções e exportações contábeis.
- [ ] Fechamento mensal com conciliações, travas por competência e relatórios.

## 10. Segurança, LGPD e operação
- [ ] Perfis por papel, tela, ação, empresa, unidade e escopo assistencial.
- [ ] Política de senha, bloqueio, expiração, MFA opcional e recuperação segura.
- [ ] LGPD: consentimento, finalidade, logs de acesso, anonimização e exportação de dados.
- [ ] Backups, restauração, monitoramento, logs, alertas e rotina de homologação.

## 11. Relatórios e indicadores
- [ ] Painéis de agendamento, recepção, fila, atendimento, exames, faturamento e financeiro.
- [ ] Relatórios operacionais exportáveis para CSV/XLSX/PDF.
- [ ] Indicadores de produção, tempo de espera, absenteísmo, glosas, receita e custo.
- [ ] Auditoria de alterações por tabela, usuário, tela, data e registro.

## 12. Ordem sugerida de implementação
- [ ] Fechar base de navegação, permissões, auditoria e componentes reutilizáveis.
- [ ] Homologar cadastros de paciente, prestador, convênio, tabelas auxiliares e empresa.
- [ ] Homologar agenda, recepção, pré-atendimento e atendimento.
- [ ] Homologar prescrições, exames, medicações e impressão.
- [ ] Homologar estoque assistencial e consumo por atendimento.
- [ ] Homologar faturamento, financeiro, contábil e fiscal.
## Atualização assistencial entregue

- [x] Calendário operacional para agendamentos com data atual, troca de mês, feriados, dias com agenda e intervalo de datas.
- [x] Seleção de agenda com calendário, múltiplas especialidades, pesquisa e confirmação somente após escolher horário.
- [x] Comprovante de agendamento imprimível e reimprimível por protocolo.
- [x] PEP com filtros por atendimento ou busca geral, lista baseada em atendimentos gerados e retorno para a ficha.
- [x] Ficha de atendimento com resumo inicial, navegação lateral, ações clínicas por papel e lista de documentos.
- [x] Documento clínico com status, marca d'água, cópia como rascunho e modelos administrativos básicos.
- [ ] Evoluir editor de documentos para componentes estruturados, assinatura digital, auditoria de impressão e versionamento de modelos.
