import json

with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\data\unac\proyecto\unac_proyecto_cuant.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cuerpo = data.get("cuerpo", [])
for cap in cuerpo:
    titulo_cap = cap.get("titulo", "")
    for i, item in enumerate(cap.get("contenido", [])):
        if isinstance(item, dict) and "imagenes" in item:
            for img in item["imagenes"]:
                print(f"Capítulo: {titulo_cap}")
                print(f"  Imagen: {img.get('titulo')}")
                print(f"    Nota: {img.get('nota') or img.get('note')}")
                print(f"    Nota Color: {img.get('nota_color') or img.get('note_color')}")
