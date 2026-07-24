from django.urls import path

from . import views


app_name = "estoque"

urlpatterns = [
    path("tabelas/gerais/estoques/", views.estoques, name="estoques"),
    path("tabelas/gerais/unidades/", views.unidades, name="unidades"),
    path("tabelas/gerais/cotas-consumo/", views.cotas_consumo, name="cotas_consumo"),
    path("tabelas/gerais/saldos/", views.saldos_produto, name="saldos_produto"),
    path("tabelas/gerais/<slug:chave>/", views.tabela_estoque, name="tabela_estoque"),
    path("tabelas/produtos/produtos/", views.produtos, name="produtos"),
    path("tabelas/produtos/classificacao/", views.classificacoes_produto, name="classificacoes_produto"),
    path("movimentacoes/", views.movimentacoes, name="movimentacoes"),
    path("movimentacoes/<slug:tipo>/", views.movimentacoes, name="movimentacoes_tipo"),
    path("solicitacoes/solicitar/", views.solicitacoes_produto, name="solicitar_produtos"),
    path("solicitacoes/atender/", views.atender_solicitacoes_produto, name="atender_solicitacoes"),
]
