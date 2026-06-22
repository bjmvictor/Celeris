from django import forms

from apps.accounts.models import Empresa

from .models import ScreenDefinition, ScreenField


class ScreenDefinitionForm(forms.ModelForm):
    class Meta:
        model = ScreenDefinition
        fields = (
            "module",
            "title",
            "slug",
            "screen_type",
            "parent_label",
            "table_name",
            "description",
            "allow_query",
            "allow_insert",
            "allow_update",
            "allow_delete",
            "active",
            "order",
        )


class ScreenFieldForm(forms.ModelForm):
    class Meta:
        model = ScreenField
        fields = (
            "screen",
            "label",
            "table_name",
            "field_name",
            "field_type",
            "required",
            "consultable",
            "editable",
            "primary_key",
            "visible",
            "lookup_table",
            "lookup_value_field",
            "lookup_display_field",
            "choices",
            "order",
        )


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = (
            "cd_empresa",
            "nm_empresa",
            "nr_cnpj",
            "nr_cnes",
            "ds_razao_social",
            "ds_nome_fantasia",
            "ds_email",
            "nr_telefone",
            "ds_endereco",
            "nr_endereco",
            "ds_bairro",
            "ds_cidade",
            "sg_estado",
            "nr_cep",
            "sn_ativo",
        )
        widgets = {
            "sn_ativo": forms.Select(choices=((True, "Ativo"), (False, "Inativo"))),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nr_cnes"].widget.attrs.update({"inputmode": "numeric", "maxlength": "7", "data-validate-cnes": "true"})
        self.fields["ds_email"].widget.attrs["data-validate-email"] = "true"
