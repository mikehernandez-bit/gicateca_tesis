"""
Archivo: app/universities/registry.py
Proposito:
- Wrapper de compatibilidad que re-exporta el registry core.

Responsabilidades:
- Mantener imports legacy sin duplicar logica.
No hace:
- No implementa discovery propio ni validaciones adicionales.

Entradas/Salidas:
- Entradas: N/A.
- Salidas: Funciones re-exportadas.

Dependencias:
- app.core.registry.

Puntos de extension:
- Eliminar cuando no existan imports legacy.

Donde tocar si falla:
- Revisar cambios en app.core.registry.
"""
from app.core.registry import discover_providers, get_provider, list_universities

__all__ = ["discover_providers", "get_provider", "list_universities"]
