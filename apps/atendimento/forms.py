import json

from django import forms
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import Setor
from apps.core.catalogos import catalogo_queryset, opcoes_catalogo
from apps.core.form_registry import aplicar_configuracao_formulario
from apps.core.models import Cep, MotivoAlteracao, TipoPrestadorConselho

from .models import AgendaProfissional, Agendamento, Atendimento, ClasseSenhaAtendimento, Convenio, EvolucaoAtendimento, IconeChamada, Paciente, PainelChamada, PreAtendimento, Prescricao, Prestador, ProtocoloSenhaAtendimento, RegraSubdivisaoSenha, ResponsavelAtendimento, ResultadoExame, SolicitacaoExame, TipoSenhaAtendimento


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
        queryset=MotivoAlteracao.objects.none(),
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
        selected_birth_state = self.data.get(self.add_prefix("sg_uf_nascimento")) or getattr(
            self.instance, "sg_uf_nascimento", ""
        )
        self.fields["nm_paciente"].required = True
        self.fields["dt_nascimento"].required = True
        self.fields["sn_ativo"].disabled = True
        if self.empresa:
            self.fields["cd_convenio"].queryset = Convenio.objects.filter(cd_empresa=self.empresa, sn_ativo=True)
        else:
            self.fields["cd_convenio"].queryset = Convenio.objects.none()
        self.fields["tp_sanguineo"].choices = self._choices_for("tipo_sanguineo")
        self.fields["tp_sexo"].choices = self._choices_for("sexo")
        self.fields["tp_genero"].choices = self._choices_for("identidade_genero")
        self.fields["ds_orientacao_sexual"].choices = self._choices_for("orientacao_sexual")
        self.fields["ds_cor_raca"].choices = self._choices_for("raca_cor")
        self.fields["tp_estado_civil"].choices = self._choices_for("estado_civil")
        self.fields["ds_nacionalidade"].choices = self._choices_for("nacionalidade")
        self.fields["ds_pais_nascimento"].choices = self._choices_for("pais")
        self.fields["sg_uf_nascimento"].choices = self._choices_for("estado")
        self.fields["ds_municipio_nascimento"].choices = self._choices_for("cidade", group=selected_birth_state)
        self.fields["ds_naturalidade"].choices = self._choices_for("cidade")
        self.fields["ds_profissao"].choices = self._choices_for("profissao")
        self.fields["ds_orgao_emissor"].choices = self._choices_for("orgao_emissor")
        self.fields["tp_logradouro"].choices = self._choices_for("tipo_logradouro")
        self.fields["ds_cidade"].choices = self._choices_for("cidade", group=selected_state)
        self.fields["sg_estado"].choices = self._choices_for("estado")
        for name in (
            "tp_sanguineo", "tp_sexo", "tp_genero", "ds_orientacao_sexual", "ds_cor_raca",
            "tp_estado_civil", "ds_nacionalidade", "ds_pais_nascimento", "sg_uf_nascimento",
            "ds_municipio_nascimento", "ds_naturalidade", "ds_profissao", "ds_orgao_emissor",
            "tp_logradouro", "ds_cidade", "sg_estado",
        ):
            self.fields[name].widget = forms.Select(choices=self.fields[name].choices)
        self.fields["cd_cep"].queryset = Cep.objects.filter(sn_ativo=True).order_by("nr_cep")
        self.fields["cd_cep"].label_from_instance = lambda cep: f"{cep.nr_cep} - {cep.ds_logradouro or cep.ds_cidade}"
        self.fields["motivo_alteracao"].queryset = catalogo_queryset("motivo_alteracao", ativos=True).order_by("ds_valor")
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
        self.fields["sg_uf_nascimento"].widget.attrs["data-linked-state"] = "nascimento"
        self.fields["ds_municipio_nascimento"].widget.attrs["data-linked-city"] = "nascimento"
        self.fields["nr_cpf"].widget.attrs.update({"maxlength": "14", "inputmode": "numeric", "data-mask": "cpf"})
        self.fields["nr_cpf"].widget.attrs["data-validate-cpf"] = "true"
        self.fields["ds_email"].widget.attrs["data-validate-email"] = "true"
        self.fields["nr_celular"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["nr_celular_2"].widget.attrs.update({"maxlength": "16", "inputmode": "numeric", "data-mask": "celular"})
        self.fields["dt_nascimento"].widget.attrs.update({"min": "1900-01-01", "max": timezone.localdate().isoformat()})
        for unique_field in ("nr_cpf", "nr_cartao_sus", "nr_rg"):
            if unique_field in self.fields:
                self.fields[unique_field].widget.attrs["data-unique-patient"] = unique_field
        aplicar_configuracao_formulario(self, "cadastro_paciente", self.empresa)

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
        return opcoes_catalogo(table_name, grupo=group)


class PrestadorForm(forms.ModelForm):
    tipos_prestador = forms.MultipleChoiceField(label="Tipos de prestador", required=False)
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
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        self.fields["nm_prestador"].required = True
        self.fields["nm_guerra"].required = True
        self.fields["dt_nascimento"].required = True
        self.fields["nr_cpf"].required = True
        self.fields["tp_prestador"].required = True
        self.fields["sn_ativo"].initial = True
        self.fields["sn_ativo"].disabled = True
        self.fields["tp_sexo"].widget = forms.Select(choices=self._choices_for("sexo"))
        self.fields["ds_cor_raca"].widget = forms.Select(choices=self._choices_for("raca_cor"))
        self.fields["tp_prestador"].widget = forms.Select(choices=self._choices_for("tipo_prestador"))
        provider_type_choices = self._choices_for("tipo_prestador")[1:]
        self.fields["tipos_prestador"].choices = provider_type_choices
        self.fields["tipos_prestador"].initial = (
            self.instance.tipos_prestador_ativos
            if self.instance and self.instance.pk
            else []
        )
        self.fields["tipos_prestador"].widget.attrs["data-assignment-values"] = "true"
        self.fields["ds_orgao_emissor"].widget = forms.Select(choices=self._choices_for("orgao_emissor"))
        self.fields["ds_grau_instrucao"].widget = forms.Select(choices=self._choices_for("grau_instrucao"))
        self.fields["tp_genero"].widget = forms.Select(choices=self._choices_for("identidade_genero"))
        self.fields["ds_nacionalidade"].widget = forms.Select(choices=self._choices_for("nacionalidade"))
        self.fields["ds_naturalidade"].widget = forms.Select(choices=self._choices_for("cidade"))
        self.fields["cd_cbo"].widget = forms.Select(choices=self._choices_for("cbo"))
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
        self.fields["tp_prestador"].widget.attrs["data-force-submit"] = "true"
        self.fields["tp_prestador"].widget.attrs["data-council-map"] = json.dumps(
            {mapping.tp_prestador: mapping.ds_conselho for mapping in mappings}
        )
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
        aplicar_configuracao_formulario(self, "cadastro_prestador", self.empresa)

    def _choices_for(self, table_name, group=None):
        return opcoes_catalogo(table_name, grupo=group)

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
        provider_types = cleaned_data.get("tipos_prestador") or []
        if not provider_types:
            provider_types = [provider_type]
            cleaned_data["tipos_prestador"] = provider_types
        if provider_type not in provider_types:
            self.add_error("tipos_prestador", "O tipo principal deve estar entre os tipos adicionados.")
        mapping = TipoPrestadorConselho.objects.filter(tp_prestador=provider_type, sn_ativo=True).first()
        if not mapping:
            cleaned_data["ds_conselho"] = ""
            return cleaned_data
        if not cleaned_data.get("nr_conselho"):
            self.add_error("nr_conselho", "Informe o número do conselho para este tipo de prestador.")
        cleaned_data["ds_conselho"] = mapping.ds_conselho
        return cleaned_data


class TipoSenhaAtendimentoForm(forms.ModelForm):
    cd_tipo_senha = forms.IntegerField(label="Código", required=False, disabled=True)

    class Meta:
        model = TipoSenhaAtendimento
        fields = (
            "cd_tipo_senha",
            "sn_ativo",
            "nm_tipo_senha",
            "sg_tipo_senha",
            "cd_setor_atendimento",
        )
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sn_ativo"].initial = True
        self.fields["sn_ativo"].disabled = True
        self.fields["cd_setor_atendimento"].queryset = (
            Setor.objects.filter(
                cd_empresa=empresa,
                tp_setor=Setor.TipoSetor.ATENDIMENTO,
                sn_ativo=True,
            ).order_by("nm_setor")
            if empresa
            else Setor.objects.none()
        )
        if self.instance and self.instance.pk:
            self.fields["cd_tipo_senha"].initial = self.instance.pk
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "tipo_senha_atendimento",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "false" if name in {"cd_tipo_senha", "sn_ativo"} else "true",
                    "data-primary-key": "true" if name == "cd_tipo_senha" else "false",
                }
            )


class ClasseSenhaAtendimentoForm(forms.ModelForm):
    class Meta:
        model = ClasseSenhaAtendimento
        fields = ("nm_classe_senha", "sg_classe_senha", "nr_prioridade", "ds_icone", "sn_ativo")
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sn_ativo"].initial = True
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "classe_senha_atendimento",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "true",
                }
            )


class ProtocoloSenhaAtendimentoForm(forms.ModelForm):
    class Meta:
        model = ProtocoloSenhaAtendimento
        fields = ("sg_protocolo", "nm_protocolo", "ds_protocolo", "sn_ativo")
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sn_ativo"].initial = True
        self.fields["sg_protocolo"].widget.attrs.update({"maxlength": "8", "data-uppercase": "true"})
        self.fields["nm_protocolo"].widget.attrs.update({"data-uppercase": "true"})
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "protocolo_senha",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "true",
                }
            )


class RegraSubdivisaoSenhaForm(forms.ModelForm):
    class Meta:
        model = RegraSubdivisaoSenha
        fields = (
            "cd_classe_senha",
            "sg_regra",
            "nr_prioridade",
            "nr_idade_minima",
            "nr_idade_maxima",
            "cd_icone_chamada",
            "cd_protocolo",
            "nr_tempo_limite",
            "sn_ativo",
        )

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cd_classe_senha"].queryset = (
            ClasseSenhaAtendimento.objects.filter(cd_empresa=empresa, sn_ativo=True)
            .order_by("nm_classe_senha")
            if empresa
            else ClasseSenhaAtendimento.objects.none()
        )
        self.fields["cd_icone_chamada"].queryset = (
            IconeChamada.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_icone")
            if empresa
            else IconeChamada.objects.none()
        )
        self.fields["cd_protocolo"].queryset = (
            ProtocoloSenhaAtendimento.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_protocolo")
            if empresa
            else ProtocoloSenhaAtendimento.objects.none()
        )
        self.fields["sg_regra"].widget.attrs.update({"maxlength": "4", "data-uppercase": "true"})


class EscalaForm(forms.ModelForm):
    cd_agenda_profissional = forms.IntegerField(label="Código", required=False, disabled=True)
    ds_dias_semana = forms.MultipleChoiceField(
        label="Dias da semana",
        choices=AgendaProfissional.DIAS_SEMANA,
        required=True,
    )

    class Meta:
        model = AgendaProfissional
        fields = (
            "cd_agenda_profissional",
            "sn_ativo",
            "ds_agenda",
            "tp_escala",
            "cd_prestador",
            "ds_especialidade",
            "cd_setor_atendimento",
            "tp_horario",
            "ds_dias_semana",
            "hr_inicio",
            "hr_fim",
            "nr_tempo_atendimento",
            "nr_intervalo",
            "qt_horarios_dia",
            "qt_encaixes",
            "sn_atende_feriado",
            "convenios",
            "ds_tipo_agendamento",
        )
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativa"), (False, "Inativa"))),
            "hr_inicio": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "hr_fim": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "convenios": forms.SelectMultiple(),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name in (
            "ds_agenda",
            "tp_escala",
            "cd_prestador",
            "ds_especialidade",
            "cd_setor_atendimento",
            "tp_horario",
            "hr_inicio",
            "hr_fim",
            "nr_tempo_atendimento",
            "qt_horarios_dia",
            "ds_tipo_agendamento",
        ):
            self.fields[name].required = True
        if empresa:
            prestadores = Prestador.objects.filter(cd_empresa=empresa)
            setores = Setor.objects.filter(cd_empresa=empresa, tp_setor=Setor.TipoSetor.ATENDIMENTO)
            convenios = Convenio.objects.filter(cd_empresa=empresa)
            if self.instance and self.instance.pk:
                prestadores = prestadores.filter(Q(sn_ativo=True, sn_permite_agenda=True) | Q(pk=self.instance.cd_prestador_id))
                setores = setores.filter(Q(sn_ativo=True) | Q(pk=self.instance.cd_setor_atendimento_id))
                convenios = convenios.filter(Q(sn_ativo=True) | Q(escalas=self.instance))
            else:
                prestadores = prestadores.filter(sn_ativo=True, sn_permite_agenda=True)
                setores = setores.filter(sn_ativo=True)
                convenios = convenios.filter(sn_ativo=True)
            self.fields["cd_prestador"].queryset = prestadores.order_by("nm_prestador")
            self.fields["cd_setor_atendimento"].queryset = setores.order_by("nm_setor")
            self.fields["convenios"].queryset = convenios.distinct().order_by("nm_convenio")
        else:
            self.fields["cd_prestador"].queryset = Prestador.objects.none()
            self.fields["cd_setor_atendimento"].queryset = Setor.objects.none()
            self.fields["convenios"].queryset = Convenio.objects.none()
        self.fields["tp_escala"].widget = forms.Select(choices=self._choices("tipo_escala", [("AMBULATORIAL", "Ambulatorial")]))
        all_specialty_choices = self._choices("especialidade")
        specialty_labels = dict(all_specialty_choices)
        provider_specialties = {}
        available_providers = self.fields["cd_prestador"].queryset
        for provider in available_providers:
            specialty_codes = list(
                dict.fromkeys(
                    code
                    for code in [*(provider.ds_especialidades or []), provider.ds_especialidade]
                    if code
                )
            )
            provider_specialties[str(provider.pk)] = [
                {
                    "value": code,
                    "label": specialty_labels.get(code) or str(code).replace("_", " ").title(),
                }
                for code in specialty_codes
            ]
        selected_provider_id = ""
        if self.is_bound:
            selected_provider_id = str(self.data.get("cd_prestador") or "")
        elif self.instance and self.instance.cd_prestador_id:
            selected_provider_id = str(self.instance.cd_prestador_id)
        selected_specialties = provider_specialties.get(selected_provider_id, [])
        self.fields["ds_especialidade"].widget = forms.Select(
            choices=[("", "")] + [(item["value"], item["label"]) for item in selected_specialties]
        )
        self.fields["cd_prestador"].widget.attrs["data-provider-specialties"] = json.dumps(
            provider_specialties,
            ensure_ascii=False,
        )
        self.fields["ds_especialidade"].widget.attrs.update(
            {
                "data-provider-specialty-target": "true",
                "data-all-specialties": json.dumps(
                    [{"value": value, "label": label} for value, label in all_specialty_choices if value],
                    ensure_ascii=False,
                ),
            }
        )
        self.fields["ds_tipo_agendamento"].widget = forms.Select(
            choices=self._choices(
                "tipo_atendimento",
                [("PRIMEIRA_CONSULTA", "Primeira consulta"), ("RETORNO", "Retorno")],
            )
        )
        for field_name in ("tp_escala", "ds_especialidade", "ds_tipo_agendamento"):
            current = getattr(self.instance, field_name, "") if self.instance else ""
            choices = list(self.fields[field_name].widget.choices)
            if current and current not in {value for value, _label in choices}:
                choices.append((current, current))
                self.fields[field_name].widget.choices = choices
        self.fields["ds_dias_semana"].initial = self.instance.dias_semana if self.instance and self.instance.pk else [0, 1, 2, 3, 4]
        self.fields["sn_ativo"].initial = True
        self.fields["sn_ativo"].disabled = True
        if self.instance and self.instance.pk:
            self.fields["cd_agenda_profissional"].initial = self.instance.pk
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "escala",
                    "data-field-name": {
                        "cd_agenda_profissional": "cd_escala",
                        "ds_agenda": "nm_escala",
                    }.get(name, name),
                    "data-primary-key": "true" if name == "cd_agenda_profissional" else "false",
                    "data-consultable": "true",
                    "data-editable": "false" if name in {"cd_agenda_profissional", "sn_ativo"} else "true",
                }
            )
        for name in ("hr_inicio", "hr_fim", "nr_tempo_atendimento", "nr_intervalo", "qt_horarios_dia"):
            self.fields[name].widget.attrs["data-scale-preview"] = name
        self.fields["convenios"].widget.attrs["data-assignment-values"] = "true"
        aplicar_configuracao_formulario(self, "cadastro_escala", empresa)

    @staticmethod
    def _choices(table_name, fallback=()):
        values = opcoes_catalogo(table_name, incluir_vazio=False)
        return [("", "")] + (values or list(fallback))

    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get("cd_prestador")
        specialty = cleaned_data.get("ds_especialidade")
        if provider and specialty:
            allowed_specialties = {
                code
                for code in [*(provider.ds_especialidades or []), provider.ds_especialidade]
                if code
            }
            if specialty not in allowed_specialties:
                self.add_error(
                    "ds_especialidade",
                    "A especialidade selecionada não está cadastrada para o prestador.",
                )
        inicio = cleaned_data.get("hr_inicio")
        fim = cleaned_data.get("hr_fim")
        duracao = cleaned_data.get("nr_tempo_atendimento") or 0
        intervalo = cleaned_data.get("nr_intervalo") or 0
        quantidade = cleaned_data.get("qt_horarios_dia") or 0
        if inicio and fim:
            minutos = (fim.hour * 60 + fim.minute) - (inicio.hour * 60 + inicio.minute)
            if minutos <= 0:
                self.add_error("hr_fim", "O horário final deve ser posterior ao inicial.")
            elif duracao > 0:
                capacidade = max((minutos + intervalo) // (duracao + intervalo), 0)
                if quantidade > capacidade:
                    self.add_error(
                        "qt_horarios_dia",
                        f"O período comporta no máximo {capacidade} horário(s) com a duração e intervalo informados.",
                    )
        if quantidade < 1:
            self.add_error("qt_horarios_dia", "Informe ao menos um horário por dia.")
        if cleaned_data.get("qt_encaixes", 0) < 0:
            self.add_error("qt_encaixes", "A quantidade de encaixes não pode ser negativa.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        dias = [int(dia) for dia in self.cleaned_data.get("ds_dias_semana", [])]
        instance.ds_dias_semana = dias
        instance.nr_dia_semana = dias[0] if dias else 0
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PainelChamadaForm(forms.ModelForm):
    cd_painel_chamada = forms.IntegerField(label="Código", required=False, disabled=True)

    class Meta:
        model = PainelChamada
        fields = (
            "cd_painel_chamada", "sn_ativo", "nm_painel", "ds_descricao", "nm_maquina",
            "tp_painel", "nr_referencia", "ds_local_exibicao", "ds_mensagem_padrao",
            "nr_tempo_exibicao", "ds_layout", "ds_tamanho", "ds_cor",
            "ds_prioridade_visual", "sn_voz", "ds_midia_url", "ds_observacao", "setores",
        )
        widgets = {
            "sn_ativo": forms.Select(choices=(("", ""), (True, "Ativo"), (False, "Inativo"))),
            "sn_voz": forms.Select(choices=(("", ""), (True, "Sim"), (False, "Não"))),
            "ds_observacao": forms.TextInput(),
            "setores": forms.SelectMultiple(),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        setores = Setor.objects.none()
        if empresa:
            setores = Setor.objects.filter(cd_empresa=empresa, tp_setor=Setor.TipoSetor.ATENDIMENTO)
            if self.instance and self.instance.pk:
                setores = setores.filter(Q(sn_ativo=True) | Q(paineis_chamada=self.instance))
            else:
                setores = setores.filter(sn_ativo=True)
        self.fields["setores"].queryset = setores.distinct().order_by("nm_setor")
        self.fields["sn_ativo"].initial = True
        self.fields["sn_voz"].initial = True
        self.fields["sn_ativo"].disabled = True
        if self.instance and self.instance.pk:
            self.fields["cd_painel_chamada"].initial = self.instance.pk
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "painel_chamada",
                    "data-field-name": name,
                    "data-primary-key": "true" if name == "cd_painel_chamada" else "false",
                    "data-consultable": "true",
                    "data-editable": "false" if name in {"cd_painel_chamada", "sn_ativo"} else "true",
                }
            )
        self.fields["setores"].widget.attrs["data-assignment-values"] = "true"
        aplicar_configuracao_formulario(self, "cadastro_painel_chamada", empresa)

    def clean_nm_maquina(self):
        value = self.cleaned_data["nm_maquina"].strip()
        duplicate = PainelChamada.objects.filter(cd_empresa=self.empresa, nm_maquina__iexact=value)
        if self.instance and self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Já existe um painel cadastrado para esta máquina.")
        return value


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
        rotulos = {
            "nr_prioridade": "Prioridade",
            "ds_queixa_principal": "Queixa principal",
            "ds_sintomas": "Sintomas",
            "cd_prestador_responsavel": "Prestador responsável",
            "nr_pressao_arterial": "Pressão arterial",
            "nr_frequencia_cardiaca": "Frequência cardíaca",
            "nr_frequencia_respiratoria": "Frequência respiratória",
            "nr_saturacao": "Saturação de O₂",
            "nr_temperatura": "Temperatura",
            "nr_peso": "Peso",
            "nr_altura": "Altura",
            "ds_observacao": "Observações",
            "ds_cor_prioridade": "Cor da prioridade",
        }
        for nome, rotulo in rotulos.items():
            if nome in self.fields:
                self.fields[nome].label = rotulo
        self.fields["cd_prestador_responsavel"].queryset = (
            Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_classificacao=True)
            if empresa
            else Prestador.objects.none()
        )
        self.fields["cd_prestador_responsavel"].required = True
        aplicar_configuracao_formulario(self, "pre_atendimento", empresa)


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


class CadastroAtendimentoForm(forms.ModelForm):
    cd_atendimento = forms.IntegerField(label="Código", required=False, disabled=True)
    cd_paciente_exibicao = forms.IntegerField(label="Prontuário", required=False, disabled=True)
    nm_paciente_exibicao = forms.CharField(label="Paciente", required=False, disabled=True)
    dh_atendimento_exibicao = forms.DateTimeField(
        label="Data e hora",
        required=False,
        widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
        input_formats=("%Y-%m-%dT%H:%M",),
    )

    class Meta:
        model = Atendimento
        fields = (
            "cd_atendimento", "cd_paciente_exibicao", "nm_paciente_exibicao",
            "dh_atendimento_exibicao", "cd_prestador", "ds_origem", "ds_recepcao_origem",
            "cd_convenio", "ds_plano", "ds_subplano", "ds_tipo_atendimento",
            "ds_local_procedencia", "ds_destino", "ds_especialidade", "ds_cid",
            "ds_meio_transporte", "ds_procedimento_principal", "ds_cbo_prestador",
            "nr_senha_chamada", "ds_observacao_recepcao", "sn_visita", "sn_retorno",
        )
        widgets = {
            "ds_observacao_recepcao": forms.TextInput(),
        }

    def __init__(self, *args, empresa=None, paciente=None, agendamento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cd_prestador"].label = "Médico/Prestador"
        self.fields["cd_convenio"].queryset = (
            Convenio.objects.filter(cd_empresa=empresa, sn_ativo=True).order_by("nm_convenio")
            if empresa else Convenio.objects.none()
        )
        self.fields["cd_prestador"].queryset = (
            Prestador.objects.filter(cd_empresa=empresa, sn_ativo=True, sn_permite_atendimento=True).order_by("nm_prestador")
            if empresa else Prestador.objects.none()
        )
        for field_name, table_name, fallback in (
            ("ds_tipo_atendimento", "tipo_atendimento", ()),
            ("ds_local_procedencia", "local_procedencia", (("DOMICILIO", "Domicílio"), ("OUTRA_UNIDADE", "Outra unidade hospitalar"))),
            ("ds_destino", "destino_atendimento", (("CONSULTORIO", "Consultório"), ("SALA", "Sala"))),
            ("ds_especialidade", "especialidade", ()),
            ("ds_meio_transporte", "meio_transporte", (("PROPRIO", "Meios próprios"), ("AMBULANCIA", "Ambulância"))),
            ("ds_recepcao_origem", "origem_recepcao", (("RECEPCAO_PRINCIPAL", "Recepção principal"),)),
        ):
            self.fields[field_name].widget = forms.Select(choices=self._choices(table_name, fallback))
        if self.instance and self.instance.pk:
            self.fields["cd_atendimento"].initial = self.instance.pk
            self.fields["dh_atendimento_exibicao"].initial = timezone.localtime(self.instance.dh_inicio)
            paciente = self.instance.cd_paciente
        else:
            self.fields["dh_atendimento_exibicao"].initial = timezone.localtime().replace(second=0, microsecond=0)
        if paciente:
            self.fields["cd_paciente_exibicao"].initial = paciente.pk
            self.fields["nm_paciente_exibicao"].initial = paciente.nm_paciente
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "atendimento",
                    "data-field-name": name.replace("_exibicao", ""),
                    "data-primary-key": "true" if name == "cd_atendimento" else "false",
                    "data-consultable": "true",
                    "data-editable": "false" if name in {
                        "cd_atendimento", "cd_paciente_exibicao", "nm_paciente_exibicao",
                    } else "true",
                }
            )
        aplicar_configuracao_formulario(self, "cadastro_atendimento", empresa)

    @staticmethod
    def _choices(table_name, fallback=()):
        values = opcoes_catalogo(table_name, incluir_vazio=False)
        return [("", "")] + (values or list(fallback))


class AlteracaoAtendimentoForm(CadastroAtendimentoForm):
    motivo_alteracao = forms.ModelChoiceField(
        label="Motivo da alteração",
        queryset=MotivoAlteracao.objects.none(),
        required=False,
        empty_label="",
    )
    observacao_alteracao = forms.CharField(
        label="Observação da alteração",
        required=False,
        widget=forms.TextInput(attrs={"maxlength": 255}),
    )
    versao_atendimento = forms.CharField(required=False, widget=forms.HiddenInput())

    CAMPOS_IMUTAVEIS = {
        "cd_atendimento",
        "cd_paciente_exibicao",
        "nm_paciente_exibicao",
        "dh_atendimento_exibicao",
        "ds_origem",
        "nr_senha_chamada",
    }

    def __init__(self, *args, empresa=None, paciente=None, agendamento=None, **kwargs):
        super().__init__(*args, empresa=empresa, paciente=paciente, agendamento=agendamento, **kwargs)
        self.fields["motivo_alteracao"].queryset = catalogo_queryset("motivo_alteracao", ativos=True).order_by("ds_valor")
        self.fields["motivo_alteracao"].label_from_instance = lambda value: value.ds_valor
        if self.instance and self.instance.pk:
            self.fields["versao_atendimento"].initial = self.instance.dh_atualizacao.isoformat()
        else:
            self.fields["cd_atendimento"].disabled = False
        for name, field in self.fields.items():
            field.widget.attrs["data-consultable"] = "true" if name == "cd_atendimento" else "false"
        for name in self.CAMPOS_IMUTAVEIS:
            field = self.fields.get(name)
            if not field:
                continue
            field.disabled = bool(self.instance and self.instance.pk) or name != "cd_atendimento"
            field.widget.attrs["data-editable"] = "false"
        for name in ("motivo_alteracao", "observacao_alteracao", "versao_atendimento"):
            self.fields[name].widget.attrs.update(
                {
                    "data-field-table": "historico_alteracao_atendimento",
                    "data-field-name": name,
                    "data-consultable": "false",
                }
            )


class ResponsavelAtendimentoForm(forms.ModelForm):
    class Meta:
        model = ResponsavelAtendimento
        exclude = (
            "cd_responsavel_atendimento", "cd_empresa", "cd_atendimento",
            "dh_criacao", "dh_atualizacao", "cd_usuario_criacao", "cd_usuario_atualizacao",
        )
        widgets = {
            "dt_expedicao": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, table_name in (
            ("ds_parentesco", "parentesco"),
            ("tp_estado_civil", "estado_civil"),
            ("ds_orgao_emissor", "orgao_emissor"),
            ("ds_profissao", "profissao"),
            ("ds_nacionalidade", "nacionalidade"),
            ("sg_estado", "estado"),
            ("ds_cidade", "cidade"),
            ("tp_logradouro", "tipo_logradouro"),
        ):
            self.fields[field_name].widget = forms.Select(
                choices=CadastroAtendimentoForm._choices(table_name)
            )
        self.fields["nr_cpf"].widget.attrs["data-mask"] = "cpf"
        self.fields["nr_celular"].widget.attrs["data-mask"] = "celular"
        self.fields["sn_mesmo_endereco_paciente"].widget.attrs["data-responsible-same-address"] = "true"
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "data-field-table": "responsavel_atendimento",
                    "data-field-name": name,
                    "data-consultable": "true",
                    "data-editable": "true",
                }
            )
        aplicar_configuracao_formulario(self, "responsavel_atendimento", empresa)


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
