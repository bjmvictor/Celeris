from django import forms
from django.forms import inlineformset_factory

from apps.accounts.models import Setor

from .models import (
    CotaConsumo,
    Estoque,
    ItemMovimentoEstoque,
    ItemSolicitacaoProduto,
    MovimentoEstoque,
    Produto,
    ProdutoClassificacao,
    ProdutoEstoque,
    SolicitacaoProduto,
    TabelaEstoque,
    UnidadeProduto,
    ValorTabelaEstoque,
)


class EmpresaScopedModelForm(forms.ModelForm):
    def __init__(self, *args, empresa=None, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if empresa:
            for field in self.fields.values():
                queryset = getattr(field, "queryset", None)
                if queryset is not None and hasattr(queryset.model, "cd_empresa"):
                    field.queryset = queryset.filter(cd_empresa=empresa)
            if "cd_setor" in self.fields:
                self.fields["cd_setor"].queryset = Setor.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_setor")
        for field in self.fields.values():
            field.widget.attrs.setdefault("data-consultable", "true")
            field.widget.attrs.setdefault("data-editable", "true")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa and hasattr(instance, "cd_empresa_id") and not instance.cd_empresa_id:
            instance.cd_empresa = self.empresa
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class EstoqueForm(EmpresaScopedModelForm):
    class Meta:
        model = Estoque
        fields = ("ds_codigo", "nm_estoque", "cd_setor", "sn_principal", "sn_ativo")


class UnidadeProdutoForm(EmpresaScopedModelForm):
    class Meta:
        model = UnidadeProduto
        fields = ("ds_sigla", "ds_descricao", "qt_fator_conversao", "sn_ativo")


class ProdutoClassificacaoForm(EmpresaScopedModelForm):
    class Meta:
        model = ProdutoClassificacao
        fields = ("nm_classificacao", "sn_ativo")


class ValorTabelaEstoqueForm(EmpresaScopedModelForm):
    class Meta:
        model = ValorTabelaEstoque
        fields = ("cd_valor", "ds_valor", "ds_observacao", "sn_ativo")


class ProdutoForm(EmpresaScopedModelForm):
    ds_carater = forms.ChoiceField(label="Caráter", required=False, choices=())
    ds_classe = forms.ChoiceField(label="Classe", required=False, choices=())

    class Meta:
        model = Produto
        fields = (
            "cd_codigo", "nm_produto", "tp_produto", "cd_unidade", "cd_classificacao",
            "ds_descricao", "ds_lote", "dt_validade", "ds_carater", "ds_classe",
            "cd_procedimento_faturamento", "sn_controla_lote", "sn_controla_validade", "sn_ativo",
        )
        widgets = {
            "dt_validade": forms.DateInput(attrs={"type": "date"}),
            "ds_descricao": forms.Textarea(attrs={"rows": 1, "class": "product-description-field"}),
            "cd_codigo": forms.TextInput(attrs={"class": "field-short-code"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, empresa=empresa, **kwargs)
        if empresa:
            self.fields["ds_carater"].choices = self._choices_tabela(empresa, "carater-produto", "Caráter de produto", [
                ("PADRAO", "Padrão"),
                ("CONTROLADO", "Controlado"),
                ("EMERGENCIAL", "Emergencial"),
                ("ALTO_CUSTO", "Alto custo"),
                ("CONSIGNADO", "Consignado"),
            ])
            self.fields["ds_classe"].choices = self._choices_tabela(empresa, "classes-produto", "Classes de produto", [
                ("MEDICAMENTO", "Medicamento"),
                ("MATERIAL_MEDICO", "Material médico"),
                ("MATERIAL_EXPEDIENTE", "Material de expediente"),
                ("SANEANTE", "Saneante"),
                ("DIETA", "Dieta"),
                ("OPME", "OPME"),
            ])

    @staticmethod
    def _choices_tabela(empresa, chave, nome, defaults):
        tabela, _ = TabelaEstoque.objects.get_or_create(cd_empresa=empresa, ds_chave=chave, defaults={"ds_nome": nome})
        for codigo, valor in defaults:
            ValorTabelaEstoque.objects.get_or_create(
                cd_empresa=empresa,
                cd_tabela=tabela,
                cd_valor=codigo,
                defaults={"ds_valor": valor},
            )
        valores = ValorTabelaEstoque.objects.filter(cd_empresa=empresa, cd_tabela=tabela, sn_ativo=True).order_by("ds_valor")
        return [("", "")] + [(valor.ds_valor, valor.ds_valor) for valor in valores]


class ProdutoEstoqueForm(EmpresaScopedModelForm):
    class Meta:
        model = ProdutoEstoque
        fields = ("cd_produto", "cd_estoque", "qt_saldo", "qt_reservado", "qt_minima", "sn_ativo")


class CotaConsumoForm(EmpresaScopedModelForm):
    class Meta:
        model = CotaConsumo
        fields = ("cd_estoque", "cd_produto", "qt_cota", "nr_dias", "dt_inicio_vigencia", "dt_fim_vigencia", "sn_ativo")
        widgets = {"dt_inicio_vigencia": forms.DateInput(attrs={"type": "date"}), "dt_fim_vigencia": forms.DateInput(attrs={"type": "date"})}


class MovimentoEstoqueForm(EmpresaScopedModelForm):
    class Meta:
        model = MovimentoEstoque
        fields = ("tp_movimento", "tp_destino", "cd_estoque_origem", "cd_estoque_destino", "cd_setor", "cd_atendimento", "ds_motivo", "ds_observacao", "ds_status")
        widgets = {
            "ds_observacao": forms.Textarea(attrs={"rows": 1, "class": "single-line-textarea"}),
        }


class SolicitacaoProdutoForm(EmpresaScopedModelForm):
    class Meta:
        model = SolicitacaoProduto
        fields = ("tp_solicitacao", "cd_estoque", "cd_setor", "cd_atendimento", "ds_motivo", "ds_observacao", "ds_status")


ItemSolicitacaoProdutoFormSet = inlineformset_factory(
    SolicitacaoProduto,
    ItemSolicitacaoProduto,
    fields=("cd_produto", "qt_solicitada"),
    extra=1,
    can_delete=True,
)

ItemMovimentoEstoqueFormSet = inlineformset_factory(
    MovimentoEstoque,
    ItemMovimentoEstoque,
    fields=("cd_produto", "qt_movimento", "ds_lote", "dt_validade"),
    widgets={"dt_validade": forms.DateInput(attrs={"type": "date"})},
    extra=1,
    can_delete=True,
)
