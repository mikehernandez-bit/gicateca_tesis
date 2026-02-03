"""
=============================================================================
ARCHIVO: app/core/settings.py
FASE: 2 - Backend View-Models
=============================================================================

PROPÓSITO:
Configuraciones globales de la aplicación leídas desde variables de entorno.
Este módulo centraliza la lectura de configuración para evitar hardcodes
dispersos en el código.

FUNCIÓN PRINCIPAL:
- get_default_uni_code() -> str
  Retorna el código de universidad por defecto.
  Lee: GICA_DEFAULT_UNI (env var)
  Fallback: "unac"

COMUNICACIÓN CON OTROS MÓDULOS:
- Es CONSUMIDO por:
  - app/modules/formats/router.py (endpoint /cover-model)
  - app/core/view_models.py (para fallbacks)
- NO depende de otros módulos del proyecto.

VARIABLES DE ENTORNO:
- GICA_DEFAULT_UNI: Código de universidad por defecto (ej: "unac", "uni")
  Si no está definida, usa "unac" como fallback.

EJEMPLO DE USO:
    from app.core.settings import get_default_uni_code
    default = get_default_uni_code()  # "unac" si no hay env var

=============================================================================
"""
import os
import logging

logger = logging.getLogger(__name__)

# Valor por defecto si no está definido GICA_DEFAULT_UNI
_FALLBACK_UNI = "unac"


def get_default_uni_code() -> str:
    """
    Retorna el código de universidad por defecto.
    Lee la variable de entorno GICA_DEFAULT_UNI.
    Si no está definida, retorna 'unac'.
    """
    value = os.getenv("GICA_DEFAULT_UNI", "").strip().lower()
    if value:
        return value
    return _FALLBACK_UNI
