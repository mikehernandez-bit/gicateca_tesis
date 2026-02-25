"""Renderers: paragraph + paragraph_centered."""
from __future__ import annotations

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.engine.registry import register
from app.engine.types import Block


@register("paragraph")
def render_paragraph(doc: Document, block: Block) -> None:
    """Renderiza un párrafo justificado normal.

    Block keys:
        text (str): Texto del párrafo.
    """
    doc.add_paragraph(block.get("text", ""))


@register("paragraph_centered")
def render_paragraph_centered(doc: Document, block: Block) -> None:
    """Renderiza un párrafo centrado con formato opcional.

    Block keys:
        text (str): Texto del párrafo.
        bold (bool): Negrita. Default False.
        size (int): Tamaño en pt. Default None (hereda estilo Normal).
        space_before (int): Espacio antes en pt. Default 0.
        space_after (int): Espacio después en pt. Default 0.
    """
    from docx.shared import Pt

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    space_before = block.get("space_before", 0)
    space_after = block.get("space_after", 0)
    if space_before:
        p.paragraph_format.space_before = Pt(space_before)
    if space_after:
        p.paragraph_format.space_after = Pt(space_after)

    run = p.add_run(block.get("text", ""))
    if block.get("bold"):
        run.bold = True
    if block.get("size"):
        run.font.size = Pt(block["size"])
    run.font.name = "Arial"
