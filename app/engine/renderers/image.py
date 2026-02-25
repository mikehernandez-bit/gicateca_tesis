"""Renderer: image — figuras con caption SEQ-numbered y fuente."""
from __future__ import annotations

import logging
import re

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.engine.registry import register
from app.engine.primitives import resolve_asset, add_seq_field
from app.engine.types import Block

logger = logging.getLogger(__name__)

# Regex defensivas para limpiar títulos de figuras
_RE_CHAPTER_SUFFIX = re.compile(r"\s*[–—-]\s*[IVXLC]+\.\s*.+$")
_RE_FIGURA_PREFIX = re.compile(r"^Figura\s*[\d.]+\s*[:.]*\s*")


def _clean_figure_title(titulo: str) -> str:
    """Remove redundant prefixes and chapter-name suffixes from figure titles."""
    titulo = _RE_FIGURA_PREFIX.sub("", titulo)
    titulo = _RE_CHAPTER_SUFFIX.sub("", titulo)
    return titulo.strip()


@register("image")
def render_image(doc: Document, block: Block) -> None:
    """Renderiza una imagen con caption numerada y fuente opcional.

    Replica _render_image() del generador:
    1. Caption: "Figura SEQ. {titulo}" (cursiva, centrada)
    2. Imagen centrada (12 cm ancho)
    3. "Fuente: ..." (cursiva, 9pt, centrada)

    Block keys:
        titulo (str): Título de la figura.
        ruta (str): Ruta del archivo de imagen.
        fuente (str): Fuente de la imagen.
    """
    ruta = block.get("ruta", "")
    titulo = _clean_figure_title(block.get("titulo", ""))

    # Omit placeholders or missing files: never inject fake "example" figures.
    if not ruta or ruta.lower() == "placeholder":
        return
    path = resolve_asset(ruta)
    if not path:
        return

    try:
        # Caption with SEQ field
        if titulo:
            pc = doc.add_paragraph()
            pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pc.paragraph_format.space_after = Pt(4)
            rl = pc.add_run("Figura ")
            rl.italic = True
            rl.font.size = Pt(10)
            add_seq_field(pc, "Figura")
            rt = pc.add_run(f". {titulo}")
            rt.italic = True
            rt.font.size = Pt(10)

        # Image
        pi = doc.add_paragraph()
        pi.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pi.add_run().add_picture(path, width=Cm(12.0))

        # Source
        if block.get("fuente"):
            ps = doc.add_paragraph(f"Fuente: {block['fuente']}")
            ps.runs[0].italic = True
            ps.runs[0].font.size = Pt(9)
            ps.alignment = WD_ALIGN_PARAGRAPH.CENTER
    except Exception as e:
        logger.warning("Image %s: %s", ruta, e)
