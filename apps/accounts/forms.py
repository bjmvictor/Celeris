from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Empresa, UsuarioEmpresa, normalize_identifier


class EmpresaAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": (
            "Usuário ou senha inválidos. A senha diferencia letras maiúsculas e minúsculas."
        ),
    }

    empresa = forms.ModelChoiceField(
        label="Empresa",
        queryset=Empresa.objects.none(),
        empty_label="",
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].widget.attrs.update({"autocomplete": "username", "data-company-user": "true"})
        self.fields["empresa"].queryset = Empresa.objects.none()
        empresa_value = self.data.get(self.add_prefix("empresa")) if self.is_bound else None
        if empresa_value:
            self.fields["empresa"].queryset = Empresa.objects.filter(sn_ativo=True).order_by("cd_empresa")

    def clean_username(self):
        return normalize_identifier(self.cleaned_data["username"])

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        empresa = self.cleaned_data.get("empresa")
        if empresa and not UsuarioEmpresa.objects.filter(usuario=user, empresa=empresa, sn_ativo=True).exists():
            raise forms.ValidationError("Usuário não vinculado à empresa selecionada.", code="invalid_company")
