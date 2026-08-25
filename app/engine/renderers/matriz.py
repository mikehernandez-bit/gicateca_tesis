"""Renderer: matriz - Matriz de Consistencia como tabla academica."""

from __future__ import annotations

from docx.document import Document

from app.engine.registry import register
from app.engine.renderers.table import _render_tabla_impl
from app.engine.types import Block


def _clean_text(value) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value if str(item).strip())
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if item in (None, "", []):
                continue
            lines.append(f"{str(key).replace('_', ' ').capitalize()}: {item}")
        return "\n".join(lines)
    return str(value or "")


def _build_variables_block(var: dict) -> str:
    if not isinstance(var, dict):
        return _clean_text(var)
    lines: list[str] = []
    indep = var.get("independiente", {}) if isinstance(var.get("independiente"), dict) else {}
    dep = var.get("dependiente", {}) if isinstance(var.get("dependiente"), dict) else {}

    if indep:
        lines.append("VARIABLE INDEPENDIENTE")
        if indep.get("nombre"):
            lines.append(str(indep.get("nombre")))
        dims = indep.get("dimensiones", [])
        if dims:
            lines.append("")
            lines.append("Dimensiones")
            lines.extend(str(d) for d in dims if str(d).strip())

    if dep:
        if lines:
            lines.append("")
        lines.append("VARIABLE DEPENDIENTE")
        if dep.get("nombre"):
            lines.append(str(dep.get("nombre")))
        dims = dep.get("dimensiones", [])
        if dims:
            lines.append("")
            lines.append("Dimensiones")
            lines.extend(str(d) for d in dims if str(d).strip())

    return "\n".join(lines).strip()


def _build_metodologia_block(met: dict) -> str:
    if not isinstance(met, dict):
        return _clean_text(met)

    ordered_keys = [
        "tipo",
        "nivel",
        "enfoque",
        "diseno",
        "diseño",
        "poblacion",
        "población",
        "muestra",
        "tecnicas",
        "técnicas",
        "instrumentos",
        "procesamiento_datos",
        "procesamiento",
    ]

    lines: list[str] = []
    used: set[str] = set()

    for key in ordered_keys:
        if key not in met or key in used:
            continue
        used.add(key)
        value = met.get(key)
        if value in (None, "", []):
            continue
        label = key.replace("_", " ").capitalize() + ":"
        lines.append(label)
        lines.append(_clean_text(value))

    for key, value in met.items():
        if key in used or value in (None, "", []):
            continue
        label = str(key).replace("_", " ").capitalize() + ":"
        lines.append(label)
        lines.append(_clean_text(value))

    return "\n".join(lines).strip()


@register("matriz")
def render_matriz(doc: Document, block: Block) -> None:
    """Renderiza la Matriz de Consistencia con 5 columnas y fusiones."""
    matriz_data = block.get("data", {})
    if not matriz_data:
        return

    landscape = block.get("landscape", True)
    prob = matriz_data.get("problemas", {})
    obj = matriz_data.get("objetivos", {})
    hip = matriz_data.get("hipotesis", {})
    var = matriz_data.get("variables", {})
    met = matriz_data.get("metodologia", {})
    titulo_investigacion = (
        matriz_data.get("titulo_investigacion")
        or matriz_data.get("titulo")
        or matriz_data.get("research_title")
        or "MATRIZ DE CONSISTENCIA"
    )

    problemas_especificos = prob.get("especificos", []) if isinstance(prob, dict) else []
    objetivos_especificos = obj.get("especificos", []) if isinstance(obj, dict) else []
    hipotesis_especificas = hip.get("especificos", []) if isinstance(hip, dict) else []

    problema_esp_1 = problemas_especificos[0] if isinstance(problemas_especificos, list) and len(problemas_especificos) > 0 else ""
    problema_esp_2 = problemas_especificos[1] if isinstance(problemas_especificos, list) and len(problemas_especificos) > 1 else ""
    objetivo_esp_1 = objetivos_especificos[0] if isinstance(objetivos_especificos, list) and len(objetivos_especificos) > 0 else ""
    objetivo_esp_2 = objetivos_especificos[1] if isinstance(objetivos_especificos, list) and len(objetivos_especificos) > 1 else ""
    hipotesis_esp_1 = hipotesis_especificas[0] if isinstance(hipotesis_especificas, list) and len(hipotesis_especificas) > 0 else ""
    hipotesis_esp_2 = hipotesis_especificas[1] if isinstance(hipotesis_especificas, list) and len(hipotesis_especificas) > 1 else ""

    filas = [
        ["PROBLEMA", "OBJETIVOS", "HIPOTESIS", "VARIABLES", "METODOLOGIA"],
        ["PROBLEMA GENERAL", "OBJETIVO GENERAL", "HIPOTESIS GENERAL", "", ""],
        [_clean_text(prob.get("general", "")), _clean_text(obj.get("general", "")), _clean_text(hip.get("general", "")), "", ""],
        ["PROBLEMAS ESPECIFICOS", "OBJETIVOS ESPECIFICOS", "HIPOTESIS ESPECIFICAS", "", ""],
        [_clean_text(problema_esp_1), _clean_text(objetivo_esp_1), _clean_text(hipotesis_esp_1), "", ""],
        [_clean_text(problema_esp_2), _clean_text(objetivo_esp_2), _clean_text(hipotesis_esp_2), "", ""],
    ]

    tabla_data = {
        "tipo": "tabla",
        "orientacion": "landscape" if landscape else "portrait",
        "restore_portrait": False,
        "encabezados": [str(titulo_investigacion), "", "", "", ""],
        "filas": filas,
        "filas_fase": [0, 1, 3],
        "celdas_combinadas": [
            {
                "fila": -1,
                "col_inicio": 0,
                "col_fin": 4,
                "texto": str(titulo_investigacion),
                "bold": True,
                "alignment": "center",
            },
            {
                "fila": 1,
                "fila_fin": 5,
                "col_inicio": 3,
                "col_fin": 3,
                "texto": _build_variables_block(var),
                "bold": False,
                "alignment": "left",
            },
            {
                "fila": 1,
                "fila_fin": 5,
                "col_inicio": 4,
                "col_fin": 4,
                "texto": _build_metodologia_block(met),
                "bold": False,
                "alignment": "left",
            },
        ],
        "estilo": {
            "encabezado_color": "D9D9D9",
            "fuente_size": 7.0,
            "ancho_columnas": [5.2, 5.2, 5.2, 4.4, 4.7],
            "titulo_exacto": False,
            "bordes": True,
            "celda_margen_twips": 35,
            "compactar_celdas": True,
        },
    }

    _render_tabla_impl(doc, tabla_data)
