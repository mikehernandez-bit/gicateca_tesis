"""Renderers: table + legacy_table.

Contiene la implementación completa de render_tabla que replica exactamente
la función original del universal_generator.py, incluyendo:
- Orientación landscape/portrait con switch automático de sección
- Títulos con campo SEQ para auto-numeración
- Encabezados con sombreado
- Fusión de celdas
- Notas de pie de tabla

La función _render_tabla_impl es reutilizada por el renderer de matriz.
"""
from __future__ import annotations

import re

from docx.document import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.engine.registry import register
from app.engine.primitives import (
    DEFAULT_HEADER_COLOR,
    DEFAULT_TABLE_FONT_SIZE,
    LANDSCAPE_FONT_SIZE,
    PORTRAIT_MARGINS,
    LANDSCAPE_MARGINS,
    add_seq_field,
    apply_cell_shading,
    format_cell_text,
    set_cell_vertical_alignment,
    switch_to_landscape,
    switch_to_portrait,
)
from app.engine.types import Block


# ─────────────────────────────────────────────────────────────
# IMPLEMENTACIÓN COMPARTIDA
# ─────────────────────────────────────────────────────────────

def _render_tabla_impl(doc: Document, tabla_data: dict) -> None:
    """Renderiza una tabla completa. Replica ``render_tabla()`` del generador.

    Esta función es el corazón del rendering de tablas y es reutilizada
    por el renderer de matriz y legacy_table.

    Parámetros del dict tabla_data:
        encabezados (list[str]): Fila de encabezados.
        filas (list[list[str]]): Filas de datos.
        orientacion (str): "portrait" | "landscape". Default "portrait".
        titulo (str): Caption con SEQ field.
        nota_pie (str): Nota al pie de la tabla.
        estilo (dict): Overrides de estilo.
        celdas_fusionadas (list[dict]): Merges.
    """
    if not tabla_data:
        return

    encabezados = tabla_data.get("encabezados", [])
    filas = tabla_data.get("filas", [])
    if not encabezados:
        return

    orientacion = (tabla_data.get("orientacion") or "portrait").strip().lower()
    is_landscape = orientacion == "landscape"
    titulo = tabla_data.get("titulo")
    nota_pie = tabla_data.get("nota_pie")
    estilo = tabla_data.get("estilo", {})

    header_color = estilo.get("encabezado_color", DEFAULT_HEADER_COLOR)
    font_size = estilo.get(
        "fuente_size",
        LANDSCAPE_FONT_SIZE if is_landscape else DEFAULT_TABLE_FONT_SIZE,
    )
    ancho_columnas = estilo.get("ancho_columnas")
    show_borders = estilo.get("bordes", True)
    merges = tabla_data.get("celdas_fusionadas", [])

    # 1. Switch to landscape if needed
    if is_landscape:
        switch_to_landscape(doc)

    # 2. Caption / Title with SEQ field
    if titulo:
        clean_title = re.sub(r"^Tabla\s*[\d.]+\s*[:.]*\s*", "", titulo).strip() or titulo
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        run_label = p.add_run("Tabla ")
        run_label.bold = True
        run_label.font.size = Pt(11)
        run_label.font.name = "Arial"
        add_seq_field(p, "Tabla")
        run_title = p.add_run(f". {clean_title}")
        run_title.bold = True
        run_title.font.size = Pt(11)
        run_title.font.name = "Arial"

    # 3. Create table
    num_cols = len(encabezados)
    num_rows = 1 + len(filas)
    table = doc.add_table(rows=num_rows, cols=num_cols)

    if show_borders:
        table.style = "Table Grid"
    table.autofit = False

    # 4. Column widths
    if ancho_columnas and len(ancho_columnas) == num_cols:
        for i, w in enumerate(ancho_columnas):
            table.columns[i].width = Cm(w)
    else:
        if is_landscape:
            available = 29.7 - LANDSCAPE_MARGINS["left"] - LANDSCAPE_MARGINS["right"]
        else:
            available = 21.0 - PORTRAIT_MARGINS["left"] - PORTRAIT_MARGINS["right"]
        col_width = available / num_cols
        for i in range(num_cols):
            table.columns[i].width = Cm(col_width)

    # 5. Headers
    for i, header_text in enumerate(encabezados):
        cell = table.rows[0].cells[i]
        format_cell_text(
            cell, header_text, font_size,
            bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
        )
        apply_cell_shading(cell, header_color)
        set_cell_vertical_alignment(cell)

    # 6. Data rows
    for row_idx, fila in enumerate(filas):
        for col_idx, cell_text in enumerate(fila):
            if col_idx >= num_cols:
                break
            cell = table.rows[row_idx + 1].cells[col_idx]
            format_cell_text(cell, cell_text or "", font_size)
            set_cell_vertical_alignment(cell)

    # 7. Cell merges
    for merge in merges:
        start_row = merge.get("fila", 0) + 1  # +1 header
        start_col = merge.get("col", 0)
        row_span = merge.get("filas_span", 1)
        col_span = merge.get("cols_span", 1)

        if start_row < num_rows and start_col < num_cols:
            end_row = min(start_row + row_span - 1, num_rows - 1)
            end_col = min(start_col + col_span - 1, num_cols - 1)
            start_cell = table.cell(start_row, start_col)
            end_cell = table.cell(end_row, end_col)
            start_cell.merge(end_cell)

    # 8. Footer note
    if nota_pie:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(nota_pie)
        run.italic = True
        run.font.size = Pt(9)
        run.font.name = "Arial"

    # 9. Restore portrait
    if is_landscape:
        switch_to_portrait(doc)


# ─────────────────────────────────────────────────────────────
# RENDERERS REGISTRADOS
# ─────────────────────────────────────────────────────────────

@register("table")
def render_table(doc: Document, block: Block) -> None:
    """Renderiza una tabla canónica (tipo: 'tabla') completa.

    Block keys (heredados del JSON):
        encabezados, filas, orientacion, titulo, nota_pie,
        estilo, celdas_fusionadas.
    """
    _render_tabla_impl(doc, block)


@register("legacy_table")
def render_legacy_table(doc: Document, block: Block) -> None:
    """Renderiza una tabla legacy (headers/rows) convirtiéndola al formato estándar.

    Block keys:
        tabla (dict): {"headers": [...], "rows": [...]}.
        titulo (str): Título de la tabla.
        nota (str): Nota al pie.
    """
    tabla = block.get("tabla", {})
    headers = tabla.get("headers", [])
    rows = tabla.get("rows", [])
    if not headers and not rows:
        return

    tabla_data = {
        "tipo": "tabla",
        "titulo": block.get("titulo") or tabla.get("titulo", ""),
        "orientacion": "landscape" if len(headers) > 5 else "portrait",
        "encabezados": headers,
        "filas": rows,
    }
    nota = block.get("nota")
    if nota:
        tabla_data["nota_pie"] = nota

    _render_tabla_impl(doc, tabla_data)
