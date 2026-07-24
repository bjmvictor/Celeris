from django import forms
from django.contrib.auth import get_user_model

from apps.accounts.models import Setor

from .models import MotivoConclusaoSuporte, MotivoServicoSuporte, OficinaSuporte, PrioridadeSuporte, Ticket, UsuarioOficinaSuporte


User = get_user_model()


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


class PrioridadeSuporteForm(EmpresaScopedModelForm):
    class Meta:
        model = PrioridadeSuporte
        fields = ("nm_prioridade", "nr_peso", "ds_cor", "sn_ativo")
        labels = {
            "nm_prioridade": "Prioridade",
            "nr_peso": "Peso",
            "ds_cor": "Cor",
            "sn_ativo": "Ativo",
        }
        widgets = {"ds_cor": forms.TextInput(attrs={"type": "color"})}


class MotivoServicoSuporteForm(EmpresaScopedModelForm):
    class Meta:
        model = MotivoServicoSuporte
        fields = ("nm_motivo", "cd_oficina", "sn_ativo")
        labels = {
            "nm_motivo": "Motivo",
            "cd_oficina": "Oficina",
            "sn_ativo": "Ativo",
        }


class MotivoConclusaoSuporteForm(EmpresaScopedModelForm):
    class Meta:
        model = MotivoConclusaoSuporte
        fields = ("nm_motivo", "cd_oficina", "sn_ativo")
        labels = {
            "nm_motivo": "Motivo",
            "cd_oficina": "Oficina",
            "sn_ativo": "Ativo",
        }


class OficinaSuporteForm(EmpresaScopedModelForm):
    class Meta:
        model = OficinaSuporte
        fields = ("nm_oficina", "ds_descricao", "sn_ativo", "usuarios")
        labels = {
            "nm_oficina": "Oficina",
            "ds_descricao": "Descrição",
            "sn_ativo": "Ativo",
            "usuarios": "Usuários",
        }


class TicketForm(EmpresaScopedModelForm):
    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        self.no_support_offices = False
        if self.empresa and usuario and not getattr(usuario, "is_superuser", False):
            office_ids = UsuarioOficinaSuporte.objects.filter(
                cd_empresa=self.empresa,
                cd_usuario=usuario,
                sn_ativo=True,
                sn_solicita=True,
                cd_oficina__sn_ativo=True,
            ).values_list("cd_oficina_id", flat=True)
            office_queryset = OficinaSuporte.objects.filter(
                cd_empresa=self.empresa,
                sn_ativo=True,
                pk__in=office_ids,
            ).order_by("nm_oficina")
            self.fields["cd_oficina"].queryset = office_queryset
            self.no_support_offices = not office_queryset.exists()

    class Meta:
        model = Ticket
        fields = ("cd_setor", "title", "cd_oficina", "cd_motivo", "cd_prioridade", "description")
        labels = {
            "cd_setor": "Setor",
            "title": "Título",
            "cd_oficina": "Oficina",
            "cd_motivo": "Motivo de serviço",
            "cd_prioridade": "Prioridade",
            "description": "Descrição",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 1, "class": "support-description-field"}),
            "cd_oficina": forms.Select(attrs={"data-support-office": "true"}),
            "cd_motivo": forms.Select(attrs={"data-support-motive": "true"}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.no_support_offices:
            self.add_error("cd_oficina", "Seu usuário não possui oficina liberada para solicitar suporte.")
        oficina = cleaned.get("cd_oficina")
        motivo = cleaned.get("cd_motivo")
        if motivo and motivo.cd_oficina_id and oficina and motivo.cd_oficina_id != oficina.pk:
            self.add_error("cd_motivo", "O motivo selecionado não pertence à oficina informada.")
        return cleaned


class TicketAtendimentoForm(EmpresaScopedModelForm):
    class Meta:
        model = Ticket
        fields = ("status", "assigned_to", "performers", "conclusion")
        labels = {
            "status": "Status",
            "assigned_to": "Responsável",
            "performers": "Executores",
            "conclusion": "Conclusão",
        }
        widgets = {
            "conclusion": forms.Textarea(attrs={"rows": 1, "class": "support-description-field"}),
        }


class UsuarioOficinaSuporteForm(EmpresaScopedModelForm):
    class Meta:
        model = UsuarioOficinaSuporte
        fields = ("cd_usuario", "cd_oficina", "sn_ativo", "sn_atende", "sn_solicita")
        labels = {
            "cd_usuario": "Usuário",
            "cd_oficina": "Oficina",
            "sn_ativo": "Ativo",
            "sn_atende": "Atende",
            "sn_solicita": "Solicita",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cd_usuario"].queryset = User.objects.filter(is_active=True).order_by("username")
