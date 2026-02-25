"""Renderers: heading + black_heading."""
from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.primitives import add_heading_formal, add_black_heading
from app.engine.types import Block


@register("heading")
def render_heading(doc: Document, block: Block) -> None:
    """Renderiza un encabezado formal (Heading 1/2).

    Block keys:
        text (str): Texto del encabezado.
        level (int): Nivel (1 o 2). Default 1.
        centered (bool): Centrado. Default False.
        space_before (int): Espacio antes en pt. Default 12.
        space_after (int): Espacio después en pt. Default 12.
    """
    add_heading_formal(
        doc,
        block.get("text", ""),
        level=block.get("level", 1),
        space_before=block.get("space_before", 12),
        space_after=block.get("space_after", 12),
        centered=block.get("centered", False),
    )


@register("black_heading")
def render_black_heading(doc: Document, block: Block) -> None:
    """Renderiza un subtítulo con fuente Arial negra.

    Block keys:
        text (str): Texto del subtítulo.
        level (int): Nivel. Default 2.
        size (int): Tamaño en pt. Default 13.
        centered (bool): Centrado. Default True.
    """
    add_black_heading(
        doc,
        block.get("text", ""),
        level=block.get("level", 2),
        size=block.get("size", 13),
        centered=block.get("centered", True),
    )
