"""Renderer: apa_examples — ejemplos APA 7 con hanging indent."""
from __future__ import annotations

from docx.document import Document
from docx.shared import Cm

from app.engine.registry import register
from app.engine.types import Block


@register("apa_examples")
def render_apa_examples(doc: Document, block: Block) -> None:
    """Renderiza una lista de ejemplos APA 7 con sangría francesa.

    Replica la lógica de render_cuerpo/render_finales para ejemplos_apa:
    1. "Ejemplos APA 7:" (bold)
    2. Cada ejemplo con left_indent=1.27cm, first_line_indent=-1.27cm

    Block keys:
        ejemplos (list[str]): Textos de ejemplo.
    """
    ejemplos = block.get("ejemplos", [])
    if not ejemplos:
        return

    doc.add_paragraph("Ejemplos APA 7:").runs[0].bold = True
    for ej in ejemplos:
        p = doc.add_paragraph(ej)
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
