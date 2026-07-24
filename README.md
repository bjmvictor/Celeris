# Celeris

Sistema de gestão hospitalar e clínica com suporte multiempresa, módulos integrados e controle de acesso por perfil.

## Objetivo

O Celeris tem como objetivo centralizar rotinas administrativas, assistenciais e operacionais em uma plataforma simples, moderna e segura.

Principais pontos:

* Gestão hospitalar e clínica.
* Suporte multiempresa.
* Controle de usuários, perfis e permissões.
* Estrutura modular para ecosistema próprio e integrado.
* Base preparada para adequação à LGPD.
* Segurança com controle de acesso e permissões escalável, contando com perfis de acesso.

## Tecnologias

* Python
* Django
* HTML, CSS e JavaScript
* SQLite/PostgreSQL

## Anotações técnicas
Decidido dividir o sistema em partes/telas externas, algumas delas sendo:
* Celeris Central — Gestão Administrativa (maior núcleo do sistema, envolvendo a maior parte ERP)
* Celeris PEP — Prontuário Eletrônico
* Celeris Class — Classificação de Risco
* Celeris Totem — Autoatendimento
* Celeris Painel — Chamada de senhas e pacientes
* Celeris BI — Indicadores

## Status

Projeto em fase inicial de desenvolvimento.
Até o momento:
* Cadastro de empresa
* Cadastro de usuários
* Cadastro de prestadores
* Cadastro de pacientes
* Cadastro de papeis e permissões
* Cadastro de tabelas auxiliares (Sexo, Raça/cor, Cidades, Estados, ...)
* Cadastro de escalas de prestadores
* Geração de horários de agendamento
* Agendamento de consulta
* Recepção e geração de atendimento
* Editor de documentos eletronicos + Editor de layout de impressão

Em desenvolvimento:
* Classificação de risco
* Senhas por prioridade e painel de chamada
* Prontuário eletrônico do paciente PEP

Implementações futuras:
* Chamados e suporte
* Medicações
* Farmácia
* Estoque
* Financeiro
* Contabilidade
* Exames e laudos
* Faturamento
