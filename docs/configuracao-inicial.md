# Configuração inicial da implantação

Os arquivos em `configuracao_inicial/` funcionam como formulários de implantação. Cada arquivo representa uma tabela ou um catálogo independente e usa o formato TOML, que permite repetir blocos `[[registros]]`.

## Como preencher

1. Abra cada arquivo `.toml` necessário.
2. Troque `habilitado = false` por `habilitado = true`.
3. Preencha ou duplique os blocos `[[registros]]`.
4. Use o mesmo `empresa_codigo` de `empresas.toml` nos setores e convênios.
5. Não repita códigos dentro do mesmo catálogo.

Os tipos válidos de setor são `EMPRESA` e `ATENDIMENTO`. Arquivos com prefixo `catalogo_` alimentam as tabelas auxiliares utilizadas nos seletores do sistema. Para criar outro catálogo, copie um desses arquivos, mantenha o prefixo e informe um novo valor em `tabela`.

## Validar antes de gravar

```powershell
python manage.py aplicar_configuracao_inicial --validar
```

Essa etapa confere sintaxe, campos obrigatórios, empresas referenciadas, tipos de setor e códigos duplicados sem alterar o banco.

## Aplicar

```powershell
python manage.py aplicar_configuracao_inicial
```

Para usar outro diretório:

```powershell
python manage.py aplicar_configuracao_inicial --diretorio C:\implantacao\cliente
```

O comando é idempotente: pode ser executado novamente. Registros existentes são atualizados pelas chaves naturais e novos registros são incluídos. Registros omitidos dos arquivos não são apagados nem desativados automaticamente.

## Arquivos fornecidos

- `empresas.toml`: dados cadastrais da empresa.
- `setores.toml`: setores administrativos e assistenciais.
- `convenios.toml`: convênios aceitos por empresa.
- `catalogo_tipo_atendimento.toml`: tipos de atendimento.
- `catalogo_local_procedencia.toml`: locais de procedência.
- `catalogo_destino_atendimento.toml`: destinos iniciais.
- `catalogo_meio_transporte.toml`: meios de transporte.
- `catalogo_origem_recepcao.toml`: recepções de origem.
- `catalogo_especialidade.toml`: especialidades.
- `catalogo_plano.toml`: planos.

Antes de aplicar em produção, faça backup do banco e execute primeiro com `--validar`.
