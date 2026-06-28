# Celeris

Sistema de gestão hospitalar e clínica com suporte multiempresa, módulos integrados e controle de acesso por perfil.

## Objetivo

O Celeris tem como objetivo centralizar rotinas administrativas, assistenciais e operacionais em uma plataforma simples, moderna e segura.

Principais pontos:

* Gestão hospitalar e clínica.
* Suporte multiempresa.
* Controle de usuários, perfis e permissões.
* Estrutura modular para evolução gradual.
* Base preparada para adequação à LGPD.

## Tecnologias

* Python
* Django
* HTML, CSS e JavaScript
* SQLite/PostgreSQL

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

Acesse:

```text
http://127.0.0.1:8000/
```

## Estrutura

```text
apps/
├── core          # Base do sistema, menu, módulos e painel inicial
├── accounts      # Usuários, autenticação e permissões
├── reports       # Relatórios e consultas internas
├── tickets       # Chamados por módulo
├── enfermagem    # Boarding e histórico assistencial
└── ti            # Inventário, agentes e suporte técnico
```

## Status

Projeto em fase inicial de desenvolvimento.

As telas atuais são bases para evolução dos módulos.
Nenhuma conexão Oracle foi implementada até o momento.
