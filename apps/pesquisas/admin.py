from django.contrib import admin

from .models import FaixaResultadoPesquisa, OpcaoRespostaPesquisa, PerguntaPesquisa, Pesquisa, RespostaPesquisa


admin.site.register((Pesquisa, PerguntaPesquisa, OpcaoRespostaPesquisa, FaixaResultadoPesquisa, RespostaPesquisa))
