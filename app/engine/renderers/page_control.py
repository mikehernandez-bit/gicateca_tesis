"""Renderers: page_break + section_break + section_switch + page_footer.

Agrupados porque todos controlan la estructura de páginas/secciones del documento.
"""
from __future__ import annotations

from docx.document import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from app.engine.registry import register
from app.engine.primitives import (
    add_fld_page,
    switch_to_landscape,
    switch_to_portrait,
)
from app.engine.types import Block


def _last_content_is_section_break(doc: Document) -> bool:
    """Verifica si el último elemento de contenido del body es un section-break paragraph.

    Cuando ``switch_to_portrait()`` (o ``switch_to_landscape()``) se ejecuta,
    python-docx crea un ``<w:p>`` cuyo ``<w:pPr>`` contiene un ``<w:sectPr>``.
    Ese section break ya inicia una nueva página (NEW_PAGE), por lo que un
    ``page_break`` inmediatamente después sería redundante y generaría una
    hoja en blanco.

    Retorna True si el último contenido del body (ignorando el ``<w:sectPr>``
    a nivel de body) es un section-break paragraph.
    """
    body = doc.element.body
    for child in reversed(list(body)):
        # Saltar el sectPr a nivel de body (propiedades de la última sección)
        if child.tag == qn("w:sectPr"):
            continue
        # ¿Es un párrafo con sectPr embebido? → section break
        if child.tag == qn("w:p"):
            p_pr = child.find(qn("w:pPr"))
            if p_pr is not None and p_pr.find(qn("w:sectPr")) is not None:
                return True
        return False
    return False


def _last_content_has_page_break(doc: Document) -> bool:
    """Verifica si el último contenido del body contiene un salto de página explícito."""
    body = doc.element.body
    for child in reversed(list(body)):
        if child.tag == qn("w:sectPr"):
            continue
        if child.tag == qn("w:p"):
            for br in child.findall(f".//{qn('w:br')}"):
                if br.get(qn("w:type")) == "page":
                    return True
        return False
    return False


@register("page_break")
def render_page_break(doc: Document, block: Block) -> None:
    """Inserta un salto de página.

    Si el último contenido del documento es un section-break paragraph
    (ej: después de ``switch_to_portrait`` al final de una tabla landscape),
    se omite el page_break porque el section break ya inició una nueva página.
    Esto evita hojas en blanco entre tablas landscape y el contenido siguiente.
    """
    force = bool(block.get("force", False))
    if _last_content_is_section_break(doc):
        return
    # Evita doble page break consecutivo (otra fuente típica de hoja en blanco).
    if not force and _last_content_has_page_break(doc):
        return
    doc.add_page_break()


@register("section_break")
def render_section_break(doc: Document, block: Block) -> None:
    """Inserta un salto de sección (nueva página)."""
    doc.add_section(WD_SECTION.NEW_PAGE)


@register("section_switch")
def render_section_switch(doc: Document, block: Block) -> None:
    """Cambia orientación de página (landscape/portrait).

    Block keys:
        orientation (str): "landscape" o "portrait".
    """
    orientation = block.get("orientation", "portrait")
    if orientation == "landscape":
        switch_to_landscape(doc)
    else:
        switch_to_portrait(doc)


@register("page_footer")
def render_page_footer(doc: Document, block: Block) -> None:
    """Inserta numeración de páginas en el footer de la última sección.

    Replica la lógica final de generate_document_unified():
    footer alineado a la derecha con campo PAGE.
    """
    section = doc.sections[-1]
    footer = section.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_fld_page(p)
