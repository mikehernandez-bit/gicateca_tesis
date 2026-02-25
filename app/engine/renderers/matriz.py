"""Renderer: matriz — Matriz de Consistencia como tabla landscape."""
from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.renderers.table import _render_tabla_impl
from app.engine.types import Block


@register("matriz")
def render_matriz(doc: Document, block: Block) -> None:
    """Renderiza la Matriz de Consistencia como tabla.

    Construye la tabla a partir de la estructura de matriz_consistencia
    y delega el rendering a _render_tabla_impl.

    Cuando landscape=False, el caller (section_switch) ya cambió la orientación,
    así que la tabla se renderiza como "portrait" (sin switch propio).

    Block keys:
        data (dict): Datos de matriz_consistencia con keys:
            problemas, objetivos, hipotesis, variables, metodologia.
        landscape (bool): Si True, la tabla maneja su propio landscape switch.
    """
    matriz_data = block.get("data", {})
    if not matriz_data:
        return

    landscape = block.get("landscape", True)

    # Helper
    def clean_text(val):
        if isinstance(val, list):
            return "\n".join(f"- {x}" for x in val)
        return str(val)

    prob = matriz_data.get("problemas", {})
    obj = matriz_data.get("objetivos", {})
    hip = matriz_data.get("hipotesis", {})
    var = matriz_data.get("variables", {})
    met = matriz_data.get("metodologia", {})

    # Variables text
    txt_var = ""
    if "independiente" in var:
        txt_var += f"V. Indep: {var['independiente'].get('nombre', '')}"
        dims = var["independiente"].get("dimensiones", [])
        if dims:
            txt_var += "\nDim: " + ", ".join(dims)
    if "dependiente" in var:
        txt_var += f"\n\nV. Dep: {var['dependiente'].get('nombre', '')}"
        dims = var["dependiente"].get("dimensiones", [])
        if dims:
            txt_var += "\nDim: " + ", ".join(dims)

    # Metodologia text
    txt_met = "\n".join(f"{k.capitalize()}: {v}" for k, v in met.items())

    filas = [
        [
            "General:\n" + clean_text(prob.get("general", "")),
            "General:\n" + clean_text(obj.get("general", "")),
            "General:\n" + clean_text(hip.get("general", "")),
            txt_var,
            txt_met,
        ],
        [
            "Específicos:\n" + clean_text(prob.get("especificos", [])),
            "Específicos:\n" + clean_text(obj.get("especificos", [])),
            "Específicos:\n" + clean_text(hip.get("especificos", [])),
            "",
            "",
        ],
    ]

    tabla_data = {
        "tipo": "tabla",
        "orientacion": "landscape" if landscape else "portrait",
        "encabezados": ["PROBLEMAS", "OBJETIVOS", "HIPÓTESIS", "VARIABLES", "METODOLOGÍA"],
        "filas": filas,
        "celdas_fusionadas": [
            {"fila": 0, "col": 3, "filas_span": 2},
            {"fila": 0, "col": 4, "filas_span": 2},
        ],
        "estilo": {
            "encabezado_color": "D9D9D9",
            "fuente_size": 9,
        },
    }

    # Render sin título SEQ — el heading del anexo ya fue emitido por el normalizer
    _render_tabla_impl(doc, tabla_data)
