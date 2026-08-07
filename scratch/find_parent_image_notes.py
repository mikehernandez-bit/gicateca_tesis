import json

with open(r'c:\Users\jhoan\Documents\gicateca_tesis\app\data\unac\proyecto\unac_proyecto_cuant.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

cuerpo = data.get("cuerpo", [])
for cap in cuerpo:
    titulo_cap = cap.get("titulo", "")
    for i, item in enumerate(cap.get("contenido", [])):
        if isinstance(item, dict) and "imagenes" in item:
            print(f"Capítulo: {titulo_cap}, Sección: {item.get('texto')}")
            print(f"  Item Nota: {item.get('nota')}")
            print(f"  Item Nota Color: {item.get('nota_color')}")
            print(f"  Item Instrucción Detallada: {item.get('instruccion_detallada')}")
