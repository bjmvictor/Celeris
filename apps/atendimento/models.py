from django.conf import settings
from django.db import models

from apps.accounts.models import Empresa
from apps.core.models import ValorAuxiliarGlobal


class Convenio(models.Model):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_convenio = models.BigAutoField(primary_key=True)
    nm_convenio = models.CharField(max_length=160)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "convenio"
        ordering = ("nm_convenio",)
        unique_together = ("cd_empresa", "nm_convenio")

    def __str__(self) -> str:
        return self.nm_convenio


class Prestador(models.Model):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_prestador = models.BigAutoField(primary_key=True)
    nm_prestador = models.CharField(max_length=180)
    ds_especialidade = models.CharField(max_length=120, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "prestador"
        ordering = ("nm_prestador",)

    def __str__(self) -> str:
        return self.nm_prestador


class AgendaProfissional(models.Model):
    DIAS_SEMANA = [
        (0, "Segunda-feira"),
        (1, "Terça-feira"),
        (2, "Quarta-feira"),
        (3, "Quinta-feira"),
        (4, "Sexta-feira"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_agenda_profissional = models.BigAutoField(primary_key=True)
    cd_prestador = models.ForeignKey(Prestador, on_delete=models.PROTECT, db_column="cd_prestador")
    ds_agenda = models.CharField(max_length=160)
    nr_dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    hr_inicio = models.TimeField()
    hr_fim = models.TimeField()
    nr_tempo_atendimento = models.PositiveIntegerField(default=30)
    nr_intervalo = models.PositiveIntegerField(default=0)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "agenda_profissional"
        ordering = ("cd_prestador__nm_prestador", "nr_dia_semana", "hr_inicio")

    def __str__(self) -> str:
        return f"{self.ds_agenda} - {self.cd_prestador}"


class Paciente(models.Model):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.BigAutoField(primary_key=True)
    nm_paciente = models.CharField(max_length=180)
    nm_social = models.CharField(max_length=180, blank=True)
    dt_nascimento = models.DateField(null=True, blank=True)
    tp_sexo = models.CharField(max_length=20, blank=True)
    tp_genero = models.CharField(max_length=40, blank=True)
    ds_cor_raca = models.CharField(max_length=40, blank=True)
    tp_estado_civil = models.CharField(max_length=40, blank=True)
    tp_sanguineo = models.CharField(max_length=5, blank=True)
    nr_cpf = models.CharField(max_length=14, blank=True)
    nr_rg = models.CharField(max_length=30, blank=True)
    nr_cartao_sus = models.CharField(max_length=30, blank=True)
    cd_convenio = models.ForeignKey(Convenio, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_convenio")
    nr_convenio = models.CharField(max_length=50, blank=True)
    nm_convenio = models.CharField(max_length=120, blank=True)
    nr_telefone = models.CharField(max_length=30, blank=True)
    nr_celular = models.CharField(max_length=30, blank=True)
    ds_email = models.EmailField(blank=True)
    nm_mae = models.CharField(max_length=180, blank=True)
    nm_pai = models.CharField(max_length=180, blank=True)
    nm_conjuge = models.CharField(max_length=180, blank=True)
    ds_naturalidade = models.CharField(max_length=120, blank=True)
    ds_nacionalidade = models.CharField(max_length=120, blank=True)
    ds_profissao = models.CharField(max_length=120, blank=True)
    ds_endereco = models.CharField(max_length=220, blank=True)
    nr_endereco = models.CharField(max_length=20, blank=True)
    ds_complemento = models.CharField(max_length=120, blank=True)
    ds_bairro = models.CharField(max_length=120, blank=True)
    ds_cidade = models.CharField(max_length=120, blank=True)
    sg_estado = models.CharField(max_length=2, blank=True)
    nr_cep = models.CharField(max_length=10, blank=True)
    ds_observacao = models.TextField(blank=True)
    sn_ativo = models.BooleanField(default=True)
    dh_criacao = models.DateTimeField(auto_now_add=True)
    dh_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "paciente"
        ordering = ("nm_paciente",)

    def __str__(self) -> str:
        return self.nm_paciente


class HistoricoAlteracaoPaciente(models.Model):
    cd_historico_alteracao_paciente = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, db_column="cd_paciente")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario")
    cd_motivo_alteracao = models.ForeignKey(
        ValorAuxiliarGlobal,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_motivo_alteracao",
    )
    ds_observacao = models.TextField()
    ds_alteracoes = models.JSONField(default=dict)
    ds_antes = models.JSONField(default=dict)
    ds_depois = models.JSONField(default=dict)
    sn_desfeito = models.BooleanField(default=False)
    dh_alteracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historico_alteracao_paciente"
        ordering = ("-dh_alteracao",)


class Agendamento(models.Model):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_agendamento = models.BigAutoField(primary_key=True)
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, db_column="cd_paciente")
    cd_agenda_profissional = models.ForeignKey(AgendaProfissional, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_agenda_profissional")
    dh_agendamento = models.DateTimeField(null=True, blank=True)
    ds_tipo_atendimento = models.CharField(max_length=120, blank=True)
    ds_especialidade = models.CharField(max_length=120, blank=True)
    ds_profissional = models.CharField(max_length=120, blank=True)
    ds_observacao = models.TextField(blank=True)
    sn_confirmado = models.BooleanField(default=False)
    dh_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agendamento"
        ordering = ("-dh_agendamento",)
