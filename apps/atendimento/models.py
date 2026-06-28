from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import Empresa, Setor
from apps.core.models import Cep, ValorAuxiliarGlobal
from apps.core.validators import validate_cpf


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
            ValorAuxiliarGlobal.objects.filter(
                cd_tabela_auxiliar_global__ds_tabela="especialidade",
                cd_valor__in=codes,
            )
            .order_by("ds_valor")
            .values_list("ds_valor", flat=True)
        )
        return ", ".join(descriptions or codes)


class AgendaProfissional(AuditoriaModel):
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


class Paciente(AuditoriaModel):
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
    cd_agenda_profissional = models.ForeignKey(AgendaProfissional, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_agenda_profissional")
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
                condition=models.Q(cd_agenda_profissional__isnull=False, dh_agendamento__isnull=False),
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
    ds_unidade_setor = models.CharField(max_length=120, blank=True)
    ds_anamnese = models.TextField(blank=True)
    ds_hipotese_diagnostica = models.TextField(blank=True)
    ds_diagnostico = models.TextField(blank=True)
    ds_conduta = models.TextField(blank=True)
    ds_destino = models.CharField(max_length=120, blank=True)
    cd_setor_atual = models.ForeignKey(Setor, null=True, blank=True, on_delete=models.PROTECT, db_column="cd_setor_atual")
    ds_procedimento_principal = models.CharField(max_length=160, blank=True)
    ds_motivo_atendimento = models.TextField(blank=True)
    ds_queixa_principal = models.TextField(blank=True)
    ds_observacao_recepcao = models.TextField(blank=True)
    ds_motivo_cancelamento = models.TextField(blank=True)
    dh_inicio = models.DateTimeField(auto_now_add=True)
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


class ChamadaPainel(AuditoriaModel):
    STATUS = [
        ("CHAMADO", "Chamado"),
        ("ATENDIDO", "Atendido"),
        ("CANCELADO", "Cancelado"),
    ]
    cd_chamada_painel = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    cd_atendimento = models.ForeignKey(Atendimento, on_delete=models.PROTECT, db_column="cd_atendimento", related_name="chamadas_painel")
    cd_setor = models.ForeignKey(Setor, on_delete=models.PROTECT, db_column="cd_setor")
    cd_painel_chamada = models.ForeignKey(PainelChamada, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_painel_chamada")
    ds_local = models.CharField(max_length=80, blank=True)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="CHAMADO")
    dh_chamada = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "chamada_painel"
        ordering = ("-dh_chamada",)


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


class ModeloDocumento(AuditoriaModel):
    TIPOS = [
        ("COMPROVANTE_AGENDAMENTO", "Comprovante de agendamento"),
        ("FICHA_ATENDIMENTO", "Ficha de atendimento"),
        ("PRESCRICAO", "Prescrição"),
        ("SOLICITACAO_EXAME", "Solicitação de exame"),
        ("EVOLUCAO", "Evolução"),
        ("RESUMO_ALTA", "Resumo de alta"),
        ("RECEITUARIO", "Receituário"),
        ("ATESTADO", "Atestado"),
        ("ENCAMINHAMENTO", "Encaminhamento"),
        ("ADMINISTRATIVO", "Administrativo"),
    ]
    cd_modelo_documento = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, db_column="cd_empresa")
    nm_modelo = models.CharField(max_length=140)
    tp_documento = models.CharField(max_length=40, choices=TIPOS)
    ds_cabecalho = models.TextField(blank=True)
    ds_corpo = models.TextField(blank=True)
    ds_rodape = models.TextField(blank=True)
    ds_variaveis = models.JSONField(default=list, blank=True)
    ds_campos_bloqueados = models.JSONField(default=list, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "modelo_documento"
        ordering = ("tp_documento", "nm_modelo")
        unique_together = ("cd_empresa", "tp_documento", "nm_modelo")


class DocumentoClinico(AuditoriaModel):
    STATUS = [
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
    tp_documento = models.CharField(max_length=40)
    ds_titulo = models.CharField(max_length=160)
    ds_conteudo = models.TextField(blank=True)
    ds_campos_bloqueados = models.JSONField(default=dict, blank=True)
    ds_status = models.CharField(max_length=20, choices=STATUS, default="RASCUNHO")
    dh_emissao = models.DateTimeField(default=timezone.now)
    dh_finalizacao = models.DateTimeField(null=True, blank=True)
    dh_assinatura = models.DateTimeField(null=True, blank=True)
    dh_cancelamento = models.DateTimeField(null=True, blank=True)
    cd_usuario_emissor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, db_column="cd_usuario_emissor", related_name="documentos_emitidos")

    class Meta:
        db_table = "documento_clinico"
        ordering = ("-dh_emissao",)
