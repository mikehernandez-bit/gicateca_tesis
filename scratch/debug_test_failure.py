import json
from app.engine.normalizer import normalize

def _minimal_json():
    return {
        "_meta": {"id": "test-format", "university": "unac"},
        "configuracion": {"ruta_logo": "app/static/assets/LogoUNAC.png"},
        "caratula": {
            "universidad": "UNIVERSIDAD TEST",
            "facultad": "FACULTAD TEST",
            "titulo_placeholder": "TÍTULO TEST",
        },
        "cuerpo": [{"titulo": "CAP I"}],
    }

data = _minimal_json()
data["finales"] = {
    "anexos": {
        "titulo_seccion": "ANEXOS",
        "lista": [
            {
                "titulo": "Anexo 1: Matriz de consistencia final",
                "_ai_content": [
                    {
                        "tipo": "parrafo",
                        "texto": "A continuacion se muestra la matriz de consistencia final.",
                    },
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 14. Matriz de consistencia final",
                        "encabezados": ["Problema", "Objetivo"],
                        "filas": [["P1", "O1"]],
                    },
                ],
            }
        ],
    }
}

blocks = normalize(data)
for i, b in enumerate(blocks):
    print(f"Block {i}: Type: {b['type']}, Keys: {list(b.keys())}, Text: {b.get('text') or b.get('titulo')}")
