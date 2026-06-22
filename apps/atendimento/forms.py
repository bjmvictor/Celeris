import json

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Cep, TipoPrestadorConselho, ValorAuxiliarGlobal

from .models import Agendamento, Atendimento, Convenio, EvolucaoAtendimento, Paciente, PreAtendimento, Prescricao, Prestador, ResultadoExame, SolicitacaoExame


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
        self.fields["nm_paciente"].required = True
        self.fields["dt_nascimento"].required = True
        self.fields["sn_ativo"].disabled = True
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
        self.fields["ds_profissao"].choices = self._choices_for("profissao")
        self.fields["ds_orgao_emissor"].choices = self._choices_for("orgao_emissor")
        self.fields["tp_logradouro"].choices = self._choices_for("tipo_logradouro")
        self.fields["ds_cidade"].choices = self._choices_for("cidade", group=selected_state)
        self.fields["sg_estado"].choices = self._choices_for("estado")
        for name in ("tp_sanguineo", "tp_sexo", "tp_genero", "ds_cor_raca", "tp_estado_civil", "ds_nacionalidade", "ds_naturalidade", "ds_profissao", "ds_orgao_emissor", "tp_logradouro", "ds_cidade", "sg_estado"):
            self.fields[name].widget = forms.Select(choices=self.fields[name].choices)
        self.fields["cd_cep"].queryset = Cep.objects.filter(sn_ativo=True).order_by("nr_cep")
        self.fields["cd_cep"].label_from_instance = lambda cep: f"{cep.nr_cep} - {cep.ds_logradouro or cep.ds_cidade}"
        self.fields["motivo_alteracao"].queryset = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela="motivo_alteracao",
            sn_ativo=True,
        ).order_by("ds_valor")
        self.fields["motivo_alteracao"].label_from_instance = lambda value: value.ds_valor
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
        self.fields["sg_estado"].widget.attrs["data-linked-state"] = "paciente"
        self.fields["ds_cidade"].widget.attrs["data-city-select"] = "true"
        self.fields["ds_cidade"].widget.attrs["data-linked-city"] = "paciente"
        self.fields["cd_cep"].widget.attrs["data-linked-cep"] = "paciente"
        self.fields["nr_cpf"].widget.attrs.update({"maxlength": "14", "inputmode": "numeric", "data-mask": "cpf"})
        self.fields["nr_cpf"].widget.attrs["data-validate-cpf"] = "true"
        self.fields["ds_email"].widget.attrs["data-validate-email"] = "true"
        self.fields["nr_celular"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["nr_celular_2"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["dt_nascimento"].widget.attrs.update({"min": "1900-01-01", "max": timezone.localdate().isoformat()})
        for unique_field in ("nr_cpf", "nr_cartao_sus", "nr_rg"):
            if unique_field in self.fields:
                self.fields[unique_field].widget.attrs["data-unique-patient"] = unique_field

    class Meta:
        model = Paciente
        exclude = (
            "cd_empresa",
            "dh_criacao",
            "dh_atualizacao",
            "cd_usuario_criacao",
            "cd_usuario_atualizacao",
            "nm_convenio",
            "nr_cep",
        )
        widgets = {
            "dt_nascimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "dt_expedicao": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "ds_observacao": forms.TextInput(),
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
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
        if cleaned_data.get("dt_expedicao") and cleaned_data["dt_expedicao"] > timezone.localdate():
            self.add_error("dt_expedicao", "A data de expedição não pode ser futura.")
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


class PrestadorSearchForm(forms.Form):
    cd_prestador = forms.IntegerField(label="Código", required=False)
    nm_prestador = forms.CharField(label="Nome", required=False)
    nr_cpf = forms.CharField(label="CPF", required=False)
    nr_conselho = forms.CharField(label="Registro profissional", required=False)
    ds_especialidade = forms.CharField(label="Especialidade", required=False)
    sn_ativo = forms.ChoiceField(
        label="Status",
        required=False,
        choices=(("", "Ativos"), ("True", "Ativo"), ("False", "Inativo"), ("todos", "Todos")),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "prestador",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "true",
                }
            )


class PrestadorForm(forms.ModelForm):
    ds_especialidades = forms.MultipleChoiceField(label="Especialidades", required=False)
    ds_especialidade_principal = forms.ChoiceField(label="Especialidade principal", required=False)
    cd_prestador = forms.IntegerField(label="Código", required=False, disabled=True)

    class Meta:
        model = Prestador
        exclude = (
            "cd_empresa",
            "dh_criacao",
            "dh_atualizacao",
            "cd_usuario_criacao",
            "cd_usuario_atualizacao",
            "nr_cep",
            "nr_cep_comercial",
        )
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
            "ds_observacao": forms.TextInput(),
            "dt_expedicao": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "dt_nascimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nm_prestador"].required = True
        self.fields["nm_guerra"].required = True
        self.fields["dt_nascimento"].required = True
        self.fields["nr_cpf"].required = True
        self.fields["tp_prestador"].required = True
        self.fields["sn_ativo"].initial = True
        self.fields["sn_ativo"].disabled = True
        self.fields["tp_sexo"].widget = forms.Select(choices=self._choices_for("sexo"))
        self.fields["ds_cor_raca"].widget = forms.Select(choices=self._choices_for("cor_raca"))
        self.fields["tp_prestador"].widget = forms.Select(choices=self._choices_for("tipo_prestador"))
        self.fields["ds_orgao_emissor"].widget = forms.Select(choices=self._choices_for("orgao_emissor"))
        self.fields["ds_grau_instrucao"].widget = forms.Select(choices=self._choices_for("grau_instrucao"))
        self.fields["tp_genero"].widget = forms.Select(choices=self._choices_for("identidade_genero"))
        self.fields["ds_nacionalidade"].widget = forms.Select(choices=self._choices_for("pais"))
        self.fields["ds_naturalidade"].widget = forms.Select(choices=self._choices_for("estado"))
        self.fields["tp_logradouro"].widget = forms.Select(choices=self._choices_for("tipo_logradouro"))
        self.fields["tp_logradouro_comercial"].widget = forms.Select(choices=self._choices_for("tipo_logradouro"))
        self.fields["tp_vinculo"].widget = forms.Select(choices=self._choices_for("tipo_vinculo"))
        self.fields["ds_especialidade"].widget = forms.HiddenInput()
        specialty_choices = self._choices_for("especialidade")[1:]
        self.fields["ds_especialidades"].choices = specialty_choices
        self.fields["ds_especialidades"].widget.attrs["data-specialty-values"] = "true"
        self.fields["ds_especialidades"].initial = (
            self.instance.ds_especialidades
            if self.instance and self.instance.pk and self.instance.ds_especialidades
            else ([self.instance.ds_especialidade] if self.instance and self.instance.ds_especialidade else [])
        )
        self.fields["ds_especialidade_principal"].choices = [("", "")] + specialty_choices
        self.fields["ds_especialidade_principal"].initial = self.instance.ds_especialidade if self.instance else ""
        self.fields["ds_especialidade_principal"].widget.attrs["data-primary-specialty"] = "true"
        mappings = TipoPrestadorConselho.objects.filter(sn_ativo=True).order_by("tp_prestador")
        self.fields["ds_conselho"].widget = forms.TextInput(attrs={"readonly": "readonly"})
        self.fields["tp_prestador"].widget.attrs["data-provider-type"] = "true"
        self.fields["tp_prestador"].widget.attrs["data-council-map"] = json.dumps(
            {mapping.tp_prestador: mapping.ds_conselho for mapping in mappings}
        )
        self.fields["tp_prestador"].widget.attrs["data-council-config-url"] = "/global/tabelas/tipo-prestador-conselho/"
        self.fields["ds_conselho"].widget.attrs["data-provider-council"] = "true"
        self.fields["sg_conselho"].widget = forms.Select(choices=self._choices_for("estado"))
        self.fields["cd_banco"].widget = forms.Select(choices=self._choices_for("banco"))
        self.fields["tp_conta"].widget = forms.Select(
            choices=(("", ""), ("CORRENTE", "Corrente"), ("POUPANCA", "Poupança"), ("SALARIO", "Salário"), ("PIX", "PIX"))
        )
        self.fields["ds_contato_principal"].widget = forms.Select(
            choices=(("", ""), ("CELULAR", "Celular"), ("CELULAR_2", "Celular 2"), ("EMAIL", "E-mail"), ("TELEFONE", "Telefone"))
        )
        self.fields["cd_cep"].queryset = Cep.objects.filter(sn_ativo=True).order_by("nr_cep")
        self.fields["cd_cep"].label_from_instance = lambda cep: f"{cep.nr_cep} - {cep.ds_logradouro or cep.ds_cidade}"
        self.fields["sg_estado"].widget = forms.Select(choices=self._choices_for("estado"))
        selected_state = self.data.get(self.add_prefix("sg_estado")) or getattr(self.instance, "sg_estado", "")
        self.fields["ds_cidade"].widget = forms.Select(choices=self._choices_for("cidade", selected_state))
        self.fields["cd_cep_comercial"].queryset = Cep.objects.filter(sn_ativo=True).order_by("nr_cep")
        self.fields["cd_cep_comercial"].label_from_instance = lambda cep: f"{cep.nr_cep} - {cep.ds_logradouro or cep.ds_cidade}"
        self.fields["sg_estado_comercial"].widget = forms.Select(choices=self._choices_for("estado"))
        selected_commercial_state = self.data.get(self.add_prefix("sg_estado_comercial")) or getattr(self.instance, "sg_estado_comercial", "")
        self.fields["ds_cidade_comercial"].widget = forms.Select(
            choices=self._choices_for("cidade", selected_commercial_state)
        )
        if self.instance and self.instance.pk:
            self.fields["cd_prestador"].initial = self.instance.cd_prestador
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "prestador",
                    "data-field-name": name,
                    "data-primary-key": "true" if name == "cd_prestador" else "false",
                    "data-consultable": "true",
                    "data-editable": "false" if name in {"cd_prestador", "sn_ativo"} else "true",
                }
            )
        self.fields["sg_estado"].widget.attrs["data-linked-state"] = "residencial"
        self.fields["ds_cidade"].widget.attrs["data-linked-city"] = "residencial"
        self.fields["cd_cep"].widget.attrs["data-linked-cep"] = "residencial"
        self.fields["sg_estado_comercial"].widget.attrs["data-linked-state"] = "comercial"
        self.fields["ds_cidade_comercial"].widget.attrs["data-linked-city"] = "comercial"
        self.fields["cd_cep_comercial"].widget.attrs["data-linked-cep"] = "comercial"
        self.fields["nr_cpf"].widget.attrs.update({"maxlength": "14", "inputmode": "numeric", "data-mask": "cpf"})
        if "nm_prestador" in self.fields:
            self.fields["nm_prestador"].widget.attrs["data-war-name-source"] = "true"
        if "nm_guerra" in self.fields:
            self.fields["nm_guerra"].widget.attrs["data-war-name"] = "true"
        self.fields["nr_cpf"].widget.attrs["data-validate-cpf"] = "true"
        self.fields["dt_nascimento"].widget.attrs.update({"min": "1900-01-01", "max": timezone.localdate().isoformat()})
        self.fields["nr_celular"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["nr_celular_2"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["ds_email"].widget.attrs["data-validate-email"] = "true"
        self.fields["sn_mesmo_endereco"].widget.attrs["data-same-address"] = "true"
        self.fields["tp_prestador"].widget.attrs["data-provider-permissions"] = "true"

    def _choices_for(self, table_name, group=None):
        values = ValorAuxiliarGlobal.objects.filter(
            cd_tabela_auxiliar_global__ds_tabela=table_name,
            sn_ativo=True,
        ).order_by("ds_valor")
        if group:
            values = values.filter(ds_grupo=group)
        return [("", "")] + [(value.cd_valor, value.ds_valor) for value in values]

    def _choices_with_current(self, table_name, current):
        choices = self._choices_for(table_name)
        if current and current not in {value for value, _ in choices}:
            choices.append((current, current))
        return choices

    def clean(self):
        cleaned_data = super().clean()
        specialties = cleaned_data.get("ds_especialidades") or []
        primary_specialty = cleaned_data.get("ds_especialidade_principal")
        if primary_specialty and primary_specialty not in specialties:
            self.add_error("ds_especialidade_principal", "A especialidade principal deve estar entre as especialidades adicionadas.")
        cleaned_data["ds_especialidade"] = primary_specialty or (specialties[0] if specialties else "")
        if cleaned_data.get("dt_expedicao") and cleaned_data["dt_expedicao"] > timezone.localdate():
            self.add_error("dt_expedicao", "A data de expedição não pode ser futura.")
        if cleaned_data.get("dt_nascimento") and cleaned_data["dt_nascimento"] > timezone.localdate():
            self.add_error("dt_nascimento", "A data de nascimento não pode ser futura.")
        cns = "".join(character for character in str(cleaned_data.get("nr_cartao_sus") or "") if character.isdigit())
        if cns and len(cns) != 15:
            self.add_error("nr_cartao_sus", "O Cartão Nacional de Saúde deve conter 15 dígitos.")
        if cleaned_data.get("nr_conselho") and not cleaned_data.get("sg_conselho"):
            self.add_error("sg_conselho", "Informe a UF do conselho.")
        contact_fields = {
            "CELULAR": "nr_celular",
            "CELULAR_2": "nr_celular_2",
            "EMAIL": "ds_email",
            "TELEFONE": "nr_telefone",
        }
        principal_contact = cleaned_data.get("ds_contato_principal")
        if principal_contact and not cleaned_data.get(contact_fields.get(principal_contact, "")):
            self.add_error(
                "ds_contato_principal",
                "O contato marcado como principal deve estar preenchido.",
            )
        if cleaned_data.get("sn_permite_atendimento") and not specialties:
            self.add_error("ds_especialidades", "Informe ao menos uma especialidade para prestadores que realizam atendimento.")
        cpf = cleaned_data.get("nr_cpf")
        if cpf:
            duplicate = Prestador.objects.filter(nr_cpf=cpf)
            if self.instance and self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                self.add_error("nr_cpf", "CPF já cadastrado para outro prestador.")
        provider_type = cleaned_data.get("tp_prestador")
        if not provider_type:
            return cleaned_data
        mapping = TipoPrestadorConselho.objects.filter(tp_prestador=provider_type, sn_ativo=True).first()
        if not mapping:
            cleaned_data["ds_conselho"] = ""
            return cleaned_data
        if not cleaned_data.get("nr_conselho"):
            self.add_error("nr_conselho", "Informe o número do conselho para este tipo de prestador.")
        cleaned_data["ds_conselho"] = mapping.ds_conselho
        return cleaned_data


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ("dh_agendamento", "ds_tipo_atendimento", "ds_especialidade", "ds_profissional", "ds_plano", "sn_particular", "sn_encaixe", "ds_observacao", "sn_confirmado")
        widgets = {
            "dh_agendamento": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ds_observacao": forms.Textarea(attrs={"rows": 3}),
        }


class PreAtendimentoForm(forms.ModelForm):
    class Meta:
        model = PreAtendimento
        exclude = (
            "cd_empresa",
            "cd_paciente",
            "cd_agendamento",
            "dh_classificacao",
            "dh_inicio",
            "dh_fim",
            "dh_criacao",
            "dh_atualizacao",
            "cd_usuario_criacao",
            "cd_usuario_atualizacao",
        )
        widgets = {
            "ds_queixa_principal": forms.Textarea(attrs={"rows": 3}),
            "ds_observacao": forms.Textarea(attrs={"rows": 3}),
            "nr_temperatura": forms.NumberInput(attrs={"step": "0.1"}),
            "nr_peso": forms.NumberInput(attrs={"step": "0.01"}),
            "nr_altura": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cd_prestador_responsavel"].queryset = (
            Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_classificacao=True)
            if empresa
            else Prestador.objects.none()
        )
        self.fields["cd_prestador_responsavel"].required = True


class AtendimentoForm(forms.ModelForm):
    class Meta:
        model = Atendimento
        fields = (
            "cd_prestador", "ds_origem", "ds_tipo_atendimento", "ds_especialidade",
            "cd_convenio", "ds_plano", "ds_unidade_setor", "ds_anamnese",
            "ds_hipotese_diagnostica", "ds_diagnostico", "ds_conduta", "ds_destino",
        )
        widgets = {
            "ds_anamnese": forms.Textarea(attrs={"rows": 6}),
            "ds_conduta": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cd_prestador"].queryset = (
            Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_atendimento=True).order_by("nm_prestador")
            if empresa
            else Prestador.objects.none()
        )
        self.fields["cd_convenio"].queryset = Convenio.objects.filter(cd_empresa=empresa, sn_ativo=True) if empresa else Convenio.objects.none()


class SolicitacaoExameForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoExame
        fields = ("ds_exame", "ds_justificativa", "ds_prioridade")


class ResultadoExameForm(forms.ModelForm):
    class Meta:
        model = ResultadoExame
        fields = ("ds_resultado", "ds_anexo", "sn_liberado")


class PrescricaoForm(forms.ModelForm):
    class Meta:
        model = Prescricao
        fields = ("ds_prescricao", "ds_orientacoes")
        widgets = {"ds_prescricao": forms.Textarea(attrs={"rows": 8}), "ds_orientacoes": forms.Textarea(attrs={"rows": 4})}


class EvolucaoAtendimentoForm(forms.ModelForm):
    class Meta:
        model = EvolucaoAtendimento
        fields = ("ds_evolucao",)
        widgets = {"ds_evolucao": forms.Textarea(attrs={"rows": 8})}
