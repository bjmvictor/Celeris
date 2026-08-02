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

O editor em `docs/admin/` usa Decap CMS e grava as mudanças como commits no repositório. O login seguro é realizado pelo GitHub; nenhuma senha é armazenada no HTML ou JavaScript.

Uma página estática não consegue validar com segurança usuário e senha do próprio Celeris. Para usar as contas do sistema seria necessário servir o editor pelo Django. Na hospedagem estática, utilize GitHub OAuth:

1. Crie um GitHub OAuth App para a URL publicada.
2. Publique um proxy OAuth compatível com Decap CMS.
3. Edite `docs/admin/config.yml`.
4. O repositório `bjmvictor/Celeris` já está configurado; ajuste-o apenas se a documentação for movida.
5. Troque `SEU-OAUTH-PROXY.example.com` pela URL HTTPS do proxy.
6. Conceda acesso ao repositório somente aos editores autorizados.

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
