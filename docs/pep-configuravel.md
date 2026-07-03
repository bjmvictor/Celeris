# PEP configurável

## Perfis e tipos de prestador

- Um prestador pode possuir vários registros em `prestador_tipo`.
- Um tipo de prestador ativo pertence a somente um perfil por empresa.
- O PEP reúne as versões publicadas de todos os perfis do prestador.
- Itens com a mesma chave técnica são mesclados; a permissão mais restritiva prevalece.
- Alterações do menu são feitas em rascunho e entram em produção somente após publicação.

## Tipos de item

- `GRUPO`: agrupador de menus.
- `ACAO`: ação interna do atendimento.
- `DOCUMENTO`: formulário clínico versionado.
- `LINK_EXTERNO`: integração HTTPS autorizada por domínio.
- `ESCALA`: perguntas pontuadas por soma ou média.
- `ANEXO`: envio privado e auditado de arquivos.
- `HISTORICO`: consulta longitudinal sem criação.

## Documentos clínicos

- Estados oficiais: `ABERTO`, `FECHADO`, `ABANDONADO` e `CANCELADO`.
- Documentos fechados, abandonados e cancelados não podem ter conteúdo alterado.
- O fechamento exige senha, valida campos obrigatórios e grava hash SHA-256 e dados do assinante.
- Assunção, alteração, fechamento, abandono, cancelamento, impressão e acesso excepcional são auditáveis.
- Cancelamento e abandono não removem registros.

## APIs

- `GET|POST|DELETE /atendimento/documentos/modelos/rascunho/`
- `GET|POST|PATCH|DELETE /atendimento/configuracao/perfis-assistenciais/<perfil>/itens/`
- `POST /atendimento/configuracao/perfis-assistenciais/<perfil>/publicar/`
- `POST /atendimento/configuracao/escalas-clinicas/testar/`
- `POST /atendimento/documentos/<documento>/assumir/`
- `POST /atendimento/documentos/<documento>/fechar/`
- `POST /atendimento/documentos/<documento>/abandonar/`
- `POST /atendimento/documentos/<documento>/cancelar/`

Todas as operações usam a empresa da sessão e validam o perfil assistencial do usuário.
