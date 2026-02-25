"""
Archivo: app/engine/types.py
Proposito:
- Define los tipos fundamentales del Block Engine.

Responsabilidades:
- Declarar Block como alias tipado.
- Declarar el protocolo BlockRenderer que todo renderer debe cumplir.
No hace:
- No contiene logica de rendering ni normalización.

Entradas/Salidas:
- Entradas: N/A (solo definiciones de tipos).
- Salidas: Block, BlockRenderer disponibles para importar.

Dependencias:
- typing, Protocol.

Puntos de extension:
- Agregar campos obligatorios al Block si se necesita validación.

Donde tocar si falla:
- Verificar que BlockRenderer coincide con la firma de los renderers.
"""
from __future__ import annotations

from typing import Any, Dict, Protocol

from docx.document import Document


# Un Block es un diccionario con "type" obligatorio y datos arbitrarios.
# Ejemplo: {"type": "heading", "text": "CAPÍTULO I", "level": 1}
Block = Dict[str, Any]


class BlockRenderer(Protocol):
    """Protocolo que todo renderer de bloque debe cumplir.

    Recibe el documento python-docx y un Block dict.
    Modifica el documento in-place; no retorna nada.
    """

    def __call__(self, doc: Document, block: Block) -> None: ...
