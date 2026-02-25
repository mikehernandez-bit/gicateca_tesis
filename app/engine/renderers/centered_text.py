"""Renderer: centered_text — texto centrado con formato personalizado."""
from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.primitives import add_p_centered
from app.engine.types import Block


@register("centered_text")
def render_centered_text(doc: Document, block: Block) -> None:
    """Renderiza un párrafo centrado.

    Block keys:
        text (str): Texto a mostrar.
        bold (bool): Negrita. Default False.
        size (int): Tamaño en pt. Default 12.
        space_before (int): Espacio antes en pt. Default 0.
        space_after (int): Espacio después en pt. Default 0.
        italic (bool): Cursiva. Default False.
    """
    add_p_centered(
        doc,
        block.get("text", ""),
        bold=block.get("bold", False),
        size=block.get("size", 12),
        space_before=block.get("space_before", 0),
        space_after=block.get("space_after", 0),
        italic=block.get("italic", False),
    )
