import json
import os
import sys

# Add app to path
sys.path.append(os.getcwd())

from app.modules.generation.preprocessor import merge_values, apply_ai_content, exclude_instruction_keys

def test_gicathesis_preprocessor():
    # 1. Load a sample format
    format_path = "app/data/unac/maestria/unac_maestria_cuant.json"
    with open(format_path, "r", encoding="utf-8") as f:
        format_data = json.load(f)
    
    # 2. Mock values (what GicaGen sends)
    values = {
        "autor1_nombres": "JUAN PEREZ",
        "autor1_dni": "12345678",
        "asesor_nombres": "PEDRO GOMEZ",
        "linea_investigacion": "INGENIERIA DE SOFTWARE",
        "anio": "2025",
        "titulo": "TESIS DE IMPACTO",
        "lugar_caratula": "Callao"
    }
    
    # 3. Mock AI sections
    ai_sections = [
        {"path": "Información Básica", "content": "Contenido generado por IA de prueba para Datos Generales."}
    ]
    
    # 4. Run preprocessor (REAL PIPELINE)
    print("--- PREPROCESSING ---")
    clean_data = exclude_instruction_keys(format_data)
    
    # Verify _meta still exists
    if "_meta" not in clean_data:
        print("[!] ERROR: _meta was stripped! Identity lost.")
    else:
        print("[OK] _meta preserved. Identity confirmed.")

    merged = merge_values(clean_data, values)
    final = apply_ai_content(merged, ai_sections)
    
    # 5. Verify Caratula
    caratula = final.get("caratula", {})
    print("\n[CARATULA]")
    print(f"Autores: {caratula.get('autores')}")
    print(f"Asesor: {caratula.get('asesor')}")
    print(f"Linea: {caratula.get('linea_investigacion')}")
    print(f"Titulo: {caratula.get('titulo')}")
    
    # 6. Verify Info Basica
    # In this format, Info Basica is part of 'cuerpo' or 'preliminares'?
    # Actually, in UNAC, it's often a chapter or section.
    
    # Check if smart replacements worked on placeholders
    # Let's search for "Bach. JUAN PEREZ" in the whole dict
    final_str = json.dumps(final, ensure_ascii=False)
    if "Bach. JUAN PEREZ" in final_str:
        print("\n[OK] Smart replacement for Autor found!")
    else:
        print("\n[!] FAIL: Smart replacement for Autor NOT found!")

    if "Contenido generado por IA" in final_str:
        print("[OK] AI Section found!")
    else:
        print("[!] FAIL: AI Section NOT found!")

if __name__ == "__main__":
    test_gicathesis_preprocessor()
