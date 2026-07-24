# Celeris

**Plataforma modular de gestão clínica e hospitalar** com suporte multiempresa, controle de acesso baseado em papéis, PEP (Prontuário Eletrônico do Paciente), senhas e painéis de chamada, ticket de suporte, integração assistencial e estrutura preparada para LGPD.

---

## Funcionalidades por módulo

### 🏥 Assistencial (apps.atendimento)

| Funcionalidade | Status |
|---|---|
| Cadastro de pacientes (dados pessoais, documentos, endereço, convênio, responsável, alertas, óbito) | ✅ Implementado |
| Cadastro de prestadores (dados profissionais, especialidades, conselho, vínculo, CEP, chave PIX, banco) | ✅ Implementado |
| Cadastro de convênios, planos e procedimentos | ✅ Implementado |
| Cadastro de escalas de prestadores por unidade, sala, especialidade, dias e horários | ✅ Implementado |
| Geração de agendas com horários baseados em escalas, feriados e indisponibilidades | ✅ Implementado |
| Agendamento de consultas por calendário com seleção de especialidade, prestador e horário | ✅ Implementado |
| Recepção de paciente agendado e demanda espontânea | ✅ Implementado |
| Pré-atendimento e classificação de risco com prioridades | ✅ Implementado |
| Atendimento assistencial (médico, enfermagem) com evolução, prescrição, exames | ✅ Implementado |
| **PEP — Prontuário Eletrônico do Paciente** (ficha, histórico, documentos clínicos, evoluções) | ✅ Implementado |
| Editor de documentos eletrônicos (GrapesJS) + Modelos de impressão (WeasyPrint) | ✅ Implementado |
| Perfis assistenciais configuráveis (itens, versões, papéis) | ✅ Implementado |
| Prescrição médica e solicitação de exames | ✅ Implementado |
| Anexos clínicos com validação de segurança | ✅ Implementado |
| Alta médica e administrativa | ✅ Implementado |
| Painel de chamada público (senhas por prioridade, classes, protocolos, ícones, máquinas) | ✅ Implementado |
| Totem de autoatendimento (geração de senhas) | ✅ Implementado |
| Acesso clínico auditado | ✅ Implementado |

### 🛠️ Administrativo (apps.accounts, apps.core)

| Funcionalidade | Status |
|---|---|
| Cadastro de empresas/unidades (CNES, endereço, contatos, setores) | ✅ Implementado |
| Cadastro de usuários com login automático por nome | ✅ Implementado |
| Controle de papéis (perfis de acesso), módulos e telas | ✅ Implementado |
| Permissões granulares por tela, módulo e ação (consultar, inserir, alterar, excluir) | ✅ Implementado |
| Setores da empresa e setores de atendimento | ✅ Implementado |
| Tabelas auxiliares globais (sexo, raça/cor, cidades, estados, CIDs, especialidades, conselhos, bancos, etc.) | ✅ Implementado |
| CEP com busca e integração | ✅ Implementado |
| Tipo de prestador × conselho profissional | ✅ Implementado |
| Configuração de campos obrigatórios por formulário | ✅ Implementado |
| Trava de edição concorrente (lock por recurso) | ✅ Implementado |
| Sessões e travas de edição | ✅ Implementado |
| Importação de dados (CSV) | ✅ Implementado |

### 🎫 Suporte (apps.tickets)

| Funcionalidade | Status |
|---|---|
| Solicitação de chamados de suporte | ✅ Implementado |
| Atendimento de chamados com recebimento, conclusão e transferência | ✅ Implementado |
| Oficinas de suporte | ✅ Implementado |
| Prioridades, motivos de serviço e motivos de conclusão | ✅ Implementado |
| Vínculo usuário × oficina (quem solicita, quem atende) | ✅ Implementado |
| Impressão de comprovante de chamado | ✅ Implementado |
| Múltiplos executores por chamado | ✅ Implementado |

### 📦 Estoque (apps.estoque)

| Funcionalidade | Status |
|---|---|
| Cadastro de produtos, materiais e classificações | ✅ Implementado |
| Entrada, saída, devolução, transferência e fracionamento | ✅ Implementado |
| Solicitação de produtos (consumo assistencial, compras) | ✅ Implementado |
| Atendimento de solicitações | ✅ Implementado |
| Unidades, cotas, consumo e saldos | ✅ Implementado |
| Motivos de baixa, devolução e cancelamento | ✅ Implementado |

### 📊 Relatórios (apps.reports)

| Funcionalidade | Status |
|---|---|
| Consultas personalizadas (SQL) | ✅ Implementado |
| Exportação de relatórios | ✅ Implementado |

### 👥 Social (apps.social)

| Funcionalidade | Status |
|---|---|
| Acompanhamento social de pacientes | ✅ Implementado |

### 🩺 Enfermagem (apps.enfermagem)

| Funcionalidade | Status |
|---|---|
| Configuração de boarding (pré-atendimento) | ✅ Implementado |
| Tabelas auxiliares de enfermagem | ✅ Implementado |

### 💻 TI / Agentes (apps.ti)

| Funcionalidade | Status |
|---|---|
| Agentes de máquina e eventos | ✅ Implementado |
| Alteração de senha de usuários | ✅ Implementado |

---

## Ecossistema Celeris

O sistema é dividido em módulos independentes que compartilham a mesma base de dados e controle de acesso:

| Produto | Descrição | Status |
|---|---|---|
| **Celeris Central** | Gestão administrativa e ERP (cadastros, agendamento, recepção, estoque, relatórios) | ✅ Operacional |
| **Celeris PEP** | Prontuário Eletrônico do Paciente (evolução, prescrição, exames, documentos clínicos) | ✅ Operacional |
| **Celeris Class** | Classificação de Risco (Triagem) | ✅ Implementado |
| **Celeris Totem** | Autoatendimento para geração de senhas | ✅ Implementado |
| **Celeris Painel** | Painel de chamada de senhas e pacientes (TV/público) | ✅ Implementado |
| **Celeris BI** | Indicadores e dashboards | 🚧 Futuro |

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+, Django 5.x |
| Frontend | HTML5, CSS3 (CSS custom properties + Bootstrap 5), JavaScript vanilla |
| Banco | SQLite (desenvolvimento) / PostgreSQL (produção) / MySQL |
| PDF | WeasyPrint com editor de layouts GrapesJS |
| Templates | Django Templates (Jinja-like) |
| Ícones | Lucide (SVG inline, sem dependência externa) |

---

## Segurança e conformidade

- ✅ Controle de acesso baseado em papéis (RBAC) por módulo e tela
- ✅ Permissões acumulativas por grupo de usuário
- ✅ Bloqueio de acesso a telas inativas ou módulos inativos
- ✅ Trava de edição concorrente (impede edição simultânea do mesmo registro)
- ✅ Auditoria de criação e alteração (usuário, data/hora)
- ✅ Senha com expiração, bloqueio por tentativas e exigência de alteração no primeiro acesso
- ✅ Logs de acesso clínico auditado (PEP)
- ✅ Middleware de verificação de rota (ScreenAccessMiddleware)
- ✅ Sessão expira por inatividade
- ✅ Estrutura preparada para LGPD (logs de consentimento, auditoria)

## Roadmap de desenvolvimento

O roadmap completo está em [docs/roadmap.md](docs/roadmap.md), organizado por prioridade, risco e dependências em 10 fases (~541h totais).

### Fase atual — Fundação Técnica e Segurança (Prioridade Crítica, ~8h)
- Forçar SECRET_KEY via ambiente (remover fallback hardcoded)
- Alterar DEBUG padrão para False
- Adicionar `transaction.atomic()` em operações de múltiplos saves
- Corrigir escapeHTML no JavaScript (prevenir XSS)
- Revisar segurança de sessão (cookies seguros)
- ✅ Dead code removido do JavaScript
- ✅ CSS statusbar corrigido
- ✅ SESSION_COOKIE_AGE mantido em 15min (adequado para dados sensíveis)

### Próximas fases (visão geral)
| Fase | Foco | Esforço |
|------|------|---------|
| **Fase 2** | Qualidade e Manutenibilidade | ~65h |
| **Fase 3** | Experiência do Usuário | ~54h |
| **Fase 4** | Performance e Infraestrutura | ~28h |
| **Fase 5** | Expansão Assistencial | ~100h |
| **Fase 6** | Faturamento e Convênios | ~88h |
| **Fase 7** | Financeiro | ~64h |
| **Fases 8-10** | Contábil, BI, LGPD | ~142h |
---

## Desenvolvimento local

```bash
# Clone o repositório
git clone https://github.com/bjmvictor/Celeris.git
cd Celeris

# Configure ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env conforme necessário

# Execute as migrações
python manage.py migrate

# Crie dados iniciais (opcional)
python manage.py loaddata initial_data

# Inicie o servidor
python manage.py runserver
```

Acesse [http://localhost:8000](http://localhost:8000)

---

## Testes

```bash
# Executar suite completa
python manage.py test

# Verificar integridade do projeto
python manage.py check
python manage.py makemigrations --check --dry-run
```

Atualmente: **111+ testes** aprovados, **0 falhas** (cobertura: accounts, core, atendimento).

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
