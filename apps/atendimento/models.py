from django.conf import settings
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible

from apps.accounts.models import Empresa, Setor
from apps.core.models import Cep, Especialidade, MotivoAlteracao, ScreenDefinition
from apps.core.validators import validate_cpf


@deconstructible
class ArmazenamentoClinicoPrivado(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=settings.BASE_DIR / "private_clinical_media",
            base_url=None,
        )


armazenamento_clinico_privado = ArmazenamentoClinicoPrivado()


class AuditoriaModel(models.Model):
    dh_criacao = models.DateTimeField(default=timezone.now, editable=False)
    dh_atualizacao = models.DateTimeField(auto_now=True)
    cd_usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_criados",
    )
    cd_usuario_atualizacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_atualizados",
    )

    class Meta:
        abstract = True


class Convenio(AuditoriaModel):
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


class Prestador(AuditoriaModel):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_prestador = models.BigAutoField(primary_key=True)
    nm_prestador = models.CharField(max_length=180)
    nm_guerra = models.CharField(max_length=120)
    dt_nascimento = models.DateField(null=True, blank=True)
    nr_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf])
    nr_rg = models.CharField(max_length=30, blank=True)
    dt_expedicao = models.DateField(null=True, blank=True)
    nm_mae = models.CharField(max_length=180, blank=True)
    nm_pai = models.CharField(max_length=180, blank=True)
    nr_cartao_sus = models.CharField(max_length=30, blank=True)
    ds_grau_instrucao = models.CharField(max_length=40, blank=True)
    tp_genero = models.CharField(max_length=40, blank=True)
    ds_nacionalidade = models.CharField(max_length=40, blank=True)
    ds_naturalidade = models.CharField(max_length=40, blank=True)
    tp_prestador = models.CharField(max_length=60, blank=True)
    cd_cbo = models.CharField(max_length=20, blank=True)
    tp_sexo = models.CharField(max_length=20, blank=True)
    ds_cor_raca = models.CharField(max_length=40, blank=True)
    ds_orgao_emissor = models.CharField(max_length=40, blank=True)
    tp_logradouro = models.CharField(max_length=40, blank=True)
    tp_vinculo = models.CharField(max_length=40, blank=True)
    ds_conselho = models.CharField(max_length=20, blank=True)
    nr_conselho = models.CharField(max_length=30, blank=True)
    sg_conselho = models.CharField(max_length=2, blank=True)
    ds_especialidade = models.CharField(max_length=120, blank=True)
    ds_especialidades = models.JSONField(default=list, blank=True)
    sn_permite_agenda = models.BooleanField(default=False)
    sn_permite_atendimento = models.BooleanField(default=False)
    sn_permite_prescricao = models.BooleanField(default=False)
    sn_permite_classificacao = models.BooleanField(default=False)
    nr_telefone = models.CharField(max_length=30, blank=True)
    nr_celular = models.CharField(max_length=30, blank=True)
    nr_celular_2 = models.CharField(max_length=30, blank=True)
    ds_email = models.EmailField(blank=True)
    ds_contato_principal = models.CharField(max_length=20, blank=True)
    cd_cep = models.ForeignKey(Cep, null=True, blank=True, on_delete=models.PROTECT, related_name="prestadores_residenciais", db_column="cd_cep")
    nr_cep = models.CharField(max_length=10, blank=True)
    sg_estado = models.CharField(max_length=2, blank=True)
    ds_cidade = models.CharField(max_length=120, blank=True)
    ds_endereco = models.CharField(max_length=220, blank=True)
    nr_endereco = models.CharField(max_length=20, blank=True)
    ds_complemento = models.CharField(max_length=120, blank=True)
    ds_bairro = models.CharField(max_length=120, blank=True)
    cd_cep_comercial = models.ForeignKey(Cep, null=True, blank=True, on_delete=models.PROTECT, related_name="prestadores_comerciais", db_column="cd_cep_comercial")
    nr_cep_comercial = models.CharField(max_length=10, blank=True)
    sg_estado_comercial = models.CharField(max_length=2, blank=True)
    ds_cidade_comercial = models.CharField(max_length=120, blank=True)
    tp_logradouro_comercial = models.CharField(max_length=40, blank=True)
    ds_endereco_comercial = models.CharField(max_length=220, blank=True)
    nr_endereco_comercial = models.CharField(max_length=20, blank=True)
    ds_complemento_comercial = models.CharField(max_length=120, blank=True)
    ds_bairro_comercial = models.CharField(max_length=120, blank=True)
    sn_mesmo_endereco = models.BooleanField(default=False)
    cd_banco = models.CharField(max_length=40, blank=True)
    nr_agencia = models.CharField(max_length=20, blank=True)
    nr_digito_agencia = models.CharField(max_length=5, blank=True)
    nm_agencia = models.CharField(max_length=120, blank=True)
    nr_conta = models.CharField(max_length=30, blank=True)
    nr_digito_conta = models.CharField(max_length=5, blank=True)
    tp_conta = models.CharField(max_length=20, blank=True)
    nm_favorecido = models.CharField(max_length=180, blank=True)
    nr_documento_favorecido = models.CharField(max_length=18, blank=True)
    ds_chave_pix = models.CharField(max_length=180, blank=True)
    ds_observacao = models.CharField(max_length=255, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "prestador"
        ordering = ("nm_prestador",)

    def __str__(self) -> str:
        return self.nm_prestador

    def save(self, *args, **kwargs):
        if not self.nm_guerra and self.nm_prestador:
            name_parts = self.nm_prestador.split()
            self.nm_guerra = " ".join(name_parts if len(name_parts) < 2 else (name_parts[0], name_parts[-1]))
        if self.ds_especialidades:
            if self.ds_especialidade not in self.ds_especialidades:
                self.ds_especialidade = self.ds_especialidades[0]
        if self.cd_cep:
            self.nr_cep = self.cd_cep.nr_cep
        if self.cd_cep_comercial:
            self.nr_cep_comercial = self.cd_cep_comercial.nr_cep
        if self.sn_mesmo_endereco:
            self.cd_cep_comercial = self.cd_cep
            self.nr_cep_comercial = self.nr_cep
            self.sg_estado_comercial = self.sg_estado
            self.ds_cidade_comercial = self.ds_cidade
            self.tp_logradouro_comercial = self.tp_logradouro
            self.ds_endereco_comercial = self.ds_endereco
            self.nr_endereco_comercial = self.nr_endereco
            self.ds_complemento_comercial = self.ds_complemento
            self.ds_bairro_comercial = self.ds_bairro
        super().save(*args, **kwargs)

    @property
    def nm_especialidade(self):
        codes = self.ds_especialidades or ([self.ds_especialidade] if self.ds_especialidade else [])
        descriptions = list(
            Especialidade.objects.filter(cd_valor__in=codes)
            .order_by("ds_valor")
            .values_list("ds_valor", flat=True)
        )
        return ", ".join(descriptions or codes)

    @property
    def tipos_prestador_ativos(self):
        tipos = list(
            self.tipos_vinculados.filter(sn_ativo=True)
            .order_by("-sn_principal", "cd_tipo_prestador")
            .values_list("cd_tipo_prestador", flat=True)
        )
        if not tipos and self.tp_prestador:
            tipos.append(self.tp_prestador)
        return tipos


class PrestadorTipo(AuditoriaModel):
    cd_prestador_tipo = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_prestador = models.ForeignKey(
        Prestador,
        on_delete=models.CASCADE,
        db_column="cd_prestador",
        related_name="tipos_vinculados",
    )
    cd_tipo_prestador = models.CharField(max_length=60)
    sn_principal = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "prestador_tipo"
        ordering = ("cd_prestador", "-sn_principal", "cd_tipo_prestador")
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_prestador", "cd_tipo_prestador"),
                name="prestador_tipo_unico_empresa",
            ),
            models.UniqueConstraint(
                fields=("cd_prestador",),
                condition=models.Q(sn_principal=True, sn_ativo=True),
                name="prestador_tipo_principal_unico",
            ),
        ]

    def __str__(self):
        return f"{self.cd_prestador} - {self.cd_tipo_prestador}"


class AgendaProfissional(AuditoriaModel):
    TIPOS_HORARIO = [
        ("HORA_MARCADA", "Hora marcada"),
        ("HORARIO_CHEGADA", "Horário de chegada"),
    ]
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
    cd_agenda_profissional = models.BigAutoField(primary_key=True, db_column="cd_escala")
    cd_prestador = models.ForeignKey(Prestador, on_delete=models.PROTECT, db_column="cd_prestador")
    cd_setor_atendimento = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor_atendimento", related_name="escalas")
    convenios = models.ManyToManyField(Convenio, blank=True, related_name="escalas", db_table="escala_convenio")
    ds_agenda = models.CharField(max_length=160, db_column="nm_escala")
    tp_escala = models.CharField(max_length=40, default="AMBULATORIAL")
    tp_horario = models.CharField(max_length=30, choices=TIPOS_HORARIO, default="HORA_MARCADA")
    ds_tipo_agendamento = models.CharField(max_length=40, blank=True)
    ds_especialidade = models.CharField(max_length=40, blank=True)
    dt_inicio = models.DateField(default=timezone.localdate)
    dt_fim = models.DateField(default=timezone.localdate)
    nr_dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)
    ds_dias_semana = models.JSONField(default=list, blank=True)
    hr_inicio = models.TimeField()
    hr_fim = models.TimeField()
    nr_tempo_atendimento = models.PositiveIntegerField(default=30)
    nr_intervalo = models.PositiveIntegerField(default=0)
    qt_horarios_dia = models.PositiveIntegerField(default=1)
    qt_encaixes = models.PositiveIntegerField(default=0)
    sn_atende_feriado = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "escala"
        ordering = ("cd_prestador__nm_prestador", "nr_dia_semana", "hr_inicio")

    def __str__(self) -> str:
        return f"{self.ds_agenda} - {self.cd_prestador}"

    @property
    def dias_semana(self):
        return [int(dia) for dia in (self.ds_dias_semana or [self.nr_dia_semana])]

    @property
    def nm_especialidade(self):
        if not self.ds_especialidade:
            return ""
        return (
            Especialidade.objects.filter(cd_valor=self.ds_especialidade)
            .values_list("ds_valor", flat=True)
            .first()
            or self.ds_especialidade.replace("_", " ").title()
        )

    def clean(self):
        super().clean()
        if self.dt_inicio and self.dt_fim and self.dt_fim < self.dt_inicio:
            from django.core.exceptions import ValidationError

            raise ValidationError({"dt_fim": "A data final deve ser igual ou posterior à data inicial."})


class AgendaGerada(AuditoriaModel):
    STATUS = [
        ("ATIVA", "Ativa"),
        ("PARCIAL", "Parcialmente cancelada"),
        ("CANCELADA", "Cancelada"),
    ]

    cd_agenda_gerada = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_escala = models.ForeignKey(AgendaProfissional, on_delete=models.PROTECT, db_column="cd_escala", related_name="agendas_geradas")
    dt_inicio = models.DateField()
    dt_fim = models.DateField()
    ds_status = models.CharField(max_length=20, choices=STATUS, default="ATIVA")
    ds_observacao = models.TextField(blank=True)

    class Meta:
        db_table = "agenda_gerada"
        ordering = ("-dt_inicio", "cd_escala__cd_prestador__nm_prestador")

    @property
    def total_horarios(self):
        return self.horarios.count()

    @property
    def total_disponiveis(self):
        return self.horarios.filter(ds_status="DISPONIVEL").count()

    @property
    def total_agendados(self):
        return self.horarios.filter(ds_status="AGENDADO").count()

    @property
    def total_dias(self):
        return (self.dt_fim - self.dt_inicio).days + 1

    @property
    def horarios_por_data(self):
        grupos = {}
        for horario in self.horarios.all():
            data = timezone.localtime(horario.dh_inicio).date()
            grupo = grupos.setdefault(
                data,
                {"data": data, "horarios": [], "total": 0, "disponiveis": 0, "agendados": 0, "cancelados": 0},
            )
            grupo["horarios"].append(horario)
            grupo["total"] += 1
            chave = {
                "DISPONIVEL": "disponiveis",
                "AGENDADO": "agendados",
                "CANCELADO": "cancelados",
            }.get(horario.ds_status)
            if chave:
                grupo[chave] += 1
        return [grupos[data] for data in sorted(grupos)]


class HorarioAgenda(AuditoriaModel):
    STATUS = [
        ("DISPONIVEL", "Disponível"),
        ("AGENDADO", "Agendado"),
        ("CANCELADO", "Cancelado"),
    ]

    cd_horario_agenda = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_agenda_gerada = models.ForeignKey(AgendaGerada, on_delete=models.CASCADE, db_column="cd_agenda_gerada", related_name="horarios")
    cd_escala = models.ForeignKey(AgendaProfissional, on_delete=models.PROTECT, db_column="cd_escala")
    cd_prestador = models.ForeignKey(Prestador, on_delete=models.PROTECT, db_column="cd_prestador")
    dh_inicio = models.DateTimeField()
    dh_fim = models.DateTimeField()
    ds_status = models.CharField(max_length=20, choices=STATUS, default="DISPONIVEL")
    ds_motivo_cancelamento = models.CharField(max_length=240, blank=True)

    class Meta:
        db_table = "horario_agenda"
        ordering = ("dh_inicio",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_prestador", "dh_inicio"),
                condition=~models.Q(ds_status="CANCELADO"),
                name="horario_agenda_prestador_unico",
            )
        ]


class Paciente(AuditoriaModel):
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.BigAutoField(primary_key=True)
    nm_paciente = models.CharField(max_length=180)
    nm_social = models.CharField(max_length=180, blank=True)
    dt_nascimento = models.DateField(null=True, blank=True)
    tp_sexo = models.CharField(max_length=20, blank=True)
    tp_genero = models.CharField(max_length=40, blank=True)
    ds_orientacao_sexual = models.CharField(max_length=40, blank=True)
    ds_cor_raca = models.CharField(max_length=40, blank=True)
    tp_estado_civil = models.CharField(max_length=40, blank=True)
    tp_sanguineo = models.CharField(max_length=5, blank=True)
    nr_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf])
    nr_rg = models.CharField(max_length=30, blank=True)
    nr_cartao_sus = models.CharField(max_length=30, blank=True)
    cd_convenio = models.ForeignKey(Convenio, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_convenio")
    nr_convenio = models.CharField(max_length=50, blank=True)
    nm_convenio = models.CharField(max_length=120, blank=True)
    nr_telefone = models.CharField(max_length=30, blank=True)
    nr_celular = models.CharField(max_length=30, blank=True)
    nr_celular_2 = models.CharField(max_length=30, blank=True)
    ds_email = models.EmailField(blank=True)
    nm_mae = models.CharField(max_length=180, blank=True)
    nm_pai = models.CharField(max_length=180, blank=True)
    nm_conjuge = models.CharField(max_length=180, blank=True)
    ds_naturalidade = models.CharField(max_length=120, blank=True)
    ds_nacionalidade = models.CharField(max_length=120, blank=True)
    ds_pais_nascimento = models.CharField(max_length=40, blank=True)
    sg_uf_nascimento = models.CharField(max_length=2, blank=True)
    ds_municipio_nascimento = models.CharField(max_length=120, blank=True)
    ds_profissao = models.CharField(max_length=120, blank=True)
    ds_orgao_emissor = models.CharField(max_length=40, blank=True)
    dt_expedicao = models.DateField(null=True, blank=True)
    tp_logradouro = models.CharField(max_length=40, blank=True)
    ds_endereco = models.CharField(max_length=220, blank=True)
    nr_endereco = models.CharField(max_length=20, blank=True)
    ds_complemento = models.CharField(max_length=120, blank=True)
    ds_bairro = models.CharField(max_length=120, blank=True)
    ds_cidade = models.CharField(max_length=120, blank=True)
    sg_estado = models.CharField(max_length=2, blank=True)
    cd_cep = models.ForeignKey(Cep, null=True, blank=True, on_delete=models.PROTECT, related_name="pacientes", db_column="cd_cep")
    nr_cep = models.CharField(max_length=10, blank=True)
    ds_observacao = models.TextField(blank=True)
    sn_obito = models.BooleanField(default=False)
    dh_obito = models.DateTimeField(null=True, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "paciente"
        ordering = ("nm_paciente",)

    def __str__(self) -> str:
        return self.nm_paciente

    def save(self, *args, **kwargs):
        if self.cd_cep:
            self.nr_cep = self.cd_cep.nr_cep
        super().save(*args, **kwargs)


class HistoricoAlteracaoPaciente(models.Model):
    cd_historico_alteracao_paciente = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, db_column="cd_paciente")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario")
    cd_motivo_alteracao = models.ForeignKey(
        MotivoAlteracao,
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


class Agendamento(AuditoriaModel):
    STATUS = [
        ("AGENDADO", "Agendado"),
        ("CONFIRMADO", "Confirmado"),
        ("RECEPCIONADO", "Recepcionado"),
        ("FALTOU", "Faltou"),
        ("REAGENDADO", "Reagendado"),
        ("AGUARDANDO_PRE_ATENDIMENTO", "Aguardando pré-atendimento"),
        ("AGUARDANDO_ATENDIMENTO", "Aguardando atendimento"),
        ("EM_ATENDIMENTO", "Em atendimento"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_agendamento = models.BigAutoField(primary_key=True)
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, db_column="cd_paciente")
    cd_agenda_profissional = models.ForeignKey(AgendaProfissional, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_escala")
    cd_horario_agenda = models.ForeignKey(HorarioAgenda, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_horario_agenda", related_name="agendamentos")
    dh_agendamento = models.DateTimeField(null=True, blank=True)
    ds_tipo_atendimento = models.CharField(max_length=120, blank=True)
    ds_especialidade = models.CharField(max_length=120, blank=True)
    ds_profissional = models.CharField(max_length=120, blank=True)
    ds_observacao = models.TextField(blank=True)
    ds_plano = models.CharField(max_length=120, blank=True)
    sn_particular = models.BooleanField(default=False)
    sn_encaixe = models.BooleanField(default=False)
    sn_confirmado = models.BooleanField(default=False)
    ds_status = models.CharField(max_length=40, choices=STATUS, default="AGENDADO")

    class Meta:
        db_table = "agendamento"
        ordering = ("-dh_agendamento",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_agenda_profissional", "dh_agendamento"),
                condition=models.Q(cd_agenda_profissional__isnull=False, dh_agendamento__isnull=False) & ~models.Q(ds_status="CANCELADO"),
                name="agendamento_horario_unico",
            )
        ]


class PreAtendimento(AuditoriaModel):
    PRIORIDADES = [
        (1, "Emergência"),
        (2, "Muito urgente"),
        (3, "Urgente"),
        (4, "Pouco urgente"),
        (5, "Não urgente"),
    ]

    cd_pre_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, db_column="cd_paciente")
    cd_agendamento = models.OneToOneField(
        Agendamento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_agendamento",
        related_name="pre_atendimento",
    )
    nr_prioridade = models.PositiveSmallIntegerField(choices=PRIORIDADES, default=3)
    ds_queixa_principal = models.TextField()
    ds_sintomas = models.TextField(blank=True)
    ds_cor_prioridade = models.CharField(max_length=30, blank=True)
    cd_prestador_responsavel = models.ForeignKey(
        Prestador,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_prestador_responsavel",
        related_name="classificacoes_realizadas",
    )
    nr_pressao_arterial = models.CharField(max_length=15, blank=True)
    nr_frequencia_cardiaca = models.PositiveSmallIntegerField(null=True, blank=True)
    nr_frequencia_respiratoria = models.PositiveSmallIntegerField(null=True, blank=True)
    nr_saturacao = models.PositiveSmallIntegerField(null=True, blank=True)
    nr_temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    nr_peso = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    nr_altura = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    ds_observacao = models.TextField(blank=True)
    ds_dados_classificacao = models.JSONField(default=dict, blank=True)
    dh_inicio = models.DateTimeField(default=timezone.now)
    dh_fim = models.DateTimeField(null=True, blank=True)
    dh_classificacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pre_atendimento"
        ordering = ("nr_prioridade", "dh_classificacao")


class Atendimento(AuditoriaModel):
    STATUS = [
        ("AGENDADO", "Agendado"),
        ("RECEPCIONADO", "Recepcionado"),
        ("ABERTO", "Aberto"),
        ("AGUARDANDO_CLASSIFICACAO", "Aguardando classificação"),
        ("EM_CLASSIFICACAO", "Em classificação"),
        ("AGUARDANDO_CONSULTA", "Aguardando consulta"),
        ("EM_ATENDIMENTO", "Em atendimento"),
        ("AGUARDANDO_EXAMES", "Aguardando exames"),
        ("RETORNO_EXAMES", "Retorno de exames"),
        ("EM_OBSERVACAO", "Em observação"),
        ("ALTA_MEDICA", "Alta médica"),
        ("ALTA_HOSPITALAR", "Alta hospitalar"),
        ("FINALIZADO", "Finalizado"),
        ("ENCAMINHADO", "Encaminhado"),
        ("INTERNADO", "Internado"),
        ("ALTA", "Alta"),
        ("CANCELADO", "Cancelado"),
        ("EVADIU", "Evadiu"),
        ("OBITO", "Óbito"),
    ]
    ORIGENS = [
        ("AGENDADO", "Agendado"),
        ("DEMANDA_ESPONTANEA", "Demanda espontânea"),
        ("ENCAIXE", "Encaixe"),
        ("RETORNO", "Retorno"),
        ("URGENCIA_EMERGENCIA", "Urgência/Emergência"),
    ]
    cd_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, db_column="cd_paciente")
    cd_agendamento = models.OneToOneField(
        Agendamento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_agendamento",
        related_name="atendimento",
    )
    cd_pre_atendimento = models.OneToOneField(
        PreAtendimento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_pre_atendimento",
    )
    cd_prestador = models.ForeignKey(Prestador, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_prestador")
    cd_convenio = models.ForeignKey(Convenio, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_convenio")
    ds_status = models.CharField(max_length=40, choices=STATUS, default="ABERTO")
    ds_origem = models.CharField(max_length=30, choices=ORIGENS, default="DEMANDA_ESPONTANEA")
    ds_tipo_atendimento = models.CharField(max_length=120, blank=True)
    ds_especialidade = models.CharField(max_length=120, blank=True)
    ds_plano = models.CharField(max_length=120, blank=True)
    ds_subplano = models.CharField(max_length=120, blank=True)
    ds_recepcao_origem = models.CharField(max_length=120, blank=True)
    ds_local_procedencia = models.CharField(max_length=120, blank=True)
    ds_unidade_setor = models.CharField(max_length=120, blank=True)
    ds_cid = models.CharField(max_length=20, blank=True)
    ds_meio_transporte = models.CharField(max_length=120, blank=True)
    ds_cbo_prestador = models.CharField(max_length=20, blank=True)
    nr_senha_chamada = models.CharField(max_length=30, blank=True)
    sn_visita = models.BooleanField(default=False)
    sn_retorno = models.BooleanField(default=False)
    ds_anamnese = models.TextField(blank=True)
    ds_hipotese_diagnostica = models.TextField(blank=True)
    ds_diagnostico = models.TextField(blank=True)
    ds_conduta = models.TextField(blank=True)
    ds_destino = models.CharField(max_length=120, blank=True)
    cd_setor_atual = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor_atual")
    ds_procedimento_principal = models.CharField(max_length=160, blank=True)
    ds_motivo_atendimento = models.TextField(blank=True)
    ds_motivo_alta = models.TextField(blank=True)
    ds_queixa_principal = models.TextField(blank=True)
    ds_observacao_recepcao = models.TextField(blank=True)
    ds_motivo_cancelamento = models.TextField(blank=True)
    dh_inicio = models.DateTimeField(default=timezone.now)
    dh_fim = models.DateTimeField(null=True, blank=True)
    dh_recepcao = models.DateTimeField(null=True, blank=True)
    dh_inicio_classificacao = models.DateTimeField(null=True, blank=True)
    dh_fim_classificacao = models.DateTimeField(null=True, blank=True)
    dh_inicio_atendimento = models.DateTimeField(null=True, blank=True)
    dh_fim_atendimento = models.DateTimeField(null=True, blank=True)
    dh_alta_medica = models.DateTimeField(null=True, blank=True)
    dh_alta_hospitalar = models.DateTimeField(null=True, blank=True)
    dh_cancelamento = models.DateTimeField(null=True, blank=True)
    cd_usuario_cancelamento = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="atendimentos_cancelados")
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "atendimento"
        ordering = ("-dh_inicio",)

    def clean(self):
        super().clean()
        if self.ds_status in {"FINALIZADO", "ALTA", "ALTA_MEDICA", "ALTA_HOSPITALAR", "ENCAMINHADO", "INTERNADO"}:
            errors = {}
            if not self.cd_prestador_id:
                errors["cd_prestador"] = "Informe o profissional responsável."
            if not self.ds_diagnostico and not self.ds_hipotese_diagnostica:
                errors["ds_diagnostico"] = "Informe o diagnóstico ou a hipótese diagnóstica."
            if not self.ds_conduta:
                errors["ds_conduta"] = "Informe a conduta."
            if not self.ds_destino:
                errors["ds_destino"] = "Informe o destino do paciente."
            if errors:
                raise ValidationError(errors)


class ResponsavelAtendimento(AuditoriaModel):
    cd_responsavel_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.OneToOneField(
        Atendimento,
        on_delete=models.CASCADE,
        db_column="cd_atendimento",
        related_name="responsavel",
    )
    ds_parentesco = models.CharField(max_length=80, blank=True)
    nm_responsavel = models.CharField(max_length=160, blank=True)
    tp_estado_civil = models.CharField(max_length=80, blank=True)
    nr_identidade = models.CharField(max_length=30, blank=True)
    ds_orgao_emissor = models.CharField(max_length=30, blank=True)
    dt_expedicao = models.DateField(null=True, blank=True)
    nr_cpf = models.CharField(max_length=14, blank=True, validators=[validate_cpf])
    ds_profissao = models.CharField(max_length=120, blank=True)
    ds_nacionalidade = models.CharField(max_length=120, blank=True)
    nr_celular = models.CharField(max_length=20, blank=True)
    sn_mesmo_endereco_paciente = models.BooleanField(default=False)
    cd_cep = models.ForeignKey(Cep, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_cep")
    sg_estado = models.CharField(max_length=2, blank=True)
    ds_cidade = models.CharField(max_length=120, blank=True)
    tp_logradouro = models.CharField(max_length=80, blank=True)
    ds_endereco = models.CharField(max_length=180, blank=True)
    nr_endereco = models.CharField(max_length=20, blank=True)
    ds_complemento = models.CharField(max_length=120, blank=True)
    ds_bairro = models.CharField(max_length=120, blank=True)

    class Meta:
        db_table = "responsavel_atendimento"


class HistoricoAlteracaoAtendimento(models.Model):
    cd_historico_alteracao_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(
        Atendimento,
        related_name="historico_alteracoes",
        on_delete=models.PROTECT,
        db_column="cd_atendimento",
    )
    cd_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario",
    )
    cd_motivo_alteracao = models.ForeignKey(
        MotivoAlteracao,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_motivo_alteracao",
    )
    ds_observacao = models.TextField()
    ds_alteracoes = models.JSONField(default=dict)
    ds_antes = models.JSONField(default=dict)
    ds_depois = models.JSONField(default=dict)
    dh_alteracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historico_alteracao_atendimento"
        ordering = ("-dh_alteracao",)


class PainelChamada(AuditoriaModel):
    TIPOS = [
        ("SALA", "Sala"),
        ("CONSULTORIO", "Consultório"),
        ("GUICHE", "Guichê"),
        ("PAINEL", "Painel"),
    ]
    cd_painel_chamada = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_painel = models.CharField(max_length=120)
    ds_descricao = models.CharField(max_length=240, blank=True)
    nm_maquina = models.CharField(max_length=120)
    tp_painel = models.CharField(max_length=20, choices=TIPOS, default="PAINEL")
    nr_referencia = models.CharField(max_length=20, blank=True)
    ds_local_exibicao = models.CharField(max_length=120, blank=True)
    ds_mensagem_padrao = models.CharField(max_length=180, blank=True)
    nr_tempo_exibicao = models.PositiveSmallIntegerField(default=10)
    ds_layout = models.CharField(max_length=40, default="padrao")
    ds_tamanho = models.CharField(max_length=20, default="medio")
    ds_cor = models.CharField(max_length=20, default="azul")
    ds_prioridade_visual = models.CharField(max_length=30, default="normal")
    sn_voz = models.BooleanField(default=True)
    ds_midia_url = models.CharField(max_length=500, blank=True)
    ds_midia_arquivo = models.FileField(upload_to="painel_chamada/midia/%Y/%m/", blank=True)
    ds_configuracao = models.JSONField(default=dict, blank=True)
    ds_observacao = models.TextField(blank=True)
    sn_ativo = models.BooleanField(default=True)
    setores = models.ManyToManyField(Setor, through="PainelChamadaSetor", related_name="paineis_chamada", blank=True)

    class Meta:
        db_table = "painel_chamada"
        ordering = ("nm_painel",)
        unique_together = ("cd_empresa", "nm_maquina")

    def __str__(self) -> str:
        return self.nm_painel


class PainelChamadaSetor(models.Model):
    cd_painel_chamada_setor = models.BigAutoField(primary_key=True)
    cd_painel_chamada = models.ForeignKey(PainelChamada, on_delete=models.CASCADE, db_column="cd_painel_chamada")
    cd_setor = models.ForeignKey(Setor, on_delete=models.PROTECT, db_column="cd_setor")

    class Meta:
        db_table = "painel_chamada_setor"
        unique_together = ("cd_painel_chamada", "cd_setor")


class IconeChamada(AuditoriaModel):
    cd_icone_chamada = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_icone = models.CharField(max_length=80)
    ds_svg = models.TextField(blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "icone_chamada"
        ordering = ("nm_icone",)
        unique_together = ("cd_empresa", "nm_icone")

    def __str__(self):
        return self.nm_icone


class MaquinaChamada(AuditoriaModel):
    TIPOS_MAQUINA = [
        ("ESTACAO", "Estação"),
        ("PAINEL", "Painel"),
    ]
    TIPOS_SALA = [
        ("CONSULTORIO", "Consultório"),
        ("SALA", "Sala"),
        ("GUICHE", "Guichê"),
        ("TRIAGEM", "Triagem"),
        ("OUTRO", "Outro"),
    ]
    cd_maquina_chamada = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_maquina = models.CharField(max_length=120)
    tp_maquina = models.CharField(max_length=20, choices=TIPOS_MAQUINA, default="ESTACAO")
    cd_setor = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor")
    nm_sala = models.CharField(max_length=120, blank=True)
    tp_sala = models.CharField(max_length=20, choices=TIPOS_SALA, default="CONSULTORIO")
    nr_sala = models.CharField(max_length=20, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "maquina_chamada"
        ordering = ("nm_maquina",)
        unique_together = ("cd_empresa", "nm_maquina")

    def __str__(self):
        destino = f"{self.get_tp_sala_display()} {self.nr_sala}".strip()
        return f"{self.nm_maquina} - {destino or self.nm_sala}"


class ChamadaPainel(AuditoriaModel):
    STATUS = [
        ("CHAMADO", "Chamado"),
        ("ATENDIDO", "Atendido"),
        ("CANCELADO", "Cancelado"),
    ]
    cd_chamada_painel = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(
        Atendimento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_atendimento",
        related_name="chamadas_painel",
    )
    cd_agendamento = models.ForeignKey(
        Agendamento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_agendamento",
        related_name="chamadas_painel",
    )
    cd_setor = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor")
    cd_senha_atendimento = models.ForeignKey(
        "SenhaAtendimento",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_senha_atendimento",
        related_name="chamadas_painel",
    )
    cd_painel_chamada = models.ForeignKey(PainelChamada, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_painel_chamada")
    ds_local = models.CharField(max_length=80, blank=True)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="CHAMADO")
    dh_chamada = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "chamada_painel"
        ordering = ("-dh_chamada",)


class TipoSenhaAtendimento(AuditoriaModel):
    cd_tipo_senha = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_setor_atendimento = models.ForeignKey(
        Setor,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_setor_atendimento",
        related_name="tipos_senha",
    )
    nm_tipo_senha = models.CharField(max_length=100)
    sg_tipo_senha = models.CharField(max_length=4)
    ds_protocolo = models.CharField(max_length=160, blank=True)
    cd_protocolo = models.ForeignKey(
        "ProtocoloSenhaAtendimento",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_protocolo",
        related_name="tipos_senha",
    )
    nr_tempo_minimo = models.PositiveSmallIntegerField(default=30)
    nr_prioridade = models.PositiveSmallIntegerField(default=5)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "tipo_senha_atendimento"
        ordering = ("nr_prioridade", "nm_tipo_senha")
        unique_together = ("cd_empresa", "sg_tipo_senha")

    def __str__(self):
        return f"{self.sg_tipo_senha} - {self.nm_tipo_senha}"


class CorClassificacaoRisco(AuditoriaModel):
    cd_cor_classificacao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_cor = models.CharField(max_length=30)
    nm_cor = models.CharField(max_length=80)
    ds_cor_hex = models.CharField(max_length=7, default="#22c55e")
    nr_prioridade = models.PositiveSmallIntegerField(default=5)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "cor_classificacao_risco"
        ordering = ("nr_prioridade", "nm_cor")
        unique_together = ("cd_empresa", "cd_cor")

    def __str__(self):
        return self.nm_cor


class ClasseSenhaAtendimento(AuditoriaModel):
    cd_classe_senha = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_tipo_senha = models.ForeignKey(
        TipoSenhaAtendimento,
        related_name="classes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_tipo_senha",
    )
    nm_classe_senha = models.CharField(max_length=100)
    sg_classe_senha = models.CharField(max_length=4, blank=True)
    nr_prioridade = models.PositiveSmallIntegerField(default=5)
    ds_icone = models.CharField(max_length=40, blank=True)
    cd_icone_chamada = models.ForeignKey(
        IconeChamada,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_icone_chamada",
    )
    cd_cor_classificacao = models.ForeignKey(
        CorClassificacaoRisco,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_cor_classificacao",
        related_name="classes_senha",
    )
    nr_idade_minima = models.PositiveSmallIntegerField(null=True, blank=True)
    nr_idade_maxima = models.PositiveSmallIntegerField(null=True, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "classe_senha_atendimento"
        ordering = ("nr_prioridade", "nm_classe_senha")
        unique_together = ("cd_tipo_senha", "sg_classe_senha")

    def __str__(self):
        prefixo = self.cd_tipo_senha.sg_tipo_senha if self.cd_tipo_senha else ""
        return f"{prefixo}{self.sg_classe_senha} - {self.nm_classe_senha}"


class ProtocoloSenhaAtendimento(AuditoriaModel):
    cd_protocolo_senha = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    sg_protocolo = models.CharField(max_length=8, blank=True)
    nm_protocolo = models.CharField(max_length=120)
    ds_protocolo = models.CharField(max_length=500, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "protocolo_senha"
        ordering = ("nm_protocolo",)
        unique_together = ("cd_empresa", "nm_protocolo")

    def __str__(self):
        return self.nm_protocolo


class RegraSubdivisaoSenha(AuditoriaModel):
    cd_regra_subdivisao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_tipo_senha = models.ForeignKey(
        TipoSenhaAtendimento,
        related_name="regras_subdivisao",
        on_delete=models.CASCADE,
        db_column="cd_tipo_senha",
    )
    cd_classe_senha = models.ForeignKey(
        ClasseSenhaAtendimento,
        related_name="regras_subdivisao",
        on_delete=models.PROTECT,
        db_column="cd_classe_senha",
    )
    sg_regra = models.CharField(max_length=4, blank=True)
    nr_prioridade = models.PositiveSmallIntegerField(default=5)
    nr_idade_minima = models.PositiveSmallIntegerField(null=True, blank=True)
    nr_idade_maxima = models.PositiveSmallIntegerField(null=True, blank=True)
    ds_icone = models.CharField(max_length=40, blank=True)
    cd_icone_chamada = models.ForeignKey(
        IconeChamada,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_icone_chamada",
        related_name="regras_subdivisao",
    )
    cd_protocolo = models.ForeignKey(
        ProtocoloSenhaAtendimento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_protocolo",
        related_name="regras_subdivisao",
    )
    nr_tempo_limite = models.PositiveSmallIntegerField(default=30)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "regra_subdivisao_senha"
        ordering = ("nr_prioridade", "cd_classe_senha__nm_classe_senha")
        unique_together = ("cd_tipo_senha", "cd_classe_senha")

    def __str__(self):
        return f"{self.cd_tipo_senha} / {self.cd_classe_senha}"


class SenhaAtendimento(AuditoriaModel):
    STATUS = [
        ("AGUARDANDO", "Aguardando"),
        ("CHAMADA", "Chamada"),
        ("EM_CLASSIFICACAO", "Em classificação"),
        ("CLASSIFICADA", "Classificada"),
        ("RECEPCIONADA", "Recepcionada"),
        ("CANCELADA", "Cancelada"),
    ]
    cd_senha_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_tipo_senha = models.ForeignKey(TipoSenhaAtendimento, on_delete=models.PROTECT, db_column="cd_tipo_senha")
    cd_classe_senha = models.ForeignKey(ClasseSenhaAtendimento, on_delete=models.PROTECT, db_column="cd_classe_senha")
    cd_paciente = models.ForeignKey(
        Paciente,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_paciente",
        related_name="senhas_atendimento",
    )
    cd_pre_atendimento = models.ForeignKey(
        PreAtendimento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_pre_atendimento",
        related_name="senhas_atendimento",
    )
    cd_atendimento = models.ForeignKey(
        Atendimento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_atendimento",
        related_name="senhas_classificacao",
    )
    cd_cor_classificacao = models.ForeignKey(
        CorClassificacaoRisco,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_cor_classificacao",
        related_name="senhas_atendimento",
    )
    nm_pre_cadastro = models.CharField(max_length=160, blank=True)
    dt_nascimento_pre_cadastro = models.DateField(null=True, blank=True)
    nm_mae_pre_cadastro = models.CharField(max_length=160, blank=True)
    tp_sexo_pre_cadastro = models.CharField(max_length=30, blank=True)
    ds_dados_classificacao = models.JSONField(default=dict, blank=True)
    dt_senha = models.DateField(default=timezone.localdate)
    nr_senha = models.PositiveIntegerField()
    ds_senha = models.CharField(max_length=16)
    nr_prioridade = models.PositiveSmallIntegerField(default=5)
    nr_tempo_limite = models.PositiveSmallIntegerField(default=30)
    nr_chamadas = models.PositiveSmallIntegerField(default=0)
    ds_status = models.CharField(max_length=24, choices=STATUS, default="AGUARDANDO")
    dh_chamada = models.DateTimeField(null=True, blank=True)
    dh_recepcao = models.DateTimeField(null=True, blank=True)
    dh_classificacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "senha_atendimento"
        ordering = ("nr_prioridade", "dh_criacao")
        unique_together = ("cd_empresa", "dt_senha", "ds_senha")

    def __str__(self):
        return self.ds_senha

    @property
    def tempo_excedido(self):
        limite = self.dh_criacao + timedelta(minutes=self.nr_tempo_limite)
        return self.ds_status in {"AGUARDANDO", "CHAMADA"} and timezone.now() > limite


class PerguntaClassificacao(AuditoriaModel):
    TIPOS_RESPOSTA = [
        ("SIM_NAO", "Sim/Não"),
        ("TEXTO", "Texto"),
        ("NUMERO", "Número"),
    ]
    cd_pergunta_classificacao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_pergunta = models.CharField(max_length=240)
    tp_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA, default="SIM_NAO")
    nr_ordem = models.PositiveSmallIntegerField(default=10)
    sn_padrao = models.BooleanField(default=False)
    sn_editavel = models.BooleanField(default=True)
    sn_obrigatoria = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "pergunta_classificacao"
        ordering = ("nr_ordem", "nm_pergunta")

    def __str__(self):
        return self.nm_pergunta


class GrupoFluxoClassificacao(AuditoriaModel):
    cd_grupo_fluxo_classificacao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_grupo = models.CharField(max_length=100)
    ds_descricao = models.CharField(max_length=300, blank=True)
    nr_ordem = models.PositiveSmallIntegerField(default=10)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "grupo_fluxo_classificacao"
        ordering = ("nr_ordem", "nm_grupo")
        unique_together = ("cd_empresa", "nm_grupo")

    def __str__(self):
        return self.nm_grupo


class FluxoClassificacao(AuditoriaModel):
    cd_fluxo_classificacao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_grupo = models.ForeignKey(
        GrupoFluxoClassificacao,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_column="cd_grupo_fluxo_classificacao",
        related_name="sintomas",
    )
    nm_grupo = models.CharField(max_length=100)
    nm_fluxo = models.CharField(max_length=160)
    ds_orientacao = models.TextField(blank=True)
    cd_cor_recomendada = models.ForeignKey(
        CorClassificacaoRisco,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_cor_recomendada",
    )
    ds_configuracao = models.JSONField(default=dict, blank=True)
    nr_ordem = models.PositiveSmallIntegerField(default=10)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "fluxo_classificacao"
        ordering = ("nm_grupo", "nr_ordem", "nm_fluxo")

    def __str__(self):
        return f"{self.nm_grupo} > {self.nm_fluxo}"

    def save(self, *args, **kwargs):
        if self.cd_grupo_id:
            self.nm_grupo = self.cd_grupo.nm_grupo
        elif self.cd_empresa_id and self.nm_grupo:
            self.cd_grupo, _ = GrupoFluxoClassificacao.objects.get_or_create(
                cd_empresa_id=self.cd_empresa_id,
                nm_grupo=self.nm_grupo.strip(),
                defaults={"nr_ordem": self.nr_ordem, "sn_ativo": True},
            )
            self.nm_grupo = self.cd_grupo.nm_grupo
        super().save(*args, **kwargs)


class AtendimentoFluxo(models.Model):
    cd_atendimento_fluxo = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, db_column="cd_atendimento", related_name="fluxos")
    ds_status_anterior = models.CharField(max_length=40, blank=True)
    ds_status_novo = models.CharField(max_length=40)
    cd_setor = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor")
    cd_prestador = models.ForeignKey(Prestador, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_prestador")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario")
    dh_evento = models.DateTimeField(default=timezone.now)
    ds_observacao = models.TextField(blank=True)
    ds_origem = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = "atendimento_fluxo"
        ordering = ("-dh_evento",)


class AtendimentoPrestador(AuditoriaModel):
    PAPEIS = [
        ("MEDICO", "Médico"),
        ("ENFERMAGEM", "Enfermagem"),
        ("LABORATORIO", "Laboratório"),
        ("FISIOTERAPIA", "Fisioterapia"),
        ("NUTRICAO", "Nutrição"),
        ("PSICOLOGIA", "Psicologia"),
        ("OUTRO", "Outro profissional"),
    ]
    cd_atendimento_prestador = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, db_column="cd_atendimento", related_name="prestadores_vinculados")
    cd_prestador = models.ForeignKey(Prestador, on_delete=models.PROTECT, db_column="cd_prestador")
    tp_papel = models.CharField(max_length=30, choices=PAPEIS, default="MEDICO")
    dh_inicio = models.DateTimeField(default=timezone.now)
    dh_fim = models.DateTimeField(null=True, blank=True)
    sn_responsavel_principal = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "atendimento_prestador"
        ordering = ("-sn_responsavel_principal", "dh_inicio")


class AtendimentoProcedimento(AuditoriaModel):
    cd_atendimento_procedimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, db_column="cd_atendimento", related_name="procedimentos")
    ds_procedimento = models.CharField(max_length=160)
    nr_quantidade = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    vl_procedimento = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cd_prestador_executante = models.ForeignKey(Prestador, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_prestador_executante")
    cd_usuario_lancamento = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario_lancamento")
    dh_lancamento = models.DateTimeField(default=timezone.now)
    sn_principal = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "atendimento_procedimento"
        ordering = ("-sn_principal", "-dh_lancamento")


class SolicitacaoExame(AuditoriaModel):
    STATUS = [("SOLICITADO", "Solicitado"), ("COLETADO", "Coletado"), ("EM_ANALISE", "Em análise"), ("LIBERADO", "Liberado"), ("CANCELADO", "Cancelado")]
    PRIORIDADES = [("ROTINA", "Rotina"), ("URGENTE", "Urgente"), ("EMERGENCIA", "Emergência")]

    cd_solicitacao_exame = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, related_name="solicitacoes_exames", on_delete=models.PROTECT, db_column="cd_atendimento")
    ds_exame = models.CharField(max_length=180)
    ds_justificativa = models.TextField(blank=True)
    ds_prioridade = models.CharField(max_length=20, choices=PRIORIDADES, default="ROTINA")
    ds_status = models.CharField(max_length=20, choices=STATUS, default="SOLICITADO")

    class Meta:
        db_table = "solicitacao_exame"
        ordering = ("-dh_criacao",)


class ResultadoExame(AuditoriaModel):
    cd_resultado_exame = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_solicitacao_exame = models.OneToOneField(SolicitacaoExame, related_name="resultado", on_delete=models.PROTECT, db_column="cd_solicitacao_exame")
    ds_resultado = models.TextField(blank=True)
    ds_anexo = models.FileField(upload_to="resultados_exames/", blank=True)
    sn_liberado = models.BooleanField(default=False)
    dh_liberacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "resultado_exame"


class Prescricao(AuditoriaModel):
    cd_prescricao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, related_name="prescricoes", on_delete=models.PROTECT, db_column="cd_atendimento")
    ds_prescricao = models.TextField()
    ds_orientacoes = models.TextField(blank=True)
    sn_ativa = models.BooleanField(default=True)

    class Meta:
        db_table = "prescricao"
        ordering = ("-dh_criacao",)


class EvolucaoAtendimento(AuditoriaModel):
    cd_evolucao_atendimento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, related_name="evolucoes", on_delete=models.PROTECT, db_column="cd_atendimento")
    cd_prestador = models.ForeignKey(Prestador, on_delete=models.PROTECT, db_column="cd_prestador")
    ds_evolucao = models.TextField()

    class Meta:
        db_table = "evolucao_atendimento"
        ordering = ("-dh_criacao",)


class PastaDocumento(AuditoriaModel):
    TIPOS = [
        ("GERAL", "Geral"),
        ("CABECALHOS", "Cabeçalhos"),
        ("RODAPES", "Rodapés"),
        ("ADMISSAO", "Documentos de admissão"),
        ("ALTA", "Documentos de alta"),
    ]

    cd_pasta_documento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_pasta_pai = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_pasta_pai", related_name="subpastas")
    nm_pasta = models.CharField(max_length=120)
    tp_pasta = models.CharField(max_length=20, choices=TIPOS, default="GERAL")
    nr_ordem = models.PositiveIntegerField(default=0)
    sn_sistema = models.BooleanField(default=False)
    sn_editavel = models.BooleanField(default=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "pasta_documento"
        ordering = ("nr_ordem", "nm_pasta")
        constraints = [
            models.UniqueConstraint(fields=("cd_empresa", "cd_pasta_pai", "nm_pasta"), name="pasta_documento_unica")
        ]

    def __str__(self):
        return self.nm_pasta

    @property
    def caminho_arvore(self):
        nomes = [self.nm_pasta]
        pasta = self.cd_pasta_pai
        while pasta:
            nomes.insert(0, pasta.nm_pasta)
            pasta = pasta.cd_pasta_pai
        return " / ".join(nomes)

    @property
    def nivel_arvore(self):
        nivel = 0
        pasta = self.cd_pasta_pai
        while pasta:
            nivel += 1
            pasta = pasta.cd_pasta_pai
        return nivel


class ModeloDocumento(AuditoriaModel):
    FINALIDADES_ASSINATURA = [
        ("MEDICO", "Documento médico"),
        ("ADMINISTRATIVO", "Documento administrativo"),
        ("OUTRO", "Outro documento"),
    ]
    ALINHAMENTOS_ASSINATURA = [
        ("ESQUERDA", "Esquerda"),
        ("CENTRO", "Centralizada"),
        ("DIREITA", "Direita"),
    ]
    TIPOS = [
        ("COMPROVANTE_AGENDAMENTO", "Comprovante de agendamento"),
        ("COMPROVANTE_CHAMADO", "Comprovante de chamado"),
        ("FICHA_CLASSIFICACAO", "Ficha de classificação"),
        ("FICHA_ATENDIMENTO", "Ficha de atendimento"),
        ("ETIQUETA_ATENDIMENTO", "Etiqueta de atendimento"),
        ("PRESCRICAO", "Prescrição"),
        ("SOLICITACAO_EXAME", "Solicitação de exame"),
        ("EVOLUCAO", "Evolução"),
        ("RESUMO_ALTA", "Resumo de alta"),
        ("RECEITUARIO", "Receituário"),
        ("ATESTADO", "Atestado"),
        ("ENCAMINHAMENTO", "Encaminhamento"),
        ("ADMINISTRATIVO", "Administrativo"),
    ]
    ELEMENTOS = [
        ("DOCUMENTO", "Documento"),
        ("CABECALHO", "Cabeçalho"),
        ("RODAPE", "Rodapé"),
        ("CAMPO", "Campo reutilizável"),
        ("VARIAVEL", "Variável personalizada"),
        ("BLOCO", "Bloco reutilizável"),
    ]
    cd_modelo_documento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_pasta = models.ForeignKey(PastaDocumento, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_pasta")
    cd_cabecalho = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_cabecalho", related_name="documentos_cabecalho")
    cd_rodape = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_rodape", related_name="documentos_rodape")
    cd_versao_anterior = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, db_column="cd_versao_anterior", related_name="versoes_seguintes")
    nm_modelo = models.CharField(max_length=140)
    tp_documento = models.CharField(max_length=40, choices=TIPOS)
    tp_elemento = models.CharField(max_length=20, choices=ELEMENTOS, default="DOCUMENTO")
    nr_versao = models.PositiveIntegerField(default=1)
    ds_alteracoes_versao = models.CharField(max_length=500, blank=True)
    ds_html_tela = models.TextField(blank=True)
    ds_css_tela = models.TextField(blank=True)
    ds_projeto_tela = models.JSONField(default=dict, blank=True)
    ds_html_impressao = models.TextField(blank=True)
    ds_css_impressao = models.TextField(blank=True)
    ds_projeto_impressao = models.JSONField(default=dict, blank=True)
    ds_cabecalho = models.TextField(blank=True)
    ds_corpo = models.TextField(blank=True)
    ds_rodape = models.TextField(blank=True)
    ds_variaveis = models.JSONField(default=list, blank=True)
    ds_campos_bloqueados = models.JSONField(default=list, blank=True)
    sn_exibe_assinatura = models.BooleanField(default=True)
    tp_alinhamento_assinatura = models.CharField(
        max_length=10,
        choices=ALINHAMENTOS_ASSINATURA,
        default="CENTRO",
    )
    sn_exibe_conselho_assinatura = models.BooleanField(default=False)
    tp_finalidade_assinatura = models.CharField(
        max_length=20,
        choices=FINALIDADES_ASSINATURA,
        default="MEDICO",
    )
    sn_versao_atual = models.BooleanField(default=True)
    sn_sistema = models.BooleanField(default=False)
    sn_editavel = models.BooleanField(default=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "modelo_documento"
        ordering = ("tp_documento", "nm_modelo")
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "tp_documento", "nm_modelo", "nr_versao"),
                name="modelo_documento_versao_unica",
            )
        ]

    def __str__(self):
        return self.nm_modelo


class ModeloDocumentoTelaImpressao(AuditoriaModel):
    cd_modelo_documento_tela = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_modelo_documento = models.ForeignKey(
        ModeloDocumento,
        on_delete=models.CASCADE,
        db_column="cd_modelo_documento",
        related_name="telas_impressao",
    )
    cd_tela = models.ForeignKey(
        ScreenDefinition,
        on_delete=models.PROTECT,
        db_column="cd_tela",
        related_name="modelos_documento_impressao",
    )
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "modelo_documento_tela_impressao"
        ordering = ("cd_tela__module__order", "cd_tela__order", "cd_tela__title")
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_modelo_documento", "cd_tela"),
                name="modelo_documento_tela_impressao_unica",
            )
        ]

    def __str__(self):
        return f"{self.cd_modelo_documento} - {self.cd_tela}"


class PerfilAssistencial(AuditoriaModel):
    cd_perfil_assistencial = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_perfil = models.CharField(max_length=120)
    ds_descricao = models.CharField(max_length=300, blank=True)
    sn_ativo = models.BooleanField(default=True)
    sn_sigiloso = models.BooleanField(default=False)
    tipos_prestador = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "perfil_assistencial"
        ordering = ("nm_perfil",)
        unique_together = ("cd_empresa", "nm_perfil")

    def __str__(self):
        return self.nm_perfil


class PerfilAssistencialVersao(AuditoriaModel):
    STATUS = [
        ("RASCUNHO", "Rascunho"),
        ("PUBLICADO", "Publicado"),
        ("ARQUIVADO", "Arquivado"),
    ]
    cd_perfil_assistencial_versao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_perfil_assistencial = models.ForeignKey(
        PerfilAssistencial,
        on_delete=models.CASCADE,
        db_column="cd_perfil_assistencial",
        related_name="versoes",
    )
    nr_versao = models.PositiveIntegerField(default=1)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="RASCUNHO")
    ds_descricao_versao = models.CharField(max_length=500, blank=True)
    ds_configuracao = models.JSONField(default=dict, blank=True)
    dh_publicacao = models.DateTimeField(null=True, blank=True)
    cd_usuario_publicacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario_publicacao",
        related_name="perfis_assistenciais_publicados",
    )

    class Meta:
        db_table = "perfil_assistencial_versao"
        ordering = ("-nr_versao",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_perfil_assistencial", "nr_versao"),
                name="perfil_assistencial_versao_unica",
            ),
            models.UniqueConstraint(
                fields=("cd_perfil_assistencial",),
                condition=models.Q(ds_status="PUBLICADO"),
                name="perfil_assistencial_publicado_unico",
            ),
        ]

    def __str__(self):
        return f"{self.cd_perfil_assistencial} v{self.nr_versao}"


class PerfilAssistencialTipo(AuditoriaModel):
    cd_perfil_assistencial_tipo = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_perfil_assistencial = models.ForeignKey(
        PerfilAssistencial,
        on_delete=models.CASCADE,
        db_column="cd_perfil_assistencial",
        related_name="tipos_vinculados",
    )
    cd_tipo_prestador = models.CharField(max_length=60)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "perfil_assistencial_tipo"
        ordering = ("cd_tipo_prestador",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_tipo_prestador"),
                condition=models.Q(sn_ativo=True),
                name="perfil_tipo_prestador_unico_empresa",
            ),
        ]

    def __str__(self):
        return f"{self.cd_perfil_assistencial} - {self.cd_tipo_prestador}"


class ItemMenuAssistencial(AuditoriaModel):
    TIPOS = [
        ("GRUPO", "Grupo"),
        ("ACAO", "Ação do sistema"),
        ("DOCUMENTO", "Modelo de documento"),
        ("LINK_EXTERNO", "Link externo"),
        ("ANCORA", "Seção da ficha"),
        ("ESCALA", "Escala clínica"),
        ("ANEXO", "Anexo clínico"),
        ("HISTORICO", "Histórico somente leitura"),
    ]
    cd_item_menu_assistencial = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_perfil_assistencial = models.ForeignKey(
        PerfilAssistencial,
        on_delete=models.CASCADE,
        db_column="cd_perfil_assistencial",
        related_name="itens",
    )
    cd_item_pai = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_column="cd_item_pai",
        related_name="filhos",
    )
    cd_modelo_documento = models.ForeignKey(
        ModeloDocumento,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_modelo_documento",
    )
    cd_versao_perfil = models.ForeignKey(
        PerfilAssistencialVersao,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_column="cd_versao_perfil",
        related_name="itens",
    )
    cd_item_tecnico = models.CharField(max_length=100, blank=True)
    nm_item = models.CharField(max_length=120)
    ds_icone = models.CharField(max_length=40, blank=True)
    nr_ordem = models.PositiveSmallIntegerField(default=0)
    tp_item = models.CharField(max_length=20, choices=TIPOS, default="ACAO")
    ds_acao = models.CharField(max_length=60, blank=True)
    ds_url = models.CharField(max_length=500, blank=True)
    sn_privado = models.BooleanField(default=False)
    sn_imprimivel = models.BooleanField(default=True)
    sn_permite_criar = models.BooleanField(default=True)
    sn_permite_abandonar = models.BooleanField(default=True)
    sn_permite_cancelar = models.BooleanField(default=False)
    sn_somente_historico = models.BooleanField(default=False)
    ds_configuracao = models.JSONField(default=dict, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "item_menu_assistencial"
        ordering = ("nr_ordem", "nm_item")

    def __str__(self):
        return self.nm_item


class DocumentoClinico(AuditoriaModel):
    STATUS = [
        ("ABERTO", "Aberto"),
        ("FECHADO", "Fechado"),
        ("ABANDONADO", "Abandonado"),
        ("RASCUNHO", "Rascunho"),
        ("FINALIZADO", "Finalizado"),
        ("ASSINADO", "Assinado"),
        ("CANCELADO", "Cancelado"),
    ]
    cd_documento_clinico = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, on_delete=models.PROTECT, db_column="cd_atendimento", related_name="documentos")
    cd_modelo_documento = models.ForeignKey(ModeloDocumento, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_modelo_documento")
    cd_documento_origem = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_documento_origem")
    cd_item_menu_assistencial = models.ForeignKey(
        ItemMenuAssistencial,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_item_menu_assistencial",
        related_name="documentos",
    )
    cd_versao_perfil = models.ForeignKey(
        PerfilAssistencialVersao,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_versao_perfil",
        related_name="documentos",
    )
    tp_documento = models.CharField(max_length=40)
    ds_titulo = models.CharField(max_length=160)
    ds_conteudo = models.TextField(blank=True)
    ds_dados_formulario = models.JSONField(default=dict, blank=True)
    ds_campos_bloqueados = models.JSONField(default=dict, blank=True)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="ABERTO")
    dh_emissao = models.DateTimeField(default=timezone.now)
    dh_finalizacao = models.DateTimeField(null=True, blank=True)
    dh_assinatura = models.DateTimeField(null=True, blank=True)
    dh_cancelamento = models.DateTimeField(null=True, blank=True)
    cd_usuario_emissor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario_emissor", related_name="documentos_emitidos")
    cd_usuario_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario_responsavel",
        related_name="documentos_clinicos_responsaveis",
    )
    cd_usuario_cancelamento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario_cancelamento",
        related_name="documentos_clinicos_cancelados",
    )
    ds_hash_conteudo = models.CharField(max_length=64, blank=True)
    ds_motivo_cancelamento = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "documento_clinico"
        ordering = ("-dh_emissao",)

    def save(self, *args, **kwargs):
        if self.pk:
            anterior = type(self).objects.filter(pk=self.pk).values(
                "ds_status",
                "ds_conteudo",
                "ds_dados_formulario",
                "cd_modelo_documento_id",
                "cd_atendimento_id",
            ).first()
            if anterior and anterior["ds_status"] in {"FECHADO", "FINALIZADO", "ASSINADO", "CANCELADO", "ABANDONADO"}:
                imutaveis = {
                    "ds_conteudo": self.ds_conteudo,
                    "ds_dados_formulario": self.ds_dados_formulario,
                    "cd_modelo_documento_id": self.cd_modelo_documento_id,
                    "cd_atendimento_id": self.cd_atendimento_id,
                }
                if any(anterior[campo] != valor for campo, valor in imutaveis.items()):
                    raise ValidationError("Documentos fechados, cancelados ou abandonados são imutáveis.")
        super().save(*args, **kwargs)


class VersaoDocumentoClinico(models.Model):
    STATUS = [
        ("FINALIZADO", "Finalizado"),
        ("ASSINADO", "Assinado"),
        ("FALHA", "Falha"),
    ]

    cd_versao_documento_clinico = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_documento_clinico = models.ForeignKey(
        DocumentoClinico,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
        related_name="versoes_finais",
    )
    nr_versao = models.PositiveIntegerField()
    ds_status = models.CharField(max_length=20, choices=STATUS)
    arquivo_pdf = models.BinaryField()
    ds_hash_sha256 = models.CharField(max_length=64, db_index=True)
    nr_tamanho_bytes = models.PositiveBigIntegerField()
    nr_paginas = models.PositiveIntegerField(default=1)
    ds_mime_type = models.CharField(max_length=80, default="application/pdf")
    ds_motivo_versao = models.CharField(max_length=500, blank=True)
    cd_versao_anterior = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_versao_anterior",
        related_name="versoes_seguintes",
    )
    cd_usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario_criacao",
        related_name="versoes_documentos_clinicos_criadas",
    )
    dh_criacao = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "versao_documento_clinico"
        ordering = ("-nr_versao",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_documento_clinico", "nr_versao"),
                name="versao_documento_clinico_unica",
            ),
        ]

    def clean(self):
        if self.cd_documento_clinico_id and self.cd_empresa_id != self.cd_documento_clinico.cd_empresa_id:
            raise ValidationError("A versão final deve pertencer à mesma empresa do documento.")
        if self.cd_versao_anterior_id:
            anterior = self.cd_versao_anterior
            documento_anterior_id = self.cd_documento_clinico.cd_documento_origem_id
            if anterior.cd_documento_clinico_id not in {
                self.cd_documento_clinico_id,
                documento_anterior_id,
            }:
                raise ValidationError("A versão anterior deve pertencer ao documento ou à sua origem imediata.")

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Versões finais de documentos são imutáveis.")
        self.full_clean()
        super().save(*args, **kwargs)


class AssinaturaDigitalDocumento(models.Model):
    STATUS = [
        ("VALIDA", "Válida"),
        ("FALHA", "Falha"),
        ("REVOGADA", "Revogada"),
    ]

    cd_assinatura_digital = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_versao_documento = models.OneToOneField(
        VersaoDocumentoClinico,
        on_delete=models.PROTECT,
        db_column="cd_versao_documento",
        related_name="assinatura_digital",
    )
    cd_certificado_digital = models.ForeignKey(
        "core.CertificadoDigitalEmpresa",
        on_delete=models.PROTECT,
        db_column="cd_certificado_digital",
        related_name="assinaturas_documentos",
    )
    cd_usuario_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario_solicitante",
        related_name="assinaturas_digitais_solicitadas",
    )
    tp_finalidade = models.CharField(max_length=20)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="VALIDA")
    ds_sujeito = models.CharField(max_length=500)
    ds_emissor = models.CharField(max_length=500)
    nr_serie = models.CharField(max_length=160)
    ds_fingerprint_sha256 = models.CharField(max_length=95)
    ds_hash_pdf_assinado = models.CharField(max_length=64)
    dh_assinatura = models.DateTimeField(default=timezone.now, editable=False)
    ds_ip = models.GenericIPAddressField(null=True, blank=True)
    ds_user_agent = models.CharField(max_length=500, blank=True)
    ds_detalhes = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "assinatura_digital_documento"
        ordering = ("-dh_assinatura",)

    def clean(self):
        if self.cd_versao_documento_id and self.cd_empresa_id != self.cd_versao_documento.cd_empresa_id:
            raise ValidationError("A assinatura deve pertencer à mesma empresa da versão do documento.")
        if self.cd_certificado_digital_id and self.cd_empresa_id != self.cd_certificado_digital.cd_empresa_id:
            raise ValidationError("O certificado da assinatura não pertence à empresa do documento.")

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Registros de assinatura digital são imutáveis.")
        self.full_clean()
        super().save(*args, **kwargs)


class AuditoriaAssinaturaDigital(models.Model):
    cd_auditoria_assinatura = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_documento_clinico = models.ForeignKey(
        DocumentoClinico,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
        related_name="auditorias_assinatura",
    )
    cd_certificado_digital = models.ForeignKey(
        "core.CertificadoDigitalEmpresa",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_certificado_digital",
        related_name="auditorias_assinatura",
    )
    cd_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario",
    )
    tp_evento = models.CharField(max_length=60)
    ds_status = models.CharField(max_length=20)
    ds_mensagem = models.CharField(max_length=500, blank=True)
    ds_hash_pdf = models.CharField(max_length=64, blank=True)
    ds_ip = models.GenericIPAddressField(null=True, blank=True)
    ds_user_agent = models.CharField(max_length=500, blank=True)
    ds_dados = models.JSONField(default=dict, blank=True)
    dh_evento = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "auditoria_assinatura_digital"
        ordering = ("-dh_evento",)


class EventoDocumentoClinico(models.Model):
    TIPOS = [
        ("CRIADO", "Criado"),
        ("ATUALIZADO", "Atualizado"),
        ("ASSUMIDO", "Assumido"),
        ("FECHADO", "Fechado"),
        ("ABANDONADO", "Abandonado"),
        ("CANCELADO", "Cancelado"),
        ("ACESSO_EXCEPCIONAL", "Acesso excepcional"),
        ("IMPRESSO", "Impresso"),
    ]
    cd_evento_documento_clinico = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_documento_clinico = models.ForeignKey(
        DocumentoClinico,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
        related_name="eventos",
    )
    cd_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="cd_usuario",
    )
    tp_evento = models.CharField(max_length=30, choices=TIPOS)
    ds_motivo = models.CharField(max_length=500, blank=True)
    ds_dados = models.JSONField(default=dict, blank=True)
    dh_evento = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "evento_documento_clinico"
        ordering = ("-dh_evento",)


class RascunhoEditorDocumento(models.Model):
    cd_rascunho_editor_documento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="cd_empresa")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="cd_usuario")
    cd_modelo_documento = models.ForeignKey(
        ModeloDocumento,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        db_column="cd_modelo_documento",
    )
    ds_chave_guia = models.CharField(max_length=180)
    ds_estado = models.JSONField(default=dict)
    dh_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rascunho_editor_documento"
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_usuario", "cd_modelo_documento", "ds_chave_guia"),
                name="rascunho_editor_unico",
            ),
        ]


class DominioExternoPermitido(AuditoriaModel):
    cd_dominio_externo_permitido = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, db_column="cd_empresa")
    ds_dominio = models.CharField(max_length=253)
    sn_permite_iframe = models.BooleanField(default=False)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "dominio_externo_permitido"
        ordering = ("ds_dominio",)
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "ds_dominio"),
                name="dominio_externo_empresa_unico",
            ),
        ]


class EscalaClinica(AuditoriaModel):
    METODOS = [("SOMA", "Soma"), ("MEDIA", "Média")]
    cd_escala_clinica = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_escala = models.CharField(max_length=160)
    ds_descricao = models.CharField(max_length=500, blank=True)
    tp_calculo = models.CharField(max_length=10, choices=METODOS, default="SOMA")
    ds_expressao_calculo = models.CharField(max_length=1000, blank=True)
    ds_condicoes_calculo = models.JSONField(default=list, blank=True)
    ds_perguntas = models.JSONField(default=list)
    ds_faixas_resultado = models.JSONField(default=list)
    nr_versao = models.PositiveIntegerField(default=1)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "escala_clinica"
        ordering = ("nm_escala", "-nr_versao")
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "nm_escala", "nr_versao"),
                name="escala_clinica_versao_unica",
            ),
        ]


class FluxoClassificacaoEscala(AuditoriaModel):
    cd_fluxo_classificacao_escala = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_fluxo_classificacao = models.ForeignKey(
        FluxoClassificacao,
        on_delete=models.CASCADE,
        db_column="cd_fluxo_classificacao",
        related_name="escalas_recomendadas",
    )
    cd_escala_clinica = models.ForeignKey(
        EscalaClinica,
        on_delete=models.PROTECT,
        db_column="cd_escala_clinica",
        related_name="fluxos_recomendados",
    )
    nr_ordem = models.PositiveSmallIntegerField(default=10)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "fluxo_classificacao_escala"
        ordering = ("nr_ordem", "cd_fluxo_classificacao_escala")
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "cd_fluxo_classificacao", "cd_escala_clinica"),
                name="fluxo_classificacao_escala_unica",
            ),
        ]


class ResultadoEscalaClinica(AuditoriaModel):
    cd_resultado_escala_clinica = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(
        Atendimento,
        on_delete=models.PROTECT,
        db_column="cd_atendimento",
        related_name="resultados_escalas",
    )
    cd_escala_clinica = models.ForeignKey(EscalaClinica, on_delete=models.PROTECT, db_column="cd_escala_clinica")
    cd_documento_clinico = models.OneToOneField(
        DocumentoClinico,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
        related_name="resultado_escala",
    )
    ds_respostas = models.JSONField(default=dict)
    nr_resultado = models.DecimalField(max_digits=10, decimal_places=2)
    ds_classificacao = models.CharField(max_length=160)
    ds_cor = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "resultado_escala_clinica"
        ordering = ("-dh_criacao",)


def caminho_anexo_clinico(instance, filename):
    return (
        f"clinico/empresa_{instance.cd_empresa_id}/atendimento_{instance.cd_atendimento_id}/"
        f"{timezone.now():%Y/%m}/{filename}"
    )


class AnexoClinico(AuditoriaModel):
    cd_anexo_clinico = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(
        Atendimento,
        on_delete=models.PROTECT,
        db_column="cd_atendimento",
        related_name="anexos_clinicos",
    )
    cd_documento_clinico = models.ForeignKey(
        DocumentoClinico,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
        related_name="anexos",
    )
    cd_item_menu_assistencial = models.ForeignKey(
        ItemMenuAssistencial,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_item_menu_assistencial",
        related_name="anexos_clinicos",
    )
    nm_arquivo = models.CharField(max_length=255)
    ds_tipo_mime = models.CharField(max_length=120)
    nr_tamanho = models.PositiveBigIntegerField()
    ds_checksum_sha256 = models.CharField(max_length=64)
    ds_arquivo = models.FileField(
        upload_to=caminho_anexo_clinico,
        storage=armazenamento_clinico_privado,
    )
    ds_status_antivirus = models.CharField(max_length=20, default="PENDENTE")
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "anexo_clinico"
        ordering = ("-dh_criacao",)


class AcessoClinicoAuditado(models.Model):
    TIPOS = [
        ("VISUALIZACAO", "Visualização"),
        ("DOWNLOAD", "Download"),
        ("ACESSO_EXCEPCIONAL", "Acesso excepcional"),
    ]
    cd_acesso_clinico_auditado = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, db_column="cd_usuario")
    cd_documento_clinico = models.ForeignKey(
        DocumentoClinico,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_documento_clinico",
    )
    cd_anexo_clinico = models.ForeignKey(
        AnexoClinico,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="cd_anexo_clinico",
    )
    tp_acesso = models.CharField(max_length=30, choices=TIPOS)
    ds_motivo = models.CharField(max_length=500, blank=True)
    ds_ip = models.GenericIPAddressField(null=True, blank=True)
    dh_acesso = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "acesso_clinico_auditado"
        ordering = ("-dh_acesso",)
