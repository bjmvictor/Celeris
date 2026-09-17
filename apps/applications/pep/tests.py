from django.http import Http404
from django.test import TestCase

from apps.accounts.models import Empresa
from apps.atendimento.models import Atendimento, Paciente

from .selectors import (
    atendimentos_do_paciente,
    buscar_pacientes,
    contexto_basico_prontuario,
    resolver_paciente,
)


class PepSelectorsTenantTests(TestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(cd_empresa=8101, nm_empresa="PEP A", sn_ativo=True)
        self.empresa_b = Empresa.objects.create(cd_empresa=8102, nm_empresa="PEP B", sn_ativo=True)
        self.paciente_a = Paciente.objects.create(cd_empresa=self.empresa_a, nm_paciente="PACIENTE A")
        self.paciente_b = Paciente.objects.create(cd_empresa=self.empresa_b, nm_paciente="PACIENTE B")
        self.atendimento_a = Atendimento.objects.create(
            cd_empresa=self.empresa_a,
            cd_paciente=self.paciente_a,
            ds_status="EM_ATENDIMENTO",
        )

    def test_busca_e_contexto_nao_atravessam_empresas(self):
        encontrados = buscar_pacientes(self.empresa_a, busca="PACIENTE")
        self.assertEqual(list(encontrados), [self.paciente_a])
        with self.assertRaises(Http404):
            resolver_paciente(self.empresa_a, self.paciente_b.pk)

        atendimentos = atendimentos_do_paciente(self.empresa_a, self.paciente_a)
        atendimento, ultimos_sinais, historico_sinais = contexto_basico_prontuario(
            self.empresa_a, self.paciente_a, atendimentos, str(self.atendimento_a.pk)
        )
        self.assertEqual(atendimento, self.atendimento_a)
        self.assertIsNone(ultimos_sinais)
        self.assertEqual(list(historico_sinais), [])

    def test_atendimento_de_outro_paciente_nao_pode_ser_resolvido(self):
        with self.assertRaises(Http404):
            contexto_basico_prontuario(
                self.empresa_b,
                self.paciente_b,
                atendimentos_do_paciente(self.empresa_b, self.paciente_b),
                str(self.atendimento_a.pk),
            )
