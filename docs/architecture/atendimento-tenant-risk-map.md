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
**45 chamadas em 44 funções consumidoras**. As linhas ainda dependentes dele são R4:
o fallback torna insegura uma troca mecânica, mesmo onde os querysets posteriores já
filtram por empresa. Quarenta e um consumidores usam agora `empresa_atual` com
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
| 48 | `_editable_escalas` | views.py | cadastro | delegado | H | L/E | EscalaClinica | queryset e escrita por empresa | R4 | H: fallback 1 | lote agenda |
| 49 | `cadastro_escala` | views.py | agenda | login/TI | H | L/E | AgendaProfissional | escala por empresa | R4 | H: fallback 1; ID URL | lote agenda |
| 50 | `alternar_status_escala` | views.py | agenda | login/TI | H | E | AgendaProfissional | escala por empresa | R4 | H: fallback 1; ID URL | lote agenda |
| 51 | `_agenda_dashboard` | views.py | agenda | delegado | H | L | AgendaProfissional, Agendamento | querysets por empresa | R4 | H: fallback 1 | lote agenda |
| 52 | `_fila_atendimento` | views.py | triagem | delegado | `empresa_atual` | L | Agendamento, Paciente | queryset e pai por empresa canônica | R2 | Lote C; rota delegada validada | tenant canônico |
| 53 | `alteracao_atendimento` | views.py | atendimento | login/Recepcionista,Enfermeiro,Médico | `empresa_atual` | L/E | Atendimento, Paciente, Responsável | ID URL/GET/POST e pai por empresa canônica | R2 | Lote C; reselect `select_for_update` scoped | tenant canônico |
| 54 | `atendimentos` | views.py | atendimento | login/Recepcionista,Enfermeiro,Médico | `empresa_atual` | L | Atendimento, Paciente | queryset e GET por empresa canônica | R2 | Lote C; registros inconsistentes ocultos | tenant canônico |
| 55 | `pep_chamar` | views.py | painel | login/TI,Médico,Enfermeiro | H | E | Atendimento, Máquina, Painel | atendimento/setor/máquina por empresa | R4 | H: fallback 1; POST IDs | lote painel/chamada |
| 56 | `paineis_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | PainelChamada, Setor | painel, ID URL e form por empresa canônica | R2 | tratado no Lote A | concluído: painel/chamada admin |
| 57 | `alternar_status_painel_chamada` | views.py | painel | login/TI | `empresa_atual` | E | PainelChamada | busca por empresa canônica | R2 | tratado no Lote A; ID URL scoped | concluído: painel/chamada admin |
| 58 | `configurar_senhas` | views.py | configuração | login/TI | `empresa_atual` | L/E | TipoSenha, classe, protocolo | filtros e referências POST por empresa canônica | R2 | tratado no Lote A; ícone/protocolo POST scoped | concluído: painel/chamada admin |
| 59 | `alternar_status_configuracao_senha` | views.py | configuração | login/TI | `empresa_atual` | E | TipoSenhaAtendimento | busca por empresa canônica | R2 | tratado no Lote A; ID URL scoped | concluído: painel/chamada admin |
| 60 | `_tabela_totem` | views.py | cadastro | delegado | H | L/E | classes/protocolos | queryset por empresa | R4 | H: fallback 1 | lote painel/chamada |
| 61 | `cores_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | CorClassificacaoRisco | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 62 | `perguntas_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | PerguntaClassificacao | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 63 | `fluxos_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | FluxoClassificacao | IDs e cor recomendada POST scoped por empresa | R2 | tratado no Lote A; cor POST scoped | concluído: classificação admin |
| 64 | `fluxo_escalas_classificacao` | views.py | classificação | login/TI | `empresa_atual` | L/E | Fluxo, Escala | fluxo URL e escalas POST por empresa canônica | R2 | tratado no Lote A | concluído: classificação admin |
| 65 | `icones_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | IconeChamada | queryset e escrita por empresa canônica | R2 | tratado no Lote A | concluído: painel/chamada admin |
| 66 | `maquinas_chamada` | views.py | painel | login/TI | `empresa_atual` | L/E | MaquinaChamada | queryset e setor POST por empresa canônica | R2 | tratado no Lote A; setor POST scoped | concluído: painel/chamada admin |
| 67 | `imprimir_senha_totem` | views.py | impressão | login/TI,Recepcionista,Enfermeiro | H | L | SenhaAtendimento | senha por empresa | R4 | H: fallback 1; ID URL | lote painel/chamada |
| 68 | `acao_senha_classificacao` | views.py | classificação | login/Enfermeiro | H | E | SenhaAtendimento | senha por empresa | R4 | H: fallback 1; ID URL | lote classificação |
| 69 | `chamar_agendamento_classificacao` | views.py | classificação | login/Enfermeiro | H | E | Agendamento, Senha | agendamento por empresa | R4 | H: fallback 1; ID URL | lote classificação |
| 70 | `imprimir_classificacao` | views.py | impressão | login/Enfermeiro | H | L | Senha, classificação | senha por empresa | R4 | H: fallback 1; GET | lote classificação |
| 71 | `fila_classificacao` | views.py | classificação | login/Enfermeiro | H | L/E | Senha, Agendamento, PreAtendimento | filtros por empresa | R4 | H: fallback 1; POST | lote classificação |
| 72 | `escalas_classificacao_standalone` | views.py | classificação | login/TI | H | L/E | EscalaClinica | queryset por empresa | R4 | H: fallback 1; ID URL/POST | lote classificação |
| 73 | `fila_medica` | views.py | atendimento | login/Médico | `empresa_atual` | L | Atendimento, Paciente | queryset por empresa canônica | R2 | Lote C; invariante atendimento→paciente | tenant canônico |
| 74 | `abrir_consulta` | views.py | atendimento | login/Médico | `empresa_atual` | E | Atendimento, Paciente | atendimento URL por empresa canônica | R2 | Lote C; ID URL e invariante atendimento→paciente | tenant canônico |
| 75 | `gerar_agenda` | views.py | agenda | login/TI,Recepcionista | H | E | AgendaProfissional, Agendamento | entidades por empresa | R4 | H: fallback 1; POST | lote agenda |
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
| 86 | `screen` | views.py | roteamento | login; papéis por tela | delegado para H | L/E | cadastros, agenda, fila | despacha para helpers 1, 48, 51, 52, 60 | R4 | rotas herdando H | migrar com cada lote delegado |
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
| R1 | 0 |
| R2 | 41 |
| R3 | 0 |
| R4 | 45 |
| R5 | 3 |
| Autenticados (diretos ou delegados) | 86 |
| Públicos/sessionless | 3 |
| Leitura | 22 |
| Escrita | 35 |
| Leitura/escrita | 32 |
| Fallback empresa 1 | 1 helper / 45 call sites |
| Sessão direta | 2 pontos (`_empresa_logada`, `painel_chamada_publico`) |
| Já usando tenant canônico | 41 |
| Acessos que exigem investigação cross-tenant | 48 (45 pelo fallback; 3 por contrato especial) |

## Lotes futuros sugeridos

1. **Lote A — configurações administrativas de classificação/chamada (10; R2, concluído).** Painéis, tipos de senha, cores, perguntas, fluxos, escalas de fluxo, ícones e máquinas. Além do tenant canônico, IDs POST de cor, setor, ícone e protocolo foram scoped localmente.
2. **Lote B — agenda e cadastro de pacientes (10 consumidores; R2, concluído).** `agendamentos_operacionais`, consulta/cadastro/seleção/confirmação/cancelamento, comprovante e validação de unicidade passaram a usar `empresa_atual`. Paciente é diretamente tenant-scoped por `cd_empresa`; foram verificados sessão ausente, empresa/vínculo inativos, duas empresas e IDs URL/POST.
3. **Lote C — recepção e atendimento base (12; R2, concluído).** Pré-atendimento, recepção, cadastro/alteração/listagem, fila e consulta usam `empresa_atual`. Atendimento e Agendamento agora são resolvidos também pela empresa do Paciente, impedindo relações B→Paciente A que o banco legado ainda consegue representar.
4. **Lote D — profissionais, perfis e roteamento de cadastros (9; R2, concluído).** Convênios, prestadores, locks e perfis usam `empresa_atual`; o POST HTML de perfil valida escala T e modelo G/T como a API JSON. `screen` foi caracterizado como roteador para consumidores de outros lotes e permaneceu R4, sem alteração funcional.
5. **Lote E — classificação, senha, painéis e escalas remanescentes (13; R4).** catálogos/filas restantes, tabelas de senha, escalas e `pep_chamar`. Testar POSTs, máquinas vinculadas e histórico de chamadas.
6. **Lote F — documentos, prescrição, exames e alta (29; R4/R3).** imprimir/preview, lifecycle e locks de documentos, anexos, exames, prescrição e alta. Executar caracterização de assinatura, eventos, arquivos e coerência `atendimento.cd_empresa` no serviço.
7. **Lote G — contratos especiais (3; R5).** painel público, mídia pública e seed demo. Não usar `empresa_atual`; primeiro definir contrato explícito de dispositivo/URL pública/comando.

Essa ordem mantém lotes entre 3 e 29 apenas onde o acoplamento clínico exige; o
Lote E deve ser quebrado em sublotes de até 10–15 consumidores após a
caracterização de documentos e prescrição.
