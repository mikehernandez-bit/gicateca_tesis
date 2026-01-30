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
import subprocess
import sys
import tempfile
import unicodedata
from typing import Dict, List, Optional, Sequence, Tuple, Union

from app.core.loaders import discover_format_files, load_format_by_id, load_json_file
from app.core.registry import get_provider

ALIASES = {
    "pregrado": "informe",
}


TIPO_LABELS = {
    "informe": "Informe de Tesis",
    "maestria": "Tesis de Maestr\u00eda",
    "posgrado": "Posgrado",
    "proyecto": "Proyecto de Tesis",
}
ENFOQUE_LABELS = {"cual": "Cualitativo", "cuant": "Cuantitativo"}
TIPO_FILTRO = {
    "informe": "Inv. Formativa",
    "maestria": "Suficiencia",
    "posgrado": "Suficiencia",
    "proyecto": "Tesis",
}
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


def _build_format_title(categoria: str, enfoque: str, raw_title: str, fallback_title: str) -> str:
    """Calcula el titulo visible de un formato."""
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
    """Construye el dict que alimenta el catalogo UI."""
    raw_title = data.get("titulo") if isinstance(data, dict) else None
    titulo = _build_format_title(item.categoria, item.enfoque, raw_title, item.titulo)
    cat_label = TIPO_LABELS.get(item.categoria, item.categoria.capitalize())
    enfoque_label = ENFOQUE_LABELS.get(item.enfoque)
    resumen = None
    if isinstance(data, dict):
        resumen = data.get("descripcion")
    caratula = data.get("caratula", {}) if isinstance(data, dict) else {}
    facultad = None
    escuela = None
    if isinstance(data, dict):
        facultad = data.get("facultad")
        escuela = data.get("escuela")
    if not facultad and isinstance(caratula, dict):
        facultad = caratula.get("facultad")
        escuela = escuela or caratula.get("escuela")
    # Forzar leyenda uniforme y escalable por universidad.
    if item.uni:
        facultad = f"Centro de Formatos {item.uni.upper()}"
    if not facultad:
        facultad = "Centro de Formatos"
    if not escuela:
        escuela = "Dirección Académica"
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
        "facultad": facultad,
        "escuela": escuela,
        "estado": "VIGENTE",
        "version": data.get("version", "1.0.0") if isinstance(data, dict) else "1.0.0",
        "fecha": (data.get("fecha") if isinstance(data, dict) and data.get("fecha") else "2026-01-17"),
        "resumen": resumen,
        "tipo_formato": item.categoria,
        "enfoque": item.enfoque,
    }


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



def _normalize_format(fmt_type: str) -> str:
    """Normaliza el tipo de formato (alias -> canonical)."""
    fmt_type = (fmt_type or "").strip().lower()
    if fmt_type in ALIASES:
        fmt_type = ALIASES[fmt_type]
    return fmt_type


def _resolve_generator_command(
    generator: Union[Path, Sequence[str]],
    json_path: Path,
    output_path: Path,
) -> Tuple[List[str], Optional[Path]]:
    """Resuelve el comando de generador y el directorio de trabajo."""
    if isinstance(generator, (list, tuple)):
        cmd = [str(part) for part in generator]
        workdir = None
        for part in reversed(generator):
            part_str = str(part)
            if part_str.endswith(".py"):
                workdir = Path(part_str).resolve().parent
                break
        return cmd + [str(json_path), str(output_path)], workdir

    script_path = Path(generator)
    if not script_path.exists():
        raise RuntimeError(f"Script no encontrado: {script_path}")
    return [sys.executable, str(script_path), str(json_path), str(output_path)], script_path.parent


def cleanup_temp_file(path: Path) -> None:
    """Elimina un archivo temporal si existe."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"[WARN] No se pudo eliminar temporal: {exc}")


def generate_document(fmt_type: str, sub_type: str, uni: str = "unac"):
    """Genera un DOCX para un formato y retorna su ruta temporal."""
    fmt_type = _normalize_format(fmt_type)
    sub_type = (sub_type or "").strip().lower()
    provider = get_provider(uni)
    generator = provider.get_generator_command(fmt_type)

    # Resuelve el JSON del formato dentro de app/data/<uni>/<categoria>/.
    json_path = provider.get_data_dir() / fmt_type / f"{provider.code}_{fmt_type}_{sub_type}.json"
    if not json_path.exists():
        raise RuntimeError(f"JSON no encontrado: {json_path}")

    filename = f"{provider.code.upper()}_{fmt_type.upper()}_{sub_type.upper()}.docx"
    tmp_file = tempfile.NamedTemporaryFile(prefix=f"{provider.code}_", suffix=".docx", delete=False)
    output_path = Path(tmp_file.name)
    tmp_file.close()

    # Ejecuta el script generador sin modificar su logica interna.
    cmd, workdir = _resolve_generator_command(generator, json_path, output_path)
    result = subprocess.run(cmd, cwd=str(workdir) if workdir else None, capture_output=True, text=True)

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
    # Reutiliza el loader central para obtener contenido legacy.
    try:
        return load_format_by_id(format_id)
    except Exception as e:
        print(f"[ERROR SERVICE] No se pudo leer JSON para {format_id}: {e}")
        raise
