from django.db import migrations


ESCALAS = (
    {
        "nome": "Régua de dor",
        "descricao": "Avaliação numérica da intensidade da dor.",
        "perguntas": [
            {
                "chave": "dor",
                "texto": "Intensidade da dor",
                "opcoes": [
                    {"valor": str(valor), "descricao": str(valor), "pontos": valor}
                    for valor in range(11)
                ],
            }
        ],
        "faixas": [
            {"minimo": 0, "maximo": 0, "descricao": "Sem dor", "cor": "#16a34a"},
            {"minimo": 1, "maximo": 3, "descricao": "Dor leve", "cor": "#84cc16"},
            {"minimo": 4, "maximo": 6, "descricao": "Dor moderada", "cor": "#eab308"},
            {"minimo": 7, "maximo": 10, "descricao": "Dor intensa", "cor": "#dc2626"},
        ],
    },
    {
        "nome": "Escala de coma de Glasgow",
        "descricao": "Avaliação da abertura ocular e das respostas verbal e motora.",
        "perguntas": [
            {
                "chave": "ocular",
                "texto": "Abertura ocular",
                "opcoes": [
                    {"valor": "1", "descricao": "Ausente", "pontos": 1},
                    {"valor": "2", "descricao": "À pressão", "pontos": 2},
                    {"valor": "3", "descricao": "Ao som", "pontos": 3},
                    {"valor": "4", "descricao": "Espontânea", "pontos": 4},
                ],
            },
            {
                "chave": "verbal",
                "texto": "Resposta verbal",
                "opcoes": [
                    {"valor": "1", "descricao": "Ausente", "pontos": 1},
                    {"valor": "2", "descricao": "Sons incompreensíveis", "pontos": 2},
                    {"valor": "3", "descricao": "Palavras inadequadas", "pontos": 3},
                    {"valor": "4", "descricao": "Confusa", "pontos": 4},
                    {"valor": "5", "descricao": "Orientada", "pontos": 5},
                ],
            },
            {
                "chave": "motora",
                "texto": "Resposta motora",
                "opcoes": [
                    {"valor": "1", "descricao": "Ausente", "pontos": 1},
                    {"valor": "2", "descricao": "Extensão anormal", "pontos": 2},
                    {"valor": "3", "descricao": "Flexão anormal", "pontos": 3},
                    {"valor": "4", "descricao": "Retirada", "pontos": 4},
                    {"valor": "5", "descricao": "Localiza estímulo", "pontos": 5},
                    {"valor": "6", "descricao": "Obedece a comandos", "pontos": 6},
                ],
            },
        ],
        "faixas": [
            {"minimo": 3, "maximo": 8, "descricao": "Grave", "cor": "#dc2626"},
            {"minimo": 9, "maximo": 12, "descricao": "Moderado", "cor": "#eab308"},
            {"minimo": 13, "maximo": 15, "descricao": "Leve", "cor": "#16a34a"},
        ],
    },
    {
        "nome": "NEWS 2",
        "descricao": "Registro da pontuação consolidada do National Early Warning Score 2.",
        "perguntas": [
            {
                "chave": "news2",
                "texto": "Pontuação NEWS 2",
                "opcoes": [
                    {"valor": str(valor), "descricao": str(valor), "pontos": valor}
                    for valor in range(21)
                ],
            }
        ],
        "faixas": [
            {"minimo": 0, "maximo": 4, "descricao": "Baixo risco", "cor": "#16a34a"},
            {"minimo": 5, "maximo": 6, "descricao": "Risco médio", "cor": "#eab308"},
            {"minimo": 7, "maximo": 20, "descricao": "Alto risco", "cor": "#dc2626"},
        ],
    },
)


def criar_escalas(apps, schema_editor):
    Empresa = apps.get_model("accounts", "Empresa")
    EscalaClinica = apps.get_model("atendimento", "EscalaClinica")
    for empresa in Empresa.objects.all():
        for dados in ESCALAS:
            EscalaClinica.objects.update_or_create(
                cd_empresa=empresa,
                nm_escala=dados["nome"],
                nr_versao=1,
                defaults={
                    "ds_descricao": dados["descricao"],
                    "tp_calculo": "SOMA",
                    "ds_perguntas": dados["perguntas"],
                    "ds_faixas_resultado": dados["faixas"],
                    "sn_ativo": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [("atendimento", "0052_documentos_por_tela_impressao")]
    operations = [migrations.RunPython(criar_escalas, migrations.RunPython.noop)]
