# Mapa de risco de tenant — Atendimento

## Escopo e contrato-alvo

Esta é uma auditoria estática, sem alteração de código produtivo, de `apps.atendimento`.
O contrato alvo é `apps.platform.tenancy.empresa_atual(request)`: usuário autenticado,
`cd_empresa` explícito na sessão, empresa e vínculo `UsuarioEmpresa` ativos e falha
fechada, traduzida por `proteger_contexto_tenant` para logout/redirecionamento.

O contrato legado encontrado é `views._empresa_logada(request)` (linhas 10259–10261):

```python
cd_empresa = request.session.get("cd_empresa") or 1
return get_object_or_404(Empresa, cd_empresa=cd_empresa, sn_ativo=True)
```

Ele recebe somente `request`, lê a sessão e faz fallback para a empresa `1`; confirma
apenas que a empresa está ativa, não verifica autenticação nem `UsuarioEmpresa`, e
converte ausência/inatividade em 404. No inventário inicial havia **86 chamadas em
85 funções consumidoras**. Após os Lotes A, B, C e D, restam
**40 chamadas em 39 funções consumidoras**. As linhas ainda dependentes dele são R4:
o fallback torna insegura uma troca mecânica, mesmo onde os querysets posteriores já
filtram por empresa. Quarenta e seis consumidores usam agora `empresa_atual` com
`proteger_contexto_tenant`; Atendimento ainda não trata `TenantContextError` localmente.

Abreviações: `H` = `_empresa_logada`; `login/role` descreve os decoradores efetivos;
`delegado` é helper interno alcançado por uma view autenticada. O motivo `H: fallback 1`
é a evidência concreta comum de R4. Onde a URL/POST recebe um ID, a coluna destaca o
escopo observado por `cd_empresa` ou pelo pai.

## Mapa por consumidor de resolução

| # | Consumidor | Arquivo | Tipo | Auth | Origem tenant | L/E | Objetos afetados | Isolamento atual | Risco | Motivo | Migração sugerida |
| - | - | - | - | - | - | - | - | - | - | - | - |
| 1 | `_editable_convenios` | views.py | cadastro | delegado | `empresa_atual` | L/E | Convenio | queryset e criação/escrita por empresa canônica | R2 | Lote D; rota delegada validada | tenant canônico |
| 2 | `_editable_prestadores` | views.py | cadastro | delegado | `empresa_atual` | L/E | Prestador | queryset e criação/escrita por empresa canônica | R2 | Lote D; helper permanece sem URL própria | tenant canônico |
| 3 | `cadastro_profissional` | views.py | cadastro | login/TI | `empresa_atual` | L/E | Prestador, PrestadorTipo | prestador URL/GET/POST e relação por empresa canônica | R2 | Lote D; tipos são catálogo global, vínculo é T | tenant canônico |
| 4 | `alternar_status_prestador` | views.py | cadastro | login/TI | `empresa_atual` | E | Prestador | busca URL por empresa canônica | R2 | Lote D; ID URL scoped | tenant canônico |
| 5 | `liberar_trava_prestador` | views.py | cadastro | login/TI | `empresa_atual` | E | Prestador | busca URL por empresa canônica | R2 | Lote D; ID URL scoped | tenant canônico |
| 6 | `adquirir_trava_prestador` | views.py | cadastro | login/TI | `empresa_atual` | E | Prestador | busca URL por empresa canônica | R2 | Lote D; ID URL scoped | tenant canônico |
| 7 | `iniciar_pre_atendimento` | views.py | triagem | login/Enfermeiro | `empresa_atual` | E | Agendamento, PreAtendimento | agendamento e paciente por empresa canônica | R2 | Lote C; ID URL e invariante agendamento→paciente | tenant canônico |
| 8 | `iniciar_pre_atendimento_atendimento` | views.py | triagem | login/Enfermeiro | `empresa_atual` | E | Atendimento, PreAtendimento | atendimento e paciente por empresa canônica | R2 | Lote C; ID URL e invariante atendimento→paciente | tenant canônico |
| 9 | `iniciar_atendimento` | views.py | atendimento | login/Recepcionista,Médico | `empresa_atual` | E | Agendamento, Atendimento | agendamento, paciente e agenda por empresa canônica | R2 | Lote C; ID URL e FKs derivados protegidos | tenant canônico |
| 10 | `recepcao` | views.py | atendimento | login/Recepcionista | `empresa_atual` | L | SenhaAtendimento, Paciente | listas e senha/paciente por empresa canônica | R2 | Lote C; GET e relações de senha filtrados | tenant canônico |
| 11 | `recepcao_revisar_paciente` | views.py | cadastro | login/Recepcionista | `empresa_atual` | L/E | Paciente, Atendimento | paciente URL e atendimento aberto por empresa canônica | R2 | Lote C; ID URL scoped | tenant canônico |
| 12 | `agendamentos_operacionais` | views.py | agenda | login/Recepcionista | `empresa_atual` | L | Agendamento | queryset por empresa canônica | R2 | Lote B concluído | tenant canônico |
| 13 | `recepcionar_agendamento` | views.py | agenda | login/Recepcionista | `empresa_atual` | E | Agendamento, Atendimento | agendamento e paciente por empresa canônica | R2 | Lote C; ID URL e invariante agendamento→paciente | tenant canônico |
| 14 | `documentos_telas_impressao` | views.py | configuração | login/TI | H | L/E | ModeloDocumento, Tela | filtros por empresa | R4 | H: fallback 1 | lote documentos |
| 15 | `cadastro_atendimento` | views.py | atendimento | login/Recepcionista | `empresa_atual` | L/E | Atendimento, Paciente, Agendamento, Senha | IDs URL/GET e forms por empresa canônica | R2 | Lote C; paciente, agenda, senha, prestador e convênio protegidos | tenant canônico |
| 16 | `ficha_atendimento` | views.py | atendimento | login | H | L | Atendimento, itens | atendimento por empresa | R4 | H: fallback 1; ID URL | lote ficha clínica |
| 17 | `abrir_modelo_assistencial` | views.py | atendimento | login | H | L/E | Atendimento, ItemMenu | atendimento/pai por empresa | R4 | H: fallback 1; IDs URL | lote ficha clínica |
| 18 | `perfis_assistenciais` | views.py | configuração | login/TI | `empresa_atual` | L/E | Perfil, versão, itens, escala, modelo | perfil e relações T por empresa canônica; modelo G/T | R2 | Lote D; POST de escala/modelo externo rejeitado | tenant canônico |
| 19 | `perfil_assistencial_itens_api` | views.py | API | login/TI | `empresa_atual` | L/E | Perfil, versão, ItemMenu | perfil URL e itens derivados por empresa canônica | R2 | Lote D; modelo G/T já validado pela API | tenant canônico |
| 20 | `publicar_perfil_assistencial_api` | views.py | API | login/TI | `empresa_atual` | E | Perfil, versão | perfil URL e versão derivada por empresa canônica | R2 | Lote D; ID URL scoped | tenant canônico |
| 21 | `solicitar_exame` | views.py | exames | login/Médico | H | E | Atendimento, SolicitaçãoExame | atendimento por empresa; serviço recebe empresa | R4 | H: fallback 1; ID URL | lote prescrição/exames |
| 22 | `resultado_exame` | views.py | exames | login/TI | H | E | SolicitaçãoExame, Resultado | solicitação por empresa | R4 | H: fallback 1; ID URL | lote prescrição/exames |
| 23 | `prescrever` | views.py | prescrição | login/Médico | H | E | Atendimento, Prescrição | atendimento por empresa; serviço recebe empresa | R4 | H: fallback 1; ID URL | lote prescrição/exames |
| 24 | `evoluir` | views.py | PEP legado | login/Médico | H | E | Atendimento, Evolução | atendimento por empresa | R4 | H: fallback 1; ID URL | lote ações clínicas |
| 25 | `_cadastro_configuracao_prescricao` | views.py | configuração | delegado | H | L/E | classes, vias, itens | filtros por empresa | R4 | H: fallback 1 | lote prescrição/exames |
| 26 | `conceder_alta` | views.py | alta | login/Médico | H | E | Atendimento, Alta | atendimento por empresa | R4 | H: fallback 1; ID URL | lote alta |
| 27 | `documento_assistencial` | views.py | documentos | login/Médico | H | E | Atendimento, DocumentoClinico | atendimento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 28 | `finalizar_atendimento` | views.py | atendimento | login/Médico | H | E | Atendimento | atendimento por empresa | R4 | H: fallback 1; ID URL | lote alta |
| 29 | `imprimir_atendimento` | views.py | impressão | login | H | L | Atendimento, documentos | atendimento por empresa | R4 | H: fallback 1; ID URL | lote impressão |
| 30 | `modelos_documento` | views.py | documentos | login/TI | H | L/E | ModeloDocumento | queryset e POST por empresa | R4 | H: fallback 1; ID URL | lote documentos |
| 31 | `testar_variavel_documento` | views.py | AJAX | login/TI | H | L | ModeloDocumento | modelo por empresa | R4 | H: fallback 1; POST | lote documentos |
| 32 | `rascunho_editor_documento` | views.py | AJAX | login/TI | H | L/E | ModeloDocumento, Rascunho | modelo por empresa | R4 | H: fallback 1; POST | lote documentos |
| 33 | `preview_pdf_modelo_documento` | views.py | impressão | login | H | L | ModeloDocumento | modelo por empresa | R4 | H: fallback 1; GET | lote impressão |
| 34 | `imprimir_documento_clinico` | views.py | impressão | login | H | L | DocumentoClinico | documento por empresa | R4 | H: fallback 1; ID URL | lote impressão |
| 35 | `assumir_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico, locks | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 36 | `fechar_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico, evento | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 37 | `abandonar_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico, locks | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 38 | `cancelar_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico, evento | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 39 | `liberar_trava_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico, locks | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 40 | `liberar_acesso_excepcional_documento` | views.py | documentos | login | H | E | DocumentoClinico, locks | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 41 | `link_externo_assistencial` | views.py | integração | login | H | L | Atendimento, ItemMenu | atendimento/item por empresa | R4 | H: fallback 1; IDs URL | lote ficha clínica |
| 42 | `executar_escala_clinica` | views.py | classificação | login | H | L/E | Atendimento, Escala | atendimento/item por empresa | R4 | H: fallback 1; IDs URL/POST | lote classificação clínica |
| 43 | `testar_escala_clinica` | views.py | AJAX | login/TI,Enfermeiro | H | L | Escala, perguntas | escala por empresa | R4 | H: fallback 1; POST | lote classificação clínica |
| 44 | `anexos_clinicos` | views.py | documentos | login | H | L/E | Atendimento, Anexo | atendimento/item por empresa | R4 | H: fallback 1; IDs URL/POST | lote documentos clínicos |
| 45 | `baixar_anexo_clinico` | views.py | documentos | login | H | L | AnexoClinico | anexo por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 46 | `historico_documentos_assistencial` | views.py | documentos | login | H | L | Atendimento, DocumentoClinico | atendimento/item por empresa | R4 | H: fallback 1; IDs URL | lote documentos clínicos |
| 47 | `copiar_documento_clinico` | views.py | documentos | login | H | E | DocumentoClinico | documento por empresa | R4 | H: fallback 1; ID URL | lote documentos clínicos |
| 48 | `_editable_escalas` | views.py | cadastro | delegado | `empresa_atual` | L/E | AgendaProfissional, Prestador | queryset, criação e prestador POST por empresa canônica | R2 | E1; prestador POST scoped antes da escrita | tenant canônico |
| 49 | `cadastro_escala` | views.py | agenda | login/TI | `empresa_atual` | L/E | AgendaProfissional, Prestador, Setor, Convenio | escala URL e form FKs T por empresa canônica; especialidade G | R2 | E1; EscalaForm já restringe FKs T | tenant canônico |
| 50 | `alternar_status_escala` | views.py | agenda | login/TI | `empresa_atual` | E | AgendaProfissional | escala URL por empresa canônica antes da escrita | R2 | E1; ID externo retorna 404 | tenant canônico |
| 51 | `_agenda_dashboard` | views.py | agenda | delegado | `empresa_atual` | L | Agendamento, AgendaProfissional, Prestador | contagens, especialidades, horários e lista por empresa canônica | R1 | E1; agregações não atravessam empresa | tenant canônico |
| 52 | `_fila_atendimento` | views.py | triagem | delegado | `empresa_atual` | L | Agendamento, Paciente | queryset e pai por empresa canônica | R2 | Lote C; rota delegada validada | tenant canônico |
| 53 | `alteracao_atendimento` | views.py | atendimento | login/Recepcionista,Enfermeiro,Médico | `empresa_atual` | L/E | Atendimento, Paciente, Responsável | ID URL/GET/POST e pai por empresa canônica | R2 | Lote C; reselect `select_for_update` scoped | tenant canônico |
| 54 | `atendimentos` | views.py | atendimento | login/Recepcionista,Enfermeiro,Médico | `empresa_atual` | L | Atendimento, Paciente | queryset e GET por empresa canônica | R2 | Lote C; registros inconsistentes ocultos | tenant canônico |
| 55 | `pep_chamar` | views.py | painel | login/TI,Médico,Enfermeiro | H | E | Atendimento, Máquina, Painel | atendimento/setor/máquina por empresa | R4 | H: fallback 1; POST IDs | lote painel/chamada |
| 56 | `paineis_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | PainelChamada, Setor | painel, ID URL e form por empresa canônica | R2 | tratado no Lote A | concluído: painel/chamada admin |
| 57 | `alternar_status_painel_chamada` | views.py | painel | login/TI | `empresa_atual` | E | PainelChamada | busca por empresa canônica | R2 | tratado no Lote A; ID URL scoped | concluído: painel/chamada admin |
| 58 | `configurar_senhas` | views.py | configuração | login/TI | `empresa_atual` | L/E | TipoSenha, classe, protocolo | filtros e referências POST por empresa canônica | R2 | tratado no Lote A; ícone/protocolo POST scoped | concluído: painel/chamada admin |
| 59 | `alternar_status_configuracao_senha` | views.py | configuração | login/TI | `empresa_atual` | E | TipoSenhaAtendimento | busca por empresa canônica | R2 | tratado no Lote A; ID URL scoped | concluído: painel/chamada admin |
| 60 | `_tabela_totem` | views.py | cadastro | delegado | `empresa_atual` | L/E | ClasseSenhaAtendimento, ProtocoloSenhaAtendimento, Icone, Cor | queryset e IDs POST por empresa canônica | R2 | E2; ícone/cor POST scoped antes da escrita | tenant canônico |
| 61 | `cores_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | CorClassificacaoRisco | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 62 | `perguntas_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | PerguntaClassificacao | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 63 | `fluxos_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | FluxoClassificacao | IDs e cor recomendada POST scoped por empresa | R2 | tratado no Lote A; cor POST scoped | concluído: classificação admin |
| 64 | `fluxo_escalas_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | Fluxo, Escala | fluxo URL e escalas POST por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 65 | `icones_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | IconeChamada | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: painel/chamada admin |
| 66 | `maquinas_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | MaquinaChamada | queryset e setor POST por empresa canônica | R2 | tratado no Lote A; setor POST scoped | concluído: painel/chamada admin |
| 67 | `imprimir_senha_totem` | views.py | impressão | login/TI,Recepcionista,Enfermeiro | `empresa_atual` | L | SenhaAtendimento | senha e pais T por empresa canônica | R2 | E2; ID URL e cadeia Senha→pais scoped | tenant canônico |
| 68 | `acao_senha_classificacao` | views.py | classificação | login/Enfermeiro | `empresa_atual` | E | SenhaAtendimento, ChamadaPainel | senha e pais T resolvidos antes da transição | R3 | E2; estado e painel preservados após escopo | tenant canônico |
| 69 | `chamar_agendamento_classificacao` | views.py | classificação | login/Enfermeiro | `empresa_atual` | E | Agendamento, Paciente, ChamadaPainel | agendamento e pais T por empresa canônica | R3 | E2; ID URL e relações inconsistentes retornam 404 | tenant canônico |
| 70 | `imprimir_classificacao` | views.py | impressão | login/Enfermeiro | `empresa_atual` | L | Senha, Agendamento, DocumentoClinico | IDs GET e pais T por empresa canônica | R3 | E2; impressão não aceita referência externa | tenant canônico |
| 71 | `fila_classificacao` | views.py | classificação | login/Enfermeiro | `empresa_atual` | L/E | Senha, Agendamento, PreAtendimento | filas/agregados e pais T por empresa canônica | R3 | E2; itens estruturalmente inconsistentes são omitidos/404 | tenant canônico |
| 72 | `escalas_classificacao_standalone` | views.py | classificação | login/TI | `empresa_atual` | L/E | EscalaClinica | escala URL/POST por empresa canônica | R3 | E2; standalone é autenticado e session-based | tenant canônico |
| 73 | `fila_medica` | views.py | atendimento | login/Médico | `empresa_atual` | L | Atendimento, Paciente | queryset por empresa canônica | R2 | Lote C; invariante atendimento→paciente | tenant canônico |
| 74 | `abrir_consulta` | views.py | atendimento | login/Médico | `empresa_atual` | E | Atendimento, Paciente | atendimento URL por empresa canônica | R2 | Lote C; ID URL e invariante atendimento→paciente | tenant canônico |
| 75 | `gerar_agenda` | views.py | agenda | login/TI,Recepcionista | `empresa_atual` | E | AgendaProfissional, AgendaGerada, HorarioAgenda | escala POST, agenda gerada e horários por empresa canônica | R3 | E1; escala e todos os registros criados mantêm a mesma empresa | tenant canônico |
| 76 | `agendar_consultar_paciente` | views.py | agenda | login/Recepcionista | `empresa_atual` | L | Paciente, Agendamento | querysets por empresa canônica | R2 | Lote B; GET scoped | tenant canônico |
| 77 | `cadastro_paciente` | views.py | cadastro | login/Recepcionista | `empresa_atual` | L/E | Paciente | Paciente diretamente tenant-scoped | R2 | Lote B; URL/GET scoped | tenant canônico |
| 78 | `alternar_status_paciente` | views.py | cadastro | login/TI | `empresa_atual` | E | Paciente | busca por empresa canônica | R2 | Lote B; ID URL scoped | tenant canônico |
| 79 | `selecionar_agenda` | views.py | agenda | login/Recepcionista | `empresa_atual` | L | Paciente, Agenda | paciente e slots por empresa canônica | R2 | Lote B; IDs URL/GET scoped | tenant canônico |
| 80 | `confirmar_horario_agenda` | views.py | agenda | login/Recepcionista | `empresa_atual` | E | Paciente, Horário | paciente e slot por empresa canônica | R2 | Lote B; IDs URL/POST scoped | tenant canônico |
| 81 | `comprovante_agendamento` | views.py | impressão | login/Recepcionista | `empresa_atual` | L | Agendamento | agendamento por empresa canônica | R2 | Lote B; ID URL scoped | tenant canônico |
| 82 | `cancelar_agendamento` | views.py | agenda | login/TI,Recepcionista | `empresa_atual` | E | Agendamento | agendamento por empresa canônica | R2 | Lote B; ID URL scoped | tenant canônico |
| 83 | `confirmar_agendamento` | views.py | agenda | login/Recepcionista | `empresa_atual` | E | Paciente, Agendamento | paciente URL e criação por empresa canônica | R2 | Lote B; POST não escolhe empresa | tenant canônico |
| 84 | `demanda_espontanea` | views.py | atendimento | login/Recepcionista | H | E | Paciente, Atendimento | paciente por empresa | R4 | H: fallback 1; POST | lote recepção/triagem |
| 85 | `verificar_paciente_unico` | views.py | AJAX | login | `empresa_atual` | L | Paciente | unicidade preservada por empresa canônica | R2 | Lote B; GET scoped | tenant canônico |
| 86 | `screen` | views.py | roteamento | login; papéis por tela | dispatcher separado | L/E | cadastros, agenda, fila | destinos E1 (`escalas`, `agendas`) agora canônicos; convênios, profissionais e fila já canônicos; auxiliares são G | fora da contagem | permanece dispatcher; não alterar até contrato de todos os destinos estar explícito | fora do E1 |
| 87 | `painel_chamada_publico` | views_painel.py | painel | público/dispositivo | máquina, sessão opcional, POST empresa | L/E | Máquina, Painel, Chamada | empresa pode vir de POST; máquina pode migrar | R5 | contrato público de dispositivo; `Empresa.objects` global e POST `empresa` | definir contrato de máquina/autorização |
| 88 | `midia_painel_publica` | views_painel.py | integração | público | painel por PK | L | PainelChamada, arquivo | `get_object_or_404(...pk...)` sem empresa | R5 | endpoint público de mídia por ID | preservar URL assinada/escopo de painel |
| 89 | `AtendimentoDemoSeedProvider.handle` | demo_seed.py | comando | sessionless | `empresa_codigo` explícito | L/E | Empresa e dados demo | valida slot e cria tudo para a empresa | R5 | comando/seed não possui request | manter contrato explícito de comando |

## Contratos de suporte e falsos positivos

Estes itens usam ou transportam empresa, mas **não** resolvem o tenant HTTP; não
integram o total 89 acima.

| Contrato | Arquivo | Origem | L/E | Avaliação |
| - | - | - | - | - |
| `perfis_assistenciais_usuario(usuario, empresa)` | services/perfis_assistenciais.py | argumento `empresa` | L | R1: filtros de perfil por argumento explícito. |
| `contexto_acao_prescricao(request, atendimento, ...)` | services/prescricoes.py | `atendimento.cd_empresa` | L | R1: o pai já determina a empresa. |
| `registrar_itens_prescricao(empresa, atendimento, ...)` | services/prescricoes.py | argumento explícito | E | R3: filtra itens/documento por empresa, mas não valida que `atendimento.cd_empresa == empresa`; manter callers tenant-safe e adicionar caracterização antes de expor o serviço. |
| `paineis_compativeis_atendimento/agendamento/senha` | views_painel.py | objeto pai | L | R1: filtra painéis pela empresa do pai. |
| `publish_atendimento_created` | signals.py | `instance.cd_empresa_id` | E/evento | R1: evento carrega tenant do aggregate; sem request. |
| `sync_clinical_profiles` | signals.py | nenhum | E/global | não é tenant: pós-migração de grupos/permissões globais. |
| Forms com `empresa=` (`TipoSenha`, `RegraSubdivisao`, `Escala`, `Painel`, `PreAtendimento`, `Atendimento`, `Cadastro`, `Alteracao`, `Responsavel`, `ItemPrescricao`, `ItemPrescricaoDocumento`) | forms.py | argumento explícito | L | não resolvem tenant; vários querysets usam o argumento. |
| `limpar_rascunhos_do_usuario` | public.py | usuário | E | não é tenant; remove rascunhos do usuário. |

Ocorrências de `cd_empresa` em models/migrations representam FKs, constraints e
operações históricas; não são resolução runtime. Os demais `or 1`/`else 1` em
`views.py` são paginação, layout, PDF, versão ou limites numéricos. A única
ocorrência de fallback de tenant é a linha 10260. Não há `cd_empresa=1` ou
`empresa_id=1` em produção fora desse fallback.

## PEP legado remanescente

`urls.py` já delega `/pep/` e `/pep/pacientes/<id>/` para
`apps.applications.pep.views`: categoria **A — compatibilidade/rota legada**.
`pep_chamar` permanece em Atendimento: categoria **B — ação clínica temporária**,
pois cria `ChamadaPainel` a partir de Atendimento/Máquina/Setor. `evoluir`,
prescrição, exames, documentos e alta são também **B**, ações clínicas ainda
pertencentes temporariamente a Atendimento. Não foi identificado código morto
por esta busca de tenant.

## Planejamento pós-Lote D — consumidores legados

### Recontagem confirmada

No código atual, `_empresa_logada` é definido uma vez em `views.py` e resolve
`request.session["cd_empresa"] or 1`. A busca estrutural confirma **45 chamadas**
em **44 funções consumidoras diretas** (a segunda chamada está em
`testar_escala_clinica`) e **41 chamadas** a `empresa_atual`. A tabela abaixo
contém somente as 44 funções diretas; `screen` e os contratos R5 estão em
seções separadas porque não são consumidores diretos do helper.

`Risco antigo` é a classificação herdada do mapa (R4 pelo fallback). `Risco
intrínseco` ignora esse fallback: R1 é leitura autenticada sem ID perigoso, R2
é escrita simples com pai já scoped, R3 requer validação coordenada, R4 exige
evidência concreta independente e R5 exige contrato que não é HTTP autenticado.
Não há evidência suficiente, nesta etapa documental, para classificar algum dos
44 consumidores diretos como R4 ou R5.

| Consumidor | Categoria | L/E | Auth | Objetos | IDs externos | Contrato tenant | Risco antigo | Risco intrínseco | Motivo | Lote sugerido |
| - | - | - | - | - | - | - | - | - | - | - |
| `documentos_telas_impressao` | configuração documental | L/E | TI | tela, modelo, impressão | tela/modelo POST | tela T; modelo G/T | R4 | R3 | formulário e relações mistas | E3 |
| `ficha_atendimento` | consulta/navegação | L | médico | Atendimento, Paciente, Prestador | atendimento URL | Atendimento e Paciente T | R4 | R3 | abre o agregado clínico e suas ações | E4 |
| `abrir_modelo_assistencial` | documento clínico | E | médico | Atendimento, modelo, Documento | atendimento/modelo | atendimento T; modelo G/T | R4 | R3 | cria/abre documento a partir de dois pais | E4 |
| `solicitar_exame` | exames | L/E | médico | Atendimento, solicitação, item | atendimento/POST | Atendimento T e itens válidos | R4 | R3 | criação clínica e itens POST | E6 |
| `resultado_exame` | exames | L/E | médico | solicitação, resultado | solicitação URL | solicitação derivada de Atendimento T | R4 | R3 | ID clínico e transição de estado | E6 |
| `prescrever` | prescrição | L/E | médico | Atendimento, prescrição, itens | atendimento/POST | empresa deve igualar atendimento | R4 | R3 | formset e serviço com empresa explícita | E6 |
| `evoluir` | evolução | E | médico | Atendimento, Documento/Evolução | atendimento/POST | Atendimento T e permissões Editor | R4 | R3 | escrita clínica/documental | E7 |
| `_cadastro_configuracao_prescricao` | configuração prescrição | L/E | TI | configuração, itens, produto | GET/POST | catálogos e configuração T | R4 | R3 | múltiplos catálogos e formulário | E6 |
| `conceder_alta` | alta | E | médico | Atendimento, alta, eventos | atendimento URL/POST | Atendimento T | R4 | R3 | estado terminal e efeitos secundários | E8 |
| `documento_assistencial` | documento clínico | L/E | médico | Atendimento, Documento, Editor | atendimento URL/tipo | Atendimento T; política Editor | R4 | R3 | fronteira Atendimento–Editor | E4 |
| `finalizar_atendimento` | alta/finalização | E | médico | Atendimento, estado, eventos | atendimento URL/POST | Atendimento T | R4 | R3 | transição terminal distinta da alta | E8 |
| `imprimir_atendimento` | impressão | L | autenticado | Atendimento, Paciente, PDF | atendimento URL | Atendimento e Paciente T | R4 | R3 | impressão recebe ID clínico | E8 |
| `modelos_documento` | configuração documental | L/E | TI | modelo, campos, telas | modelo URL/POST | modelo G/T e tela T | R4 | R3 | relações de configuração cruzadas | E3 |
| `testar_variavel_documento` | API/AJAX documental | L | TI | modelo, contexto de teste | parâmetros POST | modelo/contexto autorizados | R4 | R3 | endpoint auxiliar expõe renderização | E3 |
| `rascunho_editor_documento` | API/AJAX documental | L/E | médico | Documento, rascunho | documento/POST | Documento via Atendimento T | R4 | R3 | estado concorrente de documento | E3 |
| `preview_pdf_modelo_documento` | impressão/API | L | TI | modelo, PDF | modelo/POST | modelo G/T autorizado | R4 | R3 | preview recebe identificador de modelo | E3 |
| `imprimir_documento_clinico` | impressão documental | L | médico | Documento, PDF | documento URL | Documento → Atendimento T | R4 | R3 | PDF por ID clínico | E5 |
| `assumir_documento_clinico` | lock documental | E | médico | Documento, lock, evento | documento URL | Documento → Atendimento T | R4 | R3 | lock e auditoria compartilhados | E4 |
| `fechar_documento_clinico` | lock documental | E | médico | Documento, assinatura, evento | documento URL/POST | Documento → Atendimento T | R4 | R3 | assinatura, hash e lock | E4 |
| `abandonar_documento_clinico` | lock documental | E | médico | Documento, lock | documento URL | Documento → Atendimento T | R4 | R3 | mudança de posse do lock | E4 |
| `cancelar_documento_clinico` | lock documental | E | médico | Documento, evento | documento URL | Documento → Atendimento T | R4 | R3 | cancelamento auditável | E4 |
| `liberar_trava_documento_clinico` | lock documental | E | médico | Documento, lock | documento URL | Documento → Atendimento T | R4 | R3 | bypass de lock precisa de autorização | E4 |
| `liberar_acesso_excepcional_documento` | lock documental | E | médico | Documento, acesso excepcional | documento URL | Documento → Atendimento T | R4 | R3 | autorização excepcional e auditoria | E4 |
| `link_externo_assistencial` | consulta/navegação | L | autenticado | Atendimento, link | atendimento URL | Atendimento T | R4 | R3 | navegação depende do agregado clínico | E5 |
| `executar_escala_clinica` | escala clínica | L/E | médico | Atendimento, item, respostas | atendimento/item/POST | pais e item da escala T | R4 | R3 | respostas e classificação clínica | E7 |
| `testar_escala_clinica` | API/AJAX escala | L | TI | escala, item, respostas | POST | escala e itens T | R4 | R3 | duas chamadas ao helper; simulação POST | E7 |
| `anexos_clinicos` | anexos documentais | L/E | médico | Atendimento, item, anexo | atendimento/item | pais T e arquivo derivado | R4 | R3 | upload/listagem de arquivo clínico | E5 |
| `baixar_anexo_clinico` | anexo/impressão | L | médico | anexo, Documento/Atendimento | anexo URL | anexo → pai T | R4 | R3 | download por PK exige cadeia de posse | E5 |
| `historico_documentos_assistencial` | histórico documental | L | médico | Atendimento, item, Documento, evento | atendimento/item | pais e eventos T | R4 | R3 | histórico clínico por IDs | E5 |
| `copiar_documento_clinico` | documento clínico | E | médico | Documento origem/destino, evento | documento URL | origem e destino no Atendimento T | R4 | R3 | cópia preserva contexto e eventos | E5 |
| `_editable_escalas` | agenda/configuração | L/E | TI | Escala, Agenda | GET/POST | Escala/Agenda T | R4 | R2 | CRUD relacional simples já delimitável | E1 |
| `cadastro_escala` | agenda/configuração | L/E | TI | Escala, Agenda | escala URL/POST | Escala/Agenda T | R4 | R2 | escrita simples com ID scoped | E1 |
| `alternar_status_escala` | agenda/configuração | E | TI | Escala | escala URL | Escala T | R4 | R2 | transição simples por objeto T | E1 |
| `_agenda_dashboard` | agenda/leitura | L | autenticado | Agenda, Prestador, Setor | sem ID de objeto | queries por empresa | R4 | R1 | painel autenticado sem objeto cliente | E1 |
| `pep_chamar` | PEP/chamada | E | médico | Atendimento, Máquina, Setor, ChamadaPainel | atendimento/máquina | todos T e máquina vinculada | R4 | R3 | ponte para painel/dispositivo | E9 |
| `_tabela_totem` | classificação/leitura | L | autenticado | Senha, TipoSenha, fila | filtros de tela | Senha e configurações T | R4 | R1 | tabela sem escrita clínica | E2 |
| `imprimir_senha_totem` | classificação/impressão | L | autenticado | Senha, PDF | senha URL | Senha T | R4 | R2 | impressão por ID scoped | E2 |
| `acao_senha_classificacao` | classificação | E | autenticado | Senha, Atendimento, estado | senha URL/ação | Senha e Atendimento T | R4 | R3 | muda estado de senha clínica | E2 |
| `chamar_agendamento_classificacao` | classificação | E | autenticado | Agendamento, Senha, Atendimento | agendamento URL | Agendamento/Paciente T | R4 | R3 | cria/associa objetos clínicos | E2 |
| `imprimir_classificacao` | classificação/impressão | L | autenticado | Classificação, Atendimento, PDF | classificação/atendimento | agregado de classificação T | R4 | R3 | PDF usa agregado clínico | E2 |
| `fila_classificacao` | classificação/fila | L/E | autenticado | PreAtendimento, Atendimento, Senha | filtros/POST | fila e paciente T | R4 | R3 | entrada e transições da triagem | E2 |
| `escalas_classificacao_standalone` | classificação/configuração | L/E | TI | Escala, respostas, protocolos | escala/POST | Escala e relações T | R4 | R3 | catálogo assistencial e relações | E2 |
| `gerar_agenda` | agenda | E | TI | Agenda, Escala, Agendamento | POST | Agenda/Escala/Prestador T | R4 | R3 | criação transacional de agenda | E1 |
| `demanda_espontanea` | recepção/triagem | L/E | autenticado | Paciente, Atendimento, PreAtendimento | POST | Paciente e novo Atendimento T | R4 | R3 | cria entrada clínica com múltiplos pais | E10 |

**Reclassificação dos 44 diretos:** R1 = 2, R2 = 4, R3 = 38, R4 = 0, R5 = 0.
R3 não é prova de vulnerabilidade: é a prioridade de caracterização e testes de
cadeias pai-filho, permissões e efeitos clínicos antes da troca do helper.

### Categorias, dependências e fronteiras

Dependências que determinam a ordem (e não apenas a proximidade no arquivo):

- `screen -> _editable_escalas / _agenda_dashboard`; os demais destinos são
  migrações A–D, catálogos globais ou rotas próprias.
- `fila_classificacao -> PreAtendimento -> Atendimento -> Paciente`;
  `acao_senha_classificacao -> Senha -> Atendimento`; e
  `chamar_agendamento_classificacao -> Agendamento -> Paciente -> Atendimento/Senha`.
- `prescrever -> contexto_acao_prescricao(atendimento.cd_empresa) ->
  registrar_itens_prescricao(empresa, atendimento, ...)`.
- `documento_assistencial` e `abrir_modelo_assistencial -> selectors/permissões
  públicos do Editor -> DocumentoClinico`; lifecycle/locks ->
  `EventoDocumentoClinico` e responsabilidade compartilhada de lock.
- `evoluir -> Atendimento -> DocumentoClinico/Editor`; `conceder_alta` e
  `finalizar_atendimento -> Atendimento -> eventos/impressão`; e
  `pep_chamar -> Atendimento + Máquina + Setor -> ChamadaPainel`.

Consulta médica separa navegação (`ficha_atendimento`, `link_externo_assistencial`)
de escrita clínica (documentos/locks, evolução, prescrição, exames, escalas e
alta). A navegação depende da cadeia `Atendimento -> Paciente`; as escritas
devem preservar APIs do Editor, eventos, assinatura e locks, portanto não formam
um lote único.

Na classificação/triagem, testar que Atendimento e Paciente pertencem à empresa
canônica; que PreAtendimento, Senha, Agendamento e Classificação só referenciam
esse agregado; e que Escala, protocolo, itens/respostas e TipoSenha pertencem à
empresa da fila. Relações históricas incoerentes no banco não autorizam a view a
atravessar a fronteira.

O serviço de prescrição deriva `empresa` de `atendimento.cd_empresa` em
`contexto_acao_prescricao` e filtra classes/itens/vias pela empresa. Em contraste,
`registrar_itens_prescricao(empresa, atendimento, ...)` recebe empresa
explicitamente. Antes de E6, cada chamador deve provar
`empresa == atendimento.cd_empresa` e a mesma empresa para documento, itens,
vias e produtos; não há alteração de serviço neste lote de planejamento.

Documentos, evolução e anexos dependem dos selectors/permissões públicos do
Editor e dos locks compartilhados. A ordem é lifecycle/locks antes de leitura,
impressão, anexos e cópia; evolução apenas após essas fronteiras. Alta é coesa
para lote próprio: transição terminal de Atendimento, eventos/efeitos secundários
e sua impressão, sem criação documental.

### APIs/AJAX e impressões

| Endpoint | Auth/parâmetros | Retorno e objetos | Condição de migração |
| - | - | - | - |
| `testar_variavel_documento` | TI; POST modelo/contexto | preview de variável | não revelar modelo/contexto de outra empresa |
| `rascunho_editor_documento` | médico; POST/Documento | rascunho Editor | Documento derivado de Atendimento T |
| `preview_pdf_modelo_documento` | TI; modelo/POST | PDF de modelo | autorização explícita de modelo G/T |
| `testar_escala_clinica` | TI; POST escala/respostas | simulação | escala/itens T |

Impressões restantes: `imprimir_atendimento` (Atendimento URL),
`preview_pdf_modelo_documento` (modelo), `imprimir_documento_clinico`
(Documento), `imprimir_senha_totem` (Senha) e `imprimir_classificacao`
(Classificação/Atendimento). PDF não reduz risco: todo ID deve ser resolvido pela
cadeia tenant-local.

### R5, `screen` e seed/demo (fora dos 44 diretos)

| Fronteira | Tenant hoje | Por que `empresa_atual` não serve | Próxima arquitetura, sem implementar |
| - | - | - | - |
| `painel_chamada_publico` | sessão opcional/máquina e POST empresa | rota pública de dispositivo, sem principal | identidade de máquina ou token vinculado, rotação e auditoria; POST não pode escolher empresa livremente |
| `midia_painel_publica` | PK de `PainelChamada` na URL | mídia pública, sem sessão | identificador público não enumerável ou token assinado e regra de publicação |
| `AtendimentoDemoSeedProvider.handle` | `empresa_codigo` explícito do comando | bootstrap/sessionless | command privilegiado, validação de empresa/slot e contrato explícito |

Os três permanecem R5. `pep_chamar` é autenticado; é R3, não R5, mas só migra
depois de provar vínculo Máquina/Setor/Atendimento/empresa.

Em `screen`, `convenios`, `profissionais` e `atender-agendamento` já estão
migrados/delegados; `escalas` e `agendas` dependem de E1; tipos, especialidades
e salas são catálogos globais; telas estáticas têm contratos próprios. Ele só
poderá ser migrado/removido quando E1 eliminar os dois destinos legados e todos
os demais forem canônicos, explicitamente globais ou adaptadores sem resolução
de tenant. Remoção exige URLs diretas e nenhuma chamada produtiva ao dispatcher;
não aplicar `empresa_atual` somente para zerar contagem.

O provider demo é bootstrap por comando, não runtime HTTP/UI. Seu
`empresa_codigo` é entrada administrativa e deve validar empresa/slot; não deve
ser artificialmente convertido em contrato de sessão.

### Plano de execução

| Ordem | Lote | Consumidores | Qtd | Risco | Pré-requisito |
| -: | - | - | -: | - | - |
| 1 | E1 — agenda residual e destinos de `screen` | `_editable_escalas`, `cadastro_escala`, `alternar_status_escala`, `_agenda_dashboard`, `gerar_agenda` | 5 | R1–R3 | modelos Agenda/Escala e rotas do dispatcher caracterizados |
| 2 | E2 — fila e chamada de classificação | `_tabela_totem`, `imprimir_senha_totem`, `acao_senha_classificacao`, `chamar_agendamento_classificacao`, `imprimir_classificacao`, `fila_classificacao`, `escalas_classificacao_standalone` | 7 | R1–R3 | invariantes PreAtendimento/Agendamento/Senha/Atendimento |
| 3 | E3 — configuração e APIs de modelo documental | `documentos_telas_impressao`, `modelos_documento`, `testar_variavel_documento`, `rascunho_editor_documento`, `preview_pdf_modelo_documento` | 5 | R3 | contrato modelo G/T e APIs Editor |
| 4 | E4 — abertura, lifecycle e locks documentais | `ficha_atendimento`, `abrir_modelo_assistencial`, `documento_assistencial`, `assumir_documento_clinico`, `fechar_documento_clinico`, `abandonar_documento_clinico`, `cancelar_documento_clinico`, `liberar_trava_documento_clinico`, `liberar_acesso_excepcional_documento` | 9 | R3 | E3, selectors/permissões Editor e locks públicos |
| 5 | E5 — leitura, anexos e cópia documental | `imprimir_documento_clinico`, `link_externo_assistencial`, `anexos_clinicos`, `baixar_anexo_clinico`, `historico_documentos_assistencial`, `copiar_documento_clinico` | 6 | R3 | E4 e cadeia Documento → Atendimento |
| 6 | E6 — prescrições, exames e configuração | `solicitar_exame`, `resultado_exame`, `prescrever`, `_cadastro_configuracao_prescricao` | 4 | R3 | prova `empresa == atendimento.cd_empresa` nos chamadores/serviço |
| 7 | E7 — evolução e escalas clínicas | `evoluir`, `executar_escala_clinica`, `testar_escala_clinica` | 3 | R3 | E4 e invariantes Escala/Item/Resposta |
| 8 | E8 — alta, finalização e impressão | `conceder_alta`, `finalizar_atendimento`, `imprimir_atendimento` | 3 | R3 | eventos e efeitos de estado terminal caracterizados |
| 9 | E9 — chamada PEP residual | `pep_chamar` | 1 | R3 | vínculo Máquina/Setor/Atendimento e ChamadaPainel |
| 10 | E10 — demanda espontânea | `demanda_espontanea` | 1 | R3 | cadeia Paciente → PreAtendimento → Atendimento |
| 11 | E11 — especiais/dispatcher | `screen`, `painel_chamada_publico`, `midia_painel_publica`, provider demo | 4 | R5 | E1 canônico e contratos próprios definidos |

Lotes menores de cinco são deliberadamente isolados por uma única transição
clínica/contrato. Em todos: usar `empresa_atual` e `proteger_contexto_tenant`
somente em endpoints autenticados; resolver IDs URL/GET/POST pela empresa e
cadeia de pais; testar empresa ausente/inativa, duas empresas, ID estrangeiro,
permissões, GET/POST, efeitos clínicos, URLs reversas e `git diff --check`.

O primeiro sublote é **E1 — agenda residual e destinos de `screen`**: cinco
consumidores coesos, sem documentos ou estado clínico terminal, e remove os dois
últimos destinos legados do dispatcher. Este lote não o executa.

### Condição objetiva para excluir `_empresa_logada`

Só excluir quando a busca produtiva não retornar chamada autenticada, destino de
dispatcher ou adaptador legado; quando R5 tiver resolução própria de
dispositivo/token/publicação/comando; e quando não houver sessão direta ou
fallback `cd_empresa ... or 1` fora de contrato explicitamente documentado e
testado. A definição permanece intacta até então.

## TOP HOTSPOTS

1. `painel_chamada_publico` — R5: POST escolhe empresa e pode reatribuir máquina; preservar contrato de dispositivo e auditoria.
2. `midia_painel_publica` — R5: arquivo público é recuperado apenas por PK de painel.
3. `cadastro_atendimento` — R4: múltiplos pais e IDs de URL, escrita clínica.
4. `alteracao_atendimento` — R4: edição com ID e form; impacto direto no atendimento.
5. `documento_assistencial` — R4: cria documento clínico a partir de atendimento/URL.
6. `fechar_documento_clinico` — R4: evento, assinatura e lock por ID.
7. `executar_escala_clinica` — R4: IDs e POST em fluxo clínico.
8. `registrar_itens_prescricao` — R3: contrato sem request deve manter coerência atendimento/empresa.
9. `configurar_senhas` — R4: múltiplos catálogos e POSTs tenant-scoped.
10. `gerar_agenda` — R4: escrita transacional de agenda/agendamentos.

## Resumo quantitativo

O total abaixo refere-se às 89 fronteiras que resolvem/delegam resolução de tenant
na execução produtiva; forms, models, migrações e contratos que recebem empresa
explicitamente foram excluídos como falsos positivos de resolução.

| Métrica | Total |
| - | -: |
| Consumidores de resolução/delegação | 89 |
| Chamadas a `_empresa_logada` no inventário inicial | 86 |
| Chamadas a `_empresa_logada` após Lote A | 76 |
| Funções consumidoras diretas de `_empresa_logada` após Lote A | 75 |
| Chamadas a `_empresa_logada` após Lote B | 66 |
| Funções consumidoras diretas de `_empresa_logada` após Lote B | 65 |
| Chamadas a `_empresa_logada` após Lote C | 54 |
| Funções consumidoras diretas de `_empresa_logada` após Lote C | 53 |
| Chamadas a `_empresa_logada` após Lote D | 45 |
| Funções consumidoras diretas de `_empresa_logada` após Lote D | 44 |
| Chamadas a `_empresa_logada` após E1 | 40 |
| Funções consumidoras diretas de `_empresa_logada` após E1 | 39 |
| Chamadas a `_empresa_logada` após E2 | 33 |
| Funções consumidoras diretas de `_empresa_logada` após E2 | 32 |
| Chamadas a `_empresa_logada` após E3 | 28 |
| Funções consumidoras diretas de `_empresa_logada` após E3 | 27 |
| Chamadas a `_empresa_logada` após E4 | 19 |
| Funções consumidoras diretas de `_empresa_logada` após E4 | 18 |
| R1 | 1 |
| R2 | 46 |
| R3 | 20 |
| R4 | 19 |
| R5 | 3 |
| Autenticados (diretos ou delegados) | 86 |
| Públicos/sessionless | 3 |
| Leitura | 22 |
| Escrita | 35 |
| Leitura/escrita | 32 |
| Fallback empresa 1 | 1 helper / 45 call sites |
| Sessão direta | 2 pontos (`_empresa_logada`, `painel_chamada_publico`) |
| Já usando tenant canônico | 69 |
| Acessos que exigem investigação cross-tenant | 22 (19 pelo fallback; 3 por contrato especial) |

## Lotes futuros sugeridos

1. **Lote A — configurações administrativas de classificação/chamada (10; R2, concluído).** Painéis, tipos de senha, cores, perguntas, fluxos, escalas de fluxo, ícones e máquinas. Além do tenant canônico, IDs POST de cor, setor, ícone e protocolo foram scoped localmente.
2. **Lote B — agenda e cadastro de pacientes (10 consumidores; R2, concluído).** `agendamentos_operacionais`, consulta/cadastro/seleção/confirmação/cancelamento, comprovante e validação de unicidade passaram a usar `empresa_atual`. Paciente é diretamente tenant-scoped por `cd_empresa`; foram verificados sessão ausente, empresa/vínculo inativos, duas empresas e IDs URL/POST.
3. **Lote C — recepção e atendimento base (12; R2, concluído).** Pré-atendimento, recepção, cadastro/alteração/listagem, fila e consulta usam `empresa_atual`. Atendimento e Agendamento agora são resolvidos também pela empresa do Paciente, impedindo relações B→Paciente A que o banco legado ainda consegue representar.
4. **Lote D — profissionais, perfis e roteamento de cadastros (9; R2, concluído).** Convênios, prestadores, locks e perfis usam `empresa_atual`; o POST HTML de perfil valida escala T e modelo G/T como a API JSON. `screen` foi caracterizado como roteador para consumidores de outros lotes e permaneceu R4, sem alteração funcional.
5. **E1 — agenda residual e destinos de `screen` (5; R1–R3, concluído).** `_editable_escalas`, `cadastro_escala`, `alternar_status_escala`, `_agenda_dashboard` e `gerar_agenda` usam `empresa_atual` com `proteger_contexto_tenant`. Escala URL/POST, Prestador, Setor e Convênio T são scoped antes da escrita; AgendaGerada e HorarioAgenda recebem a mesma empresa da Escala. `screen` permanece dispatcher, mas seus destinos `escalas` e `agendas` já são canônicos.
6. **E2 — fila e chamada de classificação (7; R2–R3, concluído).** `_tabela_totem`, impressão, chamada, fila e escalas standalone usam tenant canônico. Senha, Agendamento e seus pais tenant-local são resolvidos coerentemente antes de imprimir, mudar estado, chamar ou listar; relações inconsistentes legadas são recusadas. `standalone` foi confirmado como autenticado e session-based, não R5. `screen` não possui destino E2 direto adicional.
7. **E3 — documentos, telas e impressão (5; R3, concluído).** `documentos_telas_impressao`, `modelos_documento`, `testar_variavel_documento`, `rascunho_editor_documento` e `preview_pdf_modelo_documento` usam tenant canônico. ModeloDocumento/Pasta seguem global-ou-empresa; vínculos de tela, rascunhos e Atendimento/Paciente são tenant-local. O preview agora valida o ID de modelo enviado pelo editor antes de gerar PDF. O Editor continua sendo consumido pelas APIs públicas de família/versão; não houve mudança de `screen`.
8. **E4 — documentos clínicos, lifecycle e locks (9; R3, concluído).** `ficha_atendimento`, abertura/documento assistencial e as seis ações documentais usam `empresa_atual` com `proteger_contexto_tenant`. Documento, Atendimento e Paciente são resolvidos pela mesma empresa; o modelo continua global-ou-empresa. A suíte A/B cobre isolamento cruzado, cadeia documental inconsistente, autorização independente do tenant, propriedade de lock e acesso excepcional sem alterar lifecycle, serviços Editor, URLs ou `screen`.
9. **Lote E — classificação, senha, painéis e escalas remanescentes (13; R4).** catálogos/filas restantes, tabelas de senha, escalas e `pep_chamar`. Testar POSTs, máquinas vinculadas e histórico de chamadas.
10. **Lote F — documentos, prescrição, exames e alta (29; R4/R3).** imprimir/preview, lifecycle e locks de documentos, anexos, exames, prescrição e alta. Executar caracterização de assinatura, eventos, arquivos e coerência `atendimento.cd_empresa` no serviço.
11. **Lote G — contratos especiais (3; R5).** painel público, mídia pública e seed demo. Não usar `empresa_atual`; primeiro definir contrato explícito de dispositivo/URL pública/comando.

Essa ordem mantém lotes entre 3 e 29 apenas onde o acoplamento clínico exige; o
Lote E deve ser quebrado em sublotes de até 10–15 consumidores após a
caracterização de documentos e prescrição.
