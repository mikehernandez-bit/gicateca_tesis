"""
Archivo: app/core/university_registry.py
Proposito:
- Wrapper de compatibilidad para mantener imports antiguos de registry.

Responsabilidades:
- Re-exportar funciones de app.core.registry.
- Proveer fallback a "unac" cuando el codigo no existe.
No hace:
- No implementa discovery propio ni carga datos.

Entradas/Salidas:
- Entradas: codigo de universidad.
- Salidas: provider valido (con fallback).

Dependencias:
- app.core.registry.

Puntos de extension:
- Eliminar cuando no existan imports legacy.

Donde tocar si falla:
- Revisar mapeo de get_provider y manejo de KeyError.
"""

from app.core.registry import discover_providers, get_provider as _get_provider, list_universities

__all__ = ["discover_providers", "get_provider", "list_universities"]


def get_provider(code: str):
    """Wrapper con fallback a unac para compatibilidad legacy."""
    code = (code or "unac").strip().lower()
    try:
        return _get_provider(code)
    except KeyError:
        # Mantiene compatibilidad con clientes que piden un code desconocido.
        return _get_provider("unac")
