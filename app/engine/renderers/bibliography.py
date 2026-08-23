"""Renderer for Microsoft Word's native bibliography field."""

from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.types import Block
from app.engine.word_bibliography import add_bibliography_field


@register("bibliography")
def render_bibliography(doc: Document, block: Block) -> None:
    """Insert one native BIBLIOGRAPHY field for the document's cited sources."""
    paragraph = doc.add_paragraph()
    add_bibliography_field(paragraph, block.get("word_sources") or [])
