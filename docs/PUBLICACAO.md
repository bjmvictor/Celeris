# Publicação e edição da Biblioteca Celeris

O portal em `docs/` é estático e pode ser publicado pelo GitHub Pages, GitLab Pages, Cloudflare Pages, Netlify ou qualquer servidor HTTP. O conteúdo fica em `docs/data/topics.json`.

## Visualização local

Na raiz do repositório, execute:

```powershell
python -m http.server 8000
```

Abra `http://localhost:8000/docs/`. Não abra o `index.html` diretamente pelo explorador, pois o navegador bloqueia a leitura do JSON pelo protocolo `file://`.

## Publicar no GitHub Pages

1. Envie a pasta `docs/` para o repositório.
2. Em **Settings → Pages**, escolha a publicação pela branch principal e pela pasta `/docs`.
3. Aguarde a publicação e abra a URL exibida pelo GitHub.

## Edição autenticada

Na documentação publicada, o botão **Editar** abre o editor de arquivos do próprio GitHub para `docs/data/topics.json`. Dessa forma, a autenticação é feita pelo GitHub sem depender de um proxy OAuth externo ou de uma URL fictícia.

O painel Decap CMS em `docs/admin/` fica habilitado por padrão apenas no ambiente local. Para disponibilizá-lo também no GitHub Pages é obrigatório:

1. Criar um GitHub OAuth App para a URL publicada.
2. Publicar um proxy OAuth compatível com Decap CMS.
3. Configurar `base_url` e `auth_endpoint` em `docs/admin/config.yml` com a URL real do proxy.
4. Manter o segredo OAuth exclusivamente no proxy autenticador.
5. Conceder acesso ao repositório somente aos editores autorizados.

Sem um proxy configurado, mantenha o fluxo público pelo editor do GitHub, que já está configurado no botão **Editar**.

O histórico do Git registra quem alterou cada versão. Além disso, todo tópico exige os campos `updatedAt` e `updatedBy`, exibidos no cabeçalho da página.

## Editor local

Para testar o painel administrativo antes de configurar OAuth:

```powershell
npx decap-server
python -m http.server 8000
```

Depois abra `http://localhost:8000/docs/admin/`. O `local_backend: true` existente no arquivo de configuração permite esse modo apenas no ambiente local.

## Segurança

- Nunca coloque senha, token pessoal ou segredo OAuth em `docs/admin/config.yml`.
- O segredo OAuth deve existir apenas no proxy autenticador.
- Proteja a branch principal e prefira o fluxo editorial com revisão antes da publicação.
- Revise a data, o autor e os passos operacionais antes de publicar um tópico.
