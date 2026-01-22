"""Service layer for catalog module."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
from typing import Dict, List

from app.core.university_registry import get_provider
from app.core.loaders import load_json_file, get_data_dir

ROOT = Path(__file__).resolve().parents[3]
CF_DIR = ROOT / "app" / "universities" / "unac" / "centro_formatos"
DOCS_DIR = ROOT / "docs" / "centro_formatos"

SCRIPTS_CONFIG: Dict[str, Dict[str, Dict[str, str]]] = {
    "proyecto": {
        "script": "generador_proyecto_tesis.py",
        "jsons": {
            "cuant": "proyecto/unac_proyecto_cuant.json",
            "cual": "proyecto/unac_proyecto_cual.json",
        },
    },
    "informe": {
        "script": "generador_informe_tesis.py",
        "jsons": {
            "cuant": "informe/unac_informe_cuant.json",
            "cual": "informe/unac_informe_cual.json",
        },
    },
    "maestria": {
        "script": "generador_maestria.py",
        "jsons": {
            "cuant": "maestria/unac_maestria_cuant.json",
            "cual": "maestria/unac_maestria_cual.json",
        },
    },
}

ALIASES = {
    "pregrado": "informe",
}


def get_all_formatos() -> List[Dict]:
    """Get all 6 formats (informe, maestria, proyecto × cualitativo, cuantitativo)."""
    formatos = []
    data_dir = get_data_dir()
    
    tipo_labels = {"informe": "Informe de Tesis", "maestria": "Tesis de Maestría", "proyecto": "Proyecto de Tesis"}
    enfoque_label = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
    tipo_filtro = {
        "informe": "Inv. Formativa",
        "maestria": "Suficiencia",
        "proyecto": "Tesis",
    }
    
    for tipo in ["informe", "maestria", "proyecto"]:
        for enfoque in ["cual", "cuant"]:
            json_file = data_dir / tipo / f"unac_{tipo}_{enfoque}.json"
            
            try:
                data = load_json_file(json_file)
                formatos.append({
                    "id": f"unac-{tipo}-{enfoque}",
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
                })
            except (FileNotFoundError, ValueError) as e:
                print(f"Warning: Could not load {json_file}: {e}")
                continue
    
    return formatos


def _normalize_format(fmt_type: str) -> str:
    fmt_type = (fmt_type or "").strip().lower()
    if fmt_type in ALIASES:
        fmt_type = ALIASES[fmt_type]
    return fmt_type


def _resolve_paths(fmt_type: str, sub_type: str):
    fmt_type = _normalize_format(fmt_type)
    if fmt_type not in SCRIPTS_CONFIG:
        raise ValueError("Formato no valido")

    config = SCRIPTS_CONFIG[fmt_type]
    sub_type = (sub_type or "").strip().lower()
    if sub_type not in config["jsons"]:
        raise ValueError("Subtipo no valido")

    script_path = CF_DIR / config["script"]
    if not script_path.exists():
        raise RuntimeError(f"Script no encontrado: {config['script']}")

    data_dir = get_data_dir()
    json_path = data_dir / config["jsons"][sub_type]
    if not json_path.exists():
        raise RuntimeError(f"JSON no encontrado: {config['jsons'][sub_type]}")

    return fmt_type, sub_type, script_path, json_path


def cleanup_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] No se pudo eliminar temporal: {exc}")


def generate_document(fmt_type: str, sub_type: str):
    fmt_type, sub_type, script_path, json_path = _resolve_paths(fmt_type, sub_type)

    filename = f"UNAC_{fmt_type.upper()}_{sub_type.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix="unac_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()

    cmd = [sys.executable, str(script_path), str(json_path), str(output_path)]
    result = subprocess.run(cmd, cwd=str(CF_DIR), capture_output=True, text=True)

    if result.returncode != 0:
        print("[ERROR PYTHON]", result.stderr)
        raise RuntimeError("Fallo la generacion interna. Revisa consola.")

    if not output_path.exists():
        raise RuntimeError("El script corrio pero no genero el DOCX")

    return output_path, filename

# NUEVA FUNCIÓN AGREGADA PARA LA VISTA PREVIA (CARÁTULAS)
def get_format_json_content(format_id: str) -> Dict:
    """
    Busca y devuelve el contenido crudo del JSON para las vistas previas.
    ID esperado: unac-informe-cual -> data/unac/informe/unac_informe_cual.json
    """
    try:
        parts = format_id.split("-") # ['unac', 'informe', 'cual']
        if len(parts) < 3:
            raise ValueError("ID incompleto")
            
        tipo = parts[1]    # informe, proyecto, maestria
        enfoque = parts[2] # cual, cuant
        
        # Construimos la ruta al archivo JSON
        data_dir = get_data_dir() 
        filename = f"unac_{tipo}_{enfoque}.json"
        
        # Ruta construida: app/data/unac/proyecto/unac_proyecto_cuant.json
        json_path = data_dir / tipo / filename
        
        if not json_path.exists():
            raise FileNotFoundError(f"Archivo JSON no encontrado: {json_path}")

        return load_json_file(json_path)
        
    except Exception as e:
        print(f"[ERROR SERVICE] No se pudo leer JSON para {format_id}: {e}")
        raise