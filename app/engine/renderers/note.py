"""Renderer: note — caja azul de instrucciones/validación."""
from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.primitives import add_styled_note
from app.engine.types import Block


@register("note")
def render_note(doc: Document, block: Block) -> None:
    """Renderiza una nota en caja azul (F2F8FD con bordes 8DB3E2).

    Block keys:
        text (str): Contenido de la nota.
    """
    add_styled_note(doc, block.get("text", ""))
