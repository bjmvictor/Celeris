"""Operações históricas de dados da migration 0043."""

from django.db import migrations


ICONES_PADRAO = [
    ("Paciente", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M10.177 2.254A2.102 2.102 0 0 1 14.1 3.3c0 .952-.634 1.755-1.5 2.014q-.286.085-.6.086a2.1 2.1 0 0 1-1.822-3.146m6.559 11.362L15 11.276V21.6c0 .664-.536 1.2-1.2 1.2s-1.2-.536-1.2-1.2V6.638a5 5 0 0 1 3.42 1.987l2.644 3.563c.394.532.285 1.282-.247 1.68s-1.282.285-1.68-.247zM11.4 6.638V21.6c0 .664-.536 1.2-1.2 1.2S9 22.264 9 21.6v-4.8h-.968a.602.602 0 0 1-.57-.791l1.613-4.837-1.811 2.441c-.394.532-1.147.645-1.68.247s-.645-1.147-.247-1.68l2.644-3.563a5 5 0 0 1 3.42-1.987z"/></svg>'),
    ("Criança", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path fill="currentColor" d="M14.4 4.8c0-1.324-1.076-2.4-2.4-2.4S9.6 3.476 9.6 4.8s1.076 2.4 2.4 2.4 2.4-1.076 2.4-2.4m-3.866 3.949a4.42 4.42 0 0 1-2.205-1.717l-.731-1.099c-.367-.551-1.11-.698-1.661-.33s-.701 1.11-.334 1.665l.731 1.095A6.87 6.87 0 0 0 9 10.703V20.4c0 .664.536 1.2 1.2 1.2s1.2-.536 1.2-1.2v-3.6h1.2v3.6c0 .664.536 1.2 1.2 1.2s1.2-.536 1.2-1.2v-9.69a6.84 6.84 0 0 0 2.726-2.408l.682-1.046c.36-.555.203-1.298-.352-1.661s-1.298-.206-1.661.352l-.683 1.043a4.43 4.43 0 0 1-5.078 1.793c-.034-.011-.068-.026-.101-.034"/></svg>'),
    ("Idoso", '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon icon-tabler icons-tabler-outline icon-tabler-old"><path d="M0 0h24v24H0z" stroke="none"/><path d="m11 21-1-4-2-3V8"/><path d="m5 14-1-3 4-3 3 2 3 .5M7 4a1 1 0 1 0 2 0 1 1 0 1 0-2 0m0 13-2 4m11 0v-8.5a1.5 1.5 0 0 1 3 0v.5"/></svg>'),
    ("Gestante", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 4c0-1.11.89-2 2-2s2 .89 2 2-.89 2-2 2-2-.89-2-2m7 9a3.29 3.29 0 0 0-2-3c0-1.66-1.34-3-3-3s-3 1.34-3 3v7h2v5h3v-5h3z" fill="currentColor"/></svg>'),
    ("Cadeirante", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M15.8 4.45a2 2 0 1 1-4 0 2 2 0 0 1 4 0" fill="currentColor"/><path fill-rule="evenodd" clip-rule="evenodd" d="M8.3 8.635 6.507 6.842 5.093 8.257 6.3 9.464v3.244a5 5 0 1 0 8.173 4.37c.47-.005.874-.004 1.193 0h.139l1.26 3.326a1 1 0 1 0 1.87-.709l-1.625-4.29-3.694-2.154-.616-.616v-.027l.002-.015a23 23 0 0 0 .089-.929l.011-.152c.264.21.543.427.792.598.134.091.283.186.431.26.09.045.263.128.478.163l3.422.978a1 1 0 0 0 .55-1.923l-3.164-.904a57 57 0 0 0-1.163-1.556 24 24 0 0 0-1.126-1.356 7 7 0 0 0-.542-.542 3 3 0 0 0-.274-.217 1.45 1.45 0 0 0-.744-.586c-.567-.187-1.042.059-1.301.258-.261.201-.47.472-.632.72-.17.261-.328.561-.473.874-.443.956-.841 2.212-1.056 3.271zm4.2 7.915a3 3 0 1 1-6 0 3 3 0 0 1 6 0m2.746-5.956-.017-.008z" fill="currentColor"/></svg>'),
    ("Criança de colo", '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.5 9a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" fill="currentColor"/><path fill-rule="evenodd" clip-rule="evenodd" d="M15.186 9.533a1.5 1.5 0 0 1 1.625.739l2.5 4.5a1.5 1.5 0 0 1-.063 1.56l-2.992 4.489q-.13.198-.307.341a1.504 1.504 0 0 1-2.111-.213 1.5 1.5 0 0 1-.143-1.69l.144-.258.403-.622a1.5 1.5 0 0 0-.767-2.233L11 15.288V14a1 1 0 1 0-2 0v2a1 1 0 0 0 .672.945l1.324.459-1.587 1.269.73.85a1.5 1.5 0 0 1-2.278 1.953l-3-3.5a1.5 1.5 0 0 1-.172-1.704l2.5-4.5a1.5 1.5 0 0 1 .997-.739zM15 16a2 2 0 1 0 0-4 2 2 0 0 0 0 4" fill="currentColor"/></svg>'),
]


def seed_paineis_chamada(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    Icone = apps.get_model("atendimento", "IconeChamada")
    Module = apps.get_model("core", "Module")
    Screen = apps.get_model("core", "ScreenDefinition")
    Group = apps.get_model("auth", "Group")
    Papel = apps.get_model("accounts", "Papel")
    PapelModulo = apps.get_model("accounts", "PapelModulo")
    PapelTela = apps.get_model("accounts", "PapelTela")

    for empresa in Empresa.objects.all():
        for nome, svg in ICONES_PADRAO:
            Icone.objects.get_or_create(
                cd_empresa_id=empresa.pk,
                nm_icone=nome,
                defaults={"ds_svg": svg, "sn_ativo": True},
            )

    modulo, _ = Module.objects.update_or_create(
        code="TOTEM_SENHAS",
        defaults={"title": "Painéis de Chamada", "active": True},
    )
    Screen.objects.filter(access_key__in=["acesso-totem-gerar-senha"], module=modulo).update(active=False)
    Screen.objects.filter(slug__in=["totem-gerar-senha"], module=modulo).update(active=False)
    telas = [
        ("Configurar", "paineis-configurar-senhas", "atendimento:configurar-senhas", "", 10, False),
        ("Classes", "paineis-classes-senha", "atendimento:classes-senha", "Tabelas", 20, True),
        ("Protocolos", "paineis-protocolos-senha", "atendimento:protocolos-senha", "Tabelas", 30, True),
        ("Ícones", "paineis-icones-chamada", "atendimento:icones-chamada", "Tabelas", 40, True),
        ("Máquinas", "paineis-maquinas-chamada", "atendimento:maquinas-chamada", "Tabelas", 50, True),
    ]
    for titulo, slug, acesso, parent, ordem, allow_delete in telas:
        tela, _ = Screen.objects.update_or_create(
            access_key=acesso,
            defaults={
                "module": modulo,
                "title": titulo,
                "slug": slug,
                "screen_type": "formulario",
                "parent_label": parent,
                "table_name": "",
                "allow_query": True,
                "allow_insert": True,
                "allow_update": True,
                "allow_delete": allow_delete,
                "active": True,
                "order": ordem,
            },
        )
        for grupo in Group.objects.filter(name="TI"):
            papel, _ = Papel.objects.get_or_create(grupo=grupo)
            PapelModulo.objects.get_or_create(papel=papel, modulo=modulo)
            PapelTela.objects.get_or_create(papel=papel, tela=tela)


class Migration(migrations.Migration):

    dependencies = [
        ("atendimento", "0042_iconechamada_classesenhaatendimento_cd_icone_chamada_and_more"),
        ("core", "0032_corrigir_tela_alteracao_senha"),
        ("accounts", "0015_sync_navigation_role_catalog"),
    ]

    operations = [
        migrations.RunPython(seed_paineis_chamada, migrations.RunPython.noop),
    ]
