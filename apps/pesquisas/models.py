import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import Empresa


class Pesquisa(models.Model):
    TIPOS = [
        ("SATISFACAO", "Satisfação"),
        ("CLIMA", "Clima organizacional"),
        ("AVALIACAO", "Avaliação"),
        ("CHECKLIST", "Checklist"),
        ("OUTRA", "Outra"),
    ]
    CALCULOS = [
        ("SOMA", "Soma ponderada"),
        ("MEDIA", "Média ponderada"),
        ("PERCENTUAL", "Percentual do total possível"),
    ]

    cd_pesquisa = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_token_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    nm_pesquisa = models.CharField(max_length=180)
    ds_descricao = models.TextField(blank=True)
    tp_pesquisa = models.CharField(max_length=20, choices=TIPOS, default="SATISFACAO")
    tp_calculo = models.CharField(max_length=20, choices=CALCULOS, default="MEDIA")
    sn_anonima = models.BooleanField(default=True)
    sn_publica = models.BooleanField(default=True)
    sn_ativo = models.BooleanField(default=True)
    dh_inicio = models.DateTimeField(null=True, blank=True)
    dh_fim = models.DateTimeField(null=True, blank=True)
    dh_criacao = models.DateTimeField(default=timezone.now, editable=False)
    dh_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pesquisa"
        ordering = ("nm_pesquisa",)
        constraints = [
            models.UniqueConstraint(fields=("cd_empresa", "nm_pesquisa"), name="pesquisa_empresa_nome_unico")
        ]

    def __str__(self):
        return self.nm_pesquisa

    @property
    def disponivel(self):
        agora = timezone.now()
        return bool(
            self.sn_ativo
            and (not self.dh_inicio or self.dh_inicio <= agora)
            and (not self.dh_fim or self.dh_fim >= agora)
        )


class PerguntaPesquisa(models.Model):
    TIPOS = [
        ("UNICA", "Uma resposta"),
        ("MULTIPLA", "Múltiplas respostas"),
        ("ESCALA", "Escala"),
        ("NUMERO", "Número"),
        ("TEXTO", "Texto livre"),
    ]

    cd_pergunta_pesquisa = models.BigAutoField(primary_key=True)
    cd_pesquisa = models.ForeignKey(Pesquisa, related_name="perguntas", on_delete=models.CASCADE, db_column="cd_pesquisa")
    ds_pergunta = models.CharField(max_length=500)
    tp_resposta = models.CharField(max_length=20, choices=TIPOS, default="UNICA")
    nr_peso = models.DecimalField(max_digits=8, decimal_places=3, default=1)
    nr_minimo = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    nr_maximo = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    nr_ordem = models.PositiveIntegerField(default=0)
    sn_obrigatoria = models.BooleanField(default=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "pesquisa_pergunta"
        ordering = ("nr_ordem", "cd_pergunta_pesquisa")

    def __str__(self):
        return self.ds_pergunta


class OpcaoRespostaPesquisa(models.Model):
    cd_opcao_resposta_pesquisa = models.BigAutoField(primary_key=True)
    cd_pergunta_pesquisa = models.ForeignKey(
        PerguntaPesquisa, related_name="opcoes", on_delete=models.CASCADE, db_column="cd_pergunta_pesquisa"
    )
    ds_resposta = models.CharField(max_length=300)
    nr_valor = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    nr_ordem = models.PositiveIntegerField(default=0)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "pesquisa_opcao_resposta"
        ordering = ("nr_ordem", "cd_opcao_resposta_pesquisa")

    def __str__(self):
        return self.ds_resposta


class FaixaResultadoPesquisa(models.Model):
    cd_faixa_resultado_pesquisa = models.BigAutoField(primary_key=True)
    cd_pesquisa = models.ForeignKey(Pesquisa, related_name="faixas_resultado", on_delete=models.CASCADE, db_column="cd_pesquisa")
    nm_resultado = models.CharField(max_length=120)
    nr_minimo = models.DecimalField(max_digits=12, decimal_places=3)
    nr_maximo = models.DecimalField(max_digits=12, decimal_places=3)
    ds_mensagem = models.TextField()
    ds_cor = models.CharField(max_length=20, default="#2563eb")
    nr_ordem = models.PositiveIntegerField(default=0)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "pesquisa_faixa_resultado"
        ordering = ("nr_ordem", "nr_minimo")

    def clean(self):
        if self.nr_minimo is not None and self.nr_maximo is not None and self.nr_minimo > self.nr_maximo:
            raise ValidationError({"nr_maximo": "O valor máximo deve ser maior ou igual ao mínimo."})
        if self.cd_pesquisa_id and self.sn_ativo and self.nr_minimo is not None and self.nr_maximo is not None:
            overlapping = type(self).objects.filter(
                cd_pesquisa_id=self.cd_pesquisa_id,
                sn_ativo=True,
                nr_minimo__lte=self.nr_maximo,
                nr_maximo__gte=self.nr_minimo,
            ).exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError("A faixa se sobrepõe a outra faixa ativa desta pesquisa.")

    def __str__(self):
        return self.nm_resultado


class RespostaPesquisa(models.Model):
    cd_resposta_pesquisa = models.BigAutoField(primary_key=True)
    cd_pesquisa = models.ForeignKey(Pesquisa, related_name="respostas", on_delete=models.PROTECT, db_column="cd_pesquisa")
    cd_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario"
    )
    cd_faixa_resultado = models.ForeignKey(
        FaixaResultadoPesquisa, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_faixa_resultado"
    )
    nr_resultado = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    dh_resposta = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "pesquisa_resposta"
        ordering = ("-dh_resposta",)


class ItemRespostaPesquisa(models.Model):
    cd_item_resposta_pesquisa = models.BigAutoField(primary_key=True)
    cd_resposta_pesquisa = models.ForeignKey(
        RespostaPesquisa, related_name="itens", on_delete=models.CASCADE, db_column="cd_resposta_pesquisa"
    )
    cd_pergunta_pesquisa = models.ForeignKey(
        PerguntaPesquisa, on_delete=models.PROTECT, db_column="cd_pergunta_pesquisa"
    )
    cd_opcao_resposta = models.ForeignKey(
        OpcaoRespostaPesquisa, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_opcao_resposta"
    )
    ds_resposta = models.TextField(blank=True)
    nr_valor = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "pesquisa_resposta_item"
        ordering = ("cd_pergunta_pesquisa__nr_ordem", "cd_item_resposta_pesquisa")
