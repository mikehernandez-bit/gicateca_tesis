import json

with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\data\unac\proyecto\unac_proyecto_cuant.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def search_notes(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            current_path = f"{path}.{k}" if path else k
            if k in ("nota", "note", "instruccion", "instruccion_detallada") and v:
                print(f"Path: {current_path} => {str(v)[:150]}")
            search_notes(v, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            search_notes(item, f"{path}[{i}]")

search_notes(data)
