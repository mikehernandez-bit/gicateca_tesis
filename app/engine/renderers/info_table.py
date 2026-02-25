"""Renderer: info_table — tabla de información básica (label/valor)."""
from __future__ import annotations

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from app.engine.registry import register
from app.engine.primitives import format_cell_text
from app.engine.types import Block


@register("info_table")
def render_info_table(doc: Document, block: Block) -> None:
    """Renderiza una tabla de 2 columnas con label:valor.

    Replica render_informacion_basica() del generador (solo la parte de tabla).

    Block keys:
        elementos (list[dict]): Lista de {"label": str, "valor": str}.
    """
    elementos = block.get("elementos", [])
    if not elementos:
        return

    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(5.0)
    table.columns[1].width = Cm(11.0)

    for item in elementos:
        row = table.add_row()
        # Label (bold)
        format_cell_text(
            row.cells[0],
            item.get("label", ""),
            font_size=10,
            bold=True,
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
        )
        # Valor
        format_cell_text(
            row.cells[1],
            item.get("valor", ""),
            font_size=10,
            bold=False,
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
        )
