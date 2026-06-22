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
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "modulo"

    def __str__(self) -> str:
        return self.title


class UserModule(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)

    class Meta:
        db_table = "modulo_usuario"
        unique_together = ("user", "module")


class TabelaAuxiliarGlobal(TimeStampedModel):
    cd_tabela_auxiliar_global = models.BigAutoField(primary_key=True)
    ds_tabela = models.CharField(max_length=120, unique=True)
    ds_descricao = models.CharField(max_length=220, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "tabela_auxiliar"
        ordering = ("ds_tabela",)

    def __str__(self) -> str:
        return self.ds_tabela


class ValorAuxiliarGlobal(TimeStampedModel):
    cd_valor_auxiliar_global = models.BigAutoField(primary_key=True)
    cd_tabela_auxiliar_global = models.ForeignKey(
        TabelaAuxiliarGlobal,
        related_name="valores",
        on_delete=models.CASCADE,
        db_column="cd_tabela_auxiliar_global",
    )
    cd_valor = models.CharField(max_length=40)
    ds_valor = models.CharField(max_length=160)
    ds_grupo = models.CharField(max_length=40, blank=True)
    sn_ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "valor_auxiliar"
        ordering = ("cd_tabela_auxiliar_global__ds_tabela", "ds_valor")
        unique_together = ("cd_tabela_auxiliar_global", "cd_valor")

    def __str__(self) -> str:
        return f"{self.cd_valor} - {self.ds_valor}"


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
        db_table = "cep"
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


class ScreenDefinition(TimeStampedModel):
    TYPE_FORM = "formulario"
    TYPE_REPORT = "relatorio"
    TYPE_DASHBOARD = "dashboard"
    TYPE_QUERY = "consulta"
    TYPE_WIZARD = "wizard"
    TYPE_QUEUE = "fila"
    TYPE_DOCUMENT = "documento"
    TYPE_CONFIG = "configuracao"

    SCREEN_TYPES = [
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
    title = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True)
    access_key = models.CharField(max_length=220, null=True, blank=True, unique=True, db_index=True)
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
        ordering = ("module__title", "parent_label", "order", "title")

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
