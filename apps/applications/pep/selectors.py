"""Read-only queries owned by PEP while its legacy models remain in Atendimento."""
from django.db.models import Q
from django.shortcuts import get_object_or_404

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
