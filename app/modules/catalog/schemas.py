"""
Archivo: app/modules/catalog/schemas.py
Proposito:
- Define modelos Pydantic para entradas y salidas del catalogo.

Responsabilidades:
- Tipar payloads del frontend y respuestas del API.
No hace:
- No contiene logica de negocio.

Entradas/Salidas:
- Entradas: payloads JSON para generar documentos.
- Salidas: modelos de formato y respuesta de generacion.

Dependencias:
- pydantic.BaseModel, typing.

Puntos de extension:
- Agregar campos o nuevos modelos segun evolucione el API.

Donde tocar si falla:
- Revisar validaciones de Pydantic y campos esperados por el frontend.
"""

from typing import List, Optional
from pydantic import BaseModel


class FormatoOut(BaseModel):
    """Modelo de formato para respuestas del catalogo."""
    id: Optional[str] = None
    uni: Optional[str] = None
    titulo: Optional[str] = None
    facultad: Optional[str] = None
    escuela: Optional[str] = None
    estado: Optional[str] = None
    version: Optional[str] = None
    fecha: Optional[str] = None
    resumen: Optional[str] = None
    archivos: Optional[List[dict]] = None
    historial: Optional[List[dict]] = None


class FormatoGenerateIn(BaseModel):
    """Modelo de entrada para la generacion de documentos."""
    format: str
    sub_type: str
    uni: Optional[str] = None


class FormatoGenerateOut(BaseModel):
    """Modelo de respuesta para la generacion de documentos."""
    ok: bool
    filename: str
    path: str
