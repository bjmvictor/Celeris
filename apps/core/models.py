from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class Module(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=50, default="grid", blank=True)
    order = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    is_system = models.BooleanField(
        "módulo estrutural",
        default=False,
        help_text="Impede alterações pela interface de configuração.",
    )

    class Meta:
        db_table = "modulo"
        ordering = ("order", "title")

    def __str__(self) -> str:
        return self.title


class IconeSistema(TimeStampedModel):
    cd_icone_sistema = models.BigAutoField(primary_key=True)
    cd_icone = models.CharField(max_length=50, unique=True)
    nm_icone = models.CharField(max_length=80, unique=True)
    ds_svg = models.TextField(blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "icone_sistema"
        ordering = ("nm_icone",)

    def __str__(self) -> str:
        return self.nm_icone


class UserModule(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        db_table = "modulo_usuario"
        unique_together = ("user", "module")


class CatalogoTematico(TimeStampedModel):
    cd_item_catalogo = models.BigAutoField(primary_key=True)
    cd_valor = models.CharField(max_length=40, unique=True)
    ds_valor = models.CharField(max_length=500)
    ds_grupo = models.CharField(max_length=160, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ("ds_valor",)

    def __str__(self) -> str:
        return f"{self.cd_valor} - {self.ds_valor}"


def _modelo_catalogo(nome: str, tabela: str):
    meta = type("Meta", (), {"db_table": tabela, "ordering": ("ds_valor",)})
    return type(nome, (CatalogoTematico,), {"__module__": __name__, "Meta": meta})


Bairro = _modelo_catalogo("Bairro", "bairros")
Banco = _modelo_catalogo("Banco", "bancos")
Cbo = _modelo_catalogo("Cbo", "cbos")
Cidade = _modelo_catalogo("Cidade", "cidades")
Cid = _modelo_catalogo("Cid", "cids")
ConselhoProfissional = _modelo_catalogo("ConselhoProfissional", "conselhos_profissionais")
CorRaca = _modelo_catalogo("CorRaca", "cores_racas")
DestinoAtendimento = _modelo_catalogo("DestinoAtendimento", "destinos_atendimento")
Especialidade = _modelo_catalogo("Especialidade", "especialidades")
Estado = _modelo_catalogo("Estado", "estados")
EstadoCivil = _modelo_catalogo("EstadoCivil", "estados_civis")
Feriado = _modelo_catalogo("Feriado", "feriados")
Genero = _modelo_catalogo("Genero", "generos")
GrauInstrucao = _modelo_catalogo("GrauInstrucao", "graus_instrucao")
IdentidadeGenero = _modelo_catalogo("IdentidadeGenero", "identidades_genero")
Idioma = _modelo_catalogo("Idioma", "idiomas")
LocalProcedencia = _modelo_catalogo("LocalProcedencia", "locais_procedencia")
MeioComunicacao = _modelo_catalogo("MeioComunicacao", "meios_comunicacao")
MeioTransporte = _modelo_catalogo("MeioTransporte", "meios_transporte")
MotivoAlteracao = _modelo_catalogo("MotivoAlteracao", "motivos_alteracao")
MotivoAlta = _modelo_catalogo("MotivoAlta", "motivos_alta")
Nacionalidade = _modelo_catalogo("Nacionalidade", "nacionalidades")
Naturalidade = _modelo_catalogo("Naturalidade", "naturalidades")
OrgaoEmissor = _modelo_catalogo("OrgaoEmissor", "orgaos_emissores")
OrientacaoSexual = _modelo_catalogo("OrientacaoSexual", "orientacoes_sexuais")
Origem = _modelo_catalogo("Origem", "origens")
OrigemRecepcao = _modelo_catalogo("OrigemRecepcao", "origens_recepcao")
Pais = _modelo_catalogo("Pais", "paises")
Parentesco = _modelo_catalogo("Parentesco", "parentescos")
Plano = _modelo_catalogo("Plano", "planos")
Procedimento = _modelo_catalogo("Procedimento", "procedimentos")
Profissao = _modelo_catalogo("Profissao", "profissoes")
RacaCor = _modelo_catalogo("RacaCor", "racas_cores")
Religiao = _modelo_catalogo("Religiao", "religioes")
Sala = _modelo_catalogo("Sala", "salas")
SetorExame = _modelo_catalogo("SetorExame", "setores_exame")
Sexo = _modelo_catalogo("Sexo", "sexos")
TipoIdentificadorPessoa = _modelo_catalogo("TipoIdentificadorPessoa", "tipos_identificador_pessoa")
TipoAtendimento = _modelo_catalogo("TipoAtendimento", "tipos_atendimento")
TipoEscala = _modelo_catalogo("TipoEscala", "tipos_escala")
TipoLogradouro = _modelo_catalogo("TipoLogradouro", "tipos_logradouro")
TipoMoradia = _modelo_catalogo("TipoMoradia", "tipos_moradia")
TipoOcorrencia = _modelo_catalogo("TipoOcorrencia", "tipos_ocorrencia")
TipoPrestador = _modelo_catalogo("TipoPrestador", "tipos_prestador")
TipoSanguineo = _modelo_catalogo("TipoSanguineo", "tipos_sanguineos")
TipoVinculo = _modelo_catalogo("TipoVinculo", "tipos_vinculo")
VulnerabilidadeSocial = _modelo_catalogo("VulnerabilidadeSocial", "vulnerabilidades_sociais")


MODELOS_CATALOGO_POR_TEMA = {
    "bairro": Bairro,
    "banco": Banco,
    "cbo": Cbo,
    "cidade": Cidade,
    "cids": Cid,
    "conselho_profissional": ConselhoProfissional,
    "cor_raca": CorRaca,
    "destino_atendimento": DestinoAtendimento,
    "especialidade": Especialidade,
    "estado": Estado,
    "estado_civil": EstadoCivil,
    "feriado": Feriado,
    "genero": Genero,
    "grau_instrucao": GrauInstrucao,
    "identidade_genero": IdentidadeGenero,
    "idioma": Idioma,
    "local_procedencia": LocalProcedencia,
    "meio_comunicacao": MeioComunicacao,
    "meio_transporte": MeioTransporte,
    "motivo_alteracao": MotivoAlteracao,
    "motivos_alta": MotivoAlta,
    "nacionalidade": Nacionalidade,
    "naturalidade": Naturalidade,
    "orgao_emissor": OrgaoEmissor,
    "orientacao_sexual": OrientacaoSexual,
    "origem": Origem,
    "origem_recepcao": OrigemRecepcao,
    "pais": Pais,
    "parentesco": Parentesco,
    "plano": Plano,
    "procedimento": Procedimento,
    "profissao": Profissao,
    "raca_cor": RacaCor,
    "religiao": Religiao,
    "sala": Sala,
    "setor_exame": SetorExame,
    "sexo": Sexo,
    "tipo_identificador_pessoa": TipoIdentificadorPessoa,
    "tipo_atendimento": TipoAtendimento,
    "tipo_escala": TipoEscala,
    "tipo_logradouro": TipoLogradouro,
    "tipo_moradia": TipoMoradia,
    "tipo_ocorrencia": TipoOcorrencia,
    "tipo_prestador": TipoPrestador,
    "tipo_sanguineo": TipoSanguineo,
    "tipo_vinculo": TipoVinculo,
    "vulnerabilidade_social": VulnerabilidadeSocial,
}


class Cep(TimeStampedModel):
    cd_cep = models.BigAutoField(primary_key=True)
    nr_cep = models.CharField(max_length=8, unique=True)
    sg_estado = models.CharField(max_length=2, blank=True)
    cd_cidade = models.CharField(max_length=40, blank=True)
    ds_cidade = models.CharField(max_length=160, blank=True)
    tp_logradouro = models.CharField(max_length=40, blank=True)
    ds_logradouro = models.CharField(max_length=220, blank=True)
    ds_bairro = models.CharField(max_length=160, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "ceps"
        ordering = ("nr_cep",)

    def __str__(self) -> str:
        return f"{self.nr_cep} - {self.ds_logradouro or self.ds_cidade}"


class TipoPrestadorConselho(TimeStampedModel):
    tp_prestador = models.CharField(max_length=40, unique=True)
    ds_conselho = models.CharField(max_length=20)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "tipo_prestador_conselho"
        ordering = ("tp_prestador",)

    def __str__(self) -> str:
        return f"{self.tp_prestador} - {self.ds_conselho}"


class ConfiguracaoCampoFormulario(TimeStampedModel):
    cd_configuracao_campo_formulario = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(
        "accounts.Empresa",
        related_name="configuracoes_campos_formularios",
        on_delete=models.CASCADE,
        db_column="cd_empresa",
    )
    cd_formulario = models.CharField(max_length=80)
    cd_campo = models.CharField(max_length=120)
    sn_obrigatorio = models.BooleanField(default=False)
    cd_usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="configuracoes_formularios_criadas",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="cd_usuario_criacao",
    )
    cd_usuario_atualizacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="configuracoes_formularios_atualizadas",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column="cd_usuario_atualizacao",
    )

    class Meta:
        db_table = "configuracao_campo_formulario"
        ordering = ("cd_formulario", "cd_campo")
        unique_together = ("cd_empresa", "cd_formulario", "cd_campo")

    def __str__(self) -> str:
        return f"{self.cd_formulario}.{self.cd_campo}"


class TravaEdicao(TimeStampedModel):
    cd_trava_edicao = models.BigAutoField(primary_key=True)
    cd_empresa = models.ForeignKey(
        "accounts.Empresa",
        related_name="travas_edicao",
        on_delete=models.CASCADE,
        db_column="cd_empresa",
    )
    cd_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="travas_edicao",
        on_delete=models.CASCADE,
        db_column="cd_usuario",
    )
    ds_recurso_tipo = models.CharField(max_length=80)
    ds_recurso_id = models.CharField(max_length=120)
    ds_recurso_titulo = models.CharField(max_length=180, blank=True)
    ds_identificador_guia = models.CharField(max_length=120, blank=True)
    dh_expiracao = models.DateTimeField()
    nr_tentativas_bloqueadas = models.PositiveIntegerField(default=0)
    ds_ultimo_usuario_bloqueado = models.CharField(max_length=150, blank=True)
    dh_ultimo_bloqueio = models.DateTimeField(null=True, blank=True)
    ds_liberacao = models.CharField(max_length=220, blank=True)
    sn_ativa = models.BooleanField(default=True)

    class Meta:
        db_table = "trava_edicao"
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=("cd_empresa", "ds_recurso_tipo", "ds_recurso_id", "sn_ativa")),
            models.Index(fields=("dh_expiracao", "sn_ativa")),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("cd_empresa", "ds_recurso_tipo", "ds_recurso_id"),
                condition=models.Q(sn_ativa=True),
                name="uq_trava_edicao_recurso_ativo",
            )
        ]

    def __str__(self) -> str:
        return f"{self.ds_recurso_tipo}:{self.ds_recurso_id}"


class ScreenDefinition(TimeStampedModel):
    TYPE_GROUP = "grupo"
    TYPE_FORM = "formulario"
    TYPE_REPORT = "relatorio"
    TYPE_DASHBOARD = "dashboard"
    TYPE_QUERY = "consulta"
    TYPE_WIZARD = "wizard"
    TYPE_QUEUE = "fila"
    TYPE_DOCUMENT = "documento"
    TYPE_CONFIG = "configuracao"

    SCREEN_TYPES = [
        (TYPE_GROUP, "Grupo"),
        (TYPE_FORM, "Formulário"),
        (TYPE_REPORT, "Relatório"),
        (TYPE_DASHBOARD, "Dashboard"),
        (TYPE_QUERY, "Consulta"),
        (TYPE_WIZARD, "Wizard"),
        (TYPE_QUEUE, "Fila"),
        (TYPE_DOCUMENT, "Documento"),
        (TYPE_CONFIG, "Configuração"),
    ]

    module = models.ForeignKey(Module, related_name="screens", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    access_key = models.CharField(max_length=220, null=True, blank=True, unique=True, db_index=True)
    navigation_url = models.CharField(max_length=300, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    roles = models.JSONField(default=list, blank=True)
    screen_type = models.CharField(max_length=30, choices=SCREEN_TYPES, default=TYPE_FORM)
    parent_label = models.CharField(max_length=120, blank=True)
    table_name = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    allow_query = models.BooleanField(default=True)
    allow_insert = models.BooleanField(default=True)
    allow_update = models.BooleanField(default=True)
    allow_delete = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "definicao_tela"
        ordering = ("module__order", "module__title", "parent__order", "parent_label", "order", "title")

    def __str__(self) -> str:
        return self.title


class ScreenField(TimeStampedModel):
    TYPE_TEXT = "text"
    TYPE_NUMBER = "number"
    TYPE_DATE = "date"
    TYPE_SELECT = "select"
    TYPE_TEXTAREA = "textarea"
    TYPE_CHECKBOX = "checkbox"

    FIELD_TYPES = [
        (TYPE_TEXT, "Texto"),
        (TYPE_NUMBER, "Número"),
        (TYPE_DATE, "Data"),
        (TYPE_SELECT, "Seleção"),
        (TYPE_TEXTAREA, "Texto longo"),
        (TYPE_CHECKBOX, "Checkbox"),
    ]

    screen = models.ForeignKey(ScreenDefinition, related_name="fields", on_delete=models.CASCADE)
    label = models.CharField(max_length=120)
    table_name = models.CharField(max_length=80, blank=True)
    field_name = models.CharField(max_length=80)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default=TYPE_TEXT)
    required = models.BooleanField(default=False)
    consultable = models.BooleanField(default=True)
    editable = models.BooleanField(default=True)
    primary_key = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    lookup_table = models.CharField(max_length=80, blank=True)
    lookup_value_field = models.CharField(max_length=80, blank=True)
    lookup_display_field = models.CharField(max_length=80, blank=True)
    choices = models.TextField(blank=True, help_text="Uma opção por linha para campos de seleção.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "campo_tela"
        ordering = ("order", "label")

    def __str__(self) -> str:
        table = self.table_name or self.screen.table_name
        return f"{table}.{self.field_name}" if table else self.field_name
