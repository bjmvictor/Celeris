# Relatório de validação das telas

## Execução

- Comando principal: `python manage.py test`
- Resultado mais recente: 111 testes aprovados, 0 falhas.
- Verificações adicionais: `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `node --check static/js/celeris.js` e `git diff --check`.

## Cobertura automatizada

- Prestador: inclusão, validação, filtros, multiespecialidade, conselho opcional, CEP, consulta, guia única, desativação e reativação.
- Paciente: abertura, filtros individuais e combinados, CEP, consulta, guia única, navegação por resultados e desativação.
- Global: CEP, importação CSV, vínculo tipo de prestador x conselho e reapresentação após salvar.
- Administração: abertura de usuários, papéis e permissões; criação de papel.
- Usuários: login automático e único, integração com prestador, CPF único, papéis, empresas, ativação/desativação e alteração de senha.
- Login: primeiro nome completo, iniciais dos demais nomes, partículas progressivas e numeração sequencial em duplicidades.
- Papéis e acessos: módulos, telas, status, associação múltipla ao usuário e permissões acumulativas.
- Segurança: menu por papel e bloqueio backend para usuário, papel, módulo ou tela inativos.
- Consulta → cadastro: retorno contextual com filtros, página e posição da lista preservados.
- Consultas administrativas: mensagens obrigatórias de resultado, vazio ou erro e ação Editar nas grades.
- Navegação: botão Fechar existente assume o comportamento de Voltar por contexto, sem ação textual duplicada.
- Multiseleção: Papéis, Empresas e Especialidades compartilham limpeza, remoção, inclusão e teclado.
- Labels: barra de status e cadastro de usuários exibem somente termos de negócio em português.
- Prestadores: menu abre o cadastro com consulta integrada; abertura direta não herda navegação de resultados.
- Tabelas auxiliares: linha inicial para inclusão, consulta por PK/código/descrição e exclusão condicionada à seleção.
- Planos e Procedimentos: persistência e consulta pela infraestrutura de tabelas auxiliares.
- Usuários: cadastro e consulta integrados, com filtros, navegação por resultados e senha condicionada ao registro.
- Seções: somente o primeiro agrupamento inicia aberto; recolhidos ficam compactos e horizontais.
- Ordenação: indicadores crescente/decrescente aplicados às grades ordenáveis.
- Edição inline: Enter salva e exclusões de auxiliares são lógicas.
- Consultas integradas: status vazio não aplica filtro; consulta vazia retorna ativos e inativos.
- Interface: contrato de teclado dos dropdowns, handler único de mouse e estrutura de overlay.
- Interface visual: menu compacto, distinção entre submódulos e telas finais, autocomplete desativado e rolagem até erros.
- Barra de ações: estados do primeiro, intermediário e último registro; rótulo dinâmico Ativar/Desativar.
- Barra de ações: botões condicionais por contexto, ação de status apenas por ícone e alteração de senha em sobreposição.
- Atendimento central: recepção sem duplicidade, histórico em `atendimento_fluxo`, isolamento por empresa e PEP sem paciente apenas agendado.
- Sessão: endpoint leve de status e retorno 401 JSON para requisições AJAX/fetch desconectadas.

## Falhas encontradas e corrigidas

- Filtros de paciente ignoravam diversos campos consultáveis.
- URLs com IDs criavam novas guias para o mesmo cadastro.
- Erros de backend não tinham contrato visual centralizado.
- Documentos e convênio estavam separados.
- Dropdown possuía eventos concorrentes de mouse.
- Consulta de vínculo tipo de prestador x conselho voltava vazia após salvar.
- Limpeza da consulta de prestadores mantinha especialidades ocultas selecionadas.
- Cadastro de usuário não possuía estrutura funcional, login automático nem integração com prestador.
- Login era recalculado com ordem incorreta e o modo edição acusava duplicidade contra o próprio usuário.
- Menu lateral dependia de nomes fixos de grupos e não validava módulos/telas persistidos.
- Cadastros abertos por grades não possuíam retorno explícito para a consulta de origem.
- Consulta de papéis não filtrava por código e não diferenciava corretamente Ativos de Todos.
- Empresas utilizavam um seletor múltiplo divergente do padrão de Papéis e Especialidades.
- Barra inferior priorizava nomes técnicos de campos em vez dos labels apresentados na tela.
- Consulta exclusiva de prestadores duplicava fluxo, contexto e navegação.
- Ativação e exclusão permaneciam disponíveis sem registro persistido selecionado.
- Links Gerenciar de Especialidades e Convênios abriam subtelas inválidas.
- Consulta pós-salvamento reabria com valores visuais e internos do registro anterior.
- Botão Alterar Senha permanecia ativo sem usuário carregado.
- Tela exclusiva de usuários duplicava o mecanismo já disponível no cadastro.

## Observação

Os testes de interação frontend validam o contrato estrutural do JavaScript. O projeto não possui Playwright, Selenium ou navegador headless configurado; portanto, testes de pixels e eventos reais do navegador continuam sendo uma evolução recomendada.
