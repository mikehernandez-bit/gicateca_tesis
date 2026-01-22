"""Service layer for formats module."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from app.core.loaders import find_format_index, load_json_file


ROOT = Path(__file__).resolve().parents[3]
CF_DIR = ROOT / "app" / "universities" / "unac" / "centro_formatos"

SCRIPTS_CONFIG = {
    "proyecto": "generador_proyecto_tesis.py",
    "informe": "generador_informe_tesis.py",
    "maestria": "generador_maestria.py",
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


def get_formato(format_id: str) -> Optional[Dict]:
    """
    Get a specific format by ID.
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Format not found: {format_id}")

    try:
        data = load_json_file(item.path)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Format not found: {format_id}") from exc

    return _build_format_entry(item, data)


def generate_document(format_id: str, section_filter: Optional[str] = None) -> Tuple[Path, str]:
    """
    Generate a DOCX document for the given format.
    Allows filtering by section.
    """
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Invalid format ID: {format_id}")

    tipo = item.categoria
    enfoque = item.enfoque

    if tipo not in SCRIPTS_CONFIG:
        raise ValueError(f"Unknown format type: {tipo}")

    script_name = SCRIPTS_CONFIG[tipo]
    script_path = CF_DIR / script_name

    if not script_path.exists():
        raise RuntimeError(f"Generator script not found: {script_path}")

    json_path = item.path

    if not json_path.exists():
        raise RuntimeError(f"JSON file not found: {json_path}")

    # =========================================================
    # LOGICA DE FILTRADO (SIMPLIFICADA Y AGRESIVA)
    # =========================================================
    path_to_use = json_path

    if section_filter == "planteamiento":
        print(f"[DEBUG] Filtrando SOLO CAP\u00cdTULO I para: {format_id}")

        # 1. Cargamos el JSON original
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 2. LIMPIEZA TOTAL: Vaciamos todo lo que no sea el cuerpo
        data["preliminares"] = {}
        data["finales"] = {}
        data["matriz_consistencia"] = {}

        if "caratula" in data:
            data["caratula"]["tipo_documento"] = "VISTA PREVIA - CAP\u00cdTULO I"

        # 3. FILTRO RAPIDO: Nos quedamos SOLO con el bloque que tenga "PLANTEAMIENTO"
        # Esto elimina cualquier otro capitulo de la lista.
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

    # Debug logs (util si falla)
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
