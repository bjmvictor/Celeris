from datetime import date, datetime, time, timedelta
import gzip
import json
import sys
import tempfile
import types
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.conf import settings
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Empresa, Setor, User, UsuarioEmpresa
from apps.core.catalogos import modelo_catalogo
from apps.core.models import Cep, Especialidade, Feriado, Module, MotivoAlteracao, ScreenDefinition, TipoPrestador

from .forms import EscalaForm, PacienteForm, PrestadorForm
from .models import AgendaGerada, AgendaProfissional, Agendamento, Atendimento, AtendimentoFluxo, ChamadaPainel, ClasseSenhaAtendimento, Convenio, CorClassificacaoRisco, DocumentoClinico, DominioExternoPermitido, EscalaClinica, EventoDocumentoClinico, EvolucaoAtendimento, FluxoClassificacao, FluxoClassificacaoEscala, HistoricoAlteracaoAtendimento, HorarioAgenda, IconeChamada, ItemMenuAssistencial, MaquinaChamada, ModeloDocumento, ModeloDocumentoTelaImpressao, Paciente, PainelChamada, PainelChamadaSetor, PastaDocumento, PerfilAssistencial, PerfilAssistencialTipo, PerfilAssistencialVersao, PerguntaClassificacao, PreAtendimento, Prescricao, Prestador, PrestadorTipo, ProtocoloSenhaAtendimento, RascunhoEditorDocumento, RegraSubdivisaoSenha, ResponsavelAtendimento, ResultadoEscalaClinica, SenhaAtendimento, TipoSenhaAtendimento
from .views import _avaliar_expressao_variavel, _configurar_assinatura_prestador


class ConsultaAtendimentosTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=7000, nm_empresa="Empresa Consulta", sn_ativo=True)
        self.user = User.objects.create_superuser("consulta-atendimentos", "consulta@example.com", "senha-forte")
        self.client.force_login(self.user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()
        self.paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="MARIA TESTE")
        self.atendimento = Atendimento.objects.create(cd_empresa=self.empresa, cd_paciente=self.paciente)

    def test_consulta_por_atendimento_prontuario_e_nome(self):
        url = reverse("atendimento:atendimentos")
        response = self.client.get(url, {
            "consultar": "1",
            "nr_atendimento": self.atendimento.pk,
            "nr_prontuario": self.paciente.pk,
            "nm_paciente": "Maria",
        })
        self.assertContains(response, "Consulta de atendimentos")
        self.assertContains(response, "MARIA TESTE")
        self.assertContains(response, str(self.atendimento.pk))

    def test_consulta_por_data_de_nascimento_e_nome_da_mae(self):
        self.paciente.dt_nascimento = date(1985, 4, 12)
        self.paciente.nm_mae = "JOANA TESTE"
        self.paciente.save(update_fields=["dt_nascimento", "nm_mae"])
        outro_paciente = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="OUTRA PACIENTE",
            dt_nascimento=date(1990, 1, 1),
            nm_mae="OUTRA MAE",
        )
        Atendimento.objects.create(cd_empresa=self.empresa, cd_paciente=outro_paciente)

        response = self.client.get(
            reverse("atendimento:atendimentos"),
            {
                "consultar": "1",
                "dt_nascimento": "1985-04-12",
                "nm_mae": "Joana",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_pacientes_resultado"], 1)
        self.assertEqual(response.context["atendimento_selecionado"].pk, self.atendimento.pk)
        self.assertContains(response, 'name="dt_nascimento" value="1985-04-12"')
        self.assertContains(response, 'name="nm_mae" value="Joana"')

    def test_consulta_limita_resultado_a_dez_pacientes(self):
        for indice in range(10):
            paciente = Paciente.objects.create(
                cd_empresa=self.empresa,
                nm_paciente=f"PACIENTE LIMITE {indice:02d}",
            )
            Atendimento.objects.create(
                cd_empresa=self.empresa,
                cd_paciente=paciente,
                ds_status="ABERTO",
                dh_inicio=timezone.now() + timedelta(minutes=indice + 1),
            )

        response = self.client.get(
            reverse("atendimento:atendimentos"),
            {"consultar": "1", "ds_status": "ABERTO"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_pacientes_resultado"], 10)
        self.assertEqual(response.context["current_record_status"], "Paciente 1 de 10")
        self.assertContains(response, "A consulta encontrou mais de 10 pacientes")

    def test_lista_em_ordem_decrescente_e_exibe_detalhes_somente_leitura(self):
        atendimento_novo = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_tipo_atendimento="URGÊNCIA",
            dh_inicio=timezone.now() + timedelta(hours=1),
        )
        response = self.client.get(
            reverse("atendimento:atendimentos"),
            {"consultar": "1", "nm_paciente": "MARIA"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["registros"][0].pk, atendimento_novo.pk)
        self.assertEqual(response.context["atendimento_selecionado"].pk, atendimento_novo.pk)
        self.assertContains(response, "Dados do atendimento")
        self.assertNotContains(response, "Altas e auditoria")
        self.assertContains(response, "Dados do responsável")
        self.assertContains(response, "Data da alta médica")
        self.assertFalse(response.context["current_can_save"])

    def test_consulta_exige_ao_menos_um_filtro(self):
        response = self.client.get(reverse("atendimento:atendimentos"), {"consultar": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["registros"], [])
        self.assertIsNone(response.context["atendimento_selecionado"])
        self.assertContains(response, "Informe pelo menos um filtro para realizar a consulta.")
        self.assertTrue(response.context["current_start_query"])

    def test_consulta_agrupa_por_paciente_e_navega_pelos_pacientes(self):
        paciente_recente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="ANA RECENTE")
        atendimento_recente = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=paciente_recente,
            ds_tipo_atendimento="CONSULTA",
            dh_inicio=timezone.now() + timedelta(hours=2),
        )
        atendimento_anterior = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=paciente_recente,
            ds_tipo_atendimento="RETORNO",
            dh_inicio=timezone.now() + timedelta(hours=1),
        )
        response = self.client.get(
            reverse("atendimento:atendimentos"),
            {"consultar": "1", "ds_status": self.atendimento.ds_status},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["atendimento_selecionado"].pk, atendimento_recente.pk)
        self.assertEqual(
            [item.pk for item in response.context["registros"]],
            [atendimento_recente.pk, atendimento_anterior.pk],
        )
        self.assertEqual(response.context["current_record_status"], "Paciente 1 de 2")
        self.assertIn("paciente=", response.context["current_next_url"])

    def test_alteracao_abre_em_consulta_exclusiva_pelo_codigo(self):
        url = reverse("atendimento:alteracao-atendimento")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.fields["cd_atendimento"].disabled)
        self.assertEqual(form.fields["cd_atendimento"].widget.attrs["data-consultable"], "true")
        self.assertEqual(form.fields["ds_plano"].widget.attrs["data-consultable"], "false")
        self.assertContains(response, 'data-query-code-only="cd_atendimento"')

        response = self.client.get(url, {"consultar": "1", "cd_atendimento": self.atendimento.pk})
        self.assertRedirects(
            response,
            reverse("atendimento:editar-atendimento", args=[self.atendimento.pk]),
            fetch_redirect_response=False,
        )

    def test_alteracao_exige_motivo_e_preserva_campos_estruturais(self):
        motivo = MotivoAlteracao.objects.create(
            cd_valor="CORRECAO",
            ds_valor="Correção administrativa",
        )
        dados = {
            "versao_atendimento": self.atendimento.dh_atualizacao.isoformat(),
            "ds_plano": "PLANO CORRIGIDO",
            "ds_origem": "AGENDADO",
            "motivo_alteracao": motivo.pk,
            "observacao_alteracao": "Correção solicitada pela recepção.",
            "cd_prestador": "",
            "ds_recepcao_origem": "",
            "cd_convenio": "",
            "ds_subplano": "",
            "ds_tipo_atendimento": "",
            "ds_local_procedencia": "",
            "ds_destino": "",
            "ds_especialidade": "",
            "ds_cid": "",
            "ds_meio_transporte": "",
            "ds_procedimento_principal": "",
            "ds_cbo_prestador": "",
            "ds_observacao_recepcao": "",
        }
        response = self.client.post(
            reverse("atendimento:editar-atendimento", args=[self.atendimento.pk]),
            dados,
        )
        self.assertEqual(response.status_code, 302)
        self.atendimento.refresh_from_db()
        self.assertEqual(self.atendimento.ds_plano, "PLANO CORRIGIDO")
        self.assertEqual(self.atendimento.ds_origem, "DEMANDA_ESPONTANEA")
        historico = HistoricoAlteracaoAtendimento.objects.get(cd_atendimento=self.atendimento)
        self.assertEqual(historico.cd_motivo_alteracao, motivo)
        self.assertEqual(historico.ds_depois["ds_plano"], "PLANO CORRIGIDO")

    def test_alteracao_sem_motivo_nao_persiste(self):
        response = self.client.post(
            reverse("atendimento:editar-atendimento", args=[self.atendimento.pk]),
            {
                "versao_atendimento": self.atendimento.dh_atualizacao.isoformat(),
                "ds_plano": "SEM AUDITORIA",
                "cd_prestador": "",
                "ds_recepcao_origem": "",
                "cd_convenio": "",
                "ds_subplano": "",
                "ds_tipo_atendimento": "",
                "ds_local_procedencia": "",
                "ds_destino": "",
                "ds_especialidade": "",
                "ds_cid": "",
                "ds_meio_transporte": "",
                "ds_procedimento_principal": "",
                "ds_cbo_prestador": "",
                "ds_observacao_recepcao": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.atendimento.refresh_from_db()
        self.assertNotEqual(self.atendimento.ds_plano, "SEM AUDITORIA")
        self.assertFalse(HistoricoAlteracaoAtendimento.objects.exists())


class PainelChamadaStandaloneTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=701, nm_empresa="Empresa Painel", sn_ativo=True)
        self.setor = Setor.objects.create(
            cd_empresa=self.empresa,
            nm_setor="Consultório 1",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        self.maquina = MaquinaChamada.objects.create(
            cd_empresa=self.empresa,
            nm_maquina="PAINEL01",
            tp_maquina="PAINEL",
            cd_setor=self.setor,
            nm_sala="Recepção",
        )

    def test_primeiro_acesso_configura_painel_da_maquina(self):
        response = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configurar painel")
        self.assertContains(response, ">PAINEL<")
        self.assertContains(response, "Especialidades que podem chamar")
        self.assertContains(response, "Chamar paciente")

        response = self.client.post(
            f"/painel/?maquina={self.maquina.nm_maquina}",
            {
                "empresa": self.empresa.pk,
                "layout": "compacto",
                "tamanho": "grande",
                "cor": "verde",
                "chamar_paciente": "1",
                "mostrar_nome": "1",
                "mostrar_especialidade": "1",
                "mostrar_direcao": "1",
                "som_chamada": "1",
                "voz_chamada": "1",
                "ler_nome": "1",
                "mostrar_ultimas": "1",
                "quantidade_ultimas": "5",
                "repeticoes": "1",
                "fonte_principal": "6",
                "fonte_tela_cheia": "8",
            },
        )
        self.assertEqual(response.status_code, 302)
        painel = PainelChamada.objects.get(cd_empresa=self.empresa, nm_maquina=self.maquina.nm_maquina)
        self.assertEqual((painel.ds_layout, painel.ds_tamanho, painel.ds_cor), ("compacto", "grande", "verde"))
        self.assertTrue(painel.ds_configuracao["chamar_paciente"])
        self.assertTrue(painel.ds_configuracao["mostrar_nome"])
        self.assertEqual(list(painel.setores.values_list("pk", flat=True)), [self.setor.pk])

        response = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Configurar painel</h1>")
        self.assertContains(response, "Aguardando chamada")

    def test_maquina_sem_painel_abre_configuracao_inicial(self):
        self.maquina.tp_maquina = "ESTACAO"
        self.maquina.save(update_fields=["tp_maquina"])
        response = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configurar painel")

    def test_midia_enviada_e_servida_pela_rota_publica_do_painel(self):
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                f"/painel/?maquina={self.maquina.nm_maquina}",
                {
                    "empresa": self.empresa.pk,
                    "layout": "classico",
                    "tamanho": "medio",
                    "cor": "azul",
                    "chamar_paciente": "1",
                    "habilitar_midia": "1",
                    "mostrar_nome": "1",
                    "mostrar_senha": "1",
                    "mostrar_ultimas": "1",
                    "quantidade_ultimas": "5",
                    "tempo_exibicao": "10",
                    "repeticoes": "1",
                    "midia_arquivo": SimpleUploadedFile(
                        "painel.jpg",
                        b"imagem-de-teste",
                        content_type="image/jpeg",
                    ),
                },
            )
            self.assertEqual(response.status_code, 302)
            painel = PainelChamada.objects.get(cd_empresa=self.empresa, nm_maquina=self.maquina.nm_maquina)

            pagina = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
            self.assertContains(pagina, reverse("painel_chamada_midia", args=[painel.pk]))

            midia = self.client.get(reverse("painel_chamada_midia", args=[painel.pk]))
            self.assertEqual(midia.status_code, 200)
            self.assertEqual(midia["Content-Type"], "image/jpeg")
            midia.close()

    def test_acesso_sem_identificador_cria_identificador_persistente(self):
        response = self.client.get("/painel/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configurar painel")
        self.assertRegex(response.cookies["celeris_maquina_chamada"].value, r"^PAINEL-[A-F0-9]{8}$")

    def test_catalogos_sao_separados_por_empresa(self):
        Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="Médico Cardiologista",
            nm_guerra="Cardiologista",
            ds_especialidades=["CARDIOLOGIA"],
        )
        paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="Paciente painel")
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=paciente,
            ds_especialidade="CARDIOLOGIA",
            ds_tipo_atendimento="CONSULTA",
        )
        outra_empresa = Empresa.objects.create(cd_empresa=703, nm_empresa="Outra empresa", sn_ativo=True)
        Prestador.objects.create(
            cd_empresa=outra_empresa,
            nm_prestador="Médico Neurologista",
            nm_guerra="Neurologista",
            ds_especialidades=["NEUROLOGIA"],
        )

        response = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})

        especialidades = {item["valor"] for item in response.context["catalogo_atual"]["especialidades"]}
        self.assertIn("CARDIOLOGIA", especialidades)
        self.assertNotIn("NEUROLOGIA", especialidades)
        self.assertEqual(
            {item["valor"] for item in response.context["catalogos_empresas"][str(outra_empresa.pk)]["especialidades"]},
            {"NEUROLOGIA"},
        )

    def test_debug_cria_uma_chamada_e_depois_move_para_historico(self):
        response = self.client.post(
            f"/painel/?maquina={self.maquina.nm_maquina}",
            {
                "empresa": self.empresa.pk,
                "nome_painel": "Painel principal",
                "layout": "classico",
                "tamanho": "medio",
                "cor": "azul",
                "chamar_paciente": "1",
                "mostrar_nome": "1",
                "mostrar_senha": "1",
                "mostrar_ultimas": "1",
                "quantidade_ultimas": "5",
                "tempo_exibicao": "10",
                "repeticoes": "1",
                "debug": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        painel = PainelChamada.objects.get(cd_empresa=self.empresa, nm_maquina=self.maquina.nm_maquina)
        chamada = ChamadaPainel.objects.get(cd_painel_chamada=painel)

        active = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
        self.assertContains(active, "Painel principal")
        self.assertContains(active, "TESTE 001")
        self.assertEqual(active.context["chamada_atual"]["id"], chamada.pk)

        chamada.dh_chamada = timezone.now() - timedelta(minutes=1)
        chamada.save(update_fields=["dh_chamada"])
        history = self.client.get("/painel/", {"maquina": self.maquina.nm_maquina})
        self.assertIsNone(history.context["chamada_atual"])
        self.assertEqual(history.context["historico_chamadas"][0]["id"], chamada.pk)

    def test_chamada_do_pep_e_enviada_somente_ao_painel_compativel(self):
        painel_compativel = PainelChamada.objects.create(
            cd_empresa=self.empresa,
            nm_painel="Painel compatível",
            nm_maquina=self.maquina.nm_maquina,
            ds_configuracao={
                "chamar_paciente": True,
                "todas_especialidades": False,
                "especialidades": ["CARDIOLOGIA"],
                "tipos_atendimento": ["CONSULTA"],
            },
        )
        painel_compativel.setores.add(self.setor)
        painel_incompativel = PainelChamada.objects.create(
            cd_empresa=self.empresa,
            nm_painel="Painel incompatível",
            nm_maquina="PAINEL02",
            ds_configuracao={
                "chamar_paciente": True,
                "todas_especialidades": False,
                "especialidades": ["NEUROLOGIA"],
            },
        )
        painel_incompativel.setores.add(self.setor)
        paciente = Paciente.objects.create(cd_empresa=self.empresa, nm_paciente="Paciente chamado")
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=paciente,
            cd_setor_atual=self.setor,
            ds_especialidade="CARDIOLOGIA",
            ds_tipo_atendimento="CONSULTA",
        )
        usuario = User.objects.create_superuser("painel-admin", "painel@example.com", "senha-forte")
        self.client.force_login(usuario)
        session = self.client.session
        session["cd_empresa"] = self.empresa.pk
        session.save()

        response = self.client.post(
            reverse("atendimento:pep-chamar", args=[atendimento.pk]),
            {"setor": self.setor.pk, "next": "/PEP/"},
        )

        self.assertRedirects(response, "/PEP/", fetch_redirect_response=False)
        self.assertTrue(ChamadaPainel.objects.filter(cd_atendimento=atendimento, cd_painel_chamada=painel_compativel).exists())
        self.assertFalse(ChamadaPainel.objects.filter(cd_atendimento=atendimento, cd_painel_chamada=painel_incompativel).exists())


class EscalaEspecialidadesTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=702, nm_empresa="Empresa Escalas", sn_ativo=True)
        for code, label in (
            ("CARDIOLOGIA", "Cardiologia"),
            ("CLINICA_GERAL", "Clínica Geral"),
            ("PEDIATRIA", "Pediatria"),
        ):
            Especialidade.objects.update_or_create(
                cd_valor=code,
                defaults={"ds_valor": label, "sn_ativo": True},
            )
        self.prestador = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="Médico da escala",
            nm_guerra="Médico",
            tp_prestador="MEDICO",
            ds_especialidade="CARDIOLOGIA",
            ds_especialidades=["CARDIOLOGIA", "CLINICA_GERAL"],
            sn_permite_agenda=True,
            sn_ativo=True,
        )
        Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="Pediatra",
            nm_guerra="Pediatra",
            tp_prestador="MEDICO",
            ds_especialidade="PEDIATRIA",
            ds_especialidades=["PEDIATRIA"],
            sn_permite_agenda=True,
            sn_ativo=True,
        )

    def test_especialidades_sao_limitadas_ao_prestador_selecionado(self):
        form = EscalaForm(data={"cd_prestador": self.prestador.pk}, empresa=self.empresa)
        choices = dict(form.fields["ds_especialidade"].widget.choices)
        self.assertEqual(
            choices,
            {"": "", "CARDIOLOGIA": "Cardiologia", "CLINICA_GERAL": "Clínica Geral"},
        )
        self.assertNotIn("PEDIATRIA", choices)

    def test_formulario_publica_mapa_para_atualizacao_sem_recarregar(self):
        form = EscalaForm(empresa=self.empresa)
        provider_map = json.loads(form.fields["cd_prestador"].widget.attrs["data-provider-specialties"])
        self.assertEqual(
            [item["value"] for item in provider_map[str(self.prestador.pk)]],
            ["CARDIOLOGIA", "CLINICA_GERAL"],
        )
        self.assertEqual(list(form.fields["ds_especialidade"].widget.choices), [("", "")])

    def test_servidor_rejeita_especialidade_de_outro_prestador(self):
        form = EscalaForm(
            data={
                "cd_prestador": self.prestador.pk,
                "ds_especialidade": "PEDIATRIA",
            },
            empresa=self.empresa,
        )
        form.is_valid()
        self.assertIn("ds_especialidade", form.errors)
        self.assertIn("não está cadastrada", form.errors["ds_especialidade"][0])


class FluxoHomologacaoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(cd_empresa=99, nm_empresa="Homologação", sn_ativo=True)
        self.recepcionista = self.create_user("RECEPTESTE", "Recepcionista")
        self.enfermeiro = self.create_user("ENFTESTE", "Enfermeiro")
        self.medico_user = self.create_user("MEDTESTE", "Médico")
        self.ti_user = self.create_user("TITESTE", "TI")
        self.paciente = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="PACIENTE HOMOLOGAÇÃO",
            nr_cpf="529.982.247-25",
            dt_nascimento="1990-01-01",
        )
        self.prestador = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="MÉDICO TESTE",
            nm_guerra="MÉDICO TESTE",
            tp_prestador="MEDICO",
            ds_conselho="CRM",
            nr_conselho="123",
            ds_especialidade="CLINICA_GERAL",
            ds_especialidades=["CLINICA_GERAL"],
            sn_permite_agenda=True,
            sn_permite_atendimento=True,
            sn_permite_prescricao=True,
            sn_permite_classificacao=True,
        )
        self.agenda = AgendaProfissional.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            ds_agenda="TESTE",
            nr_dia_semana=timezone.localdate().weekday(),
            hr_inicio="08:00",
            hr_fim="18:00",
        )
        self.agenda_gerada = AgendaGerada.objects.create(
            cd_empresa=self.empresa,
            cd_escala=self.agenda,
            dt_inicio=timezone.localdate(),
            dt_fim=timezone.localdate(),
        )
        inicio_slot = timezone.make_aware(datetime.combine(timezone.localdate(), time(hour=8)))
        self.horario_agenda = HorarioAgenda.objects.create(
            cd_empresa=self.empresa,
            cd_agenda_gerada=self.agenda_gerada,
            cd_escala=self.agenda,
            cd_prestador=self.prestador,
            dh_inicio=inicio_slot,
            dh_fim=inicio_slot + timedelta(minutes=30),
        )
        self.agendamento = Agendamento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_agenda_profissional=self.agenda,
            dh_agendamento=timezone.now() + timedelta(hours=1),
            ds_status="AGENDADO",
            ds_especialidade="CLINICA_GERAL",
            ds_profissional=self.prestador.nm_prestador,
        )
        self.client = Client(HTTP_HOST="localhost")

    def create_user(self, username, role):
        user = User.objects.create_user(username=username, password="123456", is_active=True)
        user.groups.add(Group.objects.get_or_create(name=role)[0])
        UsuarioEmpresa.objects.create(usuario=user, empresa=self.empresa, sn_padrao=True, sn_ativo=True)
        return user

    def login_as(self, user):
        self.client.force_login(user)
        session = self.client.session
        session["cd_empresa"] = self.empresa.cd_empresa
        session.save()

    def cadastrar_atendimento_do_agendamento(self):
        return self.client.post(
            reverse("atendimento:novo-atendimento-agendado", args=[self.agendamento.pk]),
            {
                "cd_prestador": self.prestador.pk,
                "ds_origem": "AGENDADO",
                "ds_tipo_atendimento": "CONSULTA",
                "ds_especialidade": "CLINICA_GERAL",
                "ds_plano": "PLANO TESTE",
                "ds_local_procedencia": "DOMICILIO",
                "ds_destino": "CONSULTORIO",
                "ds_meio_transporte": "PROPRIO",
                "responsavel-nm_responsavel": "",
            },
        )

    def test_fluxo_assistencial_completo(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:recepcionar-agendamento", args=[self.agendamento.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("atendimento:revisar-paciente-agendamento", args=[self.paciente.pk]), response.url)
        self.assertFalse(Atendimento.objects.filter(cd_agendamento=self.agendamento).exists())
        cadastro = self.client.get(response.url)
        self.assertContains(cadastro, "data-action=\"continue\"")
        response = self.cadastrar_atendimento_do_agendamento()
        self.assertEqual(response.status_code, 302)
        atendimento = Atendimento.objects.get(cd_agendamento=self.agendamento)
        self.assertEqual(atendimento.ds_status, "AGUARDANDO_CLASSIFICACAO")

        self.login_as(self.enfermeiro)
        response = self.client.post(
            reverse("atendimento:pre-atendimento", args=[self.agendamento.pk]),
            {
                "nr_prioridade": 3,
                "ds_queixa_principal": "Dor de cabeça",
                "ds_sintomas": "Náusea",
                "ds_cor_prioridade": "AMARELO",
                "cd_prestador_responsavel": self.prestador.pk,
                "nr_pressao_arterial": "120x80",
            },
        )
        self.assertEqual(response.status_code, 302)
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "AGUARDANDO_CONSULTA")

        self.login_as(self.medico_user)
        self.client.get(reverse("atendimento:abrir-consulta", args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "EM_ATENDIMENTO")

        response = self.client.post(
            reverse("atendimento:ficha-atendimento", args=[atendimento.pk]),
            {
                "cd_prestador": self.prestador.pk,
                "ds_origem": "AGENDADO",
                "ds_tipo_atendimento": "CONSULTA",
                "ds_especialidade": "CLINICA_GERAL",
                "ds_unidade_setor": "AMBULATÓRIO",
                "ds_anamnese": "Paciente consciente.",
                "ds_hipotese_diagnostica": "Cefaleia",
                "ds_diagnostico": "Cefaleia tensional",
                "ds_conduta": "Medicação e repouso.",
                "ds_destino": "DOMICÍLIO",
            },
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            reverse("atendimento:documento-assistencial", args=[atendimento.pk, "admissao"]),
            {"ds_conteudo": "Paciente consciente.", "finalizar": "1"},
        )
        self.assertEqual(response.status_code, 302)

        self.client.post(
            reverse("atendimento:prescrever", args=[atendimento.pk]),
            {"ds_prescricao": "Analgésico", "ds_orientacoes": "Tomar após alimentação."},
        )
        self.assertEqual(Prescricao.objects.filter(cd_atendimento=atendimento).count(), 1)

        self.client.post(
            reverse("atendimento:evoluir", args=[atendimento.pk]),
            {"ds_evolucao": "Paciente apresenta melhora clínica."},
        )
        self.assertEqual(EvolucaoAtendimento.objects.filter(cd_atendimento=atendimento).count(), 1)

        alta = self.client.post(
            reverse("atendimento:conceder-alta", args=[atendimento.pk]),
            {
                "ds_cid": "R51",
                "ds_diagnostico": "Cefaleia tensional",
                "ds_conduta": "Medicação e repouso.",
                "ds_motivo_alta": "Melhora clínica",
                "ds_destino": "DOMICÍLIO",
            },
        )
        self.assertEqual(alta.status_code, 302)
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "ALTA_MEDICA")
        self.assertEqual(atendimento.ds_cid, "R51")
        self.assertTrue(DocumentoClinico.objects.filter(cd_atendimento=atendimento, tp_documento="RESUMO_ALTA").exists())

        self.client.post(reverse("atendimento:finalizar-atendimento", args=[atendimento.pk]))
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.ds_status, "FINALIZADO")
        self.assertTrue(AtendimentoFluxo.objects.filter(cd_atendimento=atendimento, ds_status_novo="FINALIZADO").exists())

    def test_recepcao_nao_duplica_atendimento_do_mesmo_agendamento(self):
        self.login_as(self.recepcionista)
        self.cadastrar_atendimento_do_agendamento()
        response = self.client.get(reverse("atendimento:recepcionar-agendamento", args=[self.agendamento.pk]))
        atendimento = Atendimento.objects.get(cd_agendamento=self.agendamento)
        self.assertRedirects(response, reverse("atendimento:cadastro-atendimento", args=[atendimento.pk]))
        self.assertEqual(Atendimento.objects.filter(cd_agendamento=self.agendamento).count(), 1)

    def test_cadastro_atendimento_grava_responsavel_e_oferece_impressao(self):
        screen = ScreenDefinition.objects.get(access_key="atendimento:recepcao")
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Ficha configurada",
            tp_documento="FICHA_ATENDIMENTO",
            tp_elemento="DOCUMENTO",
            ds_html_impressao="<strong>FICHA CONFIGURADA {{ atendimento.codigo }}</strong>",
        )
        etiqueta = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Etiqueta configurada",
            tp_documento="ETIQUETA_ATENDIMENTO",
            tp_elemento="DOCUMENTO",
            ds_html_impressao="<strong>ETIQUETA CONFIGURADA {{ atendimento.codigo }}</strong>",
        )
        ModeloDocumentoTelaImpressao.objects.bulk_create(
            [
                ModeloDocumentoTelaImpressao(
                    cd_empresa=self.empresa,
                    cd_modelo_documento=modelo,
                    cd_tela=screen,
                ),
                ModeloDocumentoTelaImpressao(
                    cd_empresa=self.empresa,
                    cd_modelo_documento=etiqueta,
                    cd_tela=screen,
                ),
            ]
        )
        self.login_as(self.recepcionista)
        response = self.client.post(
            reverse("atendimento:novo-atendimento-agendado", args=[self.agendamento.pk]),
            {
                "cd_prestador": self.prestador.pk,
                "ds_origem": "AGENDADO",
                "ds_tipo_atendimento": "CONSULTA",
                "ds_local_procedencia": "DOMICILIO",
                "ds_destino": "CONSULTORIO",
                "responsavel-ds_parentesco": "MAE",
                "responsavel-nm_responsavel": "RESPONSÁVEL TESTE",
                "responsavel-nr_celular": "81999999999",
                "responsavel-sn_mesmo_endereco_paciente": "on",
            },
        )
        atendimento = Atendimento.objects.get(cd_agendamento=self.agendamento)
        responsavel = ResponsavelAtendimento.objects.get(cd_atendimento=atendimento)
        self.assertEqual(responsavel.nm_responsavel, "RESPONSÁVEL TESTE")
        self.assertRedirects(
            response,
            f"{reverse('atendimento:cadastro-atendimento', args=[atendimento.pk])}?salvo=1",
        )
        confirmation = self.client.get(response.url)
        self.assertContains(confirmation, "data-attendance-documents-open")
        self.assertContains(confirmation, "Documentos do atendimento")
        self.assertContains(confirmation, "Ficha configurada")
        self.assertContains(confirmation, "Etiqueta configurada")
        self.assertContains(confirmation, "data-attendance-documents-print-selected")
        self.assertContains(confirmation, "Código")
        self.assertContains(confirmation, reverse("atendimento:imprimir-atendimento", args=[atendimento.pk]))
        configured = self.client.get(
            reverse("atendimento:imprimir-atendimento", args=[atendimento.pk]),
            {"modelo": modelo.pk},
        )
        self.assertContains(configured, f"FICHA CONFIGURADA {atendimento.pk}")
        self.assertEqual(configured.headers["X-Frame-Options"], "SAMEORIGIN")
        multiple = self.client.get(
            reverse("atendimento:imprimir-atendimento", args=[atendimento.pk]),
            {"modelos": f"{modelo.pk},{etiqueta.pk}"},
        )
        self.assertContains(multiple, f"FICHA CONFIGURADA {atendimento.pk}")
        self.assertContains(multiple, f"ETIQUETA CONFIGURADA {atendimento.pk}")
        self.assertEqual(multiple.content.count(b'class="attendance-print-document"'), 2)

    def test_dados_de_outra_empresa_nao_entram_na_recepcao(self):
        outra_empresa = Empresa.objects.create(cd_empresa=100, nm_empresa="Outra empresa", sn_ativo=True)
        outro_paciente = Paciente.objects.create(cd_empresa=outra_empresa, nm_paciente="PACIENTE OUTRA EMPRESA")
        outro_agendamento = Agendamento.objects.create(
            cd_empresa=outra_empresa,
            cd_paciente=outro_paciente,
            dh_agendamento=timezone.now(),
            ds_status="AGENDADO",
        )
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:recepcao"), {"termo": "PACIENTE"})
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertNotContains(response, outro_paciente.nm_paciente)
        response = self.client.get(reverse("atendimento:recepcionar-agendamento", args=[outro_agendamento.pk]))
        self.assertEqual(response.status_code, 404)

    def test_pep_nao_lista_paciente_apenas_agendado(self):
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"))
        self.assertContains(response, 'class="pep-header-actions"')
        self.assertContains(response, 'class="pep-filter-form pep-header-fields"')
        self.assertContains(response, "grid-template-columns:max-content minmax(0,1fr)!important")
        self.assertNotContains(response, self.paciente.nm_paciente)

    def test_pep_exibe_filtros_por_engrenagem_e_lista_atendimentos_sem_alta(self):
        self.medico_user.cd_prestador = self.prestador
        self.medico_user.save(update_fields=["cd_prestador"])
        self.prestador.ds_especialidades = ["CLINICA_GERAL", "clinica_geral", " CLINICA_GERAL "]
        self.prestador.save(update_fields=["ds_especialidades"])
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="AGUARDANDO_CONSULTA",
            ds_especialidade="CLINICA_GERAL",
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"))
        self.assertContains(response, 'data-nav-icon="settings"')
        self.assertContains(response, 'data-nav-icon="filter"')
        self.assertContains(response, 'value="CLINICA_GERAL"')
        self.assertContains(response, 'value="CLINICA_GERAL"', count=1)
        self.assertContains(response, 'document.querySelectorAll(".pep-settings[open]")')
        self.assertContains(response, "Todos os setores permitidos")
        self.assertContains(response, "Atendimentos sem alta")
        self.assertContains(response, self.paciente.nm_paciente)
        #self.assertContains(response, "Abrir prontuário")

    def test_pep_todos_pacientes_consulta_prontuario_e_atendimentos(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="FINALIZADO",
            ds_diagnostico="Cefaleia",
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:pep"), {"aba": "todos", "q": "PACIENTE"})
        self.assertContains(response, 'class="pep-header-actions"')
        self.assertContains(response, 'class="pep-search-form pep-header-tools"')
        self.assertContains(response, "grid-template-columns:max-content minmax(0,1fr)!important")
        self.assertContains(response, "Prontuário")
        self.assertContains(response, self.paciente.nm_paciente)

        detail = self.client.get(
            reverse("atendimento:pep-prontuario-paciente", args=[self.paciente.pk]),
            {"atendimento": atendimento.pk},
        )
        self.assertContains(detail, f"Atendimento {atendimento.pk}")
        self.assertContains(detail, "Cefaleia")

    def test_pep_abre_paciente_sem_atendimento_e_consulta_nome_social(self):
        paciente = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="NOME DE REGISTRO SEM ATENDIMENTO",
            nm_social="NOME SOCIAL LOCALIZAVEL",
        )
        self.login_as(self.medico_user)

        resultado = self.client.get(
            reverse("atendimento:pep"),
            {"aba": "todos", "q": "SOCIAL LOCALIZAVEL"},
        )
        self.assertContains(resultado, "NOME SOCIAL LOCALIZAVEL")

        prontuario = self.client.get(
            reverse("atendimento:pep-prontuario-paciente", args=[paciente.pk]),
            {"modo": "consulta"},
        )
        self.assertEqual(prontuario.status_code, 200)
        self.assertContains(prontuario, "Este paciente ainda não possui atendimentos registrados.")
        self.assertContains(prontuario, "NOME SOCIAL LOCALIZAVEL")

    def test_documento_pode_ser_vinculado_a_tela_de_impressao(self):
        module = Module.objects.create(code="IMPRESSAO_TESTE", title="Impressão teste", order=997)
        screen = ScreenDefinition.objects.create(
            module=module,
            title="Cadastro de atendimento",
            slug="impressao-cadastro-atendimento",
            access_key="atendimento:cadastro-atendimento",
            order=10,
        )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Ficha configurada por tela",
            tp_documento="FICHA_ATENDIMENTO",
            tp_elemento="DOCUMENTO",
            sn_versao_atual=True,
            sn_ativo=True,
        )
        self.login_as(self.ti_user)

        pagina = self.client.get(
            reverse("atendimento:documentos-telas-impressao"),
            {"modelo": modelo.pk},
        )
        self.assertContains(pagina, "Ficha configurada por tela")
        self.assertContains(pagina, 'data-document-screen-module')
        self.assertContains(pagina, 'data-document-screen-select')
        self.assertContains(pagina, f'value="{module.pk}"')
        self.assertContains(pagina, 'value="Ficha configurada por tela" readonly')

        saved = self.client.post(
            reverse("atendimento:documentos-telas-impressao"),
            {
                "modelo": modelo.pk,
                "modulo": [module.pk],
                "tela": [screen.pk],
                "excluir": ["0"],
            },
        )
        self.assertRedirects(
            saved,
            f"{reverse('atendimento:documentos-telas-impressao')}?modelo={modelo.pk}",
        )
        self.assertTrue(
            ModeloDocumentoTelaImpressao.objects.filter(
                cd_empresa=self.empresa,
                cd_modelo_documento=modelo,
                cd_tela=screen,
                sn_ativo=True,
            ).exists()
        )

    def test_agendamentos_operacionais_exibe_calendario_e_comprovante(self):
        screen = ScreenDefinition.objects.filter(access_key="atendimento:agendar").first()
        if not screen:
            module = Module.objects.create(code="AGENDAMENTO_IMPRESSAO", title="Agendamento", order=996)
            screen = ScreenDefinition.objects.create(
                module=module,
                title="Agendar",
                slug="agendar-impressao-teste",
                access_key="atendimento:agendar",
                order=10,
            )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Comprovante configurado",
            tp_documento="COMPROVANTE_AGENDAMENTO",
            tp_elemento="DOCUMENTO",
            ds_html_impressao="<strong>COMPROVANTE EDITÁVEL {{ agendamento.codigo }}</strong>",
            sn_exibe_assinatura=False,
        )
        ModeloDocumentoTelaImpressao.objects.create(
            cd_empresa=self.empresa,
            cd_modelo_documento=modelo,
            cd_tela=screen,
        )
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:agendamentos-operacionais"))
        self.assertContains(response, "calendar-day")
        self.assertContains(response, "has-appointment")
        self.assertContains(response, "Com agendamento")
        self.assertContains(response, "Especialidades")
        self.assertContains(response, "Mostrar agendamentos")
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertContains(response, "Reimprimir comprovante")
        self.assertContains(response, "Recepcionar paciente")
        self.assertContains(response, 'data-nav-icon="printer"')

        comprovante = self.client.get(reverse("atendimento:comprovante-agendamento", args=[self.agendamento.pk]))
        self.assertContains(comprovante, f"COMPROVANTE EDITÁVEL {self.agendamento.pk}")
        self.assertEqual(comprovante.headers["X-Frame-Options"], "SAMEORIGIN")
        embed = self.client.get(
            reverse("atendimento:comprovante-agendamento", args=[self.agendamento.pk]),
            {"embed": "1"},
        )
        self.assertContains(embed, f"COMPROVANTE EDITÁVEL {self.agendamento.pk}")
        self.assertEqual(embed.context["modelo"], modelo)

    def test_comprovante_sem_modelo_exibe_orientacao_amigavel(self):
        self.login_as(self.recepcionista)

        response = self.client.get(
            reverse("atendimento:comprovante-agendamento", args=[self.agendamento.pk]),
            {"pdf": "1", "tela": "atendimento:agendar"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "atendimento/impressao_indisponivel.html")
        self.assertContains(response, "Comprovante não configurado")
        self.assertContains(response, "Documentos × telas de impressão")

    def test_cores_preservam_caixa_do_nome_e_rejeitam_chave_duplicada(self):
        primeira = CorClassificacaoRisco.objects.create(
            cd_empresa=self.empresa,
            cd_cor="VERDE",
            nm_cor="Verde",
            ds_cor_hex="#22c55e",
            nr_prioridade=1,
        )
        segunda = CorClassificacaoRisco.objects.create(
            cd_empresa=self.empresa,
            cd_cor="AZUL",
            nm_cor="Azul",
            ds_cor_hex="#3b82f6",
            nr_prioridade=2,
        )
        self.login_as(self.ti_user)
        url = reverse("class_cores")
        dados = {
            f"code_{primeira.pk}": "VERDE",
            f"name_{primeira.pk}": "Verde claro",
            f"hex_{primeira.pk}": "#22c55e",
            f"priority_{primeira.pk}": "1",
            f"active_{primeira.pk}": "true",
            f"code_{segunda.pk}": "AZUL",
            f"name_{segunda.pk}": "Azul profundo",
            f"hex_{segunda.pk}": "#3b82f6",
            f"priority_{segunda.pk}": "2",
            f"active_{segunda.pk}": "true",
        }

        response = self.client.post(f"{url}?consultar=1", dados)

        self.assertRedirects(response, f"{url}?consultar=1")
        primeira.refresh_from_db()
        segunda.refresh_from_db()
        self.assertEqual(primeira.nm_cor, "Verde claro")
        self.assertEqual(segunda.nm_cor, "Azul profundo")

        dados[f"priority_{primeira.pk}"] = "4"
        dados[f"priority_{segunda.pk}"] = "1"
        response = self.client.post(f"{url}?consultar=1", dados)
        self.assertRedirects(response, f"{url}?consultar=1")
        primeira.refresh_from_db()
        segunda.refresh_from_db()
        self.assertEqual(primeira.nr_prioridade, 4)
        self.assertEqual(segunda.nr_prioridade, 1)
        consulta_ordenada = self.client.get(url, {"consultar": "1"})
        self.assertEqual(
            [item.pk for item in consulta_ordenada.context["registros"].object_list],
            [segunda.pk, primeira.pk],
        )

        dados[f"code_{primeira.pk}"] = "AZUL"
        response = self.client.post(f"{url}?consultar=1", dados, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "já está sendo utilizada por outra cor")
        primeira.refresh_from_db()
        self.assertEqual(primeira.cd_cor, "VERDE")

    def test_cancelar_agendamento_preserva_filtros_da_listagem(self):
        self.login_as(self.recepcionista)
        return_to = (
            f"{reverse('atendimento:agendamentos-operacionais')}"
            "data=2026-07-02&mes=7&ano=2026&q=MEDICO&especialidades=CLINICA_GERAL"
        )
        response = self.client.post(
            reverse("atendimento:cancelar-agendamento", args=[self.agendamento.pk]),
            {"return_to": return_to},
        )
        self.assertRedirects(response, return_to, fetch_redirect_response=False)
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.ds_status, "CANCELADO")

    def test_selecionar_agenda_confirma_apenas_apos_escolher_horario(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]))
        self.assertContains(response, "calendar-day")
        self.assertContains(response, "data-schedule-patient-header")
        self.assertNotContains(response, f'window.location.assign("{reverse("atendimento:agendar")}")')
        self.assertNotContains(response, "Confirmar agendamento")
        horario = response.context["horarios"][0]
        selected = self.client.get(
            reverse(
                "atendimento:confirmar-horario-agenda",
                args=[self.paciente.pk, horario["horario"].pk],
            ),
            {"return_to": reverse("atendimento:selecionar-agenda", args=[self.paciente.pk])},
        )
        self.assertContains(selected, "Confirmar agendamento")
        self.assertContains(selected, "appointment-confirm-layout")
        self.assertContains(selected, "Convênios aceitos")
        self.assertContains(selected, "Tipo de horário")
        self.assertContains(selected, "data-appointment-type-select")
        self.assertContains(selected, "data-appointment-type-preview")

        confirmation_url = reverse(
            "atendimento:confirmar-horario-agenda",
            args=[self.paciente.pk, horario["horario"].pk],
        )
        first = self.client.post(confirmation_url, {"ds_tipo_atendimento": "CONSULTA"})
        agendamento = Agendamento.objects.latest("pk")
        expected = f"{reverse('atendimento:agendar')}?comprovante={agendamento.pk}"
        self.assertRedirects(first, expected)
        modal = self.client.get(first.url)
        self.assertContains(modal, "data-appointment-receipt-modal")
        self.assertContains(modal, "pdf=1")
        second = self.client.post(confirmation_url, {"ds_tipo_atendimento": "CONSULTA"})
        self.assertRedirects(second, reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]))
        self.assertEqual(Agendamento.objects.filter(cd_horario_agenda=horario["horario"]).count(), 1)

    def test_agenda_disponivel_somente_quando_horario_foi_gerado(self):
        amanha = timezone.localdate() + timedelta(days=1)
        self.login_as(self.recepcionista)
        sem_horario = self.client.get(
            reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]),
            {"data": amanha.isoformat()},
        )
        self.assertEqual(sem_horario.context["horarios"], [])

        lote = AgendaGerada.objects.create(cd_empresa=self.empresa, cd_escala=self.agenda, dt_inicio=amanha, dt_fim=amanha)
        inicio = timezone.make_aware(datetime.combine(amanha, time(hour=9)))
        HorarioAgenda.objects.create(
            cd_empresa=self.empresa,
            cd_agenda_gerada=lote,
            cd_escala=self.agenda,
            cd_prestador=self.prestador,
            dh_inicio=inicio,
            dh_fim=inicio + timedelta(minutes=30),
        )
        com_horario = self.client.get(
            reverse("atendimento:selecionar-agenda", args=[self.paciente.pk]),
            {"data": amanha.isoformat()},
        )
        self.assertTrue(com_horario.context["horarios"])

    def test_geracao_de_agenda_bloqueia_conflito_e_preserva_horario_agendado(self):
        data = timezone.localdate() + timedelta(days=2)
        self.agenda.ds_dias_semana = [data.weekday()]
        self.agenda.hr_inicio = time(hour=10)
        self.agenda.hr_fim = time(hour=11)
        self.agenda.nr_tempo_atendimento = 30
        self.agenda.qt_horarios_dia = 2
        self.agenda.save()
        self.login_as(self.ti_user)
        url = reverse("atendimento:gerar-agenda")
        dados = {
            "acao": "gerar",
            "escala": self.agenda.pk,
            "data_inicio": data.isoformat(),
            "data_fim": data.isoformat(),
        }

        primeira = self.client.post(url, dados, follow=True)
        self.assertContains(primeira, "Agenda gerada com 2 horário(s)")
        lote = AgendaGerada.objects.filter(dt_inicio=data).latest("pk")
        self.assertEqual(lote.horarios.count(), 2)

        conflito = self.client.post(url, dados, follow=True)
        self.assertContains(conflito, "Já existem horários gerados")
        self.assertEqual(AgendaGerada.objects.filter(dt_inicio=data).count(), 1)

        slot_ocupado = lote.horarios.order_by("dh_inicio").first()
        self.agendamento.cd_horario_agenda = slot_ocupado
        self.agendamento.dh_agendamento = slot_ocupado.dh_inicio
        self.agendamento.save()
        slot_ocupado.ds_status = "AGENDADO"
        slot_ocupado.save(update_fields=["ds_status"])
        cancelamento = self.client.post(
            url,
            {"acao": "cancelar", "agenda_gerada": lote.pk},
            follow=True,
        )
        self.assertContains(cancelamento, "Horários com pacientes agendados foram preservados")
        slot_ocupado.refresh_from_db()
        lote.refresh_from_db()
        self.assertEqual(slot_ocupado.ds_status, "AGENDADO")
        self.assertEqual(lote.ds_status, "PARCIAL")
        self.assertEqual(lote.horarios.filter(ds_status="CANCELADO").count(), 1)

    def test_geracao_inicia_somente_com_data_inicial_e_expande_linha(self):
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:gerar-agenda"))
        self.assertContains(response, f'value="{timezone.localdate():%Y-%m-%d}"')
        self.assertContains(response, 'name="data_fim" type="date" value=""')
        self.assertContains(response, "data-agenda-row-toggle")
        self.assertNotContains(response, "Visualizar horários deste período")

    def test_geracao_informa_dia_ignorado_por_feriado(self):
        data = timezone.localdate() + timedelta(days=3)
        self.agenda.ds_dias_semana = [data.weekday()]
        self.agenda.sn_atende_feriado = False
        self.agenda.save()
        Feriado.objects.create(
            cd_valor=data.isoformat(),
            ds_valor=data.isoformat(),
        )
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:gerar-agenda"),
            {
                "acao": "gerar",
                "escala": self.agenda.pk,
                "data_inicio": data.isoformat(),
                "data_fim": data.isoformat(),
            },
            follow=True,
        )
        self.assertContains(response, "não teve horários gerados porque é feriado")
        self.assertFalse(AgendaGerada.objects.filter(dt_inicio=data).exists())

    def test_menu_e_permissoes_exibem_escalas_e_geracao_de_agendas(self):
        self.login_as(self.ti_user)
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Escalas")
        self.assertContains(response, "Geração de agendas")

    def test_cadastro_escala_formulario_consulta_multivalores_e_previa(self):
        setor = Setor.objects.create(
            cd_empresa=self.empresa,
            nm_setor="CONSULTÓRIO",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        convenio = Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="CONVÊNIO TESTE")
        auxiliares = {}
        for tabela_nome, codigo, descricao in (
            ("tipo_escala", "AMBULATORIAL", "Ambulatorial"),
            ("especialidade", "CLINICA_GERAL", "Clínica geral"),
            ("tipo_atendimento", "PRIMEIRA_CONSULTA", "Primeira consulta"),
        ):
            valor, _ = modelo_catalogo(tabela_nome).objects.get_or_create(
                cd_valor=codigo,
                defaults={"ds_valor": descricao},
            )
            auxiliares[tabela_nome] = valor.cd_valor
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:escalas"),
            {
                "ds_agenda": "ESCALA AMBULATORIAL",
                "tp_escala": auxiliares["tipo_escala"],
                "cd_prestador": self.prestador.pk,
                "ds_especialidade": auxiliares["especialidade"],
                "cd_setor_atendimento": setor.pk,
                "tp_horario": "HORA_MARCADA",
                "ds_dias_semana": ["0", "2", "4"],
                "hr_inicio": "08:00",
                "hr_fim": "10:00",
                "nr_tempo_atendimento": "30",
                "nr_intervalo": "0",
                "qt_horarios_dia": "4",
                "qt_encaixes": "1",
                "convenios": [convenio.pk],
                "ds_tipo_agendamento": auxiliares["tipo_atendimento"],
            },
        )
        self.assertEqual(response.status_code, 302)
        escala = AgendaProfissional.objects.get(ds_agenda="ESCALA AMBULATORIAL")
        self.assertEqual(escala.dias_semana, [0, 2, 4])
        self.assertEqual(list(escala.convenios.all()), [convenio])

        cadastro = self.client.get(reverse("atendimento:cadastro-escala", args=[escala.pk]))
        self.assertContains(cadastro, "Visualizar horários da escala")
        self.assertNotContains(cadastro, "Ajustar escala automaticamente")
        self.assertContains(cadastro, "Os horários serão gerados conforme a quantidade")
        self.assertContains(cadastro, "data-scale-weekdays")
        consulta = self.client.get(
            reverse("atendimento:escalas"),
            {"consultar": "1", "qt_horarios_dia": "4", "ds_dias_semana": ["0", "2"]},
        )
        self.assertRedirects(
            consulta,
            f"{reverse('atendimento:cadastro-escala', args=[escala.pk])}?origem=consulta",
        )

        self.assertContains(cadastro, 'data-delete-current="true"')
        self.assertContains(cadastro, 'data-field-table="escala"')
        self.assertContains(cadastro, 'data-field-name="nm_escala"')
        delete_response = self.client.post(
            reverse("atendimento:cadastro-escala", args=[escala.pk]),
            {"_excluir_atual": "1"},
        )
        self.assertRedirects(
            delete_response,
            f"{reverse('atendimento:escalas')}?exclusao_concluida=1",
        )
        self.assertFalse(AgendaProfissional.objects.filter(pk=escala.pk).exists())

    def test_exclusao_imediata_de_escala_remove_apenas_item_atual(self):
        escalas = [
            AgendaProfissional.objects.create(
                cd_empresa=self.empresa,
                cd_prestador=self.prestador,
                ds_agenda=f"ESCALA EXCLUSAO {indice}",
                nr_dia_semana=indice,
                hr_inicio="08:00",
                hr_fim="10:00",
            )
            for indice in range(1, 5)
        ]
        self.login_as(self.ti_user)
        session = self.client.session
        session["consulta_escalas"] = [escala.pk for escala in escalas]
        session.save()

        response = self.client.post(
            f"{reverse('atendimento:cadastro-escala', args=[escalas[1].pk])}?origem=consulta",
            {"_excluir_atual": "1"},
        )

        self.assertRedirects(
            response,
            f"{reverse('atendimento:escalas')}?origem=consulta&exclusao_concluida=1",
        )
        self.assertFalse(AgendaProfissional.objects.filter(pk=escalas[1].pk).exists())
        self.assertTrue(AgendaProfissional.objects.filter(pk=escalas[2].pk).exists())
        self.assertEqual(
            self.client.session["consulta_escalas"],
            [escalas[0].pk, escalas[2].pk, escalas[3].pk],
        )

        cleared = self.client.get(
            reverse("atendimento:escalas"),
            {"origem": "consulta", "exclusao_concluida": "1"},
        )
        self.assertContains(cleared, "3 encontrado(s)")
        self.assertContains(cleared, reverse("atendimento:cadastro-escala", args=[escalas[0].pk]))

    def test_recepcao_direta_consulta_revisa_e_alerta_atendimento_aberto(self):
        self.paciente.nm_social = "PACIENTE SOCIAL"
        self.paciente.nr_cartao_sus = "898001234567890"
        self.paciente.ds_cidade = "RECIFE"
        self.paciente.sg_estado = "PE"
        self.paciente.save(update_fields=["nm_social", "nr_cartao_sus", "ds_cidade", "sg_estado"])
        self.login_as(self.recepcionista)
        reception = self.client.get(reverse("atendimento:recepcao"))
        self.assertContains(reception, "Execute uma consulta")
        self.assertContains(reception, "Pacientes classificados")
        self.assertNotContains(reception, "Fila prioritária")
        result = self.client.get(reverse("atendimento:recepcao"), {"termo": "HOMOLOGAÇÃO"})
        self.assertContains(result, self.paciente.nm_social)
        self.assertContains(result, f"Nome de registro: {self.paciente.nm_paciente}")
        self.assertContains(result, self.paciente.nr_cartao_sus)
        self.assertContains(result, "RECIFE-PE")
        scheduling = self.client.get(reverse("atendimento:agendar"), {"termo": "HOMOLOGAÇÃO"})
        self.assertContains(scheduling, self.paciente.nm_social)
        self.assertContains(scheduling, f"Nome de registro: {self.paciente.nm_paciente}")
        self.assertContains(scheduling, "RECIFE-PE")
        review = self.client.get(reverse("atendimento:recepcao-revisar-paciente", args=[self.paciente.pk]))
        expected = reverse("atendimento:revisar-paciente-agendamento", args=[self.paciente.pk])
        self.assertTrue(review.url.startswith(expected))
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_status="AGUARDANDO_CLASSIFICACAO",
        )
        warning = self.client.get(reverse("atendimento:recepcao-revisar-paciente", args=[self.paciente.pk]))
        self.assertContains(warning, "Paciente com atendimento em aberto")
        warning_json = self.client.get(
            reverse("atendimento:recepcao-revisar-paciente", args=[self.paciente.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(warning_json.status_code, 200)
        self.assertTrue(warning_json.json()["confirmacao_necessaria"])
        self.assertIn("Paciente com atendimento em aberto", warning_json.json()["titulo"])
        self.assertIn("prosseguir=1", warning_json.json()["prosseguir_url"])
        proceed = self.client.get(
            reverse("atendimento:recepcao-revisar-paciente", args=[self.paciente.pk]),
            {"prosseguir": "1"},
        )
        self.assertTrue(proceed.url.startswith(expected))

    def test_recepcao_abre_novo_paciente_em_subtela_e_habilita_confirmacao_apos_salvar(self):
        self.login_as(self.recepcionista)
        reception_url = f"{reverse('atendimento:recepcao')}?termo=NOVO"
        reception = self.client.get(reception_url)
        new_patient_url = reception.context["current_new_url"]
        self.assertIn(reverse("atendimento:cadastro-paciente-agendamento"), new_patient_url)
        self.assertIn("recepcao_direta=1", new_patient_url)
        self.assertIn("return_to=", new_patient_url)

        patient_form = self.client.get(new_patient_url)
        self.assertEqual(patient_form.context["current_close_mode"], "back")
        self.assertEqual(patient_form.context["current_tab_key"], reverse("atendimento:recepcao"))
        self.assertEqual(patient_form.context["current_close_url"], reception_url)
        self.assertFalse(patient_form.context["current_continue_url"])
        self.assertContains(patient_form, 'data-subscreen-toolbar="true"')
        self.assertContains(patient_form, 'data-subscreen-allow-continue="true"')
        self.assertContains(patient_form, 'data-nav-icon="corner-up-left"')

        saved = self.client.post(
            new_patient_url,
            {
                "nm_paciente": "PACIENTE CADASTRADO NA RECEPÇÃO",
                "dt_nascimento": "1992-03-04",
            },
        )
        paciente = Paciente.objects.get(nm_paciente="PACIENTE CADASTRADO NA RECEPÇÃO")
        expected_form_url = reverse("atendimento:revisar-paciente-agendamento", args=[paciente.pk])
        self.assertEqual(saved.status_code, 302)
        self.assertTrue(saved.url.startswith(expected_form_url))
        self.assertIn("recepcao_direta=1", saved.url)

        confirmed_form = self.client.get(saved.url)
        self.assertEqual(confirmed_form.context["current_close_url"], reception_url)
        self.assertIn(
            reverse("atendimento:novo-atendimento-direto", args=[paciente.pk]),
            confirmed_form.context["current_continue_url"],
        )
        self.assertContains(confirmed_form, 'data-continue-url="/atendimento/recepcao/pacientes/')

    def test_data_hora_do_atendimento_aceita_valor_retroativo_e_preserva_criacao(self):
        self.login_as(self.recepcionista)
        url = reverse("atendimento:novo-atendimento-direto", args=[self.paciente.pk])
        form_response = self.client.get(url)
        datetime_field = form_response.context["form"]["dh_atendimento_exibicao"]
        self.assertNotIn("disabled", datetime_field.field.widget.attrs)
        self.assertTrue(datetime_field.value())

        retroactive_value = "2024-01-15T08:30"
        saved = self.client.post(
            url,
            {
                "dh_atendimento_exibicao": retroactive_value,
                "ds_origem": "DEMANDA_ESPONTANEA",
                "responsavel-nm_responsavel": "",
            },
        )
        self.assertEqual(saved.status_code, 302)
        atendimento = Atendimento.objects.filter(cd_paciente=self.paciente).latest("cd_atendimento")
        local_start = timezone.localtime(atendimento.dh_inicio)
        self.assertEqual(local_start.strftime("%Y-%m-%dT%H:%M"), retroactive_value)
        self.assertGreater(atendimento.dh_criacao, atendimento.dh_inicio)

    def test_totem_configura_gera_e_movimenta_senha(self):
        setor = Setor.objects.create(
            cd_empresa=self.empresa,
            nm_setor="CLASSIFICAÇÃO",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        painel = PainelChamada.objects.create(
            cd_empresa=self.empresa,
            nm_painel="PAINEL CLASSIFICAÇÃO",
            nm_maquina="PAINEL-CLASSIFICACAO",
        )
        PainelChamadaSetor.objects.create(cd_painel_chamada=painel, cd_setor=setor)
        self.login_as(self.ti_user)
        configured = self.client.post(
            reverse("atendimento:configurar-senhas"),
            {
                "nm_tipo_senha": "Adulto",
                "sg_tipo_senha": "A",
                "nr_tempo_minimo": "20",
                "nr_prioridade_tipo": "3",
                "cd_setor_atendimento": setor.pk,
                "nm_classe_senha": "Normal",
                "sg_classe_senha": "N",
                "nr_prioridade_classe": "4",
            },
        )
        tipo = TipoSenhaAtendimento.objects.get(cd_empresa=self.empresa, nm_tipo_senha="Adulto")
        self.assertRedirects(
            configured,
            reverse("atendimento:editar-configuracao-senha", args=[tipo.pk]),
        )
        classe = ClasseSenhaAtendimento.objects.get(cd_empresa=self.empresa, nm_classe_senha="Normal")
        generated = self.client.post(reverse("atendimento:gerar-senha-totem"), {"classe": classe.pk})
        self.assertEqual(generated.status_code, 200)
        senha = SenhaAtendimento.objects.get()
        self.assertTrue(senha.ds_senha.startswith("AN "))
        self.login_as(self.enfermeiro)
        called = self.client.post(reverse("atendimento:acao-senha-classificacao", args=[senha.pk, "chamar"]))
        self.assertRedirects(called, f"{reverse('atendimento:fila-classificacao')}?aba=demanda")
        senha.refresh_from_db()
        self.assertEqual(senha.ds_status, "CHAMADA")
        self.assertTrue(ChamadaPainel.objects.filter(cd_senha_atendimento=senha, cd_setor=setor).exists())
        queue = self.client.get(reverse("atendimento:fila-classificacao"), {"aba": "demanda"})
        self.assertContains(queue, senha.ds_senha)
        public_panel = self.client.get(reverse("atendimento:painel-chamada-publico"), {"painel": painel.pk})
        self.assertContains(public_panel, senha.ds_senha)

    def test_classificacao_demanda_vincula_paciente_existente(self):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            nm_tipo_senha="Demanda",
            sg_tipo_senha="D",
            nr_tempo_minimo=15,
        )
        cor = CorClassificacaoRisco.objects.create(
            cd_empresa=self.empresa,
            cd_cor="AMARELO",
            nm_cor="Amarelo",
            ds_cor_hex="#eab308",
            nr_prioridade=3,
        )
        classe = ClasseSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha="Normal",
            sg_classe_senha="N",
            nr_prioridade=3,
            cd_cor_classificacao=cor,
        )
        senha = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            cd_cor_classificacao=cor,
            nr_senha=1,
            ds_senha="DN 01",
        )
        self.login_as(self.enfermeiro)

        standalone = self.client.get(
            reverse("classificacao_standalone"),
            {"aba": "demanda", "senha": senha.pk},
        )
        self.assertContains(standalone, "1. Identificação")
        self.assertContains(standalone, "6. Resumo")
        self.assertContains(standalone, "for (let position = 0; position < index; position += 1)")
        self.assertContains(standalone, "validateStage(position)")
        called = self.client.post(
            reverse("atendimento:acao-senha-classificacao", args=[senha.pk, "chamar"]),
            {"return_to": f"{reverse('classificacao_standalone')}?aba=demanda"},
        )
        self.assertRedirects(
            called,
            f"{reverse('classificacao_standalone')}?aba=demanda",
            fetch_redirect_response=False,
        )

        data_atual = timezone.localdate().isoformat()
        filtros_retorno = f"data={data_atual}&filtro=agendados&filtro=nao_classificados&q=DN"
        response = self.client.post(
            f"{reverse('classificacao_standalone')}?{filtros_retorno}",
            {
                "acao": "finalizar",
                "senha_id": senha.pk,
                "paciente_id": self.paciente.pk,
                "cor_classificacao": cor.pk,
                "nr_prioridade": "3",
                "ds_queixa_principal": "Dor abdominal",
                "cd_prestador_responsavel": self.prestador.pk,
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('classificacao_standalone')}?{filtros_retorno}",
        )
        senha.refresh_from_db()
        self.assertEqual(senha.ds_status, "CLASSIFICADA")
        self.assertEqual(senha.cd_paciente, self.paciente)
        self.assertIsNotNone(senha.cd_pre_atendimento_id)
        self.assertEqual(senha.cd_pre_atendimento.ds_cor_prioridade, "AMARELO")

    def test_classificacao_permite_salvar_rascunho_incompleto(self):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            nm_tipo_senha="Demanda em rascunho",
            sg_tipo_senha="DR",
        )
        classe = ClasseSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha="Normal",
            sg_classe_senha="N",
        )
        senha = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            nr_senha=1,
            ds_senha="DRN 01",
        )
        self.login_as(self.enfermeiro)

        response = self.client.post(
            reverse("atendimento:fila-classificacao"),
            {
                "acao": "salvar_rascunho",
                "senha_id": senha.pk,
                "etapa_atual": "abordagem",
                "nm_pre_cadastro": "PACIENTE PARCIAL",
                "ds_queixa_principal": "Queixa ainda incompleta",
                "alergia_substancia": ["Dipirona"],
                "alergia_observacao": ["Reação leve: coceira, náusea e ½ comprimido."],
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        senha.refresh_from_db()
        self.assertEqual(senha.ds_status, "EM_CLASSIFICACAO")
        self.assertEqual(senha.nm_pre_cadastro, "PACIENTE PARCIAL")
        self.assertEqual(senha.ds_dados_classificacao["etapa_atual"], "abordagem")
        self.assertEqual(senha.ds_dados_classificacao["ds_queixa_principal"], "Queixa ainda incompleta")
        self.assertEqual(
            senha.ds_dados_classificacao["alergias_itens"][0]["observacao"],
            "Reação leve: coceira, náusea e ½ comprimido.",
        )

    def test_classificacao_imprime_modelo_habilitado_com_variaveis_da_ficha(self):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            nm_tipo_senha="Demanda para impressão",
            sg_tipo_senha="DI",
        )
        classe = ClasseSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha="Normal",
            sg_classe_senha="N",
        )
        senha = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            cd_paciente=self.paciente,
            nr_senha=1,
            ds_senha="DIN 01",
            ds_dados_classificacao={
                "ds_queixa_principal": "Dor abdominal",
                "alergias_itens": [
                    {"substancia": "Dipirona", "observacao": "Reação com náusea e coceira."}
                ],
            },
        )
        tela = ScreenDefinition.objects.get(access_key="atendimento:fila-classificacao")
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Ficha de classificação configurável",
            tp_documento="FICHA_CLASSIFICACAO",
            tp_elemento="DOCUMENTO",
            ds_html_impressao="{{ classificacao.senha }} - {{ classificacao.alergias }}",
        )
        ModeloDocumentoTelaImpressao.objects.create(
            cd_empresa=self.empresa,
            cd_modelo_documento=modelo,
            cd_tela=tela,
        )
        self.login_as(self.enfermeiro)

        with patch(
            "apps.atendimento.views._resposta_pdf_documento",
            return_value=HttpResponse("documento-renderizado"),
        ) as resposta_pdf:
            response = self.client.get(
                reverse("atendimento:imprimir-classificacao"),
                {"senha": senha.pk},
            )

        self.assertEqual(response.status_code, 200)
        documento = resposta_pdf.call_args.args[1]
        self.assertEqual(documento.cd_modelo_documento, modelo)
        self.assertEqual(documento._variaveis_adicionais["classificacao.senha"], "DIN 01")
        self.assertEqual(
            documento._variaveis_adicionais["classificacao.alergias"],
            "Dipirona - Reação com náusea e coceira.",
        )

    def test_class_standalone_unifica_fila_e_oculta_acoes_antes_da_classificacao(self):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            nm_tipo_senha="Demanda Class",
            sg_tipo_senha="DC",
        )
        classe = ClasseSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha="Normal",
            sg_classe_senha="N",
        )
        senha = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            nr_senha=1,
            ds_senha="DCN 01",
        )
        senha_antiga = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            nr_senha=2,
            ds_senha="DCN 02",
            ds_status="CLASSIFICADA",
        )
        SenhaAtendimento.objects.filter(pk=senha_antiga.pk).update(
            dt_senha=timezone.localdate() - timedelta(days=3)
        )
        agendamento_classificado = Agendamento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_agenda_profissional=self.agenda,
            dh_agendamento=timezone.now() + timedelta(minutes=15),
            ds_status="AGENDADO",
            ds_especialidade="CLINICA_GERAL",
            ds_profissional=self.prestador.nm_prestador,
        )
        PreAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_agendamento=agendamento_classificado,
            ds_queixa_principal="Paciente classificado",
        )
        self.login_as(self.enfermeiro)

        response = self.client.get(reverse("classificacao_standalone"))

        self.assertContains(response, "Agendados")
        self.assertContains(response, "Classificados")
        self.assertContains(response, "Não classificados")
        self.assertContains(response, senha.ds_senha)
        self.assertContains(response, senha_antiga.ds_senha)
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertContains(response, "data-classification-search-clear")
        self.assertContains(response, "data-classification-unified-queue")
        self.assertContains(response, "data-classification-wait")
        self.assertContains(response, "contentSignature")
        self.assertContains(response, "CelerisRenderIcons")
        self.assertContains(response, "data-notifications-panel")
        self.assertContains(response, "Acessar sistema")
        self.assertNotContains(response, '> Todos</label>')
        self.assertNotContains(response, 'class="messages"')
        self.assertNotContains(response, 'class="card classification-tabs"')
        self.assertNotContains(response, ">Consultar</button>")
        self.assertNotContains(response, "class-action-toolbar")
        self.assertEqual(
            response.context["classification_list_url"],
            f"{reverse('classificacao_standalone')}?data={timezone.localdate().isoformat()}&filtro=agendados&filtro=classificados&filtro=nao_classificados",
        )
        self.assertContains(response, "has-both-queues")
        self.assertEqual(
            [item.pk for item in response.context["agendamentos"]],
            [self.agendamento.pk, agendamento_classificado.pk],
        )
        self.assertEqual(
            [item.pk for item in response.context["senhas"]],
            [senha.pk, senha_antiga.pk],
        )
        self.assertContains(response, "classification-row-completed", count=2)
        self.assertContains(response, "Paciente já classificado")
        with patch("apps.atendimento.views_painel.paineis_compativeis_agendamento") as paineis_compativeis:
            chamada_bloqueada = self.client.post(
                reverse(
                    "atendimento:chamar-agendamento-classificacao",
                    args=[agendamento_classificado.pk],
                ),
                {"return_to": reverse("classificacao_standalone")},
            )
        self.assertEqual(chamada_bloqueada.status_code, 302)
        paineis_compativeis.assert_not_called()

        data_sem_agendamentos = timezone.localdate() + timedelta(days=45)
        without_scheduled = self.client.get(
            reverse("classificacao_standalone"),
            {"data": data_sem_agendamentos.isoformat()},
        )
        self.assertEqual(
            without_scheduled.context["filtros_fila"],
            ["classificados", "nao_classificados"],
        )
        self.assertFalse(without_scheduled.context["mostrar_agendados"])
        self.assertTrue(without_scheduled.context["mostrar_demanda"])
        self.assertContains(without_scheduled, 'class="classification-unified-queue"')
        self.assertNotContains(without_scheduled, 'class="classification-unified-queue has-both-queues"')

        only_classified = self.client.get(reverse("classificacao_standalone"), {"filtro": "classificados"})
        self.assertFalse(only_classified.context["mostrar_agendados"])
        self.assertTrue(only_classified.context["mostrar_demanda"])
        self.assertEqual([item.pk for item in only_classified.context["senhas"]], [senha_antiga.pk])
        only_unclassified = self.client.get(
            reverse("classificacao_standalone"), {"filtro": "nao_classificados"}
        )
        self.assertEqual([item.pk for item in only_unclassified.context["senhas"]], [senha.pk])
        only_scheduled = self.client.get(reverse("classificacao_standalone"), {"filtro": "agendados"})
        self.assertTrue(only_scheduled.context["mostrar_agendados"])
        self.assertFalse(only_scheduled.context["mostrar_demanda"])
        self.assertEqual(only_scheduled.context["senhas"], [])
        only_scheduled_uppercase = self.client.get(
            reverse("classificacao_standalone"),
            {"filtro": "AGENDADOS", "parcial": "fila_unificada"},
        )
        self.assertContains(only_scheduled_uppercase, "data-classification-scheduled-section")
        self.assertContains(only_scheduled_uppercase, "data-classification-demand-section hidden")
        self.assertNotContains(only_scheduled_uppercase, senha.ds_senha)

        all_queues = self.client.get(
            reverse("classificacao_standalone"),
            {"filtro": ["agendados", "classificados", "nao_classificados"], "parcial": "fila_unificada"},
        )
        self.assertContains(all_queues, "data-classification-scheduled-section")
        self.assertContains(all_queues, "data-classification-demand-section")
        self.assertContains(all_queues, senha_antiga.ds_senha)

        escala_configurada = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Escala sem rotulo legado",
            ds_perguntas=[
                {
                    "chave": "ocular",
                    "texto": "Abertura ocular",
                    "opcoes": [{"valor": "1", "descricao": "Ausente", "pontos": 1}],
                }
            ],
        )
        EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Escala vazia que não deve aparecer",
            ds_perguntas=[],
        )
        fluxo = FluxoClassificacao.objects.create(
            cd_empresa=self.empresa,
            nm_grupo="Clínica geral",
            nm_fluxo="Mal-estar geral",
            nr_ordem=10,
        )
        FluxoClassificacaoEscala.objects.create(
            cd_empresa=self.empresa,
            cd_fluxo_classificacao=fluxo,
            cd_escala_clinica=escala_configurada,
        )
        modelo_catalogo("raca_cor").objects.update_or_create(
            cd_valor="03",
            defaults={"ds_valor": "Parda", "sn_ativo": True},
        )
        self.paciente.ds_cor_raca = "03"
        self.paciente.save(update_fields=["ds_cor_raca"])
        senha.cd_paciente = self.paciente
        senha.save(update_fields=["cd_paciente"])
        editor = self.client.get(reverse("classificacao_standalone"), {"senha": senha.pk})
        self.assertEqual(editor.status_code, 200)
        self.assertContains(editor, "Abertura ocular")
        self.assertNotContains(editor, "Escala vazia que não deve aparecer")
        self.assertContains(editor, f'data-flow-scales="{escala_configurada.pk}"')
        self.assertContains(editor, "class-action-toolbar")
        self.assertContains(editor, "data-classification-editor")
        self.assertContains(editor, "data-classification-patient-search")
        self.assertContains(editor, "data-classification-pre-registration")
        self.assertContains(editor, "data-scale-dialog")
        self.assertContains(editor, "Score total:")
        self.assertContains(editor, "Resultado:")
        self.assertContains(editor, "executePatientSearch")
        self.assertContains(editor, "data-classification-colors")
        self.assertContains(editor, "<b>Raça/cor</b>Parda", html=True)
        self.assertContains(editor, "data-questions-dialog")
        self.assertContains(editor, "data-allergy-add")
        self.assertContains(editor, "data-no-sort")
        self.assertContains(editor, "classification-flow-options")
        self.assertNotContains(
            editor,
            '<form class="card classification-queue-filters classification-unified-filters"',
        )
        self.assertNotContains(editor, '<div class="classification-unified-queue"')

    def test_perguntas_icones_e_escalas_recomendadas_do_fluxo(self):
        self.login_as(self.ti_user)
        pergunta = "Paciente está com dor torácica, náusea/vômito ou febre (≥ 38°C)?"
        resposta = self.client.post(
            reverse("class_perguntas"),
            {
                "new_name": pergunta,
                "new_type": "SIM_NAO",
                "new_order": "10",
                "new_required": "true",
                "new_active": "true",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(PerguntaClassificacao.objects.filter(cd_empresa=self.empresa, nm_pergunta=pergunta).exists())

        icone = IconeChamada.objects.create(
            cd_empresa=self.empresa,
            nm_icone="Prioridade clínica",
            ds_svg='<svg viewBox="0 0 24 24"><path d="M12 2v20"/></svg>',
        )
        seletor = self.client.get(reverse("class_senhas"))
        self.assertContains(seletor, "data-call-icon-label")
        self.assertContains(seletor, icone.nm_icone)

        cor = CorClassificacaoRisco.objects.create(
            cd_empresa=self.empresa,
            nm_cor="Laranja",
            cd_cor="LARANJA",
            ds_cor_hex="#f97316",
            nr_prioridade=2,
        )
        fluxo = FluxoClassificacao.objects.create(
            cd_empresa=self.empresa,
            nm_grupo="Dor",
            nm_fluxo="Dor torácica",
            ds_orientacao="Aplicar escala recomendada.",
            cd_cor_recomendada=cor,
        )
        escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Escala de dor torácica",
            ds_perguntas=[{"chave": "intensidade", "texto": "Intensidade", "opcoes": []}],
        )
        pagina = self.client.get(reverse("class_fluxos"))
        self.assertContains(pagina, reverse("class_fluxo_escalas", args=[fluxo.pk]))
        self.assertContains(pagina, "#f97316")
        self.assertContains(pagina, 'class="flow-color-picker"')
        self.assertContains(pagina, 'data-color="${escapeHTML(color.cor)}"')
        self.assertContains(pagina, 'fieldMetadata("fluxo_classificacao", "cd_cor_recomendada")')
        self.assertContains(pagina, "selectActiveRow")
        self.assertContains(pagina, "groupRowMarkup(item, index, {queryResult: true})")
        self.assertContains(pagina, 'data-group-field="nome"')
        self.assertNotContains(pagina, 'class="flow-color-swatch"')

        pagina_escalas = self.client.get(reverse("class_fluxo_escalas", args=[fluxo.pk]))
        self.assertEqual(pagina_escalas.status_code, 200)
        self.assertContains(pagina_escalas, "class-action-toolbar")
        self.assertContains(pagina_escalas, 'data-action="save"')
        self.assertContains(pagina_escalas, 'data-action="new"')
        self.assertContains(pagina_escalas, 'data-action="close"')
        self.assertContains(pagina_escalas, "<th>Ordem</th><th>Escala recomendada</th>", html=True)

        salvar = self.client.post(
            reverse("class_fluxo_escalas", args=[fluxo.pk]),
            {
                "link_id": "",
                "scale_id": str(escala.pk),
                "order": "10",
                "active": "true",
                "delete": "0",
            },
        )
        self.assertEqual(salvar.status_code, 302)
        self.assertTrue(
            FluxoClassificacaoEscala.objects.filter(
                cd_fluxo_classificacao=fluxo,
                cd_escala_clinica=escala,
            ).exists()
        )
        vinculo_salvo = FluxoClassificacaoEscala.objects.get(
            cd_fluxo_classificacao=fluxo,
            cd_escala_clinica=escala,
        )
        pagina_reaberta = self.client.get(reverse("class_fluxo_escalas", args=[fluxo.pk]))
        self.assertContains(pagina_reaberta, f'value="{vinculo_salvo.pk}" data-primary-key="true"')
        self.assertContains(pagina_reaberta, "MutationObserver")
        self.assertContains(pagina_reaberta, "maxOrder + 1")

        outro_fluxo = FluxoClassificacao.objects.create(
            cd_empresa=self.empresa,
            nm_grupo="Neurologia",
            nm_fluxo="Cefaleia",
            ds_orientacao="Aplicar a mesma escala neste outro sintoma.",
        )
        salvar_em_outro_fluxo = self.client.post(
            reverse("class_fluxo_escalas", args=[outro_fluxo.pk]),
            {
                "link_id": "",
                "scale_id": str(escala.pk),
                "order": "1",
                "active": "true",
                "delete": "0",
            },
        )
        self.assertEqual(salvar_em_outro_fluxo.status_code, 302)
        self.assertEqual(
            FluxoClassificacaoEscala.objects.filter(cd_escala_clinica=escala).count(),
            2,
        )

        duplicada = self.client.post(
            reverse("class_fluxo_escalas", args=[fluxo.pk]),
            {
                "link_id": "",
                "scale_id": str(escala.pk),
                "order": "20",
                "active": "true",
                "delete": "0",
            },
        )
        self.assertEqual(duplicada.status_code, 200)
        self.assertContains(duplicada, "já está vinculada a este mesmo sintoma")
        self.assertEqual(
            FluxoClassificacaoEscala.objects.filter(
                cd_fluxo_classificacao=fluxo,
                cd_escala_clinica=escala,
            ).count(),
            1,
        )

        outra_escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Escala respiratória",
            ds_perguntas=[{"chave": "respiracao", "texto": "Respiração", "opcoes": []}],
        )
        primeiro_vinculo = FluxoClassificacaoEscala.objects.get(
            cd_fluxo_classificacao=fluxo,
            cd_escala_clinica=escala,
        )
        segundo_vinculo = FluxoClassificacaoEscala.objects.create(
            cd_empresa=self.empresa,
            cd_fluxo_classificacao=fluxo,
            cd_escala_clinica=outra_escala,
            nr_ordem=20,
        )
        troca = self.client.post(
            reverse("class_fluxo_escalas", args=[fluxo.pk]),
            {
                "link_id": [str(primeiro_vinculo.pk), str(segundo_vinculo.pk)],
                "scale_id": [str(outra_escala.pk), str(escala.pk)],
                "order": ["10", "20"],
                "active": ["true", "true"],
                "delete": ["0", "0"],
            },
        )
        self.assertEqual(troca.status_code, 302)
        self.assertEqual(
            FluxoClassificacaoEscala.objects.get(
                cd_fluxo_classificacao=fluxo,
                cd_escala_clinica=outra_escala,
            ).nr_ordem,
            10,
        )
        self.assertEqual(
            FluxoClassificacaoEscala.objects.get(
                cd_fluxo_classificacao=fluxo,
                cd_escala_clinica=escala,
            ).nr_ordem,
            20,
        )

    def test_class_configura_escala_com_perguntas_formula_e_resultados(self):
        self.login_as(self.ti_user)
        pagina = self.client.get(reverse("class_escalas"))
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, "Perguntas e respostas")
        self.assertContains(pagina, "Fórmula de cálculo")
        self.assertContains(pagina, "Faixas de resultado")

        resposta = self.client.post(
            reverse("class_escalas"),
            {
                "nm_escala": "Escala de dor configurável",
                "ds_descricao": "Calcula o grau de dor do paciente.",
                "tp_calculo": "SOMA",
                "sn_ativo": "true",
                "perguntas_json": json.dumps([
                    {
                        "chave": "careta",
                        "texto": "Paciente faz careta?",
                        "ativo": True,
                        "opcoes": [
                            {"valor": "sim", "descricao": "Sim", "pontos": 1, "ativo": True},
                            {"valor": "nao", "descricao": "Não", "pontos": 0, "ativo": True},
                        ],
                    },
                    {
                        "chave": "choro",
                        "texto": "Paciente chora?",
                        "ativo": True,
                        "opcoes": [{"valor": "sim", "descricao": "Sim", "pontos": 2, "ativo": True}],
                    },
                ]),
                "formula_json": json.dumps([
                    {"tipo": "PERGUNTA", "valor": "careta"},
                    {"tipo": "OPERADOR", "valor": "+"},
                    {"tipo": "PERGUNTA", "valor": "choro"},
                    {
                        "tipo": "CONDICAO",
                        "variavel": "paciente.idade",
                        "comparador": ">",
                        "referencia": 70,
                        "acrescimo": 1,
                    },
                ]),
                "faixas_json": json.dumps([
                    {"min": 0, "max": 1, "descricao": "Dor leve", "cor": "#22c55e"},
                    {"min": 2, "max": 3, "descricao": "Dor moderada"},
                ]),
            },
        )
        escala = EscalaClinica.objects.get(cd_empresa=self.empresa, nm_escala="Escala de dor configurável")
        self.assertRedirects(resposta, reverse("class_escala_editar", args=[escala.pk]))
        self.assertEqual(escala.ds_expressao_calculo, "{{careta}} + {{choro}}")
        self.assertEqual(escala.ds_condicoes_calculo[0]["variavel"], "paciente.idade")
        self.assertEqual(escala.ds_condicoes_calculo[0]["acrescimo"], 1)
        self.assertEqual(len(escala.ds_perguntas), 2)
        self.assertEqual(escala.ds_perguntas[0]["opcoes"][0]["valor"], "1")
        self.assertEqual(escala.ds_perguntas[0]["opcoes"][0]["pontos"], 1)
        self.assertEqual(escala.ds_faixas_resultado[0]["cor"], "#22c55e")
        self.assertEqual(escala.ds_faixas_resultado[1]["descricao"], "Dor moderada")

        edicao = self.client.get(reverse("class_escala_editar", args=[escala.pk]))
        self.assertContains(edicao, "Paciente faz careta?")
        self.assertContains(edicao, "Dor moderada")
        self.assertContains(edicao, "data-scale-editor")
        self.assertContains(edicao, "Condição")
        self.assertContains(edicao, "Idade do paciente")
        self.assertContains(edicao, 'data-action="undo"')
        self.assertContains(edicao, 'data-action="redo"')
        self.assertContains(edicao, "data-record-status")
        self.assertContains(edicao, "data-general-record-status")
        self.assertContains(edicao, "activateTableRow")

    def test_class_exige_nova_validacao_somente_quando_formula_muda(self):
        self.login_as(self.ti_user)
        escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Escala com validação",
            ds_perguntas=[
                {
                    "chave": "dor",
                    "texto": "Dor",
                    "ativo": True,
                    "opcoes": [{"valor": "1", "descricao": "Sim", "pontos": 1, "ativo": True}],
                }
            ],
            ds_expressao_calculo="{{dor}}",
        )
        dados_base = {
            "nm_escala": escala.nm_escala,
            "ds_descricao": "Descrição atualizada",
            "tp_calculo": "SOMA",
            "sn_ativo": "true",
            "perguntas_json": json.dumps(escala.ds_perguntas),
            "formula_json": json.dumps([{"tipo": "PERGUNTA", "valor": "dor"}]),
            "faixas_json": "[]",
            "formula_validada": "false",
        }

        apenas_descricao = self.client.post(reverse("class_escala_editar", args=[escala.pk]), dados_base)
        self.assertRedirects(apenas_descricao, reverse("class_escala_editar", args=[escala.pk]))
        escala.refresh_from_db()
        self.assertEqual(escala.ds_descricao, "Descrição atualizada")

        dados_base["formula_json"] = json.dumps([{"tipo": "NUMERO", "valor": "2"}])
        formula_alterada = self.client.post(reverse("class_escala_editar", args=[escala.pk]), dados_base)
        self.assertEqual(formula_alterada.status_code, 200)
        self.assertContains(formula_alterada, "A fórmula foi alterada e ainda não foi validada")
        self.assertContains(formula_alterada, 'class="scale-formula-status invalid"')
        escala.refresh_from_db()
        self.assertEqual(escala.ds_expressao_calculo, "{{dor}}")

    def test_tabelas_class_permit_em_consulta_e_usam_layout_padrao(self):
        pergunta = PerguntaClassificacao.objects.create(
            cd_empresa=self.empresa,
            nm_pergunta="Pergunta exclusiva da homologacao",
            tp_resposta="SIM_NAO",
            nr_ordem=1,
        )
        fluxo = FluxoClassificacao.objects.create(
            cd_empresa=self.empresa,
            nm_grupo="Grupo homologacao",
            nm_fluxo="Fluxo exclusivo da homologacao",
            nr_ordem=1,
        )
        self.login_as(self.ti_user)

        perguntas = self.client.get(reverse("class_perguntas"), {"q": "exclusiva"})
        self.assertEqual(perguntas.status_code, 200)
        self.assertContains(perguntas, pergunta.nm_pergunta)
        self.assertContains(perguntas, "Obrigatória")
        self.assertContains(perguntas, 'class="class-standalone-main content"')

        fluxos = self.client.get(reverse("class_fluxos"), {"q": "exclusivo"})
        self.assertEqual(fluxos.status_code, 200)
        self.assertContains(fluxos, "Fluxo exclusivo da homologacao")
        self.assertContains(fluxos, 'data-scale-table="groups"')
        self.assertContains(fluxos, 'data-scale-table="symptoms"')
        self.assertNotContains(fluxos, "Pesquisar grupos e sintomas")
        self.assertContains(fluxos, "celeris:context-table-query-open")

        salvo = self.client.post(
            reverse("class_fluxos"),
            {
                "grupos_json": json.dumps([
                    {
                        "id": fluxo.cd_grupo_id,
                        "chave": str(fluxo.cd_grupo_id),
                        "nome": "Grupo homologacao",
                        "descricao": "Grupo principal",
                        "ordem": 10,
                        "ativo": True,
                    },
                    {
                        "id": None,
                        "chave": "novo_1",
                        "nome": "Traumas",
                        "descricao": "Sintomas traumáticos",
                        "ordem": 20,
                        "ativo": True,
                    },
                ]),
                "sintomas_json": json.dumps([
                    {
                        "id": fluxo.pk,
                        "grupo_chave": str(fluxo.cd_grupo_id),
                        "nome": fluxo.nm_fluxo,
                        "orientacao": "Orientação atualizada",
                        "cor_id": "",
                        "ordem": 10,
                        "ativo": True,
                    },
                    {
                        "id": None,
                        "grupo_chave": "novo_1",
                        "nome": "Queda",
                        "orientacao": "Avaliar trauma",
                        "cor_id": "",
                        "ordem": 10,
                        "ativo": True,
                    },
                ]),
                "grupos_excluidos_json": "[]",
                "sintomas_excluidos_json": "[]",
            },
        )
        self.assertRedirects(salvo, reverse("class_fluxos"))
        queda = FluxoClassificacao.objects.get(cd_empresa=self.empresa, nm_fluxo="Queda")
        self.assertEqual(queda.cd_grupo.nm_grupo, "Traumas")
        self.assertEqual(queda.nm_grupo, "Traumas")

    def test_configuracao_senha_aplica_protocolo_e_tempo_na_subdivisao(self):
        protocolo = ProtocoloSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            sg_protocolo="PREF",
            nm_protocolo="Atendimento preferencial",
            ds_protocolo="Priorizar conforme condição clínica.",
        )
        self.login_as(self.ti_user)
        page = self.client.get(f"{reverse('class_senhas')}?novo=1")
        self.assertContains(page, 'name="new_rule_protocol"')
        self.assertContains(page, 'data-password-rules-section')
        self.assertNotContains(page, "Adicionar subdivisão")
        self.assertNotContains(page, 'name="cd_protocolo"')

        saved = self.client.post(
            reverse("class_senhas"),
            {
                "nm_tipo_senha": "Adulto preferencial",
                "sg_tipo_senha": "AP",
                "new_rule_name": "Idoso",
                "new_rule_acronym": "I",
                "new_rule_priority": "2",
                "new_rule_min_age": "75",
                "new_rule_max_age": "",
                "new_rule_protocol": str(protocolo.pk),
                "new_rule_timeout": "20",
                "new_rule_icon": "",
                "new_rule_active": "true",
            },
        )
        tipo = TipoSenhaAtendimento.objects.get(cd_empresa=self.empresa, sg_tipo_senha="AP")
        self.assertRedirects(saved, reverse("class_senha_editar", args=[tipo.pk]))
        regra = RegraSubdivisaoSenha.objects.get(cd_tipo_senha=tipo)
        self.assertEqual(regra.cd_protocolo, protocolo)
        self.assertEqual(regra.nr_tempo_limite, 20)

        generated = self.client.post(reverse("atendimento:gerar-senha-totem"), {"regra": regra.pk})
        self.assertEqual(generated.status_code, 200)
        senha = SenhaAtendimento.objects.get(cd_tipo_senha=tipo)
        self.assertEqual(senha.nr_tempo_limite, 20)

    def test_classificacao_demanda_pre_cadastra_e_prefill_na_recepcao(self):
        tipo = TipoSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            nm_tipo_senha="Demanda",
            sg_tipo_senha="D",
        )
        cor = CorClassificacaoRisco.objects.create(
            cd_empresa=self.empresa,
            cd_cor="VERDE",
            nm_cor="Verde",
            ds_cor_hex="#22c55e",
        )
        classe = ClasseSenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            nm_classe_senha="Normal",
            sg_classe_senha="N",
            cd_cor_classificacao=cor,
        )
        senha = SenhaAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_tipo_senha=tipo,
            cd_classe_senha=classe,
            nr_senha=2,
            ds_senha="DN 02",
        )
        self.login_as(self.enfermeiro)
        classified = self.client.post(
            reverse("atendimento:fila-classificacao"),
            {
                "acao": "finalizar",
                "senha_id": senha.pk,
                "cor_classificacao": cor.pk,
                "nm_pre_cadastro": "PACIENTE PRÉ-CADASTRADO",
                "dt_nascimento_pre_cadastro": "2001-02-03",
                "nm_mae_pre_cadastro": "MÃE DO PACIENTE",
                "tp_sexo_pre_cadastro": "F",
                "nr_prioridade": "4",
                "ds_queixa_principal": "Queixa de demanda",
                "cd_prestador_responsavel": self.prestador.pk,
            },
        )
        self.assertEqual(classified.status_code, 302)
        senha.refresh_from_db()
        self.assertIsNone(senha.cd_paciente_id)
        self.assertEqual(senha.nm_pre_cadastro, "PACIENTE PRÉ-CADASTRADO")

        self.login_as(self.recepcionista)
        reception = self.client.get(reverse("atendimento:recepcao"))
        self.assertContains(reception, senha.nm_pre_cadastro)
        self.assertContains(reception, senha.nm_mae_pre_cadastro)
        self.assertContains(reception, "03/02/2001")
        self.assertContains(reception, "data-reception-wait")
        self.assertNotContains(reception, "Completar cadastro")
        self.assertNotContains(reception, "Recepcionar senha")
        cadastro_url = (
            f"{reverse('atendimento:cadastro-paciente-agendamento')}?recepcao_direta=1&senha={senha.pk}"
        )
        form_response = self.client.get(cadastro_url)
        self.assertEqual(form_response.context["form"]["nm_paciente"].value(), "PACIENTE PRÉ-CADASTRADO")
        saved = self.client.post(
            cadastro_url,
            {
                "nm_paciente": "PACIENTE PRÉ-CADASTRADO",
                "dt_nascimento": "2001-02-03",
                "nm_mae": "MÃE DO PACIENTE",
            },
        )
        self.assertEqual(saved.status_code, 302)
        senha.refresh_from_db()
        self.assertIsNotNone(senha.cd_paciente_id)
        self.assertIsNotNone(senha.cd_pre_atendimento_id)

    def test_configuracao_totem_inicia_em_consulta_e_exibe_tabelas_normalizadas(self):
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:configurar-senhas"))
        self.assertContains(response, 'data-start-query="true"')
        self.assertContains(response, 'data-consultable="true"')
        self.assertContains(response, "menor = mais prioridade")
        self.assertNotContains(response, "ticket-rules-table")
        classes = self.client.get(reverse("atendimento:classes-senha"))
        protocolos = self.client.get(reverse("atendimento:protocolos-senha"))
        self.assertContains(classes, 'data-editable-table')
        self.assertContains(protocolos, 'data-editable-table')

    def test_tabelas_totem_criam_editam_e_excluem_linhas(self):
        self.login_as(self.ti_user)
        created_class = self.client.post(
            reverse("atendimento:classes-senha"),
            {
                "new_name": "Gestante",
                "new_acronym": "G",
                "new_priority": "2",
                "new_icon": "baby",
                "new_active": "true",
            },
        )
        self.assertRedirects(created_class, f"{reverse('atendimento:classes-senha')}?consultar=1")
        classe = ClasseSenhaAtendimento.objects.get(cd_empresa=self.empresa, nm_classe_senha="Gestante")
        created_protocol = self.client.post(
            reverse("atendimento:protocolos-senha"),
            {
                "new_name": "Acolhimento",
                "new_description": "Fluxo inicial",
                "new_active": "true",
            },
        )
        self.assertRedirects(created_protocol, f"{reverse('atendimento:protocolos-senha')}?consultar=1")
        protocolo = ProtocoloSenhaAtendimento.objects.get(cd_empresa=self.empresa, nm_protocolo="Acolhimento")

        self.client.post(
            reverse("atendimento:classes-senha"),
            {
                f"name_{classe.pk}": "Gestante prioritária",
                f"acronym_{classe.pk}": "GP",
                f"priority_{classe.pk}": "1",
                f"icon_{classe.pk}": "baby",
                f"active_{classe.pk}": "true",
            },
        )
        classe.refresh_from_db()
        self.assertEqual(classe.nm_classe_senha, "Gestante prioritária")

        self.client.post(
            reverse("atendimento:protocolos-senha"),
            {f"delete_{protocolo.pk}": "1"},
        )
        self.assertFalse(ProtocoloSenhaAtendimento.objects.filter(pk=protocolo.pk).exists())

    def test_pep_lista_dois_atendimentos_abertos_do_mesmo_paciente(self):
        outro = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="ABERTO",
            ds_especialidade="CLINICA_GERAL",
        )
        segundo = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="AGUARDANDO_CLASSIFICACAO",
            ds_especialidade="CARDIOLOGIA",
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:pep"),
            {
                "aba": "atendimentos",
                "especialidades_atendimento": ["CLINICA_GERAL", "CARDIOLOGIA"],
            },
        )
        self.assertContains(response, f"<td>{outro.pk}</td>", html=True)
        self.assertContains(response, f"<td>{segundo.pk}</td>", html=True)

    def test_cadastro_painel_chamada_consulta_navega_e_alterna_status(self):
        setor = Setor.objects.create(
            cd_empresa=self.empresa,
            nm_setor="SALA DE ATENDIMENTO",
            tp_setor=Setor.TipoSetor.ATENDIMENTO,
        )
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:paineis-chamada"),
            {
                "nm_painel": "PAINEL PRINCIPAL",
                "ds_descricao": "Recepção",
                "nm_maquina": "PAINEL-01",
                "tp_painel": "PAINEL",
                "nr_referencia": "1",
                "ds_local_exibicao": "TÉRREO",
                "ds_mensagem_padrao": "DIRIJA-SE AO LOCAL",
                "nr_tempo_exibicao": "10",
                "ds_layout": "padrao",
                "ds_tamanho": "medio",
                "ds_cor": "azul",
                "ds_prioridade_visual": "normal",
                "sn_voz": "True",
                "ds_midia_url": "",
                "ds_observacao": "",
                "setores": [setor.pk],
            },
        )
        painel = PainelChamada.objects.get(nm_maquina="PAINEL-01")
        self.assertRedirects(response, reverse("atendimento:cadastro-painel-chamada", args=[painel.pk]))
        self.assertEqual(list(painel.setores.all()), [setor])

        consulta = self.client.get(reverse("atendimento:paineis-chamada"), {"consultar": "1"})
        self.assertRedirects(consulta, reverse("atendimento:cadastro-painel-chamada", args=[painel.pk]))
        cadastro = self.client.get(reverse("atendimento:cadastro-painel-chamada", args=[painel.pk]))
        self.assertContains(cadastro, "data-assignment-values")
        self.assertNotContains(cadastro, "Salvar painel")

        self.client.post(reverse("atendimento:alternar-status-painel-chamada", args=[painel.pk]))
        painel.refresh_from_db()
        self.assertFalse(painel.sn_ativo)

    def test_modelo_documento_cria_versoes_visuais(self):
        self.login_as(self.ti_user)
        pagina = self.client.get(reverse("atendimento:modelos-documento"))
        self.assertContains(pagina, "Documentos do Celeris")
        self.assertContains(pagina, "Editor de documentos")
        self.assertContains(pagina, "grapes.min.js")
        self.assertContains(pagina, "data-document-form-builder")
        self.assertNotContains(pagina, ">Adicionar campo<")
        self.assertContains(pagina, "Passe o mouse sobre uma célula vazia")
        self.assertContains(pagina, "data-grid-columns")
        self.assertContains(pagina, "data-grid-rows")
        self.assertContains(pagina, "data-grid-font-size")
        self.assertContains(pagina, "data-grid-font-family")
        self.assertContains(pagina, "Campo reutilizável")
        self.assertContains(pagina, "data-field-image-file")
        self.assertContains(pagina, 'data-settings-property="imageWidth"')
        self.assertContains(pagina, 'data-settings-property="imageHeight"')
        self.assertContains(pagina, 'data-settings-property="lockAspectRatio"')
        self.assertContains(pagina, 'data-settings-property="prefix"')
        self.assertContains(pagina, 'data-settings-property="suffix"')
        self.assertContains(pagina, 'data-settings-property="fontSize"')
        self.assertContains(pagina, 'data-settings-property="fontFamily"')
        self.assertContains(pagina, 'data-settings-property="textColor"')
        self.assertContains(pagina, 'value="static-text"')
        self.assertContains(pagina, 'value="static-variable"')
        self.assertContains(pagina, "data-screen-variable-palette")
        self.assertContains(pagina, "data-screen-variable-search")
        self.assertContains(pagina, "data-screen-variable-list")
        self.assertNotContains(pagina, "data-screen-variable-picker")
        self.assertContains(pagina, "data-grid-context-menu")
        self.assertContains(pagina, "data-grid-remove-element")
        self.assertContains(pagina, "data-document-leave-modal")
        self.assertContains(pagina, "data-document-clear-modal")
        self.assertContains(pagina, 'data-setting-types="image"')
        self.assertContains(pagina, "data-document-test-context")
        self.assertContains(pagina, "sn_exibe_assinatura")
        self.assertContains(pagina, "tp_alinhamento_assinatura")
        self.assertContains(pagina, "sn_exibe_conselho_assinatura")
        self.assertContains(pagina, "reusable-print-elements")
        self.assertContains(pagina, "Gerar impressão")
        self.assertTrue(
            ModeloDocumento.objects.filter(
                nm_modelo="Admissão e anamnese",
                sn_sistema=True,
                tp_elemento="DOCUMENTO",
            ).exists()
        )

        self.assertNotContains(pagina, 'id="editor-tela"')
        self.assertContains(pagina, "data-document-preview-active")
        self.assertContains(pagina, "data-document-print-builder")
        self.assertContains(pagina, "data-print-grid-font-size")
        self.assertContains(pagina, "data-print-grid-font-family")
        self.assertContains(pagina, 'data-print-property="fontSize"')
        self.assertContains(pagina, 'data-print-property="fontFamily"')
        self.assertContains(pagina, 'data-print-property="verticalAlign"')
        self.assertContains(pagina, "data-disable-state-persistence")
        self.assertContains(pagina, "Texto fixo e variáveis")
        self.assertContains(pagina, 'data-print-property="sourceField"')
        self.assertContains(pagina, "data-print-code-highlight")
        self.assertContains(pagina, "data-print-image-file")
        self.assertContains(pagina, 'data-print-types="line,vline"')
        self.assertContains(pagina, 'data-print-property="lineStyle"')
        self.assertContains(pagina, 'data-print-property="showBottomBorder"')
        self.assertContains(pagina, 'data-action="undo"')
        self.assertContains(pagina, 'data-action="redo"')
        self.assertContains(pagina, "data-print-variable-list")
        self.assertContains(pagina, 'data-print-property="margin"')
        self.assertContains(pagina, 'data-print-property="padding"')
        self.assertContains(pagina, "data-print-regenerate-modal")
        self.assertContains(pagina, 'data-grid-insert-row="before"')
        self.assertNotContains(pagina, "Pré-visualizar formulário")
        self.assertNotContains(pagina, "Pré-visualizar impressão")
        self.assertContains(pagina, "Salvar teste e visualizar impressão")
        self.assertContains(pagina, "Nenhum documento aberto")
        self.assertContains(pagina, "data-document-library-toggle")
        self.assertContains(pagina, "Histórico de versões")
        self.assertContains(pagina, "novo=variavel")
        self.assertContains(pagina, "novo=bloco")
        self.assertContains(pagina, "data-custom-variable-help-modal")
        self.assertContains(pagina, "Unificar variáveis")
        self.assertContains(pagina, "data-print-variable-search")
        self.assertContains(pagina, 'data-print-types="field,variable"')
        self.assertContains(pagina, 'data-print-property="labelColor"')
        self.assertContains(pagina, 'data-print-property="textColor"')
        self.assertContains(pagina, 'data-print-property="textAlign"')
        self.assertContains(pagina, 'data-print-property="textBold"')
        self.assertContains(pagina, "data-print-source-group")
        self.assertContains(pagina, "data-field-settings-help-toggle")
        self.assertContains(pagina, "data-print-settings-help-toggle")
        self.assertNotContains(pagina, "Salvar nova versão")
        self.assertContains(pagina, "novo=cabecalho")
        self.assertContains(pagina, "novo=rodape")
        self.assertNotContains(pagina, "ModeloDocumento object")

        cabecalho = self.client.get(reverse("atendimento:modelos-documento"), {"novo": "cabecalho"})
        self.assertContains(cabecalho, 'value="CABECALHO"')
        self.assertNotContains(cabecalho, "Cabeçalho reutilizável")
        variavel = self.client.get(reverse("atendimento:modelos-documento"), {"novo": "variavel"})
        self.assertContains(variavel, "data-custom-variable-test")
        self.assertNotContains(variavel, "Layout da impressão")

        dados = {
            "nm_modelo": "Ficha visual",
            "tp_documento": "FICHA_ATENDIMENTO",
            "tp_elemento": "DOCUMENTO",
            "ds_alteracoes_versao": "Versão inicial",
            "ds_html_tela": "<main>Tela</main>",
            "ds_css_tela": "main{color:blue}",
            "ds_projeto_tela": '{"formFields":[{"id":"queixa","name":"queixa","label":"Queixa","type":"textarea","placeholder":"","required":true,"options":""}]}',
            "ds_html_impressao": "<main>Impressão</main>",
            "ds_css_impressao": "main{color:black}",
            "ds_projeto_impressao": "{}",
            "sn_ativo": "on",
        }
        resposta = self.client.post(reverse("atendimento:modelos-documento"), dados)
        self.assertEqual(resposta.status_code, 302)
        primeira = ModeloDocumento.objects.get(nm_modelo="Ficha visual", nr_versao=1)

        dados["ds_alteracoes_versao"] = "Ajuste do cabeçalho"
        dados["ds_html_tela"] = "<main>Tela revisada</main>"
        dados["return_to"] = reverse("atendimento:pep")
        resposta = self.client.post(reverse("atendimento:editar-modelo-documento", args=[primeira.pk]), dados)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.url, reverse("atendimento:pep"))
        segunda = ModeloDocumento.objects.get(nm_modelo="Ficha visual", nr_versao=2)
        primeira.refresh_from_db()
        self.assertFalse(primeira.sn_versao_atual)
        self.assertFalse(primeira.sn_ativo)
        self.assertTrue(segunda.sn_versao_atual)
        self.assertTrue(segunda.sn_ativo)
        self.assertEqual(segunda.cd_versao_anterior, primeira)

        dados["ds_alteracoes_versao"] = "Descrição sem mudança real"
        dados["return_to"] = ""
        sem_mudanca = self.client.post(reverse("atendimento:editar-modelo-documento", args=[segunda.pk]), dados)
        self.assertEqual(sem_mudanca.status_code, 200)
        self.assertContains(sem_mudanca, "Nenhuma alteração real foi identificada")
        self.assertEqual(ModeloDocumento.objects.filter(nm_modelo="Ficha visual").count(), 2)

        dados_variavel = {
            "nm_modelo": "Sexo extenso",
            "tp_documento": "ADMINISTRATIVO",
            "tp_elemento": "VARIAVEL",
            "ds_alteracoes_versao": "Cria vari?vel",
            "custom_variable_name": "sexo_extenso",
            "custom_variable_expression": '"Feminino" if paciente.sexo == "F" else "Masculino"',
            "ds_html_tela": "",
            "ds_css_tela": "",
            "ds_projeto_tela": "{}",
            "ds_html_impressao": "",
            "ds_css_impressao": "",
            "ds_projeto_impressao": "{}",
            "sn_ativo": "on",
        }
        resposta_variavel = self.client.post(reverse("atendimento:modelos-documento"), dados_variavel)
        self.assertEqual(resposta_variavel.status_code, 302)
        variavel_inicial = ModeloDocumento.objects.get(nm_modelo="Sexo extenso", nr_versao=1)
        self.assertEqual(variavel_inicial.ds_projeto_tela["customVariable"]["name"], "sexo_extenso")
        self.assertIn("Feminino", variavel_inicial.ds_projeto_tela["customVariable"]["expression"])

        dados_variavel["ds_alteracoes_versao"] = "Ajusta regra"
        dados_variavel["custom_variable_expression"] = '"Outro" if paciente.sexo == "O" else "Informado"'
        resposta_variavel = self.client.post(
            reverse("atendimento:editar-modelo-documento", args=[variavel_inicial.pk]),
            dados_variavel,
        )
        self.assertEqual(resposta_variavel.status_code, 302)
        variavel_revisada = ModeloDocumento.objects.get(nm_modelo="Sexo extenso", nr_versao=2)
        self.assertIn("Outro", variavel_revisada.ds_projeto_tela["customVariable"]["expression"])
        variavel_inicial.refresh_from_db()
        self.assertFalse(variavel_inicial.sn_versao_atual)

    def test_assinatura_documento_respeita_exibicao_alinhamento_e_conselho(self):
        modelo = ModeloDocumento(
            cd_empresa=self.empresa,
            nm_modelo="ASSINATURA CONFIGURAVEL",
            tp_documento="EVOLUCAO",
            sn_exibe_assinatura=False,
        )
        html = "<main><p>Conteúdo</p></main>"
        self.assertNotIn("data-celeris-signature", _configurar_assinatura_prestador(html, modelo))

        modelo.sn_exibe_assinatura = True
        modelo.tp_alinhamento_assinatura = "DIREITA"
        modelo.sn_exibe_conselho_assinatura = True
        configurado = _configurar_assinatura_prestador(html, modelo)
        self.assertIn("text-align:right", configurado)
        self.assertIn("width:max-content", configurado)
        self.assertIn("min-width:92mm", configurado)
        self.assertIn("max-width:100%", configurado)
        self.assertIn("width:100%;height:34px", configurado)
        self.assertIn("{{ prestador.conselho }}", configurado)
        self.assertIn("{{ prestador.numero_conselho }}", configurado)
        self.assertIn("{{ prestador.uf_conselho }}", configurado)

    def test_variavel_personalizada_avalia_condicoes_e_calculos(self):
        contexto = {
            "paciente.sexo": "F",
            "paciente.nome": "Maria da silva",
            "atendimento.codigo": 10,
            "atendimento.data_hora": "28/06/2026 14:45:30",
        }
        self.assertEqual(
            _avaliar_expressao_variavel(
                '"Feminino" if paciente.sexo == "F" else "Masculino"',
                contexto,
            ),
            "Feminino",
        )
        self.assertEqual(_avaliar_expressao_variavel("atendimento.codigo * 2", contexto), 20)
        self.assertEqual(_avaliar_expressao_variavel("data(atendimento.data_hora)", contexto), "28/06/2026")
        self.assertEqual(_avaliar_expressao_variavel("hora(atendimento.data_hora)", contexto), "14:45:30")
        self.assertEqual(
            _avaliar_expressao_variavel('juntar(maiusculo(paciente.nome), " #", atendimento.codigo)', contexto),
            "MARIA DA SILVA #10",
        )
        self.assertEqual(_avaliar_expressao_variavel('__import__("os")', contexto), "")

    def test_variavel_personalizada_pode_ser_executada_com_atendimento_de_teste(self):
        self.login_as(self.ti_user)
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_tipo_atendimento="CONSULTA",
        )
        response = self.client.post(
            reverse("atendimento:testar-variavel-documento"),
            {
                "atendimento": atendimento.pk,
                "expressao": 'juntar(maiusculo(paciente.nome), " #", atendimento.codigo)',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], f"{self.paciente.nm_paciente.upper()} #{atendimento.pk}")
        invalid = self.client.post(
            reverse("atendimento:testar-variavel-documento"),
            {"atendimento": atendimento.pk, "expressao": '__import__("os")'},
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(invalid.json()["ok"])

    def test_documento_padrao_pode_ser_copiado_e_revisado_por_superusuario(self):
        self.login_as(self.ti_user)
        editor = self.client.get(reverse("atendimento:modelos-documento"))
        pasta = PastaDocumento.objects.get(cd_empresa=self.empresa, nm_pasta="Cabeçalhos")
        self.assertIn(pasta, editor.context["pastas_destino"])
        padrao = ModeloDocumento.objects.get(
            cd_empresa__isnull=True,
            nm_modelo="Admissão e anamnese",
            sn_versao_atual=True,
        )
        copia_response = self.client.post(
            reverse("atendimento:modelos-documento"),
            {
                "acao": "copiar",
                "tipo_item": "documento",
                "item_id": padrao.pk,
                "novo_nome": "Anamnese institucional",
                "destino_id": pasta.pk,
            },
        )
        copia = ModeloDocumento.objects.get(cd_empresa=self.empresa, nm_modelo="Anamnese institucional")
        self.assertRedirects(
            copia_response,
            reverse("atendimento:editar-modelo-documento", args=[copia.pk]),
        )
        self.assertEqual(copia.cd_pasta, pasta)
        self.assertTrue(copia.sn_editavel)
        self.assertFalse(copia.sn_sistema)

        self.ti_user.is_superuser = True
        self.ti_user.save(update_fields=["is_superuser"])
        review_response = self.client.post(
            reverse("atendimento:editar-modelo-documento", args=[padrao.pk]),
            {
                "pasta_selecionada": padrao.cd_pasta_id,
                "nm_modelo": padrao.nm_modelo,
                "tp_documento": padrao.tp_documento,
                "tp_elemento": padrao.tp_elemento,
                "cd_cabecalho": padrao.cd_cabecalho_id or "",
                "cd_rodape": padrao.cd_rodape_id or "",
                "ds_alteracoes_versao": "Revisão do superusuário",
                "ds_html_tela": padrao.ds_html_tela,
                "ds_css_tela": padrao.ds_css_tela,
                "ds_projeto_tela": json.dumps(padrao.ds_projeto_tela),
                "ds_html_impressao": f"{padrao.ds_html_impressao}<p>Revisado</p>",
                "ds_css_impressao": padrao.ds_css_impressao,
                "ds_projeto_impressao": json.dumps(padrao.ds_projeto_impressao),
                "sn_ativo": "on",
            },
        )
        self.assertEqual(review_response.status_code, 302)
        revisado = ModeloDocumento.objects.get(
            cd_empresa__isnull=True,
            nm_modelo=padrao.nm_modelo,
            nr_versao=2,
        )
        self.assertTrue(revisado.sn_sistema)
        self.assertFalse(revisado.sn_editavel)
        self.assertIn('data-celeris-signature="true"', revisado.ds_html_impressao)

    def test_documento_padrao_nao_superusuario_salva_como_copia_da_empresa(self):
        self.login_as(self.ti_user)
        self.client.get(reverse("atendimento:modelos-documento"))
        pasta = PastaDocumento.objects.get(cd_empresa=self.empresa, nm_pasta="Cabeçalhos")
        padrao = ModeloDocumento.objects.get(
            cd_empresa__isnull=True,
            nm_modelo="Admissão e anamnese",
            sn_versao_atual=True,
        )
        response = self.client.post(
            reverse("atendimento:editar-modelo-documento", args=[padrao.pk]),
            {
                "salvar_como_empresa": "1",
                "pasta_selecionada": pasta.pk,
                "nm_modelo": "Anamnese adaptada",
                "tp_documento": padrao.tp_documento,
                "tp_elemento": padrao.tp_elemento,
                "cd_cabecalho": padrao.cd_cabecalho_id or "",
                "cd_rodape": padrao.cd_rodape_id or "",
                "ds_alteracoes_versao": "Adaptação institucional",
                "ds_html_tela": padrao.ds_html_tela,
                "ds_css_tela": padrao.ds_css_tela,
                "ds_projeto_tela": json.dumps(padrao.ds_projeto_tela),
                "ds_html_impressao": f"{padrao.ds_html_impressao}<p>Empresa</p>",
                "ds_css_impressao": padrao.ds_css_impressao,
                "ds_projeto_impressao": json.dumps(padrao.ds_projeto_impressao),
                "sn_ativo": "on",
            },
        )
        copia = ModeloDocumento.objects.get(cd_empresa=self.empresa, nm_modelo="Anamnese adaptada")
        self.assertRedirects(response, reverse("atendimento:editar-modelo-documento", args=[copia.pk]))
        self.assertEqual(copia.cd_pasta, pasta)
        self.assertFalse(copia.sn_sistema)
        self.assertTrue(copia.sn_editavel)

    def test_editor_usa_pasta_selecionada_e_protege_pastas_padrao(self):
        self.login_as(self.ti_user)
        self.client.get(reverse("atendimento:modelos-documento"))
        criacao = self.client.post(
            reverse("atendimento:modelos-documento"),
            {"acao": "criar_pasta", "nm_pasta": "Documentos personalizados"},
        )
        self.assertEqual(criacao.status_code, 302)
        pasta = PastaDocumento.objects.get(cd_empresa=self.empresa, nm_pasta="Documentos personalizados")
        dados = {
            "pasta_selecionada": pasta.pk,
            "nm_modelo": "Documento da pasta",
            "tp_documento": "ADMINISTRATIVO",
            "tp_elemento": "DOCUMENTO",
            "ds_alteracoes_versao": "Criação inicial",
            "ds_html_tela": "<main>Formulário</main>",
            "ds_css_tela": "",
            "ds_projeto_tela": "{}",
            "ds_html_impressao": "<main>Relatório</main>",
            "ds_css_impressao": "",
            "ds_projeto_impressao": "{}",
            "sn_ativo": "on",
        }
        response = self.client.post(reverse("atendimento:modelos-documento"), dados)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ModeloDocumento.objects.get(nm_modelo="Documento da pasta").cd_pasta, pasta)

        protegida = PastaDocumento.objects.get(cd_empresa=self.empresa, tp_pasta="CABECALHOS")
        bloqueio = self.client.post(
            reverse("atendimento:modelos-documento"),
            {"acao": "renomear", "tipo_item": "pasta", "item_id": protegida.pk, "novo_nome": "ALTERADA"},
        )
        self.assertEqual(bloqueio.status_code, 403)

        documento = ModeloDocumento.objects.get(nm_modelo="Documento da pasta")
        mover_raiz = self.client.post(
            reverse("atendimento:editar-modelo-documento", args=[documento.pk]),
            {
                "acao": "mover",
                "tipo_item": "documento",
                "item_id": documento.pk,
                "destino_id": "",
                "pasta_selecionada": "",
            },
        )
        self.assertEqual(mover_raiz.status_code, 302)
        documento.refresh_from_db()
        self.assertIsNone(documento.cd_pasta)

    def test_perfil_assistencial_configura_menu_e_link_parametrizado(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        perfil = PerfilAssistencial.objects.create(
            cd_empresa=self.empresa,
            nm_perfil="MÉDICOS",
            tipos_prestador=["MEDICO"],
        )
        grupo = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nm_item="Integrações",
            tp_item="GRUPO",
            nr_ordem=1,
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_item_pai=grupo,
            nm_item="Sistema externo",
            tp_item="LINK_EXTERNO",
            ds_url="https://exemplo.test/a/<<cd_atendimento>>/p/<<cd_paciente>>",
            nr_ordem=2,
        )
        DominioExternoPermitido.objects.create(
            cd_empresa=self.empresa,
            ds_dominio="exemplo.test",
        )
        self.medico_user.cd_prestador = self.prestador
        self.medico_user.save(update_fields=["cd_prestador"])
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:ficha-atendimento", args=[atendimento.pk]))
        self.assertContains(response, "Integrações")
        self.assertContains(response, "Sistema externo")
        self.assertContains(response, f"https://exemplo.test/a/{atendimento.pk}/p/{self.paciente.pk}")
        self.assertNotContains(response, "Salvar ficha")

    def test_documento_em_tela_salva_campos_e_impressao_usa_valores(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Evolução estruturada",
            tp_documento="EVOLUCAO",
            ds_alteracoes_versao="Inicial",
            ds_html_tela='<label>Queixa <input data-document-field="true" name="campo_queixa"></label>',
            ds_html_impressao="<p>Queixa: {{ campo.queixa }}</p>",
        )
        documento = DocumentoClinico.objects.create(
            cd_empresa=self.empresa,
            cd_atendimento=atendimento,
            cd_modelo_documento=modelo,
            tp_documento="EVOLUCAO",
            ds_titulo="Evolução",
            cd_usuario_emissor=self.medico_user,
        )
        self.login_as(self.medico_user)
        response = self.client.post(
            reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]),
            {"ds_conteudo": "", "ds_dados_formulario": '{"queixa":"Dor abdominal"}'},
        )
        self.assertEqual(response.status_code, 302)
        documento.refresh_from_db()
        self.assertEqual(documento.ds_dados_formulario["queixa"], "Dor abdominal")
        impressao = self.client.get(
            reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]),
            {"modo": "impressao"},
        )
        self.assertContains(impressao, "Dor abdominal")
        self.assertContains(impressao, "document-header")
        class DummyHTML:
            def __init__(self, *args, **kwargs):
                pass

            def write_pdf(self):
                return b"%PDF-1.4\n% Celeris test\n"

        weasyprint_original = sys.modules.get("weasyprint")
        sys.modules["weasyprint"] = types.SimpleNamespace(HTML=DummyHTML)
        try:
            pdf = self.client.get(
                reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]),
                {"modo": "impressao", "pdf": "1"},
            )
        finally:
            if weasyprint_original is None:
                sys.modules.pop("weasyprint", None)
            else:
                sys.modules["weasyprint"] = weasyprint_original
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        tela = self.client.get(reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]))
        self.assertContains(tela, "campo_queixa")
        self.assertNotContains(tela, '<header class="document-header"')
        self.assertNotContains(tela, '<footer class="document-footer"')

    def test_documento_carrega_dropdown_dinamico_e_campo_nao_editavel(self):
        convenio = Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="CONVÊNIO DINÂMICO")
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Formulário dinâmico",
            tp_documento="EVOLUCAO",
            ds_alteracoes_versao="Inicial",
            ds_html_tela=(
                '<label>Paciente<input data-document-field="true" name="campo_paciente" '
                'value="{{ paciente.nome }}" readonly></label>'
                '<label>Convênio<select data-document-field="true" name="campo_convenio" '
                'data-option-source="query" data-source-query="convenios"></select></label>'
            ),
        )
        documento = DocumentoClinico.objects.create(
            cd_empresa=self.empresa,
            cd_atendimento=atendimento,
            cd_modelo_documento=modelo,
            tp_documento="EVOLUCAO",
            ds_titulo="Formulário dinâmico",
            cd_usuario_emissor=self.medico_user,
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]))
        self.assertContains(response, self.paciente.nm_paciente)
        self.assertContains(response, convenio.nm_convenio)
        self.assertContains(response, "disabled")
        self.assertContains(response, 'tabindex="-1"')
        self.assertContains(response, f'value="{convenio.pk}"')

    def test_impressao_reconstroi_grade_quando_editor_perde_estilos(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Documento com grade recuperada",
            tp_documento="EVOLUCAO",
            ds_alteracoes_versao="Inicial",
            ds_html_impressao="<main><div>Layout sem estilos</div></main>",
            ds_css_impressao="",
            ds_projeto_tela={
                "grid": {"columns": 2, "rows": 1},
                "formFields": [
                    {"name": "campo_a", "label": "Campo A", "type": "text", "col": 1, "row": 1, "colSpan": 1, "rowSpan": 1},
                    {"name": "campo_b", "label": "Campo B", "type": "text", "col": 2, "row": 1, "colSpan": 1, "rowSpan": 1},
                ],
            },
        )
        documento = DocumentoClinico.objects.create(
            cd_empresa=self.empresa,
            cd_atendimento=atendimento,
            cd_modelo_documento=modelo,
            tp_documento="EVOLUCAO",
            ds_titulo="Grade recuperada",
            ds_dados_formulario={"campo_a": "A", "campo_b": "B"},
            cd_usuario_emissor=self.medico_user,
        )
        self.login_as(self.medico_user)
        response = self.client.get(
            reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]),
            {"modo": "impressao"},
        )
        self.assertContains(response, "grid-template-columns:repeat(2,minmax(0,1fr))")
        self.assertContains(response, "grid-column:2 / span 1")
        self.assertContains(response, "column-gap:16px")
        self.assertContains(response, "Campo A")
        self.assertContains(response, "Campo B")
        self.assertNotContains(response, "document-page-number")
        self.assertContains(response, "document-print-table")
        self.assertContains(response, "<tfoot>")
        self.assertNotContains(response, "Assinatura digital:")

    def test_editor_previsualiza_dados_de_atendimento_existente(self):
        self.paciente.nm_mae = "MÃE DO PACIENTE TESTE"
        self.paciente.nm_social = "NOME SOCIAL TESTE"
        self.paciente.tp_sexo = "FEMININO"
        self.paciente.save(update_fields=["nm_mae", "nm_social", "tp_sexo"])
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
            ds_especialidade="CLINICA_GERAL",
        )
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:modelos-documento"))
        self.assertContains(response, f"Atendimento {atendimento.pk} · {self.paciente.nm_paciente}")
        contexto = response.context["contextos_teste"][0]["variables"]
        self.assertEqual(contexto["paciente.nome"], "NOME SOCIAL TESTE")
        self.assertNotIn("paciente.nome_social", contexto)
        self.assertEqual(contexto["paciente.mae"], "MÃE DO PACIENTE TESTE")
        self.assertEqual(contexto["atendimento.especialidade"], "Clínica Geral")

    def test_pep_pesquisa_por_atendimento_e_geral(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="AGUARDANDO_CONSULTA",
        )
        self.login_as(self.medico_user)
        por_codigo = self.client.get(reverse("atendimento:pep"), {"nr_atendimento": atendimento.pk, "q_atendimento": "IGNORAR"})
        self.assertContains(por_codigo, self.paciente.nm_paciente)
        self.assertEqual(por_codigo.context["busca_atendimento"], "")

        por_nome = self.client.get(reverse("atendimento:pep"), {"q_atendimento": "PACIENTE"})
        self.assertContains(por_nome, self.paciente.nm_paciente)

        geral_exato = self.client.get(
            reverse("atendimento:pep"),
            {"aba": "todos", "nr_atendimento_geral": atendimento.pk, "q": "IGNORAR"},
        )
        self.assertContains(geral_exato, self.paciente.nm_paciente)
        self.assertEqual(geral_exato.context["busca"], "")

    def test_documento_clinico_rascunho_e_copia(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        self.login_as(self.medico_user)
        self.client.post(
            reverse("atendimento:prescrever", args=[atendimento.pk]),
            {"ds_prescricao": "Dipirona", "ds_orientacoes": "Se dor."},
        )
        documento = DocumentoClinico.objects.get(cd_atendimento=atendimento, tp_documento="PRESCRICAO")
        self.assertEqual(documento.ds_status, "FECHADO")
        impressao = self.client.get(reverse("atendimento:imprimir-documento-clinico", args=[documento.pk]))
        self.assertNotContains(impressao, "document-draft-watermark")

        copia = self.client.get(reverse("atendimento:copiar-documento-clinico", args=[documento.pk]))
        self.assertEqual(copia.status_code, 302)
        self.assertEqual(DocumentoClinico.objects.filter(cd_atendimento=atendimento).count(), 2)

    def test_cadastro_prestador_com_multiespecialidade(self):
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR TESTE",
                "nm_guerra": "PRESTADOR TESTE",
                "dt_nascimento": "1980-01-01",
                "nr_cpf": "529.982.247-25",
                "tp_prestador": "MEDICO",
                "nr_conselho": "12345",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CLINICA_GERAL",
                "tp_vinculo": "CLT",
                "sn_permite_agenda": "on",
                "sn_permite_atendimento": "on",
                "sn_permite_prescricao": "on",
                "sn_ativo": "True",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        provider = form.save(commit=False)
        self.assertEqual(provider.ds_especialidades, ["CLINICA_GERAL"])
        self.assertEqual(provider.ds_especialidade, "CLINICA_GERAL")
        self.assertEqual(provider.ds_conselho, "CRM")
        self.assertTrue(provider.sn_permite_agenda)
        self.assertTrue(provider.sn_permite_atendimento)
        self.assertTrue(provider.sn_permite_prescricao)

    def test_catalogos_sociodemograficos_e_cbo_sao_independentes(self):
        modelo_catalogo("nacionalidade").objects.update_or_create(
            cd_valor="BRASILEIRA_TESTE",
            defaults={"ds_valor": "Brasileira teste", "sn_ativo": True},
        )
        modelo_catalogo("pais").objects.update_or_create(
            cd_valor="BR_TESTE",
            defaults={"ds_valor": "Brasil teste", "sn_ativo": True},
        )
        modelo_catalogo("cbo").objects.update_or_create(
            cd_valor="225125_TESTE",
            defaults={"ds_valor": "Médico clínico teste", "sn_ativo": True},
        )

        patient_form = PacienteForm(empresa=self.empresa)
        self.assertIn(("BRASILEIRA_TESTE", "Brasileira teste"), patient_form.fields["ds_nacionalidade"].choices)
        self.assertNotIn(("BR_TESTE", "Brasil teste"), patient_form.fields["ds_nacionalidade"].choices)
        self.assertIn(("BR_TESTE", "Brasil teste"), patient_form.fields["ds_pais_nascimento"].choices)

        provider_form = PrestadorForm(empresa=self.empresa)
        self.assertIn(("225125_TESTE", "Médico clínico teste"), provider_form.fields["cd_cbo"].widget.choices)
        self.assertIn("ds_conselho", provider_form.fields)
        self.assertIn("nr_conselho", provider_form.fields)
        self.assertIn("sg_conselho", provider_form.fields)

    def test_menu_de_prestadores_abre_cadastro_integrado(self):
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:profissionais"))
        self.assertRedirects(response, reverse("atendimento:cadastro-profissional-novo"))

    def test_consulta_integrada_de_prestadores_habilita_navegacao_de_resultados(self):
        self.login_as(self.ti_user)
        second_provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="MÉDICO TESTE DOIS",
            nm_guerra="MÉDICO DOIS",
            dt_nascimento="1980-01-01",
            nr_cpf="111.444.777-35",
            tp_prestador="MEDICO",
        )
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "MÉDICO TESTE"},
        )
        self.assertRedirects(
            response,
            f"{reverse('atendimento:cadastro-profissional', args=[self.prestador.pk])}?origem=consulta",
        )
        result_response = self.client.get(response.url)
        self.assertEqual(result_response.context["prestador"], self.prestador)
        self.assertContains(result_response, reverse("atendimento:cadastro-profissional", args=[second_provider.pk]))

    def test_abertura_direta_de_prestador_carrega_apenas_um_registro(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]),
        )
        self.assertEqual(response.context["prestador"], self.prestador)
        self.assertEqual(response.context["current_previous_url"], "")
        self.assertEqual(response.context["current_next_url"], "")

    def test_consulta_de_prestadores_sem_resultados_mantem_tela_integrada(self):
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "INEXISTENTE"},
        )
        self.assertRedirects(
            response,
            f'{reverse("atendimento:cadastro-profissional-novo")}?sem_resultados=1',
        )

    def test_consulta_de_prestadores_sem_filtros_retorna_ativos_e_inativos(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR INATIVO",
            nm_guerra="INATIVO",
            dt_nascimento="1980-01-01",
            nr_cpf="123.456.789-09",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        result_ids = self.client.session["consulta_prestadores"]
        self.assertIn(self.prestador.pk, result_ids)
        self.assertIn(inactive.pk, result_ids)

    def test_consulta_de_prestadores_status_so_filtra_quando_informado(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR STATUS INATIVO",
            nm_guerra="STATUS INATIVO",
            dt_nascimento="1980-01-01",
            nr_cpf="123.456.789-09",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "sn_ativo": "False"},
        )
        self.assertEqual(self.client.session["consulta_prestadores"], [inactive.pk])

    def test_endereco_comercial_pode_acompanhar_residencial(self):
        provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR COM ENDERECO",
            nm_guerra="PRESTADOR ENDERECO",
            nr_cep="01001-000",
            sg_estado="SP",
            ds_cidade="SAO PAULO",
            tp_logradouro="RUA",
            ds_endereco="PRACA DA SE",
            nr_endereco="100",
            ds_complemento="SALA 1",
            ds_bairro="SE",
            sn_mesmo_endereco=True,
        )
        self.assertEqual(provider.nr_cep_comercial, provider.nr_cep)
        self.assertEqual(provider.sg_estado_comercial, provider.sg_estado)
        self.assertEqual(provider.ds_cidade_comercial, provider.ds_cidade)
        self.assertEqual(provider.ds_endereco_comercial, provider.ds_endereco)

    def test_especialidade_principal_deve_estar_na_lista(self):
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR TESTE",
                "nm_guerra": "PRESTADOR TESTE",
                "dt_nascimento": "1980-01-01",
                "tp_prestador": "MEDICO",
                "nr_conselho": "12345",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CARDIOLOGIA",
                "sn_ativo": "True",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("ds_especialidade_principal", form.errors)

    def test_cadastro_paciente_abre_sem_campos_de_prestador(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        self.assertEqual(response.status_code, 200)

    def test_prestador_e_gravado_na_tela_unificada(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:cadastro-profissional-novo"),
            {
                "nm_prestador": "MARIA DA SILVA",
                "nm_guerra": "MARIA SILVA",
                "dt_nascimento": "1985-05-20",
                "nr_cpf": "111.444.777-35",
                "tp_prestador": "MEDICO",
                "nr_conselho": "998877",
                "sg_conselho": "SP",
                "ds_especialidades": ["CLINICA_GERAL"],
                "ds_especialidade_principal": "CLINICA_GERAL",
            },
        )
        self.assertEqual(response.status_code, 302)
        provider = Prestador.objects.get(nr_conselho="998877")
        self.assertTrue(provider.cd_prestador)

    def test_consulta_sem_filtros_retorna_todos_os_prestadores(self):
        inactive = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="PRESTADOR INATIVO",
            nm_guerra="PRESTADOR INATIVO",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session["consulta_prestadores"],
            [self.prestador.cd_prestador, inactive.cd_prestador],
        )

    def test_paciente_e_prestador_referenciam_cep_por_codigo(self):
        cep = Cep.objects.create(nr_cep="01001000", sg_estado="SP", ds_cidade="São Paulo")
        self.paciente.cd_cep = cep
        self.paciente.save()
        self.prestador.cd_cep = cep
        self.prestador.save()
        self.assertEqual(self.paciente.cd_cep_id, cep.cd_cep)
        self.assertEqual(self.prestador.cd_cep_id, cep.cd_cep)

    def test_desativacao_nao_exclui_paciente_ou_prestador(self):
        self.login_as(self.ti_user)
        self.client.post(reverse("atendimento:alternar-status-paciente", args=[self.paciente.pk]))
        self.client.post(reverse("atendimento:alternar-status-prestador", args=[self.prestador.pk]))
        self.paciente.refresh_from_db()
        self.prestador.refresh_from_db()
        self.assertFalse(self.paciente.sn_ativo)
        self.assertFalse(self.prestador.sn_ativo)
        self.assertTrue(Paciente.objects.filter(pk=self.paciente.pk).exists())
        self.assertTrue(Prestador.objects.filter(pk=self.prestador.pk).exists())

    def test_tipo_sem_conselho_apenas_alerta_e_nao_bloqueia(self):
        TipoPrestador.objects.create(
            cd_valor="ADMINISTRATIVO",
            ds_valor="ADMINISTRATIVO",
        )
        form = PrestadorForm(
            data={
                "nm_prestador": "PRESTADOR ADMINISTRATIVO",
                "nm_guerra": "PRESTADOR ADMINISTRATIVO",
                "dt_nascimento": "1990-01-01",
                "nr_cpf": "111.444.777-35",
                "tp_prestador": "ADMINISTRATIVO",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["ds_conselho"], "")

    def test_filtro_prestador_nao_reutiliza_resultado_anterior(self):
        matching = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="BENJAMIN VIEIRA",
            nm_guerra="BENJAMIN VIEIRA",
            dt_nascimento="1985-01-01",
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        first_response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "BENJ"},
        )
        self.assertRedirects(
            first_response,
            f"{reverse('atendimento:cadastro-profissional', args=[matching.pk])}?origem=consulta",
        )
        second_response = self.client.get(
            reverse("atendimento:cadastro-profissional-novo"),
            {"consultar": "1", "nm_prestador": "W"},
        )
        self.assertRedirects(
            second_response,
            f'{reverse("atendimento:cadastro-profissional-novo")}?sem_resultados=1',
        )
        self.assertEqual(self.client.session["consulta_prestadores"], [])

    def test_filtros_paciente_individuais_e_combinados(self):
        parda = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="ANA PARDA",
            dt_nascimento="1995-03-10",
            ds_cor_raca="PARDA",
            tp_sexo="F",
            nr_celular="(31) 9 1111-1111",
            ds_bairro="CENTRO",
            sn_ativo=True,
        )
        Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="BRUNO BRANCO",
            dt_nascimento="1992-02-02",
            ds_cor_raca="BRANCA",
            tp_sexo="M",
            nr_celular="(31) 9 2222-2222",
            ds_bairro="SAVASSI",
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        cases = (
            ({"ds_cor_raca": "PARDA"}, [parda.pk]),
            ({"tp_sexo": "F"}, [parda.pk]),
            ({"ds_bairro": "CENTRO"}, [parda.pk]),
            ({"ds_cor_raca": "PARDA", "tp_sexo": "F"}, [parda.pk]),
            ({"ds_cor_raca": "PARDA", "tp_sexo": "M"}, []),
        )
        for filters, expected_ids in cases:
            with self.subTest(filters=filters):
                response = self.client.get(
                    reverse("atendimento:cadastro-paciente-novo"),
                    {"consultar": "1", **filters},
                )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.client.session["consulta_pacientes"], expected_ids)

    def test_consulta_de_pacientes_sem_filtros_retorna_ativos_e_inativos(self):
        inactive = Paciente.objects.create(
            cd_empresa=self.empresa,
            nm_paciente="PACIENTE INATIVO",
            dt_nascimento="1990-01-01",
            nr_cpf="111.444.777-35",
            sn_ativo=False,
        )
        self.login_as(self.ti_user)
        response = self.client.get(
            reverse("atendimento:cadastro-paciente-novo"),
            {"consultar": "1"},
        )
        self.assertEqual(response.status_code, 302)
        result_ids = self.client.session["consulta_pacientes"]
        self.assertIn(self.paciente.pk, result_ids)
        self.assertIn(inactive.pk, result_ids)

    def test_cadastros_reutilizam_a_mesma_chave_de_guia(self):
        self.login_as(self.ti_user)
        new_provider = self.client.get(reverse("atendimento:cadastro-profissional-novo"))
        saved_provider = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        new_patient = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        saved_patient = self.client.get(reverse("atendimento:cadastro-paciente", args=[self.paciente.pk]))
        self.assertEqual(new_provider.context["current_tab_key"], saved_provider.context["current_tab_key"])
        self.assertEqual(new_patient.context["current_tab_key"], saved_patient.context["current_tab_key"])

    def test_erro_conselho_e_renderizado_no_campo(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:cadastro-profissional-novo"),
            {
                "nm_prestador": "MEDICO SEM NUMERO",
                "nm_guerra": "MEDICO NUMERO",
                "dt_nascimento": "1980-01-01",
                "tp_prestador": "MEDICO",
                "sg_conselho": "SP",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe o número do conselho")
        self.assertContains(response, "data-form-errors=")
        self.assertContains(response, "nr_conselho")

    def test_cpf_prestador_obrigatorio_invalido_duplicado_e_valido(self):
        base_data = {
            "nm_prestador": "PRESTADOR CPF",
            "nm_guerra": "PRESTADOR",
            "dt_nascimento": "1988-01-01",
            "tp_prestador": "MEDICO",
            "nr_conselho": "554433",
            "sg_conselho": "SP",
        }
        missing = PrestadorForm(data=base_data)
        self.assertFalse(missing.is_valid())
        self.assertIn("nr_cpf", missing.errors)

        invalid = PrestadorForm(data={**base_data, "nr_cpf": "111.111.111-11"})
        self.assertFalse(invalid.is_valid())
        self.assertIn("nr_cpf", invalid.errors)

        Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="CPF EXISTENTE",
            nm_guerra="CPF EXISTENTE",
            dt_nascimento="1980-01-01",
            nr_cpf="529.982.247-25",
        )
        duplicate = PrestadorForm(data={**base_data, "nr_cpf": "529.982.247-25"})
        self.assertFalse(duplicate.is_valid())
        self.assertIn("nr_cpf", duplicate.errors)

        valid = PrestadorForm(data={**base_data, "nr_cpf": "111.444.777-35"})
        self.assertTrue(valid.is_valid(), valid.errors)

    def test_filtros_prestador_por_cpf_tipo_conselho_e_especialidade(self):
        provider = Prestador.objects.create(
            cd_empresa=self.empresa,
            nm_prestador="FILTRO PRESTADOR",
            nm_guerra="FILTRO",
            dt_nascimento="1981-01-01",
            nr_cpf="111.444.777-35",
            tp_prestador="MEDICO",
            ds_conselho="CRM",
            nr_conselho="FILTER123",
            ds_especialidade="CLINICA_GERAL",
            ds_especialidades=["CLINICA_GERAL"],
            sn_ativo=True,
        )
        self.login_as(self.ti_user)
        cases = (
            {"nr_cpf": "111.444.777-35"},
            {"tp_prestador": "MEDICO", "nr_conselho": "FILTER123"},
            {"ds_conselho": "CRM"},
            {"ds_especialidades": "CLINICA_GERAL"},
        )
        for filters in cases:
            with self.subTest(filters=filters):
                response = self.client.get(
                    reverse("atendimento:cadastro-profissional-novo"),
                    {"consultar": "1", **filters},
                )
                self.assertEqual(response.status_code, 302)
                self.assertIn(provider.pk, self.client.session["consulta_prestadores"])

    def test_navegacao_habilita_apenas_direcoes_disponiveis(self):
        providers = [
            Prestador.objects.create(
                cd_empresa=self.empresa,
                nm_prestador=f"NAVEGACAO {index}",
                nm_guerra=f"NAVEGACAO {index}",
                dt_nascimento="1980-01-01",
                nr_cpf=cpf,
                sn_ativo=True,
            )
            for index, cpf in enumerate(("111.444.777-35", "529.982.247-25", "123.456.789-09"), start=1)
        ]
        self.login_as(self.ti_user)
        session = self.client.session
        session["consulta_prestadores"] = [provider.pk for provider in providers]
        session.save()

        first = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[0].pk]), {"origem": "consulta"})
        middle = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[1].pk]), {"origem": "consulta"})
        last = self.client.get(reverse("atendimento:cadastro-profissional", args=[providers[2].pk]), {"origem": "consulta"})
        self.assertFalse(first.context["current_first_url"])
        self.assertFalse(first.context["current_previous_url"])
        self.assertTrue(first.context["current_next_url"])
        self.assertTrue(first.context["current_last_url"])
        self.assertTrue(middle.context["current_first_url"])
        self.assertTrue(middle.context["current_previous_url"])
        self.assertTrue(middle.context["current_next_url"])
        self.assertTrue(middle.context["current_last_url"])
        self.assertTrue(last.context["current_first_url"])
        self.assertTrue(last.context["current_previous_url"])
        self.assertFalse(last.context["current_next_url"])
        self.assertFalse(last.context["current_last_url"])

    def test_botao_status_alterna_rotulo(self):
        self.login_as(self.ti_user)
        active = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        self.assertEqual(active.context["current_toggle_active_label"], "Desativar")
        self.client.post(reverse("atendimento:alternar-status-prestador", args=[self.prestador.pk]))
        inactive = self.client.get(reverse("atendimento:cadastro-profissional", args=[self.prestador.pk]))
        self.assertEqual(inactive.context["current_toggle_active_label"], "Ativar")

    def test_cadastro_prestador_orienta_tabelas_vazias_sem_links_de_gerenciamento(self):
        self.login_as(self.ti_user)
        provider_response = self.client.get(reverse("atendimento:cadastro-profissional-novo"))
        patient_response = self.client.get(reverse("atendimento:cadastro-paciente-novo"))
        self.assertNotContains(provider_response, "data-screen-overlay-link")
        self.assertNotContains(patient_response, "data-screen-overlay-link")
        self.assertContains(provider_response, "Atendimento > Cadastros > Tabelas > Tipos de prestador")
        self.assertContains(provider_response, "Atendimento > Agendamento > Tabelas > Especialidades")
        self.assertNotContains(patient_response, "Convênio <a")
        self.assertContains(patient_response, "Nenhum convênio cadastrado.")
        overlay_response = self.client.get(reverse("core:global_ceps"), {"overlay": "1"})
        self.assertTrue(overlay_response.context["current_overlay_mode"])

    def test_cadastro_paciente_agendamento_substitui_guia_e_volta_para_agendar(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:cadastro-paciente-agendamento"))
        self.assertEqual(response.context["current_tab_key"], reverse("atendimento:agendar"))
        self.assertEqual(response.context["current_close_mode"], "back")
        self.assertEqual(response.context["current_close_url"], reverse("atendimento:agendar"))
        self.assertEqual(response.context["current_tab_root_title"], "Cadastro de paciente")

    def test_agendar_seleciona_paciente_pela_linha_sem_botao(self):
        self.login_as(self.recepcionista)
        response = self.client.get(reverse("atendimento:agendar"), {"termo": self.paciente.nm_paciente})
        destination = reverse("atendimento:revisar-paciente-agendamento", args=[self.paciente.pk])
        self.assertContains(response, f'data-row-url="{destination}"')
        self.assertNotContains(response, ">Selecionar</a>")

    def test_telas_de_especialidade_e_convenio_abrem(self):
        self.login_as(self.ti_user)
        for route in ("atendimento:especialidades", "atendimento:convenios", "atendimento:escalas-classificacao"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                if route == "atendimento:escalas-classificacao":
                    self.assertContains(response, f'data-query-url="{reverse(route)}"')

    def test_classificacao_operacional_fica_oculta_e_configuracoes_permanecem_no_celeris(self):
        fila = ScreenDefinition.objects.select_related("parent").get(
            access_key="atendimento:fila-classificacao"
        )
        self.assertTrue(fila.active)
        self.assertIsNotNone(fila.parent)
        self.assertFalse(fila.parent.active)
        self.assertTrue(
            ScreenDefinition.objects.filter(
                access_key="atendimento:escalas-classificacao",
                active=True,
                parent__slug="atendimento-classificacao-configuracao",
            ).exists()
        )

    def test_convenios_consulta_em_branco_lista_todos(self):
        self.login_as(self.ti_user)
        Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="SUL AMERICA", sn_ativo=True)
        Convenio.objects.create(cd_empresa=self.empresa, nm_convenio="BRADESCO SAUDE", sn_ativo=True)

        response = self.client.get(reverse("atendimento:convenios"), {"consultar": "1"})

        self.assertContains(response, "SUL AMERICA")
        self.assertContains(response, "BRADESCO SAUDE")
        self.assertNotContains(response, "Nenhum dado encontrado.")

    def test_convenios_salvar_mantem_registros_exibidos(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:convenios"),
            {"new_name": ["SUL AMERICA"], "new_active": ["true"]},
        )
        self.assertRedirects(response, f"{reverse('atendimento:convenios')}?consultar=1")
        list_response = self.client.get(reverse("atendimento:convenios"), {"consultar": "1"})
        self.assertContains(list_response, "SUL AMERICA")

    def test_prestador_pode_ter_varios_tipos_e_tipo_so_um_perfil(self):
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            cd_tipo_prestador="MEDICO",
            sn_principal=True,
        )
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            cd_tipo_prestador="AUDITOR",
        )
        self.assertEqual(self.prestador.tipos_prestador_ativos, ["MEDICO", "AUDITOR"])

        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Médicos")
        PerfilAssistencialTipo.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_tipo_prestador="MEDICO",
        )
        outro = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Outro")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PerfilAssistencialTipo.objects.create(
                    cd_empresa=self.empresa,
                    cd_perfil_assistencial=outro,
                    cd_tipo_prestador="MEDICO",
                )

    def test_pep_mescla_itens_dos_perfis_do_prestador(self):
        self.medico_user.cd_prestador = self.prestador
        self.medico_user.save(update_fields=["cd_prestador"])
        for indice, tipo in enumerate(("MEDICO", "AUDITOR"), start=1):
            PrestadorTipo.objects.create(
                cd_empresa=self.empresa,
                cd_prestador=self.prestador,
                cd_tipo_prestador=tipo,
                sn_principal=indice == 1,
            )
            perfil = PerfilAssistencial.objects.create(
                cd_empresa=self.empresa,
                nm_perfil=f"Perfil {tipo}",
            )
            PerfilAssistencialTipo.objects.create(
                cd_empresa=self.empresa,
                cd_perfil_assistencial=perfil,
                cd_tipo_prestador=tipo,
            )
            versao = PerfilAssistencialVersao.objects.create(
                cd_empresa=self.empresa,
                cd_perfil_assistencial=perfil,
                nr_versao=1,
                ds_status="PUBLICADO",
            )
            ItemMenuAssistencial.objects.create(
                cd_empresa=self.empresa,
                cd_perfil_assistencial=perfil,
                cd_versao_perfil=versao,
                cd_item_tecnico=f"ITEM_{tipo}",
                nm_item=f"Tela {tipo}",
                tp_item="ANCORA",
                ds_url=f"#item-{tipo.lower()}",
            )
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        self.login_as(self.medico_user)
        response = self.client.get(reverse("atendimento:ficha-atendimento", args=[atendimento.pk]))
        self.assertContains(response, "Tela MEDICO")
        self.assertContains(response, "Tela AUDITOR")

    def test_rascunho_editor_salva_restaura_e_exclui_no_servidor(self):
        self.login_as(self.ti_user)
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Modelo rascunho",
            tp_documento="EVOLUCAO",
        )
        url = reverse("atendimento:rascunho-editor-documento")
        query = f"{url}?modelo={modelo.pk}&guia=editor-teste"
        payload = {"state": {"editorState": {"activeTab": "impressao"}, "undoStack": ["a"]}}
        response = self.client.post(query, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        restored = self.client.get(query).json()
        self.assertEqual(restored["state"]["editorState"]["activeTab"], "impressao")
        compressed_payload = gzip.compress(json.dumps({
            "state": {
                "editorState": {"activeTab": "tela", "large": "X" * 5000},
                "undoStack": ["b"],
            },
        }).encode("utf-8"))
        response = self.client.post(
            query,
            data=compressed_payload,
            content_type="application/octet-stream",
            HTTP_X_CELERIS_DRAFT_ENCODING="gzip",
        )
        self.assertEqual(response.status_code, 200)
        restored = self.client.get(query).json()
        self.assertEqual(restored["state"]["editorState"]["activeTab"], "tela")
        self.assertEqual(restored["state"]["undoStack"], ["b"])
        large_content = "X" * 3_200_000
        compressed_large_payload = gzip.compress(json.dumps({
            "state": {
                "editorState": {
                    "activeTab": "impressao",
                    "printLayout": {"elements": [{"id": "e1", "content": large_content}]},
                },
                "fields": [],
            },
        }).encode("utf-8"))
        self.assertLess(len(compressed_large_payload), 3_000_000)
        response = self.client.post(
            query,
            data=compressed_large_payload,
            content_type="application/octet-stream",
            HTTP_X_CELERIS_DRAFT_ENCODING="gzip",
        )
        self.assertEqual(response.status_code, 200)
        restored = self.client.get(query).json()
        self.assertEqual(
            restored["state"]["editorState"]["printLayout"]["elements"][0]["content"],
            large_content,
        )
        self.assertTrue(
            RascunhoEditorDocumento.objects.filter(
                cd_empresa=self.empresa,
                cd_usuario=self.ti_user,
                cd_modelo_documento=modelo,
            ).exists()
        )
        deleted = self.client.delete(query)
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(RascunhoEditorDocumento.objects.filter(cd_modelo_documento=modelo).exists())

        response = self.client.post(query, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        discarded = self.client.post(query, data={"acao": "descartar"})
        self.assertEqual(discarded.status_code, 200)
        self.assertFalse(RascunhoEditorDocumento.objects.filter(cd_modelo_documento=modelo).exists())

        response = self.client.post(query, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse("logout"))
        self.assertFalse(RascunhoEditorDocumento.objects.filter(cd_modelo_documento=modelo).exists())

    def test_documento_fecha_com_senha_hash_e_evento(self):
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        documento = DocumentoClinico.objects.create(
            cd_empresa=self.empresa,
            cd_atendimento=atendimento,
            tp_documento="EVOLUCAO",
            ds_titulo="Evolução segura",
            ds_conteudo="Conteúdo",
            ds_dados_formulario={"texto": "Conteúdo"},
            ds_status="ABERTO",
            cd_usuario_emissor=self.medico_user,
            cd_usuario_responsavel=self.medico_user,
        )
        self.login_as(self.medico_user)
        response = self.client.post(
            reverse("atendimento:fechar-documento-clinico", args=[documento.pk]),
            {"senha": "123456"},
        )
        self.assertEqual(response.status_code, 302)
        documento.refresh_from_db()
        self.assertEqual(documento.ds_status, "FECHADO")
        self.assertEqual(len(documento.ds_hash_conteudo), 64)
        self.assertTrue(
            EventoDocumentoClinico.objects.filter(
                cd_documento_clinico=documento,
                tp_evento="FECHADO",
            ).exists()
        )

    def test_escala_clinica_calcula_e_salva_documento_fechado(self):
        self.medico_user.cd_prestador = self.prestador
        self.medico_user.save(update_fields=["cd_prestador"])
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            cd_tipo_prestador="MEDICO",
            sn_principal=True,
        )
        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Médico")
        PerfilAssistencialTipo.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_tipo_prestador="MEDICO",
        )
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="PUBLICADO",
        )
        escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Risco",
            ds_perguntas=[
                {
                    "chave": "risco",
                    "texto": "Risco",
                    "opcoes": [
                        {"valor": "baixo", "descricao": "Baixo", "pontos": 1},
                        {"valor": "alto", "descricao": "Alto", "pontos": 3},
                    ],
                }
            ],
            ds_faixas_resultado=[
                {"min": 0, "max": 1, "descricao": "Baixo", "cor": "#22c55e"},
                {"min": 2, "max": 3, "descricao": "Alto", "cor": "#dc2626"},
            ],
        )
        item = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_tecnico="ESCALA_RISCO",
            nm_item="Escala de risco",
            tp_item="ESCALA",
            ds_configuracao={"escala": escala.pk},
        )
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="EM_ATENDIMENTO",
        )
        self.login_as(self.medico_user)
        response = self.client.post(
            reverse("atendimento:executar-escala-clinica", args=[atendimento.pk, item.pk]),
            {"pergunta_risco": "alto", "senha": "123456"},
        )
        self.assertEqual(response.status_code, 302)
        resultado = ResultadoEscalaClinica.objects.get(cd_atendimento=atendimento)
        self.assertEqual(float(resultado.nr_resultado), 3)
        self.assertEqual(resultado.ds_classificacao, "Alto")
        self.assertEqual(resultado.cd_documento_clinico.ds_status, "FECHADO")

    def test_editor_registra_aba_no_historico_e_compila_grade_sincronizada(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "document-editor.js").read_text(encoding="utf-8")
        self.assertIn("activeTab: activeEditorTab()", javascript)
        self.assertIn('activateEditorTab(state.activeTab || "tela")', javascript)
        self.assertIn("const useIndependentColumns = false", javascript)
        self.assertIn('data-cell-create-display="static-text"', javascript)
        self.assertIn("insertColumnDirection", javascript)
        self.assertIn("freeFormColumnSpan(row, col)", javascript)
        self.assertIn("freePrintColumnSpan(position.row, position.col)", javascript)
        self.assertIn('element.type === "junction"', javascript)
        self.assertIn("const minimumHeight = Math.max(24, Number(element.rowSpan || 1) * 24)", javascript)
        self.assertNotIn('rowSpan: type === "vline"  printLayout.grid.rows - position.row + 1 : 1', javascript)
        self.assertIn("<span>+ Campo</span>", javascript)
        self.assertIn('marginTop: Math.max(0, Number(field.marginTop || 0))', javascript)
        self.assertIn("grid-template-rows:repeat(${gridConfig.rows},minmax(0,auto))", javascript)
        self.assertIn("startPendingDuplicate", javascript)
        self.assertIn("duplicateFitsAt", javascript)
        self.assertIn("contextElement.col + contextElement.colSpan", javascript)
        self.assertIn("freePrintRowSpan(position.row, position.col)", javascript)
        self.assertIn('.filter((element) => element.type === "pagebreak")', javascript)
        self.assertIn("if (occupants.length && !insertPrintRow(targetRow)) return", javascript)
        self.assertIn("sections.push(renderPrintElement(pageBreak, \"width:100%\"))", javascript)
        self.assertIn("if (!field.fontSizeCustom)", javascript)
        self.assertIn("if (!element.fontSizeCustom)", javascript)
        self.assertIn(
            "grid-template-rows:repeat(${rowCount},minmax(16px,auto));align-content:start",
            javascript,
        )
        self.assertIn("window.location.assign(indexUrl)", javascript)
        self.assertIn("const formatRichText = (value) =>", javascript)
        self.assertIn('<span style="display:block;text-align:center">', javascript)
        self.assertIn("*texto* para negrito", javascript)
        self.assertIn('return hasOccupiedBefore(column) && hasOccupiedAfter(column) ?"minmax(0,1fr)" : "4px"', javascript)
        self.assertIn("measuredHeight(main)", javascript)
        self.assertIn("const horizontalExtension = 6", javascript)
        self.assertIn("margin-left:${hasLeftVertical ?-horizontalExtension : 0}px", javascript)
        self.assertIn("margin-right:${hasRightVertical ?-horizontalExtension : 0}px", javascript)
        self.assertIn("margin:0;padding:2px;background:#fff", javascript)
        self.assertIn("[...formFields].sort", javascript)
        self.assertIn('["prestador.uf_conselho", "UF do conselho"]', javascript)
        self.assertIn('customVariableExpressionInput?.addEventListener("drop"', javascript)
        self.assertIn("overflow-wrap:anywhere;word-break:break-word;white-space:normal", javascript)
        self.assertIn("contentWidth > availableWidth ?availableWidth / contentWidth : 1", javascript)
        self.assertNotIn('["paciente.nome_social", "Nome social"]', javascript)

        template = (settings.BASE_DIR / "templates" / "atendimento" / "modelos_documento.html").read_text(
            encoding="utf-8",
        )
        self.assertIn("↑ Linha acima", template)
        self.assertIn("Coluna à direita →", template)
        self.assertIn('data-settings-property="marginTop"', template)
        self.assertIn("data-grid-duplicate-element", template)
        self.assertIn("data-editor-index-url", template)
        self.assertIn("document-settings-row-break", template)

    def test_escala_clinica_aceita_expressao_e_faixa_por_operador(self):
        escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Expressão configurável",
            ds_expressao_calculo="{{pergunta_1}} * 2 + {{pergunta_2}}",
            ds_perguntas=[
                {
                    "chave": "pergunta_1",
                    "texto": "Primeira",
                    "opcoes": [{"valor": "sim", "descricao": "Sim", "pontos": 2}],
                },
                {
                    "chave": "pergunta_2",
                    "texto": "Segunda",
                    "opcoes": [{"valor": "sim", "descricao": "Sim", "pontos": 1}],
                },
            ],
            ds_faixas_resultado=[
                {
                    "operador": ">=",
                    "valor": 5,
                    "descricao": "Alto",
                    "cor": "#DC2626",
                    "negrito": True,
                },
            ],
        )
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:testar-escala-clinica"),
            data=json.dumps({
                "escala": escala.pk,
                "respostas": {"pergunta_1": "sim", "pergunta_2": "sim"},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["resultado"], 5)
        self.assertEqual(response.json()["classificacao"], "Alto")
        self.assertTrue(response.json()["negrito"])

    def test_escala_clinica_aplica_condicao_segura_por_idade(self):
        self.paciente.dt_nascimento = date(1940, 1, 1)
        self.paciente.save(update_fields=["dt_nascimento"])
        escala = EscalaClinica.objects.create(
            cd_empresa=self.empresa,
            nm_escala="Condição por idade",
            ds_perguntas=[{
                "chave": "risco",
                "texto": "Risco",
                "opcoes": [{"valor": "sim", "descricao": "Sim", "pontos": 2}],
            }],
            ds_condicoes_calculo=[{
                "variavel": "paciente.idade",
                "comparador": ">",
                "referencia": 70,
                "acrescimo": 1,
            }],
        )
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:testar-escala-clinica"),
            data=json.dumps({
                "escala": escala.pk,
                "paciente": self.paciente.pk,
                "respostas": {"risco": "sim"},
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["resultado"], 3)

    def test_copia_perfil_preserva_estrutura_sem_tipos_prestador(self):
        perfil = PerfilAssistencial.objects.create(
            cd_empresa=self.empresa,
            nm_perfil="Perfil para copiar",
            tipos_prestador=["MEDICO"],
        )
        PerfilAssistencialTipo.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_tipo_prestador="MEDICO",
        )
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="RASCUNHO",
        )
        menu = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            nm_item="Atendimento",
            cd_item_tecnico="ATENDIMENTO",
            tp_item="GRUPO",
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_pai=menu,
            nm_item="Evolução",
            cd_item_tecnico="EVOLUCAO",
            tp_item="ACAO",
            ds_acao="EVOLUIR",
        )
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:perfis-assistenciais"),
            {"acao": "copiar_perfil", "perfil": perfil.pk},
        )
        self.assertEqual(response.status_code, 302)
        copia = PerfilAssistencial.objects.exclude(pk=perfil.pk).get(nm_perfil__startswith="Perfil para copiar - Cópia")
        self.assertEqual(copia.tipos_prestador, [])
        self.assertFalse(copia.tipos_vinculados.exists())
        itens = copia.versoes.get().itens.order_by("nr_ordem", "pk")
        self.assertEqual(itens.count(), 2)
        self.assertEqual(itens.get(cd_item_tecnico="EVOLUCAO").cd_item_pai, itens.get(cd_item_tecnico="ATENDIMENTO"))

    def test_perfis_exibem_construtor_visual_sem_json_bruto(self):
        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Construtor")
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="RASCUNHO",
        )
        menu = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            nm_item="Menu raiz",
            cd_item_tecnico="MENU_RAIZ",
            tp_item="GRUPO",
        )
        ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_pai=menu,
            nm_item="Tela filha",
            cd_item_tecnico="TELA_FILHA",
            tp_item="ACAO",
        )
        ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="DOCUMENTO VISÍVEL",
            tp_documento="EVOLUCAO",
            tp_elemento="DOCUMENTO",
        )
        ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="CABEÇALHO OCULTO",
            tp_documento="ADMINISTRATIVO",
            tp_elemento="CABECALHO",
        )
        self.login_as(self.ti_user)
        response = self.client.get(reverse("atendimento:perfis-assistenciais"), {"perfil": perfil.pk})
        self.assertContains(response, "data-profile-item-builder")
        self.assertContains(response, "data-profile-item-modal")
        self.assertContains(response, "data-profile-tree-toggle")
        self.assertContains(response, "data-profile-item-settings")
        self.assertContains(response, "data-native-select")
        self.assertNotContains(response, 'name="ds_descricao" value="{{ request.GET')
        self.assertNotContains(response, 'name="sn_sigiloso">')
        self.assertContains(response, 'aria-label="Consultar perfil"')
        self.assertContains(response, "data-scale-add-question")
        self.assertContains(response, "data-scale-add-range")
        self.assertContains(response, "DOCUMENTO VISÍVEL")
        self.assertNotContains(response, "CABEÇALHO OCULTO")
        self.assertContains(response, "--profile-depth:1")
        self.assertContains(response, f'data-new-url="{reverse("atendimento:perfis-assistenciais")}"')
        self.assertNotContains(response, "Configuração JSON")
        self.assertNotContains(response, "Salvar perfil")

    def test_salvar_perfil_exige_e_grava_descricao_da_versao(self):
        self.login_as(self.ti_user)
        response = self.client.post(
            reverse("atendimento:perfis-assistenciais"),
            {
                "acao": "salvar_perfil",
                "nm_perfil": "Perfil versionado",
                "ds_descricao": "Teste",
                "ds_descricao_versao": "Criação inicial",
                "sn_ativo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        perfil = PerfilAssistencial.objects.get(nm_perfil="Perfil versionado")
        self.assertEqual(perfil.versoes.get().ds_descricao_versao, "Criação inicial")

    def test_ordenacao_api_nao_altera_grupo_pai(self):
        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Ordem protegida")
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="RASCUNHO",
        )
        primeiro = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            nm_item="Primeiro",
            cd_item_tecnico="PRIMEIRO",
            tp_item="GRUPO",
        )
        segundo = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            nm_item="Segundo",
            cd_item_tecnico="SEGUNDO",
            tp_item="GRUPO",
        )
        filho = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_pai=primeiro,
            nm_item="Filho",
            cd_item_tecnico="FILHO",
            tp_item="ACAO",
        )
        self.login_as(self.ti_user)
        response = self.client.patch(
            reverse("atendimento:perfil-assistencial-itens-api", args=[perfil.pk]),
            data=json.dumps({"items": [{"id": filho.pk, "parent_id": segundo.pk, "order": 9}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        filho.refresh_from_db()
        self.assertEqual(filho.cd_item_pai, primeiro)
        self.assertEqual(filho.nr_ordem, 9)

    def test_api_perfil_cria_rascunho_e_publica_versao(self):
        self.login_as(self.ti_user)
        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="API")
        url = reverse("atendimento:perfil-assistencial-itens-api", args=[perfil.pk])
        criado = self.client.post(
            url,
            data=json.dumps({
                "technical_key": "ATENDER",
                "name": "Atender",
                "type": "GRUPO",
                "order": 1,
            }),
            content_type="application/json",
        )
        self.assertEqual(criado.status_code, 200)
        versao = perfil.versoes.get(ds_status="RASCUNHO")
        self.assertTrue(versao.itens.filter(cd_item_tecnico="ATENDER").exists())
        publicado = self.client.post(
            reverse("atendimento:publicar-perfil-assistencial-api", args=[perfil.pk]),
            data=json.dumps({"description": "Estrutura inicial"}),
            content_type="application/json",
        )
        self.assertEqual(publicado.status_code, 200)
        versao.refresh_from_db()
        self.assertEqual(versao.ds_status, "PUBLICADO")

    def test_pep_exibe_historico_sinais_e_menu_configurado_e_cria_documento(self):
        self.medico_user.cd_prestador = self.prestador
        self.medico_user.save(update_fields=["cd_prestador"])
        PrestadorTipo.objects.create(
            cd_empresa=self.empresa,
            cd_prestador=self.prestador,
            cd_tipo_prestador="MEDICO",
            sn_principal=True,
        )
        perfil = PerfilAssistencial.objects.create(cd_empresa=self.empresa, nm_perfil="Perfil clínico")
        PerfilAssistencialTipo.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_tipo_prestador="MEDICO",
        )
        versao = PerfilAssistencialVersao.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            nr_versao=1,
            ds_status="PUBLICADO",
        )
        grupo = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_tecnico="ATENDER",
            nm_item="Atender",
            ds_icone="activity",
            tp_item="GRUPO",
        )
        modelo = ModeloDocumento.objects.create(
            cd_empresa=self.empresa,
            nm_modelo="Admissão configurada",
            tp_documento="ADMISSAO",
            tp_elemento="DOCUMENTO",
        )
        item = ItemMenuAssistencial.objects.create(
            cd_empresa=self.empresa,
            cd_perfil_assistencial=perfil,
            cd_versao_perfil=versao,
            cd_item_pai=grupo,
            cd_item_tecnico="ADMISSAO",
            cd_modelo_documento=modelo,
            nm_item="Admissão",
            ds_icone="document",
            tp_item="DOCUMENTO",
            sn_imprimivel=True,
            sn_permite_criar=True,
        )
        pre_atendimento = PreAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_queixa_principal="Dor",
            nr_pressao_arterial="120/80",
            nr_frequencia_cardiaca=72,
            nr_saturacao=98,
        )
        PreAtendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            ds_queixa_principal="Coleta anterior",
            nr_pressao_arterial="130/90",
            nr_frequencia_cardiaca=80,
            nr_temperatura="37.1",
        )
        atendimento = Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            cd_pre_atendimento=pre_atendimento,
            ds_status="EM_ATENDIMENTO",
            ds_especialidade="Clínica Geral",
            ds_tipo_atendimento="Consulta",
        )
        Atendimento.objects.create(
            cd_empresa=self.empresa,
            cd_paciente=self.paciente,
            cd_prestador=self.prestador,
            ds_status="FINALIZADO",
            ds_especialidade="Cardiologia",
            ds_tipo_atendimento="Retorno",
        )
        self.login_as(self.medico_user)
        url = reverse("atendimento:pep-prontuario-paciente", args=[self.paciente.pk])
        response = self.client.get(url, {"atendimento": atendimento.pk, "item": item.pk})
        self.assertContains(response, "Histórico de atendimentos")
        self.assertContains(response, "Atendimento {}".format(atendimento.pk))
        self.assertContains(response, "Últimos sinais vitais")
        self.assertContains(response, "Histórico de sinais vitais")
        self.assertContains(response, "130/90")
        self.assertContains(response, "Resumo clínico do prontuário")
        self.assertContains(response, "120/80")
        self.assertContains(response, "Atender")
        self.assertContains(response, "Admissão")
        self.assertContains(response, "Impressão")
        self.assertContains(response, "Novo")

        consulta = self.client.get(
            url,
            {"modo": "consulta", "atendimento": atendimento.pk, "item": item.pk},
        )
        self.assertContains(consulta, "Prontuário — consulta")
        self.assertContains(consulta, "Admissão")
        self.assertNotContains(consulta, "data-pep-new-document")

        response = self.client.post(
            f"{url}?atendimento={atendimento.pk}&item={item.pk}",
            {
                "acao": "novo_documento",
                "item": item.pk,
                "dh_documento": "2026-07-02T09:30",
            },
        )
        self.assertEqual(response.status_code, 302)
        documento = DocumentoClinico.objects.get(cd_atendimento=atendimento, cd_modelo_documento=modelo)
        self.assertEqual(documento.cd_item_menu_assistencial, item)
        self.assertEqual(documento.ds_status, "ABERTO")

    def test_editor_suporta_checkboxes_exclusivos_com_campo_condicional(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "document-editor.js").read_text(encoding="utf-8")
        template = (
            settings.BASE_DIR / "templates" / "atendimento" / "documento_clinico.html"
        ).read_text(encoding="utf-8")
        self.assertIn('"exclusive-checkboxes"', javascript)
        self.assertIn("data-exclusive-choice", javascript)
        self.assertIn("data-exclusive-detail", javascript)
        self.assertIn("HIPOT.[hipot]", javascript)
        self.assertIn("HIPOT.[hipot; Pressão arterial]", javascript)
        self.assertIn("splitStructuredOptions", javascript)
        self.assertIn("detailPlaceholder", javascript)
        self.assertNotIn('placeholder=\"${escapeHtml(detailName)}\"', javascript)
        self.assertIn("data-exclusive-required", template)
        self.assertIn("syncExclusive", template)
        self.assertIn('data[name] = field.value', template)

    def test_pesquisa_lateral_restaura_estado_anterior_dos_modulos(self):
        javascript = (settings.BASE_DIR / "static" / "js" / "celeris.js").read_text(encoding="utf-8")
        self.assertIn("openStateBeforeSearch = new Map", javascript)
        self.assertIn("group.open = openStateBeforeSearch.get(group) || false", javascript)
        self.assertIn("if (!term && searchActive)", javascript)
        self.assertIn("formHasActualChanges(form)", javascript)
        self.assertIn('form.method?.toLowerCase() === "get"', javascript)
        self.assertIn('document.addEventListener("pointerdown"', javascript)
        patient_template = (
            settings.BASE_DIR / "templates" / "atendimento" / "cadastro_paciente.html"
        ).read_text(encoding="utf-8")
        self.assertIn("data-confirmation-review", patient_template)
        self.assertIn("data-disable-state-persistence", patient_template)
