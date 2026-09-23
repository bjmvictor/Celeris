"""Stable, narrow public operations exposed by legacy Atendimento."""
from django.apps import apps


def limpar_rascunhos_do_usuario(usuario) -> int:
    draft_model = apps.get_model("atendimento", "RascunhoEditorDocumento")
    deleted, _ = draft_model.objects.filter(cd_usuario=usuario).delete()
    return deleted
