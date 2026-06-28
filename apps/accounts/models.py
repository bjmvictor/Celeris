from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.validators import validate_cnes, validate_cpf


def normalize_identifier(value: str) -> str:
    return slugify(value or "", allow_unicode=False).replace("-", "_").upper()


def generate_username(full_name: str) -> str:
    candidates = username_candidates(full_name)
    return candidates[0] if candidates else ""


def username_candidates(full_name: str) -> list[str]:
    particles = {"DA", "DAS", "DE", "DO", "DOS", "E"}
    parts = [normalize_identifier(part) for part in (full_name or "").split() if normalize_identifier(part)]
    if not parts:
        return []
    if len(parts) == 1:
        return [parts[0]]
    without_particles = parts[0] + "".join(part[0] for part in parts[1:] if part not in particles)
    with_particles = parts[0] + "".join(part[0] for part in parts[1:])
    candidates = [without_particles[:150]]
    if with_particles != without_particles:
        candidates.append(with_particles[:150])
    return candidates


def available_username(full_name: str, *, exclude_user_id=None) -> str:
    candidates = username_candidates(full_name)
    if not candidates:
        return ""
    queryset = User.objects.all()
    if exclude_user_id:
        queryset = queryset.exclude(pk=exclude_user_id)
    for candidate in candidates:
        if not queryset.filter(username=candidate).exists():
            return candidate
    base = candidates[0]
    suffix = 1
    while queryset.filter(username=f"{base}{suffix}"[:150]).exists():
        suffix += 1
    return f"{base}{suffix}"[:150]


class Empresa(models.Model):
    cd_empresa = models.PositiveIntegerField("codigo", primary_key=True)
    nm_empresa = models.CharField("nome", max_length=180)
    nr_cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    nr_cnes = models.CharField("CNES", max_length=7, blank=True, validators=[validate_cnes])
    ds_razao_social = models.CharField("razao social", max_length=220, blank=True)
    ds_nome_fantasia = models.CharField("nome fantasia", max_length=180, blank=True)
    ds_email = models.EmailField("email", blank=True)
    nr_telefone = models.CharField("telefone", max_length=30, blank=True)
    ds_endereco = models.CharField("endereco", max_length=220, blank=True)
    nr_endereco = models.CharField("numero", max_length=20, blank=True)
    ds_bairro = models.CharField("bairro", max_length=120, blank=True)
    ds_cidade = models.CharField("cidade", max_length=120, blank=True)
    sg_estado = models.CharField("UF", max_length=2, blank=True)
    nr_cep = models.CharField("CEP", max_length=10, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)
    dh_criacao = models.DateTimeField("data de criação", default=timezone.now, editable=False)
    dh_atualizacao = models.DateTimeField("data de alteração", auto_now=True)
    cd_usuario_criacao = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="empresas_criadas",
    )
    cd_usuario_atualizacao = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="empresas_atualizadas",
    )

    class Meta:
        db_table = "empresa"
        ordering = ("cd_empresa",)

    def __str__(self) -> str:
        return f"{self.cd_empresa} - {self.nm_empresa}"


class User(AbstractUser):
    full_name = models.CharField("nome completo", max_length=180, blank=True)
    cd_prestador = models.ForeignKey(
        "atendimento.Prestador",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="usuarios",
        db_column="cd_prestador",
    )
    dt_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    nr_cpf = models.CharField("CPF", max_length=14, blank=True, validators=[validate_cpf])
    ds_idioma = models.CharField("idioma", max_length=40, blank=True)
    ds_profissao = models.CharField("profissão", max_length=120, blank=True)
    nr_matricula_rh = models.CharField("matrícula RH", max_length=40, blank=True)
    nr_celular = models.CharField("celular", max_length=30, blank=True)
    is_coordinator = models.BooleanField("coordenador", default=False)
    must_change_password = models.BooleanField("alterar senha", default=False)
    is_blocked = models.BooleanField("usuário bloqueado", default=False)
    invalid_login_attempts = models.PositiveIntegerField("tentativas inválidas", default=0)
    password_expires_at = models.DateTimeField("senha expira em", null=True, blank=True)
    can_register_patient = models.BooleanField("cadastra paciente", default=False)
    can_change_patient = models.BooleanField("altera paciente", default=False)
    can_create_users = models.BooleanField("cria usuários", default=False)
    can_deactivate_users = models.BooleanField("desativa usuários", default=False)
    can_manage_auxiliary_tables = models.BooleanField("gerencia tabelas auxiliares", default=False)
    can_configure_system = models.BooleanField("configura sistema", default=False)
    empresas = models.ManyToManyField(Empresa, through="UsuarioEmpresa", related_name="usuarios", blank=True)

    class Meta:
        db_table = "usuario"

    def clean(self):
        super().clean()
        self.username = normalize_identifier(self.username)

    def save(self, *args, **kwargs):
        if not self.username and self.full_name:
            self.username = available_username(self.full_name, exclude_user_id=self.pk)
        self.username = normalize_identifier(self.username)
        super().save(*args, **kwargs)

    def display_name(self) -> str:
        return self.full_name or self.get_full_name() or self.username


class UsuarioEmpresa(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    sn_padrao = models.BooleanField("padrao", default=False)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "usuario_empresa"
        unique_together = ("usuario", "empresa")
        ordering = ("usuario__username", "empresa__cd_empresa")

    def __str__(self) -> str:
        return f"{self.usuario} - {self.empresa}"


class Setor(models.Model):
    class TipoSetor(models.TextChoices):
        EMPRESA = "EMPRESA", "Setor da empresa"
        ATENDIMENTO = "ATENDIMENTO", "Setor de atendimento"

    cd_setor = models.BigAutoField("codigo", primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa", related_name="setores")
    nm_setor = models.CharField("nome", max_length=120)
    tp_setor = models.CharField("tipo", max_length=20, choices=TipoSetor.choices)
    ds_observacao = models.CharField("observacao", max_length=240, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)
    dh_criacao = models.DateTimeField("data de criacao", default=timezone.now, editable=False)
    dh_atualizacao = models.DateTimeField("data de alteracao", auto_now=True)
    usuarios = models.ManyToManyField(User, through="SetorUsuario", related_name="setores", blank=True)

    class Meta:
        db_table = "setor"
        ordering = ("cd_empresa", "tp_setor", "nm_setor")
        unique_together = ("cd_empresa", "tp_setor", "nm_setor")

    def __str__(self) -> str:
        return f"{self.nm_setor} ({self.get_tp_setor_display()})"


class SetorUsuario(models.Model):
    cd_setor_usuario = models.BigAutoField("codigo", primary_key=True)
    cd_setor = models.ForeignKey(Setor, on_delete=models.CASCADE, db_column="cd_setor")
    cd_usuario = models.ForeignKey(User, on_delete=models.CASCADE, db_column="cd_usuario")

    class Meta:
        db_table = "setor_usuario"
        unique_together = ("cd_setor", "cd_usuario")

    def __str__(self) -> str:
        return f"{self.cd_setor} - {self.cd_usuario}"


class Papel(models.Model):
    grupo = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="papel")
    ds_descricao = models.CharField("descrição", max_length=240, blank=True)
    sn_ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "papel"
        ordering = ("grupo__name",)

    def __str__(self) -> str:
        return self.grupo.name


class PapelModulo(models.Model):
    papel = models.ForeignKey(Papel, on_delete=models.CASCADE, related_name="modulos")
    modulo = models.ForeignKey("core.Module", on_delete=models.CASCADE, related_name="papeis")

    class Meta:
        db_table = "papel_modulo"
        unique_together = ("papel", "modulo")


class PapelTela(models.Model):
    papel = models.ForeignKey(Papel, on_delete=models.CASCADE, related_name="telas")
    tela = models.ForeignKey("core.ScreenDefinition", on_delete=models.CASCADE, related_name="papeis")

    class Meta:
        db_table = "papel_tela"
        unique_together = ("papel", "tela")
