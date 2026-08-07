import json

with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\data\unac\proyecto\unac_proyecto_cuant.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cuerpo = data.get("cuerpo", [])
for cap in cuerpo:
    titulo = cap.get("titulo", "")
    if "MARCO" in titulo.upper() or "BASES" in titulo.upper() or "II" in titulo:
        print(f"Capítulo: {titulo}")
        for i, item in enumerate(cap.get("contenido", [])):
            print(f"  Item {i}: Keys: {list(item.keys()) if isinstance(item, dict) else 'str'}, Texto/Titulo: {item.get('texto') or item.get('titulo') or item.get('titulo_placeholder')}")
            if isinstance(item, dict) and "imagenes" in item:
                print(f"    Imágenes: {item['imagenes']}")
            if isinstance(item, dict) and "tabla" in item:
                print(f"    Tabla: {item['tabla']}")
