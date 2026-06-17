from django.urls import path

from . import views


app_name = "atendimento"

urlpatterns = [
    path("agendamento/agendar/", views.agendar_consultar_paciente, name="agendar"),
    path("agendamento/pacientes/<int:cd_paciente>/", views.cadastro_paciente, name="revisar-paciente-agendamento"),
    path("agendamento/pacientes/novo/", views.cadastro_paciente, name="cadastro-paciente-agendamento"),
    path("pacientes/cadastro/", views.cadastro_paciente_geral, name="cadastro-paciente-novo"),
    path("pacientes/cadastro/<int:cd_paciente>/", views.cadastro_paciente_geral, name="cadastro-paciente"),
    path("agendamento/pacientes/<int:cd_paciente>/agenda/", views.selecionar_agenda, name="selecionar-agenda"),
    path("agendamento/pacientes/<int:cd_paciente>/confirmar/", views.confirmar_agendamento, name="confirmar-agendamento"),
    path("pacientes/verificar-unico/", views.verificar_paciente_unico, name="verificar-paciente-unico"),
    path("agendamento/atender/", views.screen, {"screen": "atender-agendamento"}, name="atender-agendamento"),
    path("agendamento/consultar/", views.screen, {"screen": "consultar-agendamento"}, name="consultar-agendamento"),
    path("agendamento/agendas/", views.screen, {"screen": "agendas"}, name="agendas"),
    path("agendamento/gerar-agenda/", views.gerar_agenda, name="gerar-agenda"),
    path("agendamento/tabelas/convenios/", views.screen, {"screen": "convenios-agendamento"}, name="convenios-agendamento"),
    path("agendamento/tabelas/tipos-atendimento/", views.screen, {"screen": "tipos-atendimento-agendamento"}, name="tipos-atendimento-agendamento"),
    path("agendamento/tabelas/especialidades/", views.screen, {"screen": "especialidades-agendamento"}, name="especialidades-agendamento"),
    path("atendimento/", views.screen, {"screen": "atendimento"}, name="atendimento"),
    path("atendimento/consultar/", views.screen, {"screen": "consulta-atendimento"}, name="consulta-atendimento"),
    path("atendimento/pacientes/novo/", views.screen, {"screen": "cadastro-paciente-atendimento"}, name="cadastro-paciente-atendimento"),
    path("atendimento/tabelas/convenios/", views.screen, {"screen": "convenios-atendimento"}, name="convenios-atendimento"),
    path("atendimento/tabelas/tipos-atendimento/", views.screen, {"screen": "tipos-atendimento-atendimento"}, name="tipos-atendimento-atendimento"),
    path("atendimento/tabelas/especialidades/", views.screen, {"screen": "especialidades-atendimento"}, name="especialidades-atendimento"),
    path("tabelas/convenios/", views.screen, {"screen": "convenios"}, name="convenios"),
    path("tabelas/tipos-atendimento/", views.screen, {"screen": "tipos-atendimento"}, name="tipos-atendimento"),
    path("tabelas/especialidades/", views.screen, {"screen": "especialidades"}, name="especialidades"),
    path("tabelas/profissionais/", views.screen, {"screen": "profissionais"}, name="profissionais"),
    path("tabelas/escalas/", views.screen, {"screen": "escalas"}, name="escalas"),
    path("tabelas/salas/", views.screen, {"screen": "salas"}, name="salas"),
    path("relatorios/agendamentos/", views.screen, {"screen": "relatorio-agendamentos"}, name="relatorio-agendamentos"),
    path("relatorios/atendimentos/", views.screen, {"screen": "relatorio-atendimentos"}, name="relatorio-atendimentos"),
    path("relatorios/produtividade/", views.screen, {"screen": "relatorio-produtividade"}, name="relatorio-produtividade"),
]
