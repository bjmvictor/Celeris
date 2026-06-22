from datetime import time

from django.contrib.auth.hashers import make_password
from django.db import migrations


USERS = [
    ("ADMIN", "Administrador TI", "TI", True),
    ("RECEPCAO", "Recepcionista Homologação", "Recepcionista", False),
    ("ENFERMAGEM", "Enfermeiro Homologação", "Enfermeiro", False),
    ("MEDICO", "Médico Homologação", "Médico", False),
]


def seed(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    User = apps.get_model("accounts", "User")
    UsuarioEmpresa = apps.get_model("accounts", "UsuarioEmpresa")
    Group = apps.get_model("auth", "Group")
    Convenio = apps.get_model("atendimento", "Convenio")
    Prestador = apps.get_model("atendimento", "Prestador")
    AgendaProfissional = apps.get_model("atendimento", "AgendaProfissional")
    TabelaAuxiliarGlobal = apps.get_model("core", "TabelaAuxiliarGlobal")
    ValorAuxiliarGlobal = apps.get_model("core", "ValorAuxiliarGlobal")

    empresa, _ = Empresa.objects.get_or_create(
        cd_empresa=1,
        defaults={"nm_empresa": "CLÍNICA HOMOLOGAÇÃO", "sn_ativo": True},
    )

    for username, full_name, group_name, is_ti in USERS:
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "full_name": full_name,
                "password": make_password("123456"),
                "is_active": True,
                "is_staff": is_ti,
                "is_superuser": is_ti,
            },
        )
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.set([group])
        UsuarioEmpresa.objects.update_or_create(
            usuario=user,
            empresa=empresa,
            defaults={"sn_padrao": True, "sn_ativo": True},
        )

    Convenio.objects.update_or_create(
        cd_empresa=empresa,
        nm_convenio="PARTICULAR",
        defaults={"sn_ativo": True},
    )
    specialty_table, _ = TabelaAuxiliarGlobal.objects.get_or_create(
        ds_tabela="especialidade",
        defaults={"ds_descricao": "Especialidades", "sn_ativo": True},
    )
    ValorAuxiliarGlobal.objects.update_or_create(
        cd_tabela_auxiliar_global=specialty_table,
        cd_valor="CLINICA_GERAL",
        defaults={"ds_valor": "CLÍNICA GERAL", "sn_ativo": True},
    )
    provider, _ = Prestador.objects.update_or_create(
        cd_empresa=empresa,
        nr_conselho="HOMOLOGACAO",
        defaults={
            "nm_prestador": "MÉDICO HOMOLOGAÇÃO",
            "tp_prestador": "MEDICO",
            "ds_conselho": "CRM",
            "ds_especialidade": "CLINICA_GERAL",
            "sn_ativo": True,
        },
    )
    for weekday in range(5):
        AgendaProfissional.objects.update_or_create(
            cd_empresa=empresa,
            cd_prestador=provider,
            nr_dia_semana=weekday,
            defaults={
                "ds_agenda": "AGENDA HOMOLOGAÇÃO",
                "hr_inicio": time(8, 0),
                "hr_fim": time(18, 0),
                "nr_tempo_atendimento": 30,
                "nr_intervalo": 0,
                "sn_ativo": True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("atendimento", "0010_prescricao_evolucaoatendimento"),
        ("core", "0015_seed_erp_auxiliaries"),
    ]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
