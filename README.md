# Celeris

Plataforma integrada para gestão clínica e hospitalar, desenvolvida para centralizar processos administrativos, assistenciais e operacionais em um único ambiente.

O Celeris oferece suporte multiempresa, controle de acesso por papéis, prontuário eletrônico, classificação de risco, agendamento, atendimento, estoque, suporte interno e relatórios, com arquitetura modular preparada para evolução contínua.

## Visão geral

O projeto foi criado para reduzir a fragmentação de informações, padronizar processos e facilitar a rotina de instituições de saúde.

A plataforma acompanha a jornada do paciente desde o agendamento e recepção até a classificação de risco, atendimento clínico, prescrição, solicitação de exames e alta.

Também contempla processos administrativos como gestão de usuários, unidades, setores, prestadores, convênios, materiais, chamados internos e auditoria.

## Público-alvo

O Celeris é direcionado a:

* Hospitais públicos e privados
* Clínicas e policlínicas
* Unidades de pronto atendimento
* Centros médicos e ambulatoriais
* Redes de saúde com múltiplas unidades
* Instituições que buscam digitalizar processos assistenciais e administrativos

A estrutura multiempresa permite centralizar a gestão de diferentes unidades, mantendo regras de acesso, configurações e operações específicas para cada instituição.

## Principais funcionalidades

### Gestão assistencial

* Cadastro completo de pacientes e prestadores
* Agendamento de consultas e gerenciamento de agendas
* Recepção de pacientes agendados e demanda espontânea
* Pré-atendimento e classificação de risco
* Atendimento médico e de enfermagem
* Prontuário Eletrônico do Paciente
* Evoluções, prescrições e solicitações de exames
* Documentos clínicos personalizados
* Alta médica e administrativa
* Histórico clínico centralizado
* Auditoria de acessos ao prontuário

### Gestão operacional

* Cadastro de empresas, unidades, setores e salas
* Gestão de convênios, planos e procedimentos
* Controle de produtos, materiais e movimentações de estoque
* Solicitações internas e atendimento de materiais
* Chamados de suporte e acompanhamento de execução
* Consultas personalizadas e exportação de relatórios
* Importação de dados por arquivos CSV

### Atendimento e comunicação

* Totem de autoatendimento para emissão de senhas
* Painel público para chamada de pacientes
* Priorização de chamadas por classificação e protocolo
* Configuração de máquinas, painéis e pontos de atendimento

### Segurança e governança

* Controle de acesso baseado em papéis
* Permissões por funcionalidade, tela e ação
* Suporte a múltiplas empresas por usuário
* Expiração de sessão por inatividade
* Bloqueio por tentativas de autenticação
* Alteração obrigatória de senha no primeiro acesso
* Controle de edição simultânea de registros
* Auditoria de criação e alteração
* Registro de acessos clínicos
* Estrutura preparada para adequação à LGPD

## Ecossistema

O Celeris pode ser utilizado como uma plataforma única ou dividido em produtos especializados:

| Produto             | Finalidade                                                    |
| ------------------- | ------------------------------------------------------------- |
| **Celeris Central** | Gestão administrativa, operacional e integração dos processos |
| **Celeris PEP**     | Prontuário eletrônico e atendimento assistencial              |
| **Celeris Class**   | Pré-atendimento e classificação de risco                      |
| **Celeris Totem**   | Autoatendimento e geração de senhas                           |
| **Celeris Painel**  | Chamada pública de pacientes e senhas                         |
| **Celeris BI**      | Indicadores gerenciais e dashboards                           |

## Evolução planejada

O Celeris está em desenvolvimento contínuo. As próximas etapas têm como objetivo ampliar a cobertura da plataforma e consolidá-la como uma solução completa de gestão em saúde.

Entre as principais implementações planejadas estão:

* Faturamento hospitalar e ambulatorial
* Gestão de contas e convênios
* Controle financeiro e fluxo de caixa
* Contas a pagar e contas a receber
* Gestão de compras e fornecedores
* Integração entre estoque, compras e faturamento
* Gestão contábil e centros de custo
* Indicadores assistenciais e administrativos
* Dashboards gerenciais no Celeris BI
* Gestão de leitos e internações
* Ampliação dos recursos de enfermagem
* Protocolos clínicos configuráveis
* Assinatura eletrônica de documentos
* Integração com serviços e sistemas externos
* Aprimoramento dos recursos de privacidade e LGPD
* Expansão da cobertura de testes automatizados

O planejamento detalhado está disponível em [docs/roadmap.md](docs/roadmap.md).

## Tecnologias

| Camada         | Tecnologia                            |
| -------------- | ------------------------------------- |
| Backend        | Python 3.12 e Django 5                |
| Frontend       | HTML5, CSS3, Bootstrap 5 e JavaScript |
| Banco de dados | SQLite, PostgreSQL ou MySQL           |
| Templates      | Django Templates                      |
| Documentos     | GrapesJS + WeasyPrint                 |

## Desenvolvimento local

Clone o repositório:

```bash
git clone https://github.com/bjmvictor/Celeris.git
cd Celeris
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente:

```powershell
# Windows
.\.venv\Scripts\activate
```

```bash
# Linux ou macOS
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure o ambiente:

```bash
cp .env.example .env
```

Execute as migrações e inicie o servidor:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

A aplicação estará disponível em:

```text
http://localhost:8000
```

## Testes

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

O projeto possui mais de 111 testes automatizados, com cobertura das principais regras de autenticação, permissões, cadastros e processos assistenciais.

## Status do projeto

O Celeris está em desenvolvimento ativo.

As funcionalidades centrais de cadastro, agendamento, atendimento, prontuário eletrônico, classificação de risco, estoque, chamados, relatórios, totem e painel de chamadas já possuem implementação funcional.

Novos recursos estão sendo adicionados de forma progressiva, priorizando segurança, estabilidade, usabilidade e integração entre os processos.

## Licença

Este projeto está disponível sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais informações.
