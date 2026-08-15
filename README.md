<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![CCL-1.0 License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<br />

<div align="center">
  <a href="https://github.com/bjmvictor/Celeris">
    <img src="static/img/logo.png" alt="Celeris" width="96" height="96">
  </a>

  <h2 align="center">Celeris</h2>

  <p align="center">
    <strong>Plataforma modular de gestão clínica e hospitalar</strong>
    <br />
    Uma base integrada para processos administrativos, assistenciais e operacionais em instituições de saúde.
    <br />
    <br />
    <a href="https://bjmvictor.github.io/Celeris/"><strong>Acessar documentação »</strong></a>
    <br />
    <br />
    <a href="https://github.com/bjmvictor/Celeris/issues">Reportar problema</a>
    ·
    <a href="https://github.com/bjmvictor/Celeris/issues">Solicitar funcionalidade</a>
  </p>
</div>

---

## Sobre o projeto

O **Celeris** é uma plataforma de gestão clínica e hospitalar desenvolvida com foco em modularidade, organização de processos, controle de acesso e evolução contínua.

O projeto busca concentrar em uma única solução funcionalidades administrativas e assistenciais que normalmente ficam distribuídas entre sistemas, planilhas e fluxos manuais.

Entre os principais objetivos do Celeris estão:

- centralizar informações e rotinas clinicas e hospitalares;
- reduzir tarefas manuais e retrabalho;
- padronizar fluxos operacionais;
- permitir crescimento por módulos;
- oferecer controle de acesso por usuário, papel e empresa;
- disponibilizar uma base preparada para novos recursos assistenciais e integrações.

> O Celeris está em desenvolvimento contínuo. Funcionalidades, fluxos e estruturas podem sofrer alterações entre versões.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Principais funcionalidades

### Gestão e cadastros

- Cadastro e manutenção de pacientes.
- Cadastro de prestadores e profissionais.
- Cadastro de usuários.
- Controle de empresas.
- Perfis, papéis e permissões.
- Cadastros de dados auxiliares utilizados pelos demais módulos.

### Atendimento

- Organização do fluxo de atendimento.
- Geração e acompanhamento de atendimentos.
- Integração com agendas e prestadores.
- Estrutura para classificação e acompanhamento assistencial.

### Prontuário Eletrônico do Paciente

- Estrutura de PEP integrada ao atendimento.
- Evoluções e registros assistenciais.
- Organização dos documentos do prontuário.
- Prescrições e informações clínicas.
- Fluxos de alta e encerramento de atendimento.
- PDFs finais imutáveis e assinatura digital PAdES com certificado A1, quando configurada.

Configuração operacional: [`docs/assinatura-digital.md`](docs/assinatura-digital.md).

### Agendas

- Cadastro de agendas por prestador.
- Configuração de especialidades.
- Controle de horários.
- Tratamento de dias disponíveis e feriados.
- Seleção de agenda por data e profissional.

### Enfermagem e indicadores

- Estrutura para indicadores assistenciais.
- Classificação e coleta de sinais vitais e acompanhamento do paciente
- Administração de medicação e acompanhamento
- Relatórios por competência e setor.
- Evolução contínua de indicadores e relatórios operacionais.

### Tecnologia da Informação

- Recursos voltados ao acompanhamento do parque tecnológico.
- Integrações com agentes e serviços auxiliares.
- Estrutura para inventário e acompanhamento de equipamentos.

### Relatórios e consultas

- Consultas estruturadas por módulo.
- Filtros e pesquisa de registros.
- Exportação e impressão conforme a funcionalidade.
- Relatórios operacionais e assistenciais.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Tecnologias

O Celeris utiliza uma arquitetura web baseada principalmente em:

[![Python][Python]][Python-url]
[![Django][Django]][Django-url]
[![HTML5][HTML5]][HTML5-url]
[![CSS3][CSS3]][CSS3-url]
[![JavaScript][JavaScript]][JavaScript-url]

O projeto também possui integrações e componentes auxiliares que podem utilizar outras tecnologias de acordo com cada módulo.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Primeiros passos

### Pré-requisitos

Para executar o projeto localmente, tenha instalado:

- Python 3
- Git
- Banco de dados relacional para implantação em produção
  - Em desenvolvimento e testes locais, o projeto pode utilizar SQLite.

### Instalação

1. Clone o repositório:

```bash
git clone https://github.com/bjmvictor/Celeris.git
```

2. Acesse a pasta do projeto:

```bash
cd Celeris
```

3. Crie um ambiente virtual:

```bash
python -m venv .venv
```

4. Ative o ambiente virtual.

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD**

```cmd
.venv\Scripts\activate.bat
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

5. Instale as dependências:

```bash
pip install -r requirements.txt
```

6. Configure as variáveis de ambiente necessárias para sua instalação.

7. Execute as migrations:

```bash
python manage.py migrate
```

8. Crie um usuário mestre, necessário para o setup inicial:

```bash
python manage.py createsuperuser
```

9. Inicie o servidor:

```bash
python manage.py runserver
```

### Dados fictícios para teste e homologação

Para criar uma empresa demonstrativa já em uso, com setores, convênios, papéis,
prestadores, usuários, pacientes, fila de classificação e atendimentos em vários
estágios, execute:

```bash
python manage.py populate
```

O comando é idempotente e pode ser executado novamente sem duplicar o cenário do
dia. Os usuários `ADMINDEMO`, `RECEPCAODEMO`, `ENFERMAGEMDEMO`, `MEDICODEMO` e
`AUDITORDEMO` são criados com a senha inicial `Celeris@123`. Para escolher outra
senha, use `--senha-padrao`. Quando `DEBUG=False`, é necessário confirmar o uso em
homologação com `--permitir-fora-debug`.

Por padrão, o ambiente de desenvolvimento ficará disponível em:

```text
http://127.0.0.1:8000/
```

> Consulte a [documentação oficial do Celeris](https://bjmvictor.github.io/Celeris/) para detalhes de configuração e uso.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Estrutura e filosofia

O projeto é desenvolvido com foco em:

- **Modularidade** — novas áreas podem ser adicionadas sem concentrar toda a regra de negócio em um único módulo.
- **Multiempresa** — estrutura preparada para utilização por diferentes empresas ou unidades.
- **Controle de acesso** — permissões baseadas em usuários, papéis, funcionalidades e empresa.
- **Padronização** — telas e fluxos seguem padrões comuns de navegação e operação.
- **Evolução incremental** — novas funcionalidades são incorporadas gradualmente conforme a necessidade dos processos.
- **Integração** — arquitetura preparada para comunicação com sistemas, serviços e bases externas.

---

## Roadmap

O desenvolvimento do Celeris é contínuo. Entre os principais pontos de evolução estão:

- [x] Estrutura multiempresa.
- [x] Cadastro de pacientes.
- [x] Cadastro de prestadores.
- [x] Cadastro e gerenciamento de usuários.
- [x] Papéis e permissões.
- [x] Estrutura de agendas.
- [x] Base do Prontuário Eletrônico do Paciente.
- [x] Fluxos iniciais de atendimento.
- [x] Documentação web do projeto.
- [x] Acolhimento de paciente e coleta de dados.
- [x] Editor de documentos eletrônicos + impressão de layout.
- [x] Criação de telas personalizaveis para o fluxo no PEP.
- [x] Painel de chamada configurável com narração de voz.
- [x] Estrutura de suporte com solicitação de chamados, acompanhamento e baixa.
- [ ] Expansão dos recursos do PEP.
- [ ] Implementação de indicadores assistenciais.
- [ ] Evolução dos relatórios gerenciais, operacionais, administrativos e assistenciais.
- [ ] Novas integrações com sistemas hospitalares(HL7, MWL, MPPS).
- [ ] Expansão dos recursos de auditoria e rastreabilidade.
- [ ] Aprimoramento de notificações e automações.
- [ ] Novos módulos administrativos e assistenciais.

Veja as [issues abertas](https://github.com/bjmvictor/Celeris/issues) para acompanhar melhorias, correções e funcionalidades propostas.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Contribuindo

Contribuições são bem-vindas.

Se quiser propor uma melhoria:

1. Faça um fork do projeto.
2. Crie uma branch para sua alteração:

```bash
git checkout -b feature/minha-funcionalidade
```

3. Faça suas alterações.
4. Crie um commit:

```bash
git commit -m "Adiciona nova funcionalidade"
```

5. Envie sua branch:

```bash
git push origin feature/minha-funcionalidade
```

6. Abra um Pull Request.

Para sugestões, bugs ou melhorias, também é possível utilizar as [issues do projeto](https://github.com/bjmvictor/Celeris/issues).

### Contribuidores

<a href="https://github.com/bjmvictor/Celeris/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=bjmvictor/Celeris" alt="Contribuidores do Celeris" />
</a>

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Licença

Distribuído sob a licença **CCL-1.0**.

Consulte o arquivo [`LICENSE`](LICENSE) para mais informações.

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Contato

**Benjamin Victor**

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Instagram][instagram-shield]][instagram-url]
[![WhatsApp][whatsapp-shield]][whatsapp-url]
[![E-mail][gmail-shield]][gmail-url]


Projeto: [github.com/bjmvictor/Celeris](https://github.com/bjmvictor/Celeris)

Documentação: [bjmvictor.github.io/Celeris](https://bjmvictor.github.io/Celeris/)

<p align="right">(<a href="#readme-top">voltar ao topo</a>)</p>

---

## Referências e recursos

- [Django](https://www.djangoproject.com/)
- [Python](https://www.python.org/)
- [Shields.io](https://shields.io/)
- [GitHub Pages](https://pages.github.com/)
- [Font Awesome](https://fontawesome.com/)
- [Lucide](https://lucide.dev/)

---

<!-- MARKDOWN LINKS & IMAGES -->

[contributors-shield]: https://img.shields.io/github/contributors/bjmvictor/Celeris.svg?style=for-the-badge
[contributors-url]: https://github.com/bjmvictor/Celeris/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/bjmvictor/Celeris.svg?style=for-the-badge
[forks-url]: https://github.com/bjmvictor/Celeris/network/members

[linkedin-shield]: https://img.shields.io/badge/LinkedIn-Perfil-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white
[linkedin-url]: https://www.linkedin.com/in/bjmvictor/

[instagram-shield]: https://img.shields.io/badge/Instagram-@bjm.victor-E4405F?style=for-the-badge&logo=instagram&logoColor=white
[instagram-url]: https://www.instagram.com/bjm.victor/

[whatsapp-shield]: https://img.shields.io/badge/WhatsApp-Contato-25D366?style=for-the-badge&logo=whatsapp&logoColor=white
[whatsapp-url]: https://wa.me/5581992138687

[gmail-shield]: https://img.shields.io/badge/E--mail-bjm.victor@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white
[gmail-url]: mailto:bjm.victor@gmail.com

[stars-shield]: https://img.shields.io/github/stars/bjmvictor/Celeris.svg?style=for-the-badge
[stars-url]: https://github.com/bjmvictor/Celeris/stargazers

[issues-shield]: https://img.shields.io/github/issues/bjmvictor/Celeris.svg?style=for-the-badge
[issues-url]: https://github.com/bjmvictor/Celeris/issues

[license-shield]: https://img.shields.io/badge/License-CCL--1.0-yellow?style=for-the-badge
[license-url]: https://github.com/bjmvictor/Celeris/blob/main/LICENSE

[linkedin-shield]: https://img.shields.io/badge/LinkedIn-Perfil-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white
[linkedin-url]: https://www.linkedin.com/in/bjmvictor/

[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/

[Django]: https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white
[Django-url]: https://www.djangoproject.com/

[HTML5]: https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white
[HTML5-url]: https://developer.mozilla.org/docs/Web/HTML

[CSS3]: https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white
[CSS3-url]: https://developer.mozilla.org/docs/Web/CSS

[JavaScript]: https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=000
[JavaScript-url]: https://developer.mozilla.org/docs/Web/JavaScript
