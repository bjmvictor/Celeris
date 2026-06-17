from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.core.models import ValorAuxiliarGlobal

from .models import Agendamento, Convenio, Paciente


class PacienteSearchForm(forms.Form):
    cd_paciente = forms.IntegerField(label="Prontuário", required=False)
    termo = forms.CharField(label="Nome", required=False)
    nr_cpf = forms.CharField(label="CPF", required=False)
    nm_mae = forms.CharField(label="Nome da mãe", required=False)
    nr_cartao_sus = forms.CharField(label="Cartão SUS", required=False)
    dt_nascimento = forms.DateField(label="Data de nascimento", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "paciente",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "true",
                }
            )


class PacienteForm(forms.ModelForm):
    cd_paciente = forms.IntegerField(label="Código", required=False, disabled=True)
    motivo_alteracao = forms.ModelChoiceField(
        label="Motivo da alteração",
        queryset=ValorAuxiliarGlobal.objects.none(),
        required=False,
        empty_label="",
    )
    observacao_alteracao = forms.CharField(
        label="Observação da alteração",
        required=False,
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        selected_state = self.data.get(self.add_prefix("sg_estado")) or getattr(self.instance, "sg_estado", "")
        self.fields["nr_cpf"].required = True
        self.fields["dt_nascimento"].required = True
        if self.empresa:
            self.fields["cd_convenio"].queryset = Convenio.objects.filter(cd_empresa=self.empresa, sn_ativo=True)
        else:
            self.fields["cd_convenio"].queryset = Convenio.objects.none()
        self.fields["tp_sanguineo"].choices = self._choices_for("tipo_sanguineo")
        self.fields["tp_sexo"].choices = self._choices_for("sexo")
        self.fields["tp_genero"].choices = self._choices_for("genero")
        self.fields["ds_cor_raca"].choices = self._choices_for("cor_raca")
        self.fields["tp_estado_civil"].choices = self._choices_for("estado_civil")
        self.fields["ds_nacionalidade"].choices = self._choices_for("pais")
        self.fields["ds_naturalidade"].choices = self._choices_for("estado")
        self.fields["ds_cidade"].choices = self._choices_for("cidade", group=selected_state)
        self.fields["sg_estado"].choices = self._choices_for("estado")
        for name in ("tp_sanguineo", "tp_sexo", "tp_genero", "ds_cor_raca", "tp_estado_civil", "ds_nacionalidade", "ds_naturalidade", "ds_cidade", "sg_estado"):
            self.fields[name].widget = forms.Select(choices=self.fields[name].choices)
        self.fields["motivo_alteracao"].queryset = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela="motivo_alteracao",
            sn_ativo=True,
        ).order_by("ds_valor")
        if not self.instance or not self.instance.pk:
            self.fields.pop("motivo_alteracao")
            self.fields.pop("observacao_alteracao")
        if self.instance and self.instance.pk:
            self.fields["cd_paciente"].initial = self.instance.cd_paciente
        for name, field in self.fields.items():
            if name == "observacao_alteracao":
                table_name = "historico_alteracao_paciente"
                field_name = "ds_observacao"
            else:
                table_name = "paciente"
                field_name = name
            field.widget.attrs.update(
                {
                    "data-field-table": table_name,
                    "data-field-name": field_name,
                    "data-primary-key": "true" if name == "cd_paciente" else "false",
                    "data-consultable": "true",
                    "data-editable": "false" if name == "cd_paciente" else "true",
                }
            )
        self.fields["sg_estado"].widget.attrs["data-state-select"] = "true"
        self.fields["ds_cidade"].widget.attrs["data-city-select"] = "true"
        self.fields["nr_cpf"].widget.attrs.update({"maxlength": "14", "inputmode": "numeric", "data-mask": "cpf"})
        self.fields["nr_celular"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["dt_nascimento"].widget.attrs.update({"min": "1900-01-01", "max": timezone.localdate().isoformat()})
        for unique_field in ("nr_cpf", "nr_cartao_sus", "nr_rg"):
            if unique_field in self.fields:
                self.fields[unique_field].widget.attrs["data-unique-patient"] = unique_field

    class Meta:
        model = Paciente
        exclude = ("cd_empresa", "dh_criacao", "dh_atualizacao", "nm_convenio")
        widgets = {
            "dt_nascimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "ds_observacao": forms.TextInput(),
            "sn_ativo": forms.Select(choices=((True, "Ativo"), (False, "Inativo"))),
        }

    def clean(self):
        cleaned_data = super().clean()
        cpf = self._digits(cleaned_data.get("nr_cpf"))
        celular = self._digits(cleaned_data.get("nr_celular"))
        if cpf:
            cleaned_data["nr_cpf"] = self._format_cpf(cpf)
        if celular:
            cleaned_data["nr_celular"] = self._format_cellphone(celular)
        if not self.empresa:
            return cleaned_data
        current_pk = self.instance.pk if self.instance else None
        checks = {
            "nr_cpf": "CPF",
            "nr_cartao_sus": "Cartão SUS",
            "nr_rg": "RG",
        }
        for field_name, label in checks.items():
            value = cleaned_data.get(field_name)
            if not value:
                continue
            duplicate_filter = {field_name: value}
            if field_name == "nr_cpf":
                duplicate = Paciente.objects.filter(cd_empresa=self.empresa).filter(
                    Q(nr_cpf=value) | Q(nr_cpf=self._digits(value))
                )
            else:
                duplicate = Paciente.objects.filter(cd_empresa=self.empresa, **duplicate_filter)
            if current_pk:
                duplicate = duplicate.exclude(pk=current_pk)
            if duplicate.exists():
                self.add_error(field_name, f"{label} já cadastrado para outro paciente.")
        convenio = cleaned_data.get("cd_convenio")
        if convenio:
            cleaned_data["nm_convenio"] = convenio.nm_convenio
        return cleaned_data

    def _digits(self, value):
        return "".join(character for character in str(value or "") if character.isdigit())

    def _format_cpf(self, digits):
        digits = digits[:11]
        if len(digits) != 11:
            return digits
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    def _format_cellphone(self, digits):
        digits = digits[:11]
        if len(digits) != 11:
            return digits
        return f"({digits[:2]}) {digits[2]} {digits[3:7]}-{digits[7:]}"

    def _choices_for(self, table_name, group=None):
        values = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela=table_name,
            sn_ativo=True,
        ).order_by("ds_valor")
        if group:
            values = values.filter(ds_grupo=group)
        return [("", "")] + [(value.cd_valor, value.ds_valor) for value in values]


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ("dh_agendamento", "ds_tipo_atendimento", "ds_especialidade", "ds_profissional", "ds_observacao", "sn_confirmado")
        widgets = {
            "dh_agendamento": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ds_observacao": forms.Textarea(attrs={"rows": 3}),
        }
