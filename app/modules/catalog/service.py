"""Service layer for catalog module."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
from typing import Dict, List

from app.core.loaders import discover_format_files, load_format_by_id, load_json_file, get_data_dir

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


TIPO_LABELS = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestr\u00eda",
    "proyecto": "Proyecto de Tesis",
}
ENFOQUE_LABELS = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
TIPO_FILTRO = {
    "informe": "Inv. Formativa",
    "maestria": "Suficiencia",
    "proyecto": "Tesis",
}


def _build_format_title(categoria: str, enfoque: str, raw_title: str, fallback_title: str) -> str:
    if raw_title:
        return raw_title
    cat_label = TIPO_LABELS.get(categoria)
    enfoque_label = ENFOQUE_LABELS.get(enfoque)
    if cat_label and enfoque_label:
        return f"{cat_label} - {enfoque_label}"
    if cat_label:
        return cat_label
    return fallback_title or categoria.capitalize()


def _build_format_entry(item, data: Dict) -> Dict:
    raw_title = data.get("titulo") if isinstance(data, dict) else None
    titulo = _build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)
    cat_label = TIPO_LABELS.get(item.categoria, item.categoria.capitalize())
    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    if not resumen:
        if enfoque_label:
            resumen = f"Plantilla oficial de {cat_label} con enfoque {enfoque_label}"
        else:
            resumen = f"Plantilla oficial de {cat_label}"

    return {
        "id": item.format_id,
        "uni": item.uni.upper(),
        "uni_code": item.uni,
        "tipo": TIPO_FILTRO.get(item.categoria, "Otros"),
        "titulo": titulo,
        "facultad": "Centro de Formatos UNAC",
        "escuela": "Direcci\u00f3n Acad\u00e9mica",
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": "2026-01-17",
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": item.enfoque,
    }


def build_catalog(uni: str = "unac") -> Dict[str, Dict]:
    formatos: List[Dict] = []
    grouped: Dict[str, Dict] = {}

    for item in discover_format_files(uni):
        try:
            data = load_json_file(item.path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Warning: Could not load {item.path}: {exc}")
            continue

        entry = _build_format_entry(item, data)
        formatos.append(entry)
        grouped.setdefault(item.uni, {}).setdefault(item.categoria, {}).setdefault(item.enfoque, []).append(entry)

    return {"formatos": formatos, "grouped": grouped}


def get_all_formatos() -> List[Dict]:
    """Get all formats discovered under app/data."""
    return build_catalog()["formatos"]



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
    ID esperado: unac-informe-cual -> app/data/unac/informe/unac_informe_cual.json
    """
    try:
        return load_format_by_id(format_id)
    except Exception as e:
        print(f"[ERROR SERVICE] No se pudo leer JSON para {format_id}: {e}")
        raise
