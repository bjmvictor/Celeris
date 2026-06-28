from django.urls import path

from . import views


app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("em-desenvolvimento/", views.placeholder, name="placeholder"),
    path("lookup/", views.lookup_options, name="lookup_options"),
    path("telas/<slug:slug>/", views.dynamic_screen, name="dynamic_screen"),
    path("configuracao/telas/", views.system_screens, name="system_screens"),
    path("configuracao/telas/nova/", views.system_screen_edit, name="system_screen_new"),
    path("configuracao/telas/<int:pk>/", views.system_screen_edit, name="system_screen_edit"),
    path("configuracao/campos/", views.system_fields, name="system_fields"),
    path("configuracao/campos/novo/", views.system_field_edit, name="system_field_new"),
    path("configuracao/campos/<int:pk>/", views.system_field_edit, name="system_field_edit"),
    path("configuracao/empresas/", views.system_companies, name="system_companies"),
    path("configuracao/empresas/nova/", views.system_company_edit, name="system_company_new"),
    path("configuracao/empresas/<int:pk>/", views.system_company_edit, name="system_company_edit"),
    path("global/empresa/setores/", views.setores, name="setores"),
    path("global/empresa/setores-atendimento/", views.setores, {"tipo": "ATENDIMENTO"}, name="setores_atendimento"),
    path("global/tabelas/auxiliares/tipo-sanguineo/", views.global_auxiliary_values, {"tabela": "tipo_sanguineo"}, name="global_tipo_sanguineo"),
    path("global/tabelas/auxiliares/sexo/", views.global_auxiliary_values, {"tabela": "sexo"}, name="global_sexo"),
    path("global/tabelas/auxiliares/estado-civil/", views.global_auxiliary_values, {"tabela": "estado_civil"}, name="global_estado_civil"),
    path("global/tabelas/auxiliares/naturalidade/", views.global_auxiliary_values, {"tabela": "naturalidade"}, name="global_naturalidade"),
    path("global/tabelas/auxiliares/nacionalidade/", views.global_auxiliary_values, {"tabela": "nacionalidade"}, name="global_nacionalidade"),
    path("global/tabelas/auxiliares/cidade/", views.global_auxiliary_values, {"tabela": "cidade"}, name="global_cidade"),
    path("global/tabelas/auxiliares/cidades-opcoes/", views.city_options, name="global_city_options"),
    path("global/tabelas/auxiliares/cep-opcao/", views.cep_option, name="global_cep_option"),
    path("global/tabelas/auxiliares/estado/", views.global_auxiliary_values, {"tabela": "estado"}, name="global_estado"),
    path("global/tabelas/auxiliares/motivos-alteracao/", views.global_auxiliary_values, {"tabela": "motivo_alteracao"}, name="global_motivo_alteracao"),
    path("global/tabelas/tipo-prestador-conselho/", views.tipo_prestador_conselho, name="tipo_prestador_conselho"),
    path("global/ceps/", views.global_ceps, name="global_ceps"),
    path("global/tabelas/", views.global_tables, name="global_tables"),
    path("global/integracoes/", views.global_integrations, name="global_integrations"),
    path("global/tabelas/auxiliares/<slug:tabela>/", views.global_auxiliary_values, name="global_auxiliar"),
]
