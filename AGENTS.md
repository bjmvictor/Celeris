# AGENTS.md

## Definition of Done

Uma tarefa NÃO está concluída apenas porque o código compila.

Antes de entregar qualquer alteração, o agente deve:

1. Entender o fluxo afetado antes de modificar o código.
2. Executar os testes existentes relacionados à alteração.
3. Executar lint e type-check quando disponíveis.
4. Iniciar a aplicação real.
5. Abrir a aplicação em um navegador real.
6. Navegar até a tela alterada.
7. Executar manualmente pelo navegador o fluxo afetado.
8. Confirmar que o resultado visual e funcional corresponde ao solicitado.
9. Verificar o console do navegador.
10. Não deixar erros ou warnings relevantes no console.
11. Verificar requisições de rede relacionadas ao fluxo.
12. Confirmar que não existem requisições 4xx/5xx inesperadas.
13. Verificar estados de loading, erro e sucesso.
14. Testar pelo menos uma resolução desktop.
15. Quando a alteração afetar responsividade, testar também uma resolução mobile.
16. Corrigir qualquer problema encontrado e repetir os testes.

## Browser testing

Para alterações de frontend, use o navegador integrado do Codex quando disponível.

O teste deve validar comportamento real e não apenas inspecionar o código.

Sempre que possível:

- abra a URL real da aplicação;
- autentique-se quando necessário;
- clique nos controles envolvidos;
- preencha formulários;
- abra modais e menus;
- execute pesquisas;
- valide alterações de URL;
- valide conteúdo renderizado;
- verifique console;
- verifique network requests;
- tire screenshots para comprovar o resultado.

Se o navegador integrado não estiver disponível, utilize Playwright.

Não considere `npm run build`, `npm test` ou análise estática como substitutos
para um teste de interface no navegador.

## Playwright

Quando apropriado, utilize os testes E2E existentes.

Se não existirem testes E2E para um fluxo crítico alterado, considere adicionar
um teste Playwright reutilizável.

Prefira testar comportamentos do usuário em vez de detalhes internos da implementação.

## Regression testing

Após corrigir um problema:

1. reproduza o problema original;
2. confirme que a correção resolveu o problema;
3. teste funcionalidades próximas que possam ter sido afetadas;
4. recarregue a página e teste novamente;
5. confirme que não surgiram novos erros no console.

## Final report

Ao finalizar, informe:

- o que foi alterado;
- quais arquivos principais foram alterados;
- quais testes automatizados foram executados;
- qual fluxo foi testado no navegador;
- URL utilizada;
- ações executadas;
- resultado observado;
- erros encontrados durante os testes;
- correções realizadas;
- erros restantes;
- screenshots relevantes, quando possível.

Nunca diga apenas "funciona" sem ter executado os testes.

Se não for possível executar algum teste, explique claramente o motivo.