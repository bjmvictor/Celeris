# Celeris

Reestruturação do SGR em Django, mantendo uma aplicação monolítica com banco principal da própria aplicação e sem dependência de Oracle.

## Objetivo

- Centralizar backend e frontend em Django.
- Manter estilos, menus e telas base de forma local, sem CDN.
- Preservar a organização por módulos do SGR.
- Usar apenas o banco principal da aplicação.
- Preparar tabelas próprias para chamados, relatórios, serviço social, boarding e agentes.

## Rodar localmente

```powershell
cd Celeris
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Estrutura

- `apps/core`: navegação, painel inicial, permissões de módulos.
- `apps/accounts`: usuário customizado.
- `apps/reports`: consultas SQL internas e destinos de relatório.
- `apps/tickets`: chamados genéricos por módulo.
- `apps/social`: atendimentos e prestações sociais.
- `apps/enfermagem`: boarding e histórico.
- `apps/ti`: agentes conectados e inventário.

As telas ainda são base para evolução gradual. Nenhuma conexão Oracle foi criada.
