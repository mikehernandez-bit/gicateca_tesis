"""
Archivo: app/core/paths.py
Proposito:
- Centraliza la resolucion de rutas base del proyecto.

Responsabilidades:
- Resolver rutas del app root, project root y data root.
- Proveer ubicaciones estandar para datos y exports.
No hace:
- No accede a archivos ni valida existencia.

Entradas/Salidas:
- Entradas: N/A (usa ubicacion del archivo actual).
- Salidas: Paths absolutos.

Dependencias:
- pathlib.Path.

Puntos de extension:
- Agregar nuevas rutas base si aparecen mas carpetas comunes.

Donde tocar si falla:
- Revisar calculo de parents si cambia la estructura del repo.
"""
from __future__ import annotations

from pathlib import Path


def get_app_root() -> Path:
    """Retorna la raiz de la carpeta app/."""
    return Path(__file__).resolve().parents[1]


def get_project_root() -> Path:
    """Retorna la raiz del proyecto."""
    return get_app_root().parent


def get_data_root() -> Path:
    """Retorna la raiz de app/data/."""
    return get_app_root() / "data"


def get_data_dir(code: str) -> Path:
    """Retorna la carpeta de datos para una universidad."""
    code = (code or "").strip().lower()
    return get_data_root() / code


def get_exports_dir() -> Path:
    """Retorna el directorio de exports/documentos."""
    return get_project_root() / "docs"
