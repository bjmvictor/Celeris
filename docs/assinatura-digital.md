# Assinatura digital de PDFs

O Celeris gera o PDF definitivo com WeasyPrint e, quando existe um certificado ativo para a finalidade do modelo, incorpora uma assinatura PAdES/SHA-256 com pyHanko. No fechamento, o PDF final é persistido como uma versão imutável. Visualizar, imprimir ou baixar um documento fechado sempre retorna exatamente os mesmos bytes armazenados; o layout não é reconstruído.

## O que são as duas chaves

Existem duas credenciais diferentes e elas não devem ser confundidas:

1. **Certificado A1 (`.pfx` ou `.p12`)**: pertence à empresa ou ao profissional. Contém o certificado público e a chave privada usada para assinar documentos. Ele possui sua própria senha, informada no cadastro.
2. **`CELERIS_CERTIFICATE_MASTER_KEY`**: é uma chave interna do Celeris, gerada aleatoriamente, usada apenas para proteger no banco o PFX e a senha dele. Ela não é um certificado, não assina PDFs e não substitui a senha do PFX.

O Celeris usa a chave mestra com **AES-256-GCM**:

- **AES-256** significa que a chave simétrica possui 256 bits, ou 32 bytes aleatórios;
- **GCM** adiciona autenticação ao conteúdo criptografado, detectando alterações ou corrupção;
- o PFX e a senha são criptografados separadamente;
- cada conteúdo recebe um nonce aleatório próprio;
- os nonces podem ficar no banco, pois não são senhas nem chaves;
- a chave mestra nunca é gravada no banco.

Se alguém obtiver somente o banco de dados, não conseguirá abrir os certificados sem também possuir a chave mestra configurada no servidor.

## Instalação

Instale as dependências do projeto dentro do ambiente virtual:

```powershell
py -m pip install -r requirements.txt
py manage.py migrate
```

## Gerar a chave mestra

Gere a chave uma única vez para cada ambiente:

```powershell
python -c "from apps.core.services.certificados_digitais import gerar_chave_mestra; print(gerar_chave_mestra())"
```

O comando imprime uma sequência Base64 aleatória. Não copie valores de exemplo da documentação e não utilize senhas comuns, CNPJ, CPF ou textos inventados.

Crie ou edite o arquivo `.env` na raiz do projeto:

```dotenv
CELERIS_CERTIFICATE_MASTER_KEY=COLE_AQUI_O_VALOR_GERADO
CELERIS_CERTIFICATE_MASTER_KEY_VERSION=v1
```

Reinicie o servidor após alterar o `.env`.

### Regras importantes

- gere a chave somente uma vez e mantenha o mesmo valor após reinicializações e atualizações;
- não gere uma chave nova enquanto houver certificados cadastrados com a chave anterior;
- não grave a chave no Git, banco de dados, código-fonte ou logs;
- em produção, prefira secret manager, Vault ou variável protegida do serviço;
- utilize uma chave diferente em desenvolvimento, homologação e produção;
- mantenha backup seguro e separado da chave mestra e do banco de dados.

Sem a chave mestra correta, os certificados já cadastrados não podem ser descriptografados. Isso é intencional e protege as chaves privadas em caso de vazamento do banco.

## Cadastro e controle por finalidade

Abra **Global > Empresa > Certificados digitais**. Envie somente `.pfx` ou `.p12`, informe a senha original do certificado e marque as finalidades autorizadas:

- documentos médicos;
- documentos administrativos;
- outros documentos.

As finalidades de um certificado ativo podem ser atualizadas na própria tela. Para interromper todas as assinaturas, desative o certificado. Desativar ou substituir um certificado não modifica documentos já assinados.

O backend valida formato, senha, presença da chave privada, período de validade e metadados X.509 antes de armazenar o certificado. Nenhum segredo retorna ao navegador e não existe download do PFX cadastrado.

Certificados profissionais podem ser vinculados a um usuário da empresa. Para esse usuário, o backend prioriza o certificado profissional habilitado; quando não houver um aplicável, utiliza o institucional da empresa.

## Aviso sobre arquivos PKCS#12 antigos

Alguns emissores geram pacotes PKCS#12 usando codificação BER em vez de DER estrito. A biblioteca `cryptography` consegue interpretar esses arquivos, mas versões recentes podem emitir o aviso:

```text
PKCS#12 bundle could not be parsed as DER, falling back to parsing as BER
```

O Celeris ignora somente esse aviso conhecido e continua validando senha, certificado e chave privada. Arquivos realmente inválidos continuam sendo rejeitados com uma mensagem segura. Se a autoridade certificadora oferecer uma exportação mais recente do PFX, prefira substituir o arquivo antigo.

## Fechamento, assinatura e armazenamento

1. O fechamento bloqueia o registro do documento com `select_for_update`.
2. WeasyPrint gera uma única vez o PDF definitivo em memória.
3. O certificado e sua senha são descriptografados somente em memória.
4. pyHanko incorpora a assinatura PAdES/SHA-256.
5. A assinatura é revalidada antes da confirmação da transação.
6. PDF, hash SHA-256, certificado utilizado, usuário, data, finalidade e auditoria são persistidos atomicamente.
7. Somente após o sucesso o documento recebe o estado `ASSINADO`.

Se não houver certificado habilitado para a finalidade, o fechamento persiste uma versão final imutável sem assinatura. Se existir certificado configurado, mas ele estiver vencido, futuro, corrompido ou inacessível, o fechamento falha e o documento permanece aberto.

Documentos fechados não são remontados ao abrir ou imprimir. O sistema confere o hash SHA-256 do arquivo armazenado antes de devolvê-lo ao navegador.

## Carimbo de tempo TSA

O carimbo de tempo é opcional. Para habilitá-lo, informe uma TSA HTTPS compatível:

```dotenv
CELERIS_TSA_URL=https://endereco-da-tsa
CELERIS_TSA_TIMEOUT=10
```

Quando configurada, a TSA participa do fechamento. Se ela estiver indisponível ou retornar uma resposta inválida, o documento permanece aberto e nenhuma versão parcial é persistida. URLs HTTP não são aceitas.

## Validade e monitoramento

Execute diariamente, por agendador do sistema operacional:

```powershell
py manage.py verificar_certificados_digitais
```

Os níveis padrão são 60, 30, 15, 7 e 1 dia e podem ser alterados por `CELERIS_CERTIFICATE_EXPIRY_WARNING_LEVELS`. Os avisos da interface são calculados sem criar notificações duplicadas. Certificados vencidos permanecem disponíveis para auditoria, mas não assinam novos documentos.

## Backup, restauração e rotação

Para uma restauração completa são necessários:

- backup do banco contendo os certificados criptografados;
- a chave mestra correspondente à versão registrada em cada certificado.

Guarde os dois itens separadamente. Antes de trocar a chave principal, mantenha a chave anterior disponível em uma variável versionada, por exemplo:

```dotenv
CELERIS_CERTIFICATE_MASTER_KEY_V1=CHAVE_ANTERIOR
CELERIS_CERTIFICATE_MASTER_KEY_VERSION=v2
CELERIS_CERTIFICATE_MASTER_KEY=CHAVE_NOVA
```

Não remova a chave anterior antes de recriptografar os certificados relacionados. Nunca exclua certificados usados em assinaturas históricas; apenas desative-os.

## Validação e limitações atuais

Os testes automatizados criam certificados autoassinados temporários somente em memória. Certificados reais e senhas nunca devem entrar no repositório.

O Celeris valida a integridade criptográfica da assinatura e o hash do PDF. Para validação jurídica externa, utilize Adobe Acrobat Reader ou um validador compatível com PAdES e ICP-Brasil. PAdES-LT/LTV, consulta contínua de OCSP/CRL e validação completa da cadeia ICP-Brasil dependem dos serviços de confiança disponíveis no ambiente de produção.

O backend de assinatura foi isolado para permitir uma futura substituição do PFX A1 por HSM ou assinatura remota sem alterar o fluxo de fechamento e versionamento dos documentos.

## Testes com certificados digitais

Em ambientes de desenvolvimento e homologação, utilize preferencialmente certificados destinados ```exclusivamente a testes```, evitando qualquer risco de exposição de certificados reais da instituição.

Uma opção para geração e utilização de certificados de teste está disponível na documentação da [Lacuna Software](https://docs.lacunasoftware.com/):

[Baixar certificados digitais para testes](https://docs.lacunasoftware.com/pt-br/articles/pki-guide/test-certs.html)

> Importante: certificados de teste não possuem validade jurídica e devem ser utilizados exclusivamente para desenvolvimento, homologação e testes automatizados.

## Solução de problemas

### `Requested setting INSTALLED_APPS, but settings are not configured`

Esse erro ocorria porque o gerador importava modelos Django. O gerador agora é independente e o comando `python -c` informado nesta documentação funciona sem iniciar o Django.

No Windows, execute o comando com o ambiente virtual ativado para garantir que `python` aponte para `.venv\Scripts\python.exe`. Se preferir o Python Launcher, force Python 3 com `py -3 -c`.

### `CELERIS_CERTIFICATE_MASTER_KEY deve representar exatamente 32 bytes`

O valor configurado não foi gerado pelo comando oficial, foi cortado ou recebeu espaços. Gere novamente apenas se ainda não houver certificados cadastrados. Se já houver certificados, restaure a chave original.

### O certificado não abre após mover o banco para outro servidor

Configure no novo servidor a mesma chave mestra e a mesma versão usadas no servidor anterior. Restaurar apenas o banco não é suficiente.
