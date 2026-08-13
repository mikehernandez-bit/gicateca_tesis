"""Renderers: heading + black_heading."""

from __future__ import annotations

from docx.document import Document

from app.engine.render_state import register_heading
from app.engine.registry import register
from app.engine.primitives import add_heading_formal, add_black_heading
from app.engine.types import Block


from docx.shared import Pt


@register("heading")
def render_heading(doc: Document, block: Block) -> None:
    """Renderiza un encabezado formal (Heading 1/2).

    Block keys:
        text (str): Texto del encabezado.
        level (int): Nivel (1 o 2). Default 1.
        centered (bool): Centrado. Default False.
        space_before (int): Espacio antes en pt. Default 12.
        space_after (int): Espacio después en pt. Default 12.
        page_break_before (bool): Salto de página previo en párrafo. Default False.
    """
    page_break_before = bool(block.get("page_break_before", False))
    if page_break_before:
        from app.engine.renderers.page_control import _last_empty_trailing_paragraph
        trailing = _last_empty_trailing_paragraph(doc)
        if trailing is not None:
            trailing.paragraph_format.space_before = Pt(0)
            trailing.paragraph_format.space_after = Pt(0)
            trailing.paragraph_format.line_spacing = Pt(1)
            for r in trailing.runs:
                r.font.size = Pt(1)

    add_heading_formal(
        doc,
        block.get("text", ""),
        level=block.get("level", 1),
        space_before=block.get("space_before", 12),
        space_after=block.get("space_after", 12),
        centered=block.get("centered", False),
        page_break_before=page_break_before,
    )
    register_heading(
        str(block.get("text") or ""),
        level=int(block.get("level", 1) or 1),
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
    register_heading(
        str(block.get("text") or ""),
        level=int(block.get("level", 2) or 2),
    )
