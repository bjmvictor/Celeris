from django import forms
from django.contrib.auth.models import Group

from apps.accounts.models import Empresa

from .models import IconeSistema, Module, ScreenDefinition, ScreenField


class SystemIconSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option["attrs"]["data-icon-key"] = str(value)
        return option


def _system_icon_choices(current_icon="", query_mode=False):
    icons = list(
        IconeSistema.objects.filter(sn_ativo=True)
        .order_by("nm_icone")
        .values_list("cd_icone", "nm_icone")
    )
    known_icons = {value for value, _label in icons}
    if current_icon and current_icon not in known_icons:
        stored_name = IconeSistema.objects.filter(cd_icone=current_icon).values_list("nm_icone", flat=True).first()
        icons.append((current_icon, stored_name or current_icon))
    empty_label = "Todos" if query_mode else "Sem ícone"
    return (("", empty_label), *icons)


class ModuleForm(forms.ModelForm):
    icon = forms.ChoiceField(
        label="Ícone",
        choices=(),
        required=False,
        widget=SystemIconSelect(attrs={"data-system-icon-select": "true"}),
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
        self.is_protected = bool(self.instance.pk and self.instance.is_system)
        self.fields["active"].required = not query_mode
        if query_mode:
            self.fields["active"].choices = (("", "Todos"),) + tuple(self.fields["active"].choices)
        elif not self.is_bound and not self.instance.pk:
            self.initial["active"] = True
            self.initial["icon"] = "grid"

        current_icon = self.instance.icon if self.instance.pk else self.initial.get("icon")
        self.fields["icon"].choices = _system_icon_choices(current_icon, query_mode=query_mode)
        self.fields["title"].widget.attrs["data-preserve-characters"] = "true"

        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-consultable": "true",
                    "data-table": "modulo",
                    "data-field": name,
                }
            )
            if self.is_protected and not query_mode:
                field.disabled = True

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper().replace(" ", "_")


class ScreenDefinitionForm(forms.ModelForm):
    icon = forms.ChoiceField(
        label="Ícone",
        choices=(),
        required=False,
        widget=SystemIconSelect(attrs={"data-system-icon-select": "true"}),
    )
    roles = forms.MultipleChoiceField(
        label="Roles",
        choices=(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

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
        labels = {
            "module": "Módulo",
            "parent": "Item pai",
            "title": "Nome",
            "slug": "Identificador da tela",
            "navigation_url": "URL de navegação",
            "access_key": "Chave de acesso",
            "screen_type": "Tipo",
            "parent_label": "Grupo legado",
            "table_name": "Tabela",
            "description": "Descrição",
            "allow_query": "Permite consultar",
            "allow_insert": "Permite inserir",
            "allow_update": "Permite alterar",
            "allow_delete": "Permite excluir",
            "active": "Ativo",
            "order": "Ordem",
        }

    def __init__(self, *args, protected=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_protected = protected
        self.fields["parent"].queryset = ScreenDefinition.objects.filter(
            screen_type=ScreenDefinition.TYPE_GROUP,
            active=True,
        ).select_related("module").order_by("module__order", "module__title", "order", "title")
        current_icon = self.instance.icon if self.instance.pk else self.initial.get("icon", "")
        self.fields["icon"].choices = _system_icon_choices(current_icon)
        role_names = list(Group.objects.order_by("name").values_list("name", flat=True))
        current_roles = list(self.instance.roles or []) if self.instance.pk else list(self.initial.get("roles", []))
        for role_name in current_roles:
            if role_name and role_name not in role_names:
                role_names.append(role_name)
        self.fields["roles"].choices = tuple((name, name) for name in role_names)
        if not self.is_bound:
            self.initial["roles"] = current_roles
        if self.is_protected:
            for field in self.fields.values():
                field.disabled = True

    def clean(self):
        cleaned = super().clean()
        module = cleaned.get("module")
        parent = cleaned.get("parent")
        if module and module.is_system and (
            not self.instance.pk or self.instance.module_id != module.pk
        ):
            self.add_error("module", "Módulos estruturais não aceitam itens criados pela interface.")
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

    def clean_screen(self):
        screen = self.cleaned_data["screen"]
        if screen.module.is_system and (
            not self.instance.pk or self.instance.screen_id != screen.pk
        ):
            raise forms.ValidationError(
                "Módulos estruturais não aceitam campos criados pela interface."
            )
        return screen


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
