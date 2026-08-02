from django import forms

from .models import FaixaResultadoPesquisa, OpcaoRespostaPesquisa, PerguntaPesquisa, Pesquisa


class PesquisaForm(forms.ModelForm):
    class Meta:
        model = Pesquisa
        fields = (
            "nm_pesquisa", "tp_pesquisa", "ds_descricao", "sn_anonima", "sn_publica",
            "sn_ativo", "dh_inicio", "dh_fim",
        )
        widgets = {
            "ds_descricao": forms.Textarea(attrs={"rows": 3}),
            "dh_inicio": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
            "dh_fim": forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["dh_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["dh_fim"].input_formats = ["%Y-%m-%dT%H:%M"]
        for name, field in self.fields.items():
            field.widget.attrs.update({"data-field-table": "pesquisa", "data-field-name": name})


class PerguntaPesquisaForm(forms.ModelForm):
    class Meta:
        model = PerguntaPesquisa
        fields = (
            "ds_pergunta", "tp_resposta", "nr_peso", "nr_minimo", "nr_maximo",
            "nr_ordem", "sn_obrigatoria", "sn_ativo",
        )
        widgets = {"ds_pergunta": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"data-field-table": "pesquisa_pergunta", "data-field-name": name})


class OpcaoRespostaPesquisaForm(forms.ModelForm):
    class Meta:
        model = OpcaoRespostaPesquisa
        fields = ("ds_resposta", "nr_valor", "nr_ordem", "sn_ativo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"data-field-table": "pesquisa_opcao_resposta", "data-field-name": name})


class FaixaResultadoPesquisaForm(forms.ModelForm):
    class Meta:
        model = FaixaResultadoPesquisa
        fields = ("nm_resultado", "nr_minimo", "nr_maximo", "ds_mensagem", "ds_cor", "nr_ordem", "sn_ativo")
        widgets = {
            "ds_mensagem": forms.Textarea(attrs={"rows": 3}),
            "ds_cor": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({"data-field-table": "pesquisa_faixa_resultado", "data-field-name": name})
