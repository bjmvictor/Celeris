from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


def normalize_identifier(value: str) -> str:
    return slugify(value or "", allow_unicode=False).replace("-", "_").upper()


class Empresa(models.Model):
    cd_empresa = models.PositiveIntegerField("codigo", primary_key=True)
    nm_empresa = models.CharField("nome", max_length=180)
    nr_cnpj = models.CharField("CNPJ", max_length=18, blank=True)
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

    class Meta:
        ordering = ("cd_empresa",)

    def __str__(self) -> str:
        return f"{self.cd_empresa} - {self.nm_empresa}"


class User(AbstractUser):
    full_name = models.CharField("nome completo", max_length=180, blank=True)
    is_coordinator = models.BooleanField("coordenador", default=False)
    must_change_password = models.BooleanField("alterar senha", default=False)
    empresas = models.ManyToManyField(Empresa, through="UsuarioEmpresa", related_name="usuarios", blank=True)

    def clean(self):
        super().clean()
        self.username = normalize_identifier(self.username)

    def save(self, *args, **kwargs):
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
        unique_together = ("usuario", "empresa")
        ordering = ("usuario__username", "empresa__cd_empresa")

    def __str__(self) -> str:
        return f"{self.usuario} - {self.empresa}"
