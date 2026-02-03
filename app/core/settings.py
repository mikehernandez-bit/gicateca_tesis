"""
Archivo: app/core/settings.py
Propósito:
- Configuraciones globales de la aplicación leídas desde variables de entorno.

Responsabilidades:
- Proveer get_default_uni_code() para fallback cuando _meta.uni falta.
No hace:
- No contiene lógica de negocio, solo lectura de configuración.

Dependencias:
- os (stdlib)

Donde tocar si falla:
- Verificar que las variables de entorno estén definidas en el ambiente.
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
