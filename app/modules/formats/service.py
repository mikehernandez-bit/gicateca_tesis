"""
Archivo: app/modules/formats/service.py
Proposito:
- Implementa logica para obtener formatos y generar DOCX por format_id.

Responsabilidades:
- Construir el detalle de un formato desde el indice.
- Delegar la generacion DOCX a app.core.document_generator.
- Aplicar filtros temporales (ej. vista previa de planteamiento).
No hace:
- No define rutas HTTP ni renderiza templates.

Entradas/Salidas:
- Entradas: format_id, filtros opcionales.
- Salidas: dict de formato o rutas de archivos generados.

Dependencias:
- app.core.loaders, app.core.format_builder, app.core.document_generator.

Puntos de extension:
- Ajustar filtros de secciones o labels del catalogo.

Donde tocar si falla:
- Revisar find_format_index/load_json_file y core/document_generator.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple

from app.core.loaders import find_format_index, load_json_file, load_format_by_id
from app.core.format_builder import build_format_entry
from app.core.document_generator import (
    generate_document_by_id,
    cleanup_temp_file,
)


def get_formato(format_id: str) -> Optional[Dict]:
    """Retorna el detalle de un formato por ID."""
    item = find_format_index(format_id)
    if not item:
        raise ValueError(f"Format not found: {format_id}")

    # Carga JSON asociado al formato y construye salida.
    try:
        data = item.data if item.data is not None else load_json_file(item.path)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"Format not found: {format_id}") from exc

    return build_format_entry(item, data)


# generate_document delega a core/document_generator.py
def generate_document(
    format_id: str,
    section_filter: Optional[str] = None,
    override_json_path: Optional[Path] = None,
) -> Tuple[Path, str]:
    """
    Genera un DOCX para el formato indicado.
    Permite filtrar secciones o usar un JSON custom (override).
    """
    return generate_document_by_id(format_id, section_filter, override_json_path)


# NUEVA FUNCION AGREGADA PARA LA VISTA PREVIA (CARATULAS)
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
