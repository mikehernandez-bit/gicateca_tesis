"""Renderers: toc_field + index_items.

Agrupados porque ambos generan índices/listas de contenido del documento.
"""
from __future__ import annotations

from docx.document import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.engine.registry import register
from app.engine.primitives import add_toc_field, add_heading_formal
from app.engine.types import Block


@register("toc_field")
def render_toc_field(doc: Document, block: Block) -> None:
    """Renderiza un campo TOC de Word (índice auto-actualizable).

    Inserta: heading + campo Word + placeholder + page_break.

    Block keys:
        field_code (str): Código del campo Word (ej: ' TOC \\o "1-3" ').
        heading_text (str): Título del índice.
    """
    add_toc_field(
        doc,
        block.get("field_code", ""),
        block.get("heading_text", ""),
        exclude_from_toc=block.get("exclude_from_toc", False),
    )


@register("index_items")
def render_index_items(doc: Document, block: Block) -> None:
    """Renderiza una lista de índice estática con tab stops y puntos.

    Usado para índices que NO son TOC de Word (abreviaturas, etc.).
    Replica la lógica de render_preliminares para indices tipo list con items.

    Block keys:
        items (list[dict]): Lista de {"texto": str, "pag": str|int, "bold": bool}.
    """
    for item in block.get("items", []):
        p = doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS,
        )
        run = p.add_run(item.get("texto", ""))
        if item.get("bold"):
            run.bold = True
        p.add_run(f"\t{item.get('pag', '')}")


def _set_abbr_cell_text(cell, text: str, *, bold: bool = False) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(10)


@register("abbreviations_table")
def render_abbreviations_table(doc: Document, block: Block) -> None:
    """Renderiza abreviaturas como tabla de 2 columnas (SIGLA | SIGNIFICADO)."""
    rows = block.get("rows", []) or []

    if not rows:
        note = doc.add_paragraph("(Completar abreviaturas)")
        note.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = note.runs[0] if note.runs else note.add_run("(Completar abreviaturas)")
        run.italic = True
        run.font.name = "Arial"
        run.font.size = Pt(10)
        return

    table = doc.add_table(rows=1 + len(rows), cols=2)
    table.style = "Table Grid"
    table.autofit = False
    table.columns[0].width = Cm(4.0)   # ~25%
    table.columns[1].width = Cm(12.0)  # ~75%

    _set_abbr_cell_text(table.cell(0, 0), "SIGLA", bold=True)
    _set_abbr_cell_text(table.cell(0, 1), "SIGNIFICADO", bold=True)

    for index, row in enumerate(rows, start=1):
        sigla = str(row.get("sigla", "")).strip()
        meaning = str(row.get("meaning", "")).strip()
        _set_abbr_cell_text(table.cell(index, 0), sigla)
        _set_abbr_cell_text(table.cell(index, 1), meaning)
