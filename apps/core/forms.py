from django import forms

from apps.accounts.models import Empresa

from .models import Module, ScreenDefinition, ScreenField


MODULE_ICON_CHOICES = (
    ("grid", "Grade"),
    ("activity", "Atendimento"),
    ("users", "Usuários"),
    ("user", "Profissional"),
    ("stethoscope", "Clínico"),
    ("clipboard-plus", "Prontuário"),
    ("calendar", "Agenda"),
    ("boxes", "Caixas"),
    ("package", "Produto"),
    ("shopping-cart", "Compras"),
    ("coins", "Financeiro"),
    ("headset", "Suporte"),
    ("wrench", "Ferramentas"),
    ("monitor", "Tecnologia"),
    ("globe", "Global"),
    ("table", "Tabelas"),
    ("form", "Formulários"),
    ("ticket", "Senhas"),
    ("presentation", "Painéis"),
    ("briefcase", "Maleta"),
    ("car", "Carro"),
    ("ambulance", "Ambulância"),
)


class ModuleForm(forms.ModelForm):
    icon = forms.ChoiceField(
        label="Ícone",
        choices=(("", "Sem ícone"),) + MODULE_ICON_CHOICES,
        required=False,
    )
    active = forms.TypedChoiceField(
        label="Situação",
        choices=((True, "Ativo"), (False, "Inativo")),
        coerce=lambda value: str(value).lower() == "true",
    )

    class Meta:
        model = Module
        fields = ("code", "title", "icon", "order", "active")
        labels = {
            "code": "Chave técnica",
            "title": "Nome do módulo",
            "icon": "Ícone",
            "order": "Ordem",
        }
        widgets = {
            "order": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, query_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["active"].required = not query_mode
        if query_mode:
            self.fields["active"].choices = (("", "Todos"),) + tuple(self.fields["active"].choices)
            self.fields["icon"].choices = (("", "Todos"),) + MODULE_ICON_CHOICES
        elif not self.is_bound and not self.instance.pk:
            self.initial["active"] = True
            self.initial["icon"] = "grid"

        current_icon = self.instance.icon if self.instance.pk else self.initial.get("icon")
        known_icons = {value for value, _label in self.fields["icon"].choices}
        if current_icon and current_icon not in known_icons:
            self.fields["icon"].choices = tuple(self.fields["icon"].choices) + ((current_icon, current_icon),)

        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-consultable": "true",
                    "data-table": "modulo",
                    "data-field": name,
                }
            )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper().replace(" ", "_")


class ScreenDefinitionForm(forms.ModelForm):
    class Meta:
        model = ScreenDefinition
        fields = (
            "module",
            "parent",
            "title",
            "slug",
            "navigation_url",
            "access_key",
            "icon",
            "roles",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = ScreenDefinition.objects.filter(
            screen_type=ScreenDefinition.TYPE_GROUP,
            active=True,
        ).select_related("module").order_by("module__order", "module__title", "order", "title")

    def clean(self):
        cleaned = super().clean()
        module = cleaned.get("module")
        parent = cleaned.get("parent")
        if parent and module and parent.module_id != module.pk:
            self.add_error("parent", "O item pai deve pertencer ao mesmo módulo.")
        if self.instance.pk and parent and parent.pk == self.instance.pk:
            self.add_error("parent", "Um item não pode ser pai dele mesmo.")
        return cleaned


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
