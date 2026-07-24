from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class EmpresaModel(TimeStampedModel):
    cd_empresa = models.ForeignKey(
        "accounts.Empresa",
        on_delete=models.PROTECT,
        db_column="cd_empresa",
    )

    class Meta:
        abstract = True


class Estoque(EmpresaModel):
    cd_estoque = models.BigAutoField(primary_key=True)
    nm_estoque = models.CharField("nome", max_length=140)
    ds_codigo = models.CharField("codigo", max_length=40, blank=True)
    cd_setor = models.ForeignKey(
        "accounts.Setor",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_setor",
    )
    sn_principal = models.BooleanField("principal", default=False)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "estoque"
        ordering = ("nm_estoque",)
        unique_together = ("cd_empresa", "nm_estoque")

    def __str__(self):
        return self.nm_estoque


class UnidadeProduto(EmpresaModel):
    cd_unidade_produto = models.BigAutoField(primary_key=True)
    ds_sigla = models.CharField("sigla", max_length=20)
    ds_descricao = models.CharField("descricao", max_length=120)
    qt_fator_conversao = models.DecimalField("fator", max_digits=10, decimal_places=3, default=Decimal("1.000"))
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "unidade_produto"
        ordering = ("ds_sigla",)
        unique_together = ("cd_empresa", "ds_sigla")

    def __str__(self):
        return f"{self.ds_sigla} - {self.ds_descricao}"


class ProdutoClassificacao(EmpresaModel):
    cd_classificacao_produto = models.BigAutoField(primary_key=True)
    nm_classificacao = models.CharField("classificacao", max_length=120)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "produto_classificacao"
        ordering = ("nm_classificacao",)
        unique_together = ("cd_empresa", "nm_classificacao")

    def __str__(self):
        return self.nm_classificacao


class TabelaEstoque(EmpresaModel):
    cd_tabela_estoque = models.BigAutoField(primary_key=True)
    ds_chave = models.SlugField("chave", max_length=80)
    ds_nome = models.CharField("nome", max_length=140)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "tabela_estoque"
        ordering = ("ds_nome",)
        unique_together = ("cd_empresa", "ds_chave")

    def __str__(self):
        return self.ds_nome


class ValorTabelaEstoque(EmpresaModel):
    cd_valor_tabela_estoque = models.BigAutoField(primary_key=True)
    cd_tabela = models.ForeignKey(
        TabelaEstoque,
        related_name="valores",
        on_delete=models.CASCADE,
        db_column="cd_tabela_estoque",
    )
    cd_valor = models.CharField("codigo", max_length=40)
    ds_valor = models.CharField("valor", max_length=160)
    ds_observacao = models.CharField("observacao", max_length=240, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "valor_tabela_estoque"
        ordering = ("cd_tabela__ds_nome", "ds_valor")
        unique_together = ("cd_tabela", "cd_valor")

    def __str__(self):
        return f"{self.cd_valor} - {self.ds_valor}"


class Produto(EmpresaModel):
    class TipoProduto(models.TextChoices):
        MATERIAL = "MATERIAL", "Material"
        MEDICAMENTO = "MEDICAMENTO", "Medicamento"
        EXAME = "EXAME", "Exame/insumo"
        OPME = "OPME", "OPME"
        OUTRO = "OUTRO", "Outro"

    cd_produto = models.BigAutoField(primary_key=True)
    cd_codigo = models.CharField("codigo", max_length=40, blank=True)
    nm_produto = models.CharField("produto", max_length=180)
    tp_produto = models.CharField("tipo", max_length=20, choices=TipoProduto.choices, default=TipoProduto.MATERIAL)
    cd_unidade = models.ForeignKey(UnidadeProduto, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_unidade_produto")
    cd_classificacao = models.ForeignKey(ProdutoClassificacao, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_classificacao_produto")
    ds_descricao = models.TextField("descricao", blank=True)
    ds_lote = models.CharField("lote padrao", max_length=60, blank=True)
    dt_validade = models.DateField("validade padrao", null=True, blank=True)
    ds_carater = models.CharField("carater", max_length=80, blank=True)
    ds_classe = models.CharField("classe", max_length=80, blank=True)
    cd_procedimento_faturamento = models.CharField("procedimento de faturamento", max_length=80, blank=True)
    sn_controla_lote = models.BooleanField("controla lote", default=False)
    sn_controla_validade = models.BooleanField("controla validade", default=False)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "produto"
        ordering = ("nm_produto",)
        unique_together = ("cd_empresa", "nm_produto")

    def __str__(self):
        return self.nm_produto


class ProdutoEstoque(EmpresaModel):
    cd_produto_estoque = models.BigAutoField(primary_key=True)
    cd_produto = models.ForeignKey(Produto, related_name="saldos", on_delete=models.PROTECT, db_column="cd_produto")
    cd_estoque = models.ForeignKey(Estoque, related_name="produtos", on_delete=models.PROTECT, db_column="cd_estoque")
    qt_saldo = models.DecimalField("saldo", max_digits=14, decimal_places=3, default=Decimal("0.000"))
    qt_reservado = models.DecimalField("reservado", max_digits=14, decimal_places=3, default=Decimal("0.000"))
    qt_minima = models.DecimalField("minimo", max_digits=14, decimal_places=3, default=Decimal("0.000"))
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "produto_estoque"
        ordering = ("cd_estoque__nm_estoque", "cd_produto__nm_produto")
        unique_together = ("cd_empresa", "cd_produto", "cd_estoque")

    @property
    def qt_disponivel(self):
        return self.qt_saldo - self.qt_reservado

    def __str__(self):
        return f"{self.cd_produto} - {self.cd_estoque}"


class CotaConsumo(EmpresaModel):
    cd_cota_consumo = models.BigAutoField(primary_key=True)
    cd_estoque = models.ForeignKey(Estoque, on_delete=models.PROTECT, db_column="cd_estoque")
    cd_produto = models.ForeignKey(Produto, on_delete=models.PROTECT, db_column="cd_produto")
    qt_cota = models.DecimalField("cota", max_digits=14, decimal_places=3)
    nr_dias = models.PositiveIntegerField("dias", default=30)
    dt_inicio_vigencia = models.DateField("inicio da vigencia")
    dt_fim_vigencia = models.DateField("fim da vigencia", null=True, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "cota_consumo"
        ordering = ("cd_estoque__nm_estoque", "cd_produto__nm_produto")

    def __str__(self):
        return f"{self.cd_estoque} - {self.cd_produto}"


class MovimentoEstoque(EmpresaModel):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saida"
        DEVOLUCAO = "DEVOLUCAO", "Devolucao"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        FRACIONAMENTO = "FRACIONAMENTO", "Fracionamento"
        ACERTO = "ACERTO", "Acerto de estoque"

    class Destino(models.TextChoices):
        SETOR = "SETOR", "Setor"
        PACIENTE = "PACIENTE", "Paciente"
        FORNECEDOR = "FORNECEDOR", "Fornecedor"
        GASTO_SALA = "GASTO_SALA", "Gasto de sala"
        ESTOQUE = "ESTOQUE", "Estoque"

    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        FINALIZADO = "FINALIZADO", "Finalizado"
        CANCELADO = "CANCELADO", "Cancelado"

    cd_movimento_estoque = models.BigAutoField(primary_key=True)
    tp_movimento = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    tp_destino = models.CharField("destino", max_length=20, choices=Destino.choices, blank=True)
    cd_estoque_origem = models.ForeignKey(Estoque, null=True, blank=True, related_name="movimentos_origem", on_delete=models.PROTECT, db_column="cd_estoque_origem")
    cd_estoque_destino = models.ForeignKey(Estoque, null=True, blank=True, related_name="movimentos_destino", on_delete=models.PROTECT, db_column="cd_estoque_destino")
    cd_setor = models.ForeignKey("accounts.Setor", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor")
    cd_atendimento = models.ForeignKey("atendimento.Atendimento", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_atendimento")
    ds_motivo = models.CharField("motivo", max_length=180, blank=True)
    ds_observacao = models.TextField("observacao", blank=True)
    ds_status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.ABERTO)
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario")

    class Meta:
        db_table = "movimento_estoque"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_tp_movimento_display()} #{self.pk}"


class ItemMovimentoEstoque(models.Model):
    cd_item_movimento_estoque = models.BigAutoField(primary_key=True)
    cd_movimento = models.ForeignKey(MovimentoEstoque, related_name="itens", on_delete=models.CASCADE, db_column="cd_movimento_estoque")
    cd_produto = models.ForeignKey(Produto, on_delete=models.PROTECT, db_column="cd_produto")
    qt_movimento = models.DecimalField("quantidade", max_digits=14, decimal_places=3)
    ds_lote = models.CharField("lote", max_length=60, blank=True)
    dt_validade = models.DateField("validade", null=True, blank=True)

    class Meta:
        db_table = "item_movimento_estoque"


class SolicitacaoProduto(EmpresaModel):
    class Tipo(models.TextChoices):
        SETOR = "SETOR", "Para setor"
        PACIENTE = "PACIENTE", "Para paciente"
        COMPRA = "COMPRA", "Compra"
        DEVOLUCAO = "DEVOLUCAO", "Devolucao"

    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        RECEBIDA = "RECEBIDA", "Recebida"
        ATENDIDA = "ATENDIDA", "Atendida"
        CANCELADA = "CANCELADA", "Cancelada"

    cd_solicitacao_produto = models.BigAutoField(primary_key=True)
    tp_solicitacao = models.CharField("tipo", max_length=20, choices=Tipo.choices, default=Tipo.SETOR)
    cd_estoque = models.ForeignKey(Estoque, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_estoque")
    cd_setor = models.ForeignKey("accounts.Setor", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor")
    cd_atendimento = models.ForeignKey("atendimento.Atendimento", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_atendimento")
    ds_motivo = models.CharField("motivo", max_length=180, blank=True)
    ds_observacao = models.TextField("observacao", blank=True)
    ds_status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.ABERTA)
    cd_usuario_solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="solicitacoes_produto", on_delete=models.SET_NULL, db_column="cd_usuario_solicitante")
    cd_usuario_atendente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="atendimentos_solicitacao_produto", on_delete=models.SET_NULL, db_column="cd_usuario_atendente")

    class Meta:
        db_table = "solicitacao_produto"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Solicitacao #{self.pk}"


class ItemSolicitacaoProduto(models.Model):
    cd_item_solicitacao_produto = models.BigAutoField(primary_key=True)
    cd_solicitacao = models.ForeignKey(SolicitacaoProduto, related_name="itens", on_delete=models.CASCADE, db_column="cd_solicitacao_produto")
    cd_produto = models.ForeignKey(Produto, on_delete=models.PROTECT, db_column="cd_produto")
    qt_solicitada = models.DecimalField("quantidade", max_digits=14, decimal_places=3)
    qt_saldo_estoque = models.DecimalField("saldo no estoque", max_digits=14, decimal_places=3, default=Decimal("0.000"))
    sn_alerta_estoque = models.BooleanField("sem estoque suficiente", default=False)

    class Meta:
        db_table = "item_solicitacao_produto"
