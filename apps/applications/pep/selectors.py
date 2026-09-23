"""Read-only queries owned by PEP while its legacy models remain in Atendimento."""
from django.db.models import Q
from django.shortcuts import get_object_or_404

from apps.accounts.models import Setor
from apps.atendimento.models import Atendimento, Paciente, PreAtendimento


def buscar_pacientes(empresa, *, busca="", nr_atendimento="", data_inicio="", data_fim=""):
    """Return the PEP patient search with the legacy filters and ordering."""
    pacientes = Paciente.objects.filter(cd_empresa=empresa, sn_ativo=True)
    if nr_atendimento.isdigit():
        pacientes = pacientes.filter(atendimento__cd_atendimento=int(nr_atendimento))
    elif busca:
        filtros = (
            Q(nm_paciente__icontains=busca)
            | Q(nm_social__icontains=busca)
            | Q(nm_mae__icontains=busca)
            | Q(nr_cpf__icontains=busca)
            | Q(nr_cartao_sus__icontains=busca)
            | Q(nr_rg__icontains=busca)
            | Q(atendimento__cd_atendimento__icontains=busca)
        )
        if busca.isdigit():
            filtros |= Q(cd_paciente=int(busca))
        pacientes = pacientes.filter(filtros)
    elif not data_inicio and not data_fim:
        return Paciente.objects.none()
    if data_inicio:
        pacientes = pacientes.filter(atendimento__dh_inicio__date__gte=data_inicio)
    if data_fim:
        pacientes = pacientes.filter(atendimento__dh_inicio__date__lte=data_fim)
    return pacientes.distinct().order_by("nm_paciente")[:50]


def resolver_paciente(empresa, cd_paciente):
    return get_object_or_404(
        Paciente.objects.select_related("cd_convenio"),
        cd_empresa=empresa,
        pk=cd_paciente,
    )


def atendimentos_do_paciente(empresa, paciente):
    return (
        Atendimento.objects.select_related(
            "cd_prestador", "cd_pre_atendimento", "cd_convenio", "cd_setor_atual"
        )
        .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes", "documentos")
        .filter(cd_empresa=empresa, cd_paciente=paciente)
        .order_by("-dh_inicio")
    )


def resolver_atendimento_do_paciente(atendimentos, cd_atendimento):
    """Resolve only an encounter already scoped to the patient and tenant."""
    return get_object_or_404(atendimentos, pk=int(cd_atendimento))


def contexto_basico_prontuario(empresa, paciente, atendimentos, cd_atendimento=""):
    """Select the encounter and vital-sign history without clinical writes."""
    if cd_atendimento.isdigit():
        atendimento = resolver_atendimento_do_paciente(atendimentos, cd_atendimento)
    else:
        abertos = (
            "AGUARDANDO_CONSULTA", "EM_ATENDIMENTO", "AGUARDANDO_EXAMES",
            "RETORNO_EXAMES", "EM_OBSERVACAO",
        )
        atendimento = atendimentos.filter(ds_status__in=abertos).first() or atendimentos.first()
    ultimos_sinais = (
        atendimento.cd_pre_atendimento
        if atendimento and atendimento.cd_pre_atendimento_id
        else PreAtendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente)
        .order_by("-dh_classificacao")
        .first()
    )
    historico_sinais = (
        PreAtendimento.objects.filter(cd_empresa=empresa, cd_paciente=paciente)
        .select_related("cd_prestador_responsavel")
        .order_by("-dh_classificacao")[:30]
    )
    return atendimento, ultimos_sinais, historico_sinais


def usuario_pep_eh_ti(usuario):
    return usuario.groups.filter(name="TI").exists()


def contexto_setores_pep(empresa, usuario, setor_ids, usar_todos_setores):
    """Return the sectors visible to a user and the current queue filter."""
    usuario_eh_ti = usuario_pep_eh_ti(usuario)
    setores = Setor.objects.filter(
        cd_empresa=empresa,
        tp_setor=Setor.TipoSetor.ATENDIMENTO,
        sn_ativo=True,
    )
    if not usuario_eh_ti:
        setores = setores.filter(usuarios=usuario)
    setores = setores.distinct().order_by("nm_setor")
    setores_filtrados = setores if usar_todos_setores else setores.filter(pk__in=setor_ids)
    return usuario_eh_ti, setores, setores_filtrados


def codigos_especialidades_pep(empresa, prestador, usuario_eh_ti):
    """Resolve the specialty options allowed in the PEP workspace."""
    if prestador:
        codigos = [
            str(codigo).strip().upper()
            for codigo in list(prestador.ds_especialidades or []) + [prestador.ds_especialidade]
            if str(codigo or "").strip()
        ]
    elif usuario_eh_ti:
        codigos = [
            str(codigo).strip().upper()
            for codigo in Atendimento.objects.filter(cd_empresa=empresa)
            .exclude(ds_especialidade="")
            .values_list("ds_especialidade", flat=True)
            .distinct()
            if str(codigo or "").strip()
        ]
    else:
        codigos = []
    return list(dict.fromkeys(codigos))


def atendimentos_base_da_fila_pep(
    empresa,
    setores,
    setores_filtrados,
    prestador,
    usuario_eh_ti,
    codigos_especialidades_permitidas,
    especialidades_selecionadas,
):
    """Return the tenant-scoped operational queue before status/search filters."""
    atendimentos = (
        Atendimento.objects.select_related(
            "cd_paciente",
            "cd_paciente__cd_convenio",
            "cd_convenio",
            "cd_prestador",
            "cd_pre_atendimento",
            "cd_setor_atual",
        )
        .prefetch_related("solicitacoes_exames", "prescricoes")
        .filter(cd_empresa=empresa, sn_ativo=True)
        .order_by("cd_pre_atendimento__nr_prioridade", "dh_inicio")
    )
    if setores_filtrados.exists():
        atendimentos = atendimentos.filter(
            Q(cd_setor_atual__in=setores_filtrados) | Q(cd_setor_atual__isnull=True)
        )
    elif setores.exists():
        atendimentos = atendimentos.none()
    if prestador and not usuario_eh_ti:
        atendimentos = atendimentos.filter(
            Q(cd_prestador=prestador)
            | Q(
                cd_prestador__isnull=True,
                ds_especialidade__in=codigos_especialidades_permitidas,
            )
        )
    if especialidades_selecionadas:
        atendimentos = atendimentos.filter(ds_especialidade__in=especialidades_selecionadas)
    return atendimentos


def filtrar_fila_pep(atendimentos, status, *, busca="", nr_atendimento=""):
    """Apply the existing status and search filters to a PEP queue QuerySet."""
    atendimentos = atendimentos.filter(ds_status__in=status)
    if nr_atendimento.isdigit():
        return atendimentos.filter(cd_atendimento=int(nr_atendimento))
    if not busca:
        return atendimentos
    filtros = (
        Q(cd_paciente__nm_paciente__icontains=busca)
        | Q(cd_paciente__nm_social__icontains=busca)
        | Q(cd_paciente__nm_mae__icontains=busca)
        | Q(cd_paciente__nr_cpf__icontains=busca)
        | Q(cd_paciente__nr_cartao_sus__icontains=busca)
        | Q(cd_paciente__nr_rg__icontains=busca)
    )
    if busca.isdigit():
        filtros |= Q(cd_paciente_id=int(busca)) | Q(cd_atendimento=int(busca))
    return atendimentos.filter(filtros)


def atendimentos_da_aba_todos_pep(empresa, paciente):
    """Return the legacy detail list used by the PEP's 'todos' tab."""
    return (
        Atendimento.objects.select_related("cd_prestador", "cd_pre_atendimento", "cd_convenio")
        .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes")
        .filter(cd_empresa=empresa, cd_paciente=paciente)
        .order_by("-dh_inicio")
    )


def resolver_atendimento_da_aba_todos_pep(empresa, cd_atendimento):
    """Resolve an encounter for the PEP's 'todos' tab with tenant isolation."""
    return get_object_or_404(
        Atendimento.objects.select_related("cd_paciente", "cd_prestador", "cd_pre_atendimento", "cd_convenio")
        .prefetch_related("solicitacoes_exames__resultado", "prescricoes", "evolucoes"),
        cd_empresa=empresa,
        pk=cd_atendimento,
    )
