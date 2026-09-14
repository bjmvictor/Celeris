from django.db import migrations


TIPOS_ADMINISTRATIVOS = {
    "COMPROVANTE_AGENDAMENTO",
    "COMPROVANTE_CHAMADO",
    "FICHA_ATENDIMENTO",
    "ETIQUETA_ATENDIMENTO",
    "ADMINISTRATIVO",
}


def classificar_modelos(apps, schema_editor):
    ModeloDocumento = apps.get_model("atendimento", "ModeloDocumento")
    ModeloDocumento.objects.filter(tp_documento__in=TIPOS_ADMINISTRATIVOS).update(
        tp_finalidade_assinatura="ADMINISTRATIVO"
    )


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0064_assinaturadigitaldocumento_cd_certificado_digital_and_more")]

    operations = [migrations.RunPython(classificar_modelos, migrations.RunPython.noop)]
