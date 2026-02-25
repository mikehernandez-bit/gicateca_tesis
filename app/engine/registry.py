"""
Archivo: app/engine/registry.py
Proposito:
- Registry central de renderers con patron decorador @register('tipo').

Responsabilidades:
- Almacenar la relacion tipo → renderer.
- Despachar blocks al renderer correcto via render_block().
- Proveer render_blocks() para procesar listas completas.
No hace:
- No implementa renderers concretos (eso va en renderers/).
- No normaliza JSON (eso va en normalizer.py).

Entradas/Salidas:
- Entradas: block dicts con campo "type".
- Salidas: documento python-docx modificado in-place.

Dependencias:
- app.engine.types.

Puntos de extension:
- Agregar middleware pre/post rendering.
- Agregar validación de blocks antes de despachar.

Donde tocar si falla:
- Verificar que el tipo del block coincide con un renderer registrado.
- Verificar que renderers/__init__.py importa todos los módulos.
"""
from __future__ import annotations

import logging
from typing import Callable, Dict, List

from docx.document import Document

from app.engine.types import Block, BlockRenderer

logger = logging.getLogger(__name__)

# Mapa interno: tipo de block → función renderer.
_RENDERERS: Dict[str, BlockRenderer] = {}


def register(block_type: str) -> Callable[[BlockRenderer], BlockRenderer]:
    """Decorador para registrar un renderer de bloque.

    Uso::

        from app.engine.registry import register

        @register("heading")
        def render_heading(doc: Document, block: Block) -> None:
            ...

    Lanza ValueError si el tipo ya está registrado (previene duplicados).
    """
    if not isinstance(block_type, str) or not block_type.strip():
        raise ValueError("block_type debe ser un string no vacío")

    def decorator(fn: BlockRenderer) -> BlockRenderer:
        if block_type in _RENDERERS:
            raise ValueError(
                f"Renderer duplicado para tipo '{block_type}': "
                f"ya registrado como {_RENDERERS[block_type].__name__}"
            )
        _RENDERERS[block_type] = fn
        logger.debug("Registered renderer for '%s': %s", block_type, fn.__name__)
        return fn

    return decorator


def render_block(doc: Document, block: Block) -> None:
    """Despacha un Block al renderer correspondiente.

    Si el tipo no tiene renderer registrado, emite warning y continúa
    (no lanza excepción para no interrumpir la generación del documento).
    """
    if not isinstance(block, dict):
        logger.warning("Block inválido (no es dict): %s", type(block))
        return

    block_type = block.get("type", "")
    if not block_type:
        logger.warning("Block sin campo 'type': %s", block)
        return

    renderer = _RENDERERS.get(block_type)
    if renderer is None:
        logger.warning("No hay renderer registrado para tipo '%s'", block_type)
        return

    renderer(doc, block)


def render_blocks(doc: Document, blocks: List[Block]) -> None:
    """Renderiza una lista de Blocks en orden secuencial.

    Cada block se despacha individualmente a su renderer.
    Si un renderer falla, logea el error y continúa con el siguiente.
    """
    for i, block in enumerate(blocks):
        try:
            render_block(doc, block)
        except Exception:
            block_type = block.get("type", "???") if isinstance(block, dict) else "???"
            logger.exception(
                "Error renderizando block #%d (tipo='%s')", i, block_type
            )


def list_registered() -> List[str]:
    """Lista los tipos de block registrados (para debugging y tests)."""
    return sorted(_RENDERERS.keys())


def is_registered(block_type: str) -> bool:
    """Verifica si un tipo de block tiene renderer registrado."""
    return block_type in _RENDERERS


def _clear_registry() -> None:
    """Limpia el registry. SOLO para tests."""
    _RENDERERS.clear()
