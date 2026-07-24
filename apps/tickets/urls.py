from django.urls import path

from . import views


app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list, name="list"),
    path("solicitacoes/solicitar/", views.solicitar, name="solicitar"),
    path("solicitacoes/atender/", views.atender, name="atender"),
    path("solicitacoes/<int:cd_ticket>/imprimir/", views.imprimir_chamado, name="imprimir_chamado"),
    path("tabelas/prioridades/", views.prioridades, name="prioridades"),
    path("tabelas/motivos-servico/", views.motivos_servico, name="motivos_servico"),
    path("tabelas/motivos-conclusao/", views.motivos_conclusao, name="motivos_conclusao"),
    path("tabelas/oficinas/", views.oficinas, name="oficinas"),
    path("acessos/usuario-oficina/", views.usuario_oficina, name="usuario_oficina"),
]
