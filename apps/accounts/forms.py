from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.db.models import Q

from apps.atendimento.models import Prestador
from apps.core.models import Module, ScreenDefinition, ValorAuxiliarGlobal

from .models import Empresa, Papel, PapelModulo, PapelTela, User, UsuarioEmpresa, normalize_identifier


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


class UsuarioForm(UserCreationForm):
    empresas = forms.ModelMultipleChoiceField(
        label="Empresas",
        queryset=Empresa.objects.filter(sn_ativo=True).order_by("nm_empresa"),
        required=True,
    )
    grupos = forms.ModelMultipleChoiceField(
        label="Papéis",
        queryset=Group.objects.filter(papel__sn_ativo=True).order_by("name"),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "username", "full_name", "is_active", "cd_prestador", "dt_nascimento", "nr_cpf",
            "ds_idioma", "ds_profissao", "nr_matricula_rh", "email", "nr_celular",
            "must_change_password", "is_blocked", "invalid_login_attempts", "password_expires_at",
            "can_register_patient", "can_change_patient", "can_create_users", "can_deactivate_users",
            "can_manage_auxiliary_tables", "can_configure_system", "empresas", "grupos",
        )
        widgets = {
            "dt_nascimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "password_expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, instance=None, empresa=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.fields["username"].required = False
        labels = {
            "username": "Login",
            "full_name": "Nome Completo",
            "is_active": "Status",
            "cd_prestador": "Prestador",
            "dt_nascimento": "Data de Nascimento",
            "nr_cpf": "CPF",
            "ds_idioma": "Idioma",
            "ds_profissao": "Profissão",
            "nr_matricula_rh": "Matrícula RH",
            "email": "E-mail",
            "nr_celular": "Celular",
            "must_change_password": "Alterar senha no próximo login",
            "is_blocked": "Usuário Bloqueado",
            "invalid_login_attempts": "Tentativas Inválidas",
            "password_expires_at": "Senha Expira em",
            "can_register_patient": "Cadastra Paciente",
            "can_change_patient": "Altera Paciente",
            "can_create_users": "Cria Usuários",
            "can_deactivate_users": "Desativa Usuários",
            "can_manage_auxiliary_tables": "Gerencia Tabelas Auxiliares",
            "can_configure_system": "Configura Sistema",
        }
        for field_name, label in labels.items():
            self.fields[field_name].label = label
        self.fields["username"].disabled = True
        self.fields["full_name"].required = False
        self.fields["nr_cpf"].required = False
        self.fields["is_active"].initial = True
        self.fields["is_active"].disabled = True
        self.fields["is_blocked"].disabled = True
        self.fields["invalid_login_attempts"].disabled = True
        self.fields["password_expires_at"].disabled = True
        self.fields["cd_prestador"].queryset = (
            Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_prestador")
            if empresa
            else Prestador.objects.none()
        )
        self.fields["ds_idioma"].widget = forms.Select(choices=self._choices_for("idioma"))
        self.fields["ds_profissao"].widget = forms.Select(choices=self._choices_for("profissao"))
        self.fields["full_name"].widget.attrs.update({"data-user-full-name": "true", "required": "required"})
        self.fields["username"].widget.attrs["data-user-login"] = "true"
        self.fields["cd_prestador"].widget.attrs["data-user-provider"] = "true"
        self.fields["grupos"].widget.attrs["data-assignment-values"] = "true"
        self.fields["empresas"].widget.attrs["data-assignment-values"] = "true"
        self.fields["empresas"].label_from_instance = lambda company: company.nm_empresa
        self.fields["nr_cpf"].widget.attrs.update(
            {"data-mask": "cpf", "data-validate-cpf": "true", "required": "required"}
        )
        self.fields["nr_celular"].widget.attrs.update({"data-mask": "celular"})
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("data-consultable", "true")
            if field_name in {"username", "is_active", "is_blocked", "invalid_login_attempts", "password_expires_at"}:
                field.widget.attrs["data-editable"] = "false"
        if instance and instance.pk:
            self.fields.pop("password1")
            self.fields.pop("password2")
            self.fields["empresas"].initial = instance.empresas.all()
            self.fields["grupos"].initial = instance.groups.all()

    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get("cd_prestador")
        if provider:
            defaults = {
                "full_name": provider.nm_prestador,
                "nr_cpf": provider.nr_cpf,
                "dt_nascimento": provider.dt_nascimento,
                "email": provider.ds_email,
                "nr_celular": provider.nr_celular,
                "ds_profissao": provider.tp_prestador,
            }
            for field_name, value in defaults.items():
                if not cleaned_data.get(field_name) and value:
                    cleaned_data[field_name] = value
        if not cleaned_data.get("full_name"):
            self.add_error("full_name", "Informe o nome completo.")
        cpf = cleaned_data.get("nr_cpf")
        if not cpf:
            self.add_error("nr_cpf", "Informe o CPF.")
        else:
            digits = "".join(character for character in cpf if character.isdigit())
            formatted = (
                f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
                if len(digits) == 11
                else cpf
            )
            duplicate = User.objects.filter(Q(nr_cpf=cpf) | Q(nr_cpf=digits) | Q(nr_cpf=formatted))
            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error("nr_cpf", "CPF já cadastrado para outro usuário.")
        return cleaned_data

    def clean_username(self):
        if self.instance and self.instance.pk:
            return self.instance.username
        return super().clean_username()

    def save(self, commit=True):
        user = forms.ModelForm.save(self, commit=False) if self.instance.pk else super().save(commit=False)
        if not user.pk:
            user.is_active = True
        if commit:
            user.save()
            user.groups.set(self.cleaned_data.get("grupos", []))
            selected = list(self.cleaned_data.get("empresas", []))
            UsuarioEmpresa.objects.filter(usuario=user).exclude(empresa__in=selected).update(sn_ativo=False)
            for index, empresa in enumerate(selected):
                UsuarioEmpresa.objects.update_or_create(
                    usuario=user,
                    empresa=empresa,
                    defaults={"sn_ativo": True, "sn_padrao": index == 0},
                )
        return user

    def _choices_for(self, table_name):
        values = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela=table_name,
            sn_ativo=True,
        ).order_by("ds_valor")
        return [("", "")] + [(value.cd_valor, value.ds_valor) for value in values]


class UsuarioPasswordForm(SetPasswordForm):
    username = forms.CharField(label="Login", disabled=True, required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["username"].initial = user.username
        self.order_fields(["username", "new_password1", "new_password2"])

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1", "")
        if len(password) < 8:
            raise forms.ValidationError("A senha deve possuir no mínimo 8 caracteres.")
        return password


class PerfilForm(forms.ModelForm):
    ds_descricao = forms.CharField(label="Descrição", required=False)
    modulos = forms.ModelMultipleChoiceField(
        label="Módulos Permitidos",
        queryset=Module.objects.filter(active=True).order_by("title"),
        required=False,
    )
    telas = forms.ModelMultipleChoiceField(
        label="Telas Permitidas",
        queryset=ScreenDefinition.objects.filter(active=True, module__active=True).order_by(
            "module__title", "order", "title"
        ),
        required=False,
    )

    class Meta:
        model = Group
        fields = ("name",)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.fields["name"].label = "Nome do Papel"
        self.fields["name"].widget.attrs.update({"data-consultable": "true", "required": "required"})
        if instance and instance.pk:
            papel, _ = Papel.objects.get_or_create(grupo=instance)
            self.fields["ds_descricao"].initial = papel.ds_descricao
            self.fields["modulos"].initial = papel.modulos.values_list("modulo_id", flat=True)
            self.fields["telas"].initial = papel.telas.values_list("tela_id", flat=True)

    def clean(self):
        cleaned_data = super().clean()
        modules = set(cleaned_data.get("modulos", []))
        screens = cleaned_data.get("telas", [])
        invalid_screens = [screen for screen in screens if screen.module not in modules]
        if invalid_screens:
            self.add_error("telas", "Remova as telas pertencentes a módulos não selecionados.")
        return cleaned_data

    def save(self, commit=True):
        group = super().save(commit=commit)
        if not commit:
            return group
        papel, _ = Papel.objects.get_or_create(grupo=group)
        papel.ds_descricao = self.cleaned_data.get("ds_descricao", "")
        papel.save(update_fields=["ds_descricao"])
        selected_modules = list(self.cleaned_data.get("modulos", []))
        selected_screens = [
            screen for screen in self.cleaned_data.get("telas", []) if screen.module in selected_modules
        ]
        PapelModulo.objects.filter(papel=papel).exclude(modulo__in=selected_modules).delete()
        for module in selected_modules:
            PapelModulo.objects.get_or_create(papel=papel, modulo=module)
        PapelTela.objects.filter(papel=papel).exclude(tela__in=selected_screens).delete()
        for screen in selected_screens:
            PapelTela.objects.get_or_create(papel=papel, tela=screen)
        return group
