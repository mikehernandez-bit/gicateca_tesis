"""
Archivo: app/modules/catalog/service.py
Proposito:
- Implementa la logica del catalogo y la generacion de documentos DOCX.

Responsabilidades:
- Construir el catalogo agrupado desde discovery.
- Resolver comandos de generador y ejecutar subprocess.
- Exponer helpers para obtener formatos y limpiar temporales.
No hace:
- No define rutas HTTP ni renderiza templates.

Entradas/Salidas:
- Entradas: ids de formato, tipo/subtipo y codigo de universidad.
- Salidas: estructuras de catalogo, rutas de archivos y excepciones controladas.

Dependencias:
- app.core.loaders, app.core.registry, subprocess, tempfile.

Puntos de extension:
- Ajustar etiquetas del catalogo o mapping de categorias.
- Integrar nuevos generadores por categoria.

Donde tocar si falla:
- Revisar resolucion de JSON y ejecucion de generadores.
"""

from pathlib import Path
import re
import unicodedata
from typing import Dict, List, Optional

from app.core.loaders import discover_format_files, load_format_by_id, load_json_file
from app.core.format_builder import (
    TIPO_LABELS,
    ENFOQUE_LABELS,
    TIPO_FILTRO,
    build_format_entry,
    build_format_title,
)
from app.core.document_generator import (
    generate_document_by_type,
    cleanup_temp_file,
)
_REFERENCE_KEYWORDS = {
    "references",
    "referencias",
    "bibliografia",
    "bibliografica",
    "bibliograficas",
}


def _normalize_text(value: str) -> str:
    """Normaliza texto para comparar keywords (sin tildes)."""
    text = (value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9_-]+", "", text)
    return text


def _is_reference_like(item, data: Dict) -> bool:
    """Detecta si un item corresponde a referencias (debe excluirse del catalogo)."""
    format_id = _normalize_text(getattr(item, "format_id", ""))
    categoria = _normalize_text(getattr(item, "categoria", ""))
    stem = _normalize_text(getattr(getattr(item, "path", None), "stem", ""))
    raw_title = ""
    if isinstance(data, dict):
        raw_title = data.get("titulo") or data.get("title") or ""
    title = _normalize_text(raw_title)

    if categoria in _REFERENCE_KEYWORDS:
        return True
    if stem in _REFERENCE_KEYWORDS:
        return True
    if any(keyword in format_id for keyword in _REFERENCE_KEYWORDS):
        return True
    if title in _REFERENCE_KEYWORDS:
        return True
    return False


# _build_format_title y _build_format_entry ahora viven en app.core.format_builder
# Se re-exportan por compatibilidad de imports existentes.
_build_format_title = build_format_title
_build_format_entry = build_format_entry


def build_catalog(uni: Optional[str] = None) -> Dict[str, Dict]:
    """Construye el catalogo agrupado por universidad/categoria/enfoque."""
    formatos: List[Dict] = []
    grouped: Dict[str, Dict] = {}

    for item in discover_format_files(uni):
        # Carga data asociada al item descubierto.
        try:
            data = item.data if item.data is not None else load_json_file(item.path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Warning: Could not load {item.path}: {exc}")
            continue
        if _is_reference_like(item, data):
            continue

        entry = _build_format_entry(item, data)
        formatos.append(entry)
        grouped.setdefault(item.uni, {}).setdefault(item.categoria, {}).setdefault(item.enfoque, []).append(entry)

    # Implement custom sorting for UNI
    if uni == "uni" or uni is None:
        PRIORITY = {"proyecto": 1, "informe": 2, "posgrado": 3, "maestria": 3}
        formatos.sort(key=lambda x: PRIORITY.get(x.get("tipo_formato", ""), 99))
    
    return {"formatos": formatos, "grouped": grouped}


def get_all_formatos() -> List[Dict]:
    """Retorna todos los formatos descubiertos bajo app/data."""
    return build_catalog(None)["formatos"]



# generate_document y cleanup_temp_file ahora viven en app.core.document_generator
# Se delegan para mantener compatibilidad con catalog/router.py
def generate_document(fmt_type: str, sub_type: str, uni: str = "unac"):
    """Genera un DOCX para un formato y retorna su ruta temporal."""
    return generate_document_by_type(fmt_type, sub_type, uni)

# NUEVA FUNCIÓN AGREGADA PARA LA VISTA PREVIA (CARÁTULAS)
def get_format_json_content(format_id: str) -> Dict:
    """
    Busca y devuelve el contenido crudo del JSON para las vistas previas.
    ID esperado: unac-informe-cual -> app/data/unac/informe/unac_informe_cual.json
    """
    # Reutiliza el loader central para obtener contenido legacy.
    try:
        return load_format_by_id(format_id)
    except Exception as e:
        print(f"[ERROR SERVICE] No se pudo leer JSON para {format_id}: {e}")
        raise
