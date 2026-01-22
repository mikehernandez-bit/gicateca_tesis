"""Service layer for formats module."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.core.loaders import load_json_file, get_data_dir


ROOT = Path(__file__).resolve().parents[3]
CF_DIR = ROOT / "app" / "universities" / "unac" / "centro_formatos"

SCRIPTS_CONFIG = {
    "proyecto": "generador_proyecto_tesis.py",
    "informe": "generador_informe_tesis.py",
    "maestria": "generador_maestria.py",
}


def get_formato(format_id: str) -> Optional[Dict]:
    """
    Get a specific format by ID.
    ID format: "unac-{tipo}-{enfoque}"
    """
    parts = format_id.split("-")
    
    if len(parts) < 3 or parts[0] != "unac":
        raise ValueError(f"Invalid format ID: expected 'unac-tipo-enfoque', got '{format_id}'")
    
    tipo = parts[1]
    enfoque = parts[2]
    
    data_dir = get_data_dir()
    json_file = data_dir / tipo / f"unac_{tipo}_{enfoque}.json"
    
    try:
        data = load_json_file(json_file)
        
        tipo_labels = {"informe": "Informe de Tesis", "maestria": "Tesis de Maestría", "proyecto": "Proyecto de Tesis"}
        enfoque_label = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
        tipo_filtro = {
            "informe": "Inv. Formativa",
            "maestria": "Suficiencia",
            "proyecto": "Tesis",
        }
        
        return {
            "id": format_id,
            "uni": "UNAC",
            "uni_code": "unac",
            "tipo": tipo_filtro[tipo],
            "titulo": f"{tipo_labels[tipo]} - {enfoque_label[enfoque]}",
            "facultad": "Centro de Formatos UNAC",
            "escuela": "Dirección Académica",
            "estado": "VIGENTE",
            "version": data.get("version", "1.0.0"),
            "fecha": "2026-01-17",
            "resumen": data.get("descripcion", f"Plantilla oficial de {tipo_labels[tipo]} con enfoque {enfoque_label[enfoque]}"),
            "tipo_formato": tipo,
            "enfoque": enfoque,
        }
    except (FileNotFoundError, ValueError, KeyError) as e:
        raise ValueError(f"Format not found: {format_id}") from e


def generate_document(format_id: str, section_filter: Optional[str] = None) -> Tuple[Path, str]:
    """
    Generate a DOCX document for the given format.
    Allows filtering by section.
    """
    parts = format_id.split("-")
    
    if len(parts) < 3 or parts[0] != "unac":
        raise ValueError(f"Invalid format ID: {format_id}")
    
    tipo = parts[1]
    enfoque = parts[2]
    
    if tipo not in SCRIPTS_CONFIG:
        raise ValueError(f"Unknown format type: {tipo}")
    
    script_name = SCRIPTS_CONFIG[tipo]
    script_path = CF_DIR / script_name
    
    if not script_path.exists():
        raise RuntimeError(f"Generator script not found: {script_path}")
    
    data_dir = get_data_dir()
    json_path = data_dir / tipo / f"unac_{tipo}_{enfoque}.json"
    
    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    # =========================================================
    # LÓGICA DE FILTRADO (SIMPLIFICADA Y AGRESIVA)
    # =========================================================
    path_to_use = json_path
    
    if section_filter == "planteamiento":
        print(f"[DEBUG] Filtrando SOLO CAPÍTULO I para: {format_id}")
        
        # 1. Cargamos el JSON original
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 2. LIMPIEZA TOTAL: Vaciamos todo lo que no sea el cuerpo
        data["preliminares"] = {} 
        data["finales"] = {}
        data["matriz_consistencia"] = {}
        
        if "caratula" in data:
            data["caratula"]["tipo_documento"] = "VISTA PREVIA - CAPÍTULO I"

        # 3. FILTRO RÁPIDO: Nos quedamos SOLO con el bloque que tenga "PLANTEAMIENTO"
        # Esto elimina cualquier otro capítulo de la lista.
        data["cuerpo"] = [
            cap for cap in data.get("cuerpo", [])
            if "PLANTEAMIENTO" in cap.get("titulo", "").upper()
        ]
        
        # 4. Guardamos el JSON filtrado
        tmp_json = tempfile.NamedTemporaryFile(prefix="filtered_", suffix=".json", delete=False, mode="w", encoding="utf-8")
        json.dump(data, tmp_json, ensure_ascii=False, indent=2)
        tmp_json.close()
        
        path_to_use = Path(tmp_json.name)
    # =========================================================

    filename = f"UNAC_{tipo.upper()}_{enfoque.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix="unac_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()
    
    cmd = [sys.executable, str(script_path), str(path_to_use), str(output_path)]
    result = subprocess.run(cmd, cwd=str(CF_DIR), capture_output=True, text=True)
    
    # Debug logs (útil si falla)
    # print(f"[DEBUG] Stderr: {result.stderr}")
    
    # Limpiamos el JSON temporal
    if path_to_use != json_path:
        try:
            path_to_use.unlink()
        except Exception:
            pass
    
    if result.returncode != 0:
        print("[ERROR]", result.stderr)
        raise RuntimeError("Document generation failed. Check console for details.")
    
    if not output_path.exists():
        raise RuntimeError("Generator script executed but did not create DOCX file.")
    
    return output_path, filename


def cleanup_temp_file(path: Path) -> None:
    """Clean up temporary file."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] Could not delete temp file: {exc}")