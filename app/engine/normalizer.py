"""
Archivo: app/engine/normalizer.py
Proposito:
- Transforma la estructura anidada del JSON canónico v2 en una lista plana de Blocks.

Responsabilidades:
- Leer cada sección del JSON (caratula, preliminares, cuerpo, finales, etc.).
- Generar Blocks tipados que los renderers procesan sin conocer el JSON.
- Manejar AMBOS formatos de índices (dict simple y list detallada).
- Manejar tablas legacy (headers/rows) y canónicas (tipo: "tabla").
- Resolver la lógica de pre-scan de anexos (landscape antes de headings si primer
  anexo es matriz).
No hace:
- No renderiza nada en python-docx (eso es de los renderers).
- No modifica los JSONs originales.

Entradas/Salidas:
- Entradas: dict del JSON completo (ya parseado).
- Salidas: List[Block] — lista plana y ordenada.

Dependencias:
- app.engine.types (Block).

Puntos de extension:
- Agregar nuevos _normalize_X para secciones futuras.
- Modificar _normalize_content_item para soportar nuevos tipos de contenido.

Donde tocar si falla:
- Verificar que la lógica coincide exactamente con universal_generator.py.
- Comparar el orden de blocks con el orden de rendering del generador actual.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List

from app.engine.types import Block


# ═══════════════════════════════════════════════════════════════
# MAPEO DE CAMPOS TOC (Word field codes)
# ═══════════════════════════════════════════════════════════════

# indices como dict → key → (field_code, exclude_from_toc)
_FIELD_MAP: Dict[str, tuple] = {
    "contenido": (' TOC \\o "1-3" \\h \\z \\u ', True),
    "tablas": (' TOC \\c "Tabla" \\h \\z ', False),
    "figuras": (' TOC \\c "Figura" \\h \\z ', False),
    "abreviaturas": (None, False),  # sin campo TOC, pero aparece en el índice
}

# indices como list → titulo → (field_code, exclude_from_toc)
_LIST_FIELD_MAP: Dict[str, tuple] = {
    "ÍNDICE": (' TOC \\o "1-3" \\h \\z \\u ', True),
    "ÍNDICE DE TABLAS": (' TOC \\c "Tabla" \\h \\z ', False),
    "ÍNDICE DE FIGURAS": (' TOC \\c "Figura" \\h \\z ', False),
    "ÍNDICE DE ABREVIATURAS": (None, False),
}

_ABBR_LINE_RE = re.compile(
    r"^\s*([A-Za-z0-9./-]{2,})\s*(?:\t|:|[-–—])\s*(.+?)\s*$"
)
_ABBR_PAREN_RE = re.compile(r"^\s*(.+?)\s*\(([^()]{2,20})\)\s*$")


def _first_nonempty_text(candidates: List[Any]) -> str:
    for value in candidates:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_upper(text: str) -> str:
    return _strip_accents(str(text or "")).upper().strip()


def _looks_like_cover_title_placeholder(text: str) -> bool:
    value = _norm_upper(text)
    if not value:
        return True
    if "[" in value and "]" in value:
        return True
    if "{" in value and "}" in value:
        return True
    markers = (
        "TITULO DEL PROYECTO",
        "TITULO COMPLETO DEL TRABAJO",
        "TITULO DE LA TESIS",
        "ESCRIBA AQUI",
    )
    return any(marker in value for marker in markers)


def _is_instructional_cover_phrase(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False

    normalized = _norm_upper(value)
    markers = (
        "[NOTA:",
        "NOTA:",
        "MAXIMO 15 PALABRAS",
        "UNIDAD DE ANALISIS",
        "AMBITO DE ESTUDIO",
        "CONTIENE: LAS VARIABLES",
    )
    return any(marker in normalized for marker in markers)


def _indices_include_abbreviations(idx: Any) -> bool:
    if isinstance(idx, dict):
        return "abreviaturas" in idx
    if isinstance(idx, list):
        for item in idx:
            if not isinstance(item, dict):
                continue
            titulo = str(item.get("titulo", "")).upper()
            if "ABREVIATURAS" in titulo:
                return True
    return False


def _parse_abbreviation_line(line: str) -> tuple[str, str] | None:
    raw = (line or "").strip()
    if not raw:
        return None

    tab_split = raw.split("\t", 1)
    if len(tab_split) == 2 and tab_split[0].strip() and tab_split[1].strip():
        return tab_split[0].strip().upper(), tab_split[1].strip()

    match = _ABBR_LINE_RE.match(raw)
    if match:
        return match.group(1).strip().upper(), match.group(2).strip()

    paren_match = _ABBR_PAREN_RE.match(raw)
    if paren_match:
        meaning = paren_match.group(1).strip()
        sigla = paren_match.group(2).strip().upper()
        return sigla, meaning

    return None


def _collect_abbreviation_rows(source: Any) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    seen: set[str] = set()
    lines: List[str] = []

    def add_line(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
                cleaned = line.strip()
                if cleaned:
                    lines.append(cleaned)
            return
        if isinstance(value, list):
            for item in value:
                add_line(item)
            return
        if isinstance(value, dict):
            sigla = str(value.get("sigla", "")).strip()
            meaning = str(value.get("significado") or value.get("texto") or "").strip()
            if sigla and meaning:
                lines.append(f"{sigla}: {meaning}")
            else:
                for key in ("texto", "contenido", "parrafos", "ejemplo"):
                    add_line(value.get(key))
                for item in value.get("items", []) if isinstance(value.get("items"), list) else []:
                    if isinstance(item, dict):
                        if item.get("sigla") and item.get("significado"):
                            lines.append(f"{item['sigla']}: {item['significado']}")
                        else:
                            add_line(item.get("texto"))
                    else:
                        add_line(item)

    add_line(source)

    for line in lines:
        parsed = _parse_abbreviation_line(line)
        if not parsed:
            continue
        sigla, meaning = parsed
        if not sigla or not meaning:
            continue
        if sigla in seen:
            continue
        seen.add(sigla)
        rows.append({"sigla": sigla, "meaning": meaning})

    return rows


def _build_abbreviations_blocks(title: str, source: Any) -> List[Block]:
    heading = str(title or "").strip() or "INDICE DE ABREVIATURAS"
    return [
        {
            "type": "heading",
            "text": heading,
            "level": 1,
            "centered": True,
        },
        {
            "type": "abbreviations_table",
            "rows": _collect_abbreviation_rows(source),
        },
        {"type": "page_break"},
    ]


# ═══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════

def normalize(data: dict) -> List[Block]:
    """Transforma un JSON canónico v2 completo en una lista plana de Blocks.

    El orden de las secciones replica exactamente el de
    ``generate_document_unified()`` en universal_generator.py:
      1. caratula
      2. pagina_respeto  (solo si existe)
      3. informacion_basica  (solo si existe)
      4. preliminares
      5. cuerpo
      6. finales
      7. page_footer  (numeración de páginas)
    """
    blocks: List[Block] = []

    blocks.extend(_normalize_caratula(data))
    blocks.extend(_normalize_pagina_respeto(data))
    blocks.extend(_normalize_informacion_basica(data))
    blocks.extend(_normalize_preliminares(data))
    blocks.extend(_normalize_cuerpo(data))
    blocks.extend(_normalize_finales(data))
    blocks.append({"type": "page_footer"})

    return blocks


# ═══════════════════════════════════════════════════════════════
# CARÁTULA
# ═══════════════════════════════════════════════════════════════

def _normalize_caratula(data: dict) -> List[Block]:
    c = data.get("caratula", {})
    if not c:
        return []

    blocks: List[Block] = []

    # Universidad (con fallback desde _meta)
    uni_name = c.get("universidad", "").upper()
    if not uni_name:
        meta = data.get("_meta", {})
        _UNI_NAMES = {
            "uni": "UNIVERSIDAD NACIONAL DE INGENIERÍA",
            "unac": "UNIVERSIDAD NACIONAL DEL CALLAO",
        }
        uni_name = _UNI_NAMES.get(meta.get("university", ""), "")

    if uni_name:
        blocks.append({
            "type": "centered_text", "text": uni_name,
            "bold": True, "size": 16, "space_after": 6,
        })

    if c.get("facultad"):
        blocks.append({
            "type": "centered_text", "text": c["facultad"].upper(),
            "bold": True, "size": 14, "space_after": 6,
        })
    if c.get("escuela"):
        blocks.append({
            "type": "centered_text", "text": c["escuela"].upper(),
            "bold": True, "size": 14, "space_after": 24,
        })

    # Logo — el renderer resolverá el path usando resolve_logo_path(data)
    blocks.append({
        "type": "logo",
        "data": {
            "configuracion": data.get("configuracion", {}),
            "_meta": data.get("_meta", {}),
        },
        "width_inches": 2.0,
    })

    if c.get("tipo_documento"):
        blocks.append({
            "type": "centered_text", "text": c["tipo_documento"].upper(),
            "bold": True, "size": 16, "space_before": 40,
        })

    raw_title = _first_nonempty_text([c.get("titulo")])
    fallback_title = _first_nonempty_text([
        data.get("title"),
        (data.get("project") or {}).get("title")
        if isinstance(data.get("project"), dict)
        else None,
        (data.get("values") or {}).get("title")
        if isinstance(data.get("values"), dict)
        else None,
    ])
    placeholder_title = _first_nonempty_text([c.get("titulo_placeholder")])

    if raw_title and not _looks_like_cover_title_placeholder(raw_title):
        titulo = raw_title
    elif fallback_title:
        titulo = fallback_title
    else:
        titulo = raw_title or placeholder_title

    if titulo:
        blocks.append({
            "type": "centered_text", "text": titulo,
            "bold": True, "size": 14, "space_before": 30, "space_after": 30,
        })

    frase_grado = c.get("frase_grado")
    if frase_grado and not _is_instructional_cover_phrase(frase_grado):
        blocks.append({
            "type": "centered_text", "text": frase_grado,
            "size": 12, "space_before": 10,
        })

    grado = c.get("grado_objetivo") or c.get("grado") or c.get("carrera")
    if grado:
        blocks.append({
            "type": "centered_text", "text": grado.upper(),
            "bold": True, "size": 13, "space_after": 40,
        })

    # Autor / Asesor
    if c.get("label_autor"):
        blocks.append({
            "type": "centered_text", "text": c["label_autor"],
            "bold": True, "size": 12,
        })
    if c.get("autor_valor"):
        blocks.append({
            "type": "centered_text", "text": c["autor_valor"],
            "size": 12, "space_after": 12,
        })
    if c.get("label_asesor"):
        blocks.append({
            "type": "centered_text", "text": c["label_asesor"],
            "bold": True, "size": 12, "space_before": 12,
        })
    if c.get("asesor_valor"):
        blocks.append({
            "type": "centered_text", "text": c["asesor_valor"],
            "size": 12, "space_after": 12,
        })

    if c.get("label_linea"):
        blocks.append({
            "type": "centered_text", "text": c["label_linea"],
            "size": 11, "italic": True, "space_after": 40,
        })

    # Footer: lugar + año
    lugar = c.get("lugar", "")
    anio = c.get("anio", "")
    footer = f"{lugar}\n{anio}".strip() if (lugar or anio) else ""
    if not footer:
        footer = c.get("lugar_fecha") or f"{c.get('fecha', '')}\n{c.get('pais', '')}"
    if footer.strip():
        blocks.append({
            "type": "centered_text", "text": footer,
            "bold": True, "size": 12, "space_before": 60,
        })

    blocks.append({"type": "page_break"})
    return blocks


# ═══════════════════════════════════════════════════════════════
# PÁGINA DE RESPETO (solo unac_proyecto)
# ═══════════════════════════════════════════════════════════════

def _normalize_pagina_respeto(data: dict) -> List[Block]:
    if "pagina_respeto" not in data:
        return []

    p = data["pagina_respeto"]
    blocks: List[Block] = []

    if isinstance(p, dict):
        if p.get("titulo"):
            blocks.append({
                "type": "centered_text", "text": p["titulo"],
                "bold": True, "size": 14, "space_before": 200,
            })

        if "notas" in p:
            for nota in p["notas"]:
                if isinstance(nota, dict) and nota.get("texto"):
                    blocks.append({"type": "note", "text": nota["texto"]})

    # Siempre generar el salto de página de respeto.
    # Va forzado para que no sea colapsado por la lógica anti-duplicados.
    blocks.append({"type": "page_break", "force": True})
    return blocks


# ═══════════════════════════════════════════════════════════════
# INFORMACIÓN BÁSICA (solo unac_proyecto y unac_maestria)
# ═══════════════════════════════════════════════════════════════

def _normalize_informacion_basica(data: dict) -> List[Block]:
    info = data.get("informacion_basica", {})
    if not info:
        return []

    blocks: List[Block] = []

    blocks.append({
        "type": "paragraph_centered",
        "text": info.get("titulo", "INFORMACIÓN BÁSICA"),
        "bold": True, "size": 14,
        "space_before": 12, "space_after": 12,
    })

    if "elementos" in info:
        blocks.append({
            "type": "info_table",
            "elementos": info["elementos"],
        })

    blocks.append({"type": "page_break"})
    return blocks


# ═══════════════════════════════════════════════════════════════
# PRELIMINARES
# ═══════════════════════════════════════════════════════════════

def _normalize_preliminares(data: dict) -> List[Block]:
    pre = data.get("preliminares", {})
    if not pre:
        return []

    blocks: List[Block] = []

    # Nueva sección
    blocks.append({"type": "section_break"})

    # Secciones de texto simples
    for key in ["dedicatoria", "agradecimiento", "agradecimientos", "resumen"]:
        if key not in pre:
            continue
        item = pre[key]
        if isinstance(item, str):
            blocks.append({
                "type": "heading", "text": item,
                "level": 1, "centered": True,
            })
        else:
            blocks.append({
                "type": "heading",
                "text": item.get("titulo", key.upper()),
                "level": 1, "centered": True,
            })
            if item.get("texto"):
                blocks.append({"type": "paragraph", "text": item["texto"]})
        blocks.append({"type": "page_break"})

    rendered_abbreviations_from_indices = False

    # Índices
    if "indices" in pre:
        rendered_abbreviations_from_indices = _indices_include_abbreviations(pre["indices"])
        blocks.extend(_normalize_indices(pre["indices"], pre.get("abreviaturas")))

    # Abreviaturas fuera del bloque de indices
    if "abreviaturas" in pre and not rendered_abbreviations_from_indices:
        abbr = pre.get("abreviaturas")
        title = "INDICE DE ABREVIATURAS"
        if isinstance(abbr, dict):
            title = str(abbr.get("titulo", title) or title)
        elif isinstance(abbr, str) and abbr.strip():
            title = abbr.strip()
        blocks.extend(_build_abbreviations_blocks(title, abbr))

    # Tablas en preliminares (contenido extra)
    for item in pre.get("contenido", []):
        if isinstance(item, dict) and item.get("tipo") == "tabla":
            blocks.append({"type": "table", **item})

    # Introducción
    if "introduccion" in pre:
        intro = pre["introduccion"]
        blocks.append({
            "type": "heading",
            "text": intro.get("titulo", "INTRODUCCIÓN"),
            "level": 1, "centered": True,
        })
        blocks.append({"type": "paragraph", "text": intro.get("texto", "")})
        blocks.append({"type": "page_break"})

    return blocks


def _normalize_indices(idx, abbreviations_source: Any = None) -> List[Block]:
    """Normaliza índices en ambos formatos (dict simple o list detallada)."""
    blocks: List[Block] = []

    if isinstance(idx, dict):
        for k, title in idx.items():
            if k == "placeholder":
                continue
            if k == "abreviaturas":
                heading_title = title if isinstance(title, str) else ""
                blocks.extend(_build_abbreviations_blocks(heading_title, abbreviations_source))
                continue

            entry = _FIELD_MAP.get(k)
            if entry:
                field_code, exclude = entry
                if field_code:
                    # Campo TOC de Word (contenido, tablas, figuras)
                    blocks.append({
                        "type": "toc_field",
                        "field_code": field_code,
                        "heading_text": title,
                        "exclude_from_toc": exclude,
                    })
                else:
                    # Sin campo TOC, pero con Heading 1 para aparecer en el indice
                    blocks.append({
                        "type": "heading", "text": title,
                        "level": 1, "centered": True,
                    })
                    blocks.append({"type": "page_break"})
            else:
                # Otra key custom
                blocks.append({
                    "type": "paragraph_centered",
                    "text": title,
                    "bold": True, "size": 14,
                    "space_before": 12, "space_after": 12,
                })
                blocks.append({"type": "page_break"})

    elif isinstance(idx, list):
        for item in idx:
            titulo = item.get("titulo", "")

            if "ABREVIATURAS" in str(titulo).upper():
                source = item if item else abbreviations_source
                heading_title = titulo if isinstance(titulo, str) else ""
                blocks.extend(_build_abbreviations_blocks(heading_title, source))
                continue

            entry = _LIST_FIELD_MAP.get(titulo)
            if entry:
                field_code, exclude = entry
                if field_code:
                    blocks.append({
                        "type": "toc_field",
                        "field_code": field_code,
                        "heading_text": titulo,
                        "exclude_from_toc": exclude,
                    })
                else:
                    # Sin campo TOC, pero con Heading 1 para aparecer en el indice
                    blocks.append({
                        "type": "heading", "text": titulo,
                        "level": 1, "centered": True,
                    })
                    if "items" in item:
                        blocks.append({
                            "type": "index_items",
                            "items": item["items"],
                        })
                    blocks.append({"type": "page_break"})
            else:
                blocks.append({
                    "type": "paragraph_centered",
                    "text": titulo,
                    "bold": True, "size": 14,
                    "space_before": 12, "space_after": 12,
                })
                if "items" in item:
                    blocks.append({
                        "type": "index_items",
                        "items": item["items"],
                    })
                blocks.append({"type": "page_break"})

    return blocks


# ═══════════════════════════════════════════════════════════════
# CUERPO (capítulos)
# ═══════════════════════════════════════════════════════════════

def _normalize_cuerpo(data: dict) -> List[Block]:
    cuerpo = data.get("cuerpo", [])
    if not cuerpo:
        return []

    blocks: List[Block] = []

    for index, cap in enumerate(cuerpo):
        # Salto de pagina antes de cada capitulo (excepto el primero).
        # Evita insertar un salto justo despues del titulo.
        if index > 0:
            blocks.append({"type": "page_break"})

        # Título del capítulo
        blocks.append({
            "type": "heading",
            "text": cap.get("titulo", ""),
            "level": 1, "centered": False,
        })

        # Nota del capítulo
        if "nota_capitulo" in cap:
            blocks.append({"type": "note", "text": cap["nota_capitulo"]})

        # Contenido del capítulo
        for item in cap.get("contenido", []):
            blocks.extend(_normalize_content_item(item))

        # Ejemplos APA a nivel de capítulo
        if "ejemplos_apa" in cap:
            blocks.append({
                "type": "apa_examples",
                "ejemplos": cap["ejemplos_apa"],
            })

    return blocks


def _normalize_content_item(item) -> List[Block]:
    """Normaliza un item de contenido (dentro de cuerpo o anexos).

    Soporta:
    - str → párrafo
    - dict con tipo='tabla' → tabla canónica
    - dict con texto → subtítulo + content_block
    """
    blocks: List[Block] = []

    # String simple
    if isinstance(item, str):
        blocks.append({"type": "paragraph", "text": item})
        return blocks

    if not isinstance(item, dict):
        return blocks

    # Tabla canónica directa (tipo == "tabla" a nivel de contenido[])
    if item.get("tipo") == "tabla":
        blocks.append({"type": "table", **item})
        return blocks

    # Subtítulo
    if "texto" in item:
        blocks.append({
            "type": "black_heading",
            "text": item["texto"],
            "level": 2, "size": 12, "centered": False,
        })

    # Content block compartido (notas, párrafos, tablas, imágenes)
    blocks.extend(_normalize_content_block(item))

    # Placeholder de matriz
    if item.get("mostrar_matriz"):
        blocks.append({
            "type": "paragraph",
            "text": "[Se insertará la Matriz de Consistencia aquí]",
        })

    return blocks


def _normalize_content_block(item: dict) -> List[Block]:
    """Normaliza el contenido compartido de un item (usado en cuerpo y anexos).

    Replica exactamente la lógica de _render_content_block():
    instruccion_detallada → nota → párrafos → tabla legacy → tablas_especiales
    → tabla_data → imágenes.
    """
    blocks: List[Block] = []

    # Instrucción / nota
    if "instruccion_detallada" in item:
        blocks.append({"type": "note", "text": item["instruccion_detallada"]})
    if "nota" in item:
        blocks.append({"type": "note", "text": item["nota"]})

    # Párrafos
    if "parrafos" in item:
        for p_text in item["parrafos"]:
            blocks.append({"type": "paragraph", "text": p_text})

    # Tabla legacy (dict con headers/rows)
    if "tabla" in item and isinstance(item["tabla"], dict):
        blocks.append({
            "type": "legacy_table",
            "tabla": item["tabla"],
            "titulo": item.get("tabla_titulo"),
            "nota": item.get("tabla_nota"),
        })

    # tablas_especiales (array de tablas legacy)
    if "tablas_especiales" in item:
        for te in item["tablas_especiales"]:
            if isinstance(te, dict):
                blocks.append({
                    "type": "legacy_table",
                    "tabla": te,
                    "titulo": te.get("titulo"),
                })

    # Tabla canónica (tabla_data)
    if "tabla_data" in item and isinstance(item["tabla_data"], dict):
        blocks.append({"type": "table", **item["tabla_data"]})

    # Imágenes
    if "imagenes" in item:
        for img in item["imagenes"]:
            ruta = str(img.get("ruta", "") or "").strip()
            if not ruta or ruta.lower() == "placeholder":
                continue
            blocks.append({
                "type": "image",
                "titulo": img.get("titulo", ""),
                "ruta": ruta,
                "fuente": img.get("fuente", ""),
            })

    return blocks


# ═══════════════════════════════════════════════════════════════
# FINALES (referencias + anexos)
# ═══════════════════════════════════════════════════════════════

def _normalize_finales(data: dict) -> List[Block]:
    fin = data.get("finales", {})
    if not fin:
        return []

    blocks: List[Block] = []

    # ── Referencias ──
    blocks.extend(_normalize_referencias(fin))

    # ── Tablas sueltas en finales ──
    for item in fin.get("contenido", []):
        if isinstance(item, dict) and item.get("tipo") == "tabla":
            blocks.append({"type": "table", **item})

    # ── Anexos ──
    blocks.extend(_normalize_anexos(data, fin))

    return blocks


def _normalize_referencias(fin: dict) -> List[Block]:
    """Normaliza la sección de referencias bibliográficas."""
    if "referencias" not in fin:
        return []

    blocks: List[Block] = []
    ref = fin["referencias"]

    if isinstance(ref, str):
        blocks.append({
            "type": "heading", "text": ref,
            "level": 1, "centered": False,
        })
    else:
        blocks.append({
            "type": "heading",
            "text": ref.get("titulo", "REFERENCIAS BIBLIOGRÁFICAS"),
            "level": 1, "centered": False,
        })
        if "nota" in ref:
            blocks.append({"type": "note", "text": ref["nota"]})
        ejemplos = ref.get("ejemplos") or ref.get("ejemplos_apa", [])
        if ejemplos:
            blocks.append({"type": "apa_examples", "ejemplos": ejemplos})

    blocks.append({"type": "page_break"})
    return blocks


def _normalize_anexos(data: dict, fin: dict) -> List[Block]:
    """Normaliza la sección de anexos con su lógica de landscape/matriz.

    Replica exactamente la lógica de render_finales() para anexos:
    1. Pre-scan: ¿primer anexo es matriz? → landscape ANTES de headings
    2. Heading "ANEXOS"
    3. Items de la lista
    4. Si primer item es matriz → render con landscape=False (ya switcheado)
    5. Restore portrait
    6. Fallback: si hay matriz_consistencia pero no estaba en la lista
    """
    if "anexos" not in fin:
        return []

    blocks: List[Block] = []
    anx = fin["anexos"]
    rendered_matriz = False

    # Pre-scan
    lista = anx.get("lista", []) if isinstance(anx, dict) else []
    first_is_matriz = (
        lista
        and isinstance(lista[0], dict)
        and "matriz" in lista[0].get("titulo", "").lower()
        and "matriz_consistencia" in data
    )

    # Switch a landscape ANTES de los headings
    if first_is_matriz:
        blocks.append({"type": "section_switch", "orientation": "landscape"})

    if isinstance(anx, str):
        blocks.append({
            "type": "heading", "text": anx,
            "level": 1, "centered": False,
        })
    else:
        blocks.append({
            "type": "heading",
            "text": anx.get("titulo_seccion", "ANEXOS"),
            "level": 1, "centered": False,
        })
        if anx.get("nota"):
            blocks.append({"type": "note", "text": anx["nota"]})

        for item in lista:
            # Tabla canónica directa
            if isinstance(item, dict) and item.get("tipo") == "tabla":
                blocks.append({"type": "table", **item})
                continue
            # String simple
            if isinstance(item, str):
                blocks.append({"type": "paragraph", "text": item})
                continue

            titulo_anexo = item.get("titulo", "")
            if titulo_anexo:
                blocks.append({
                    "type": "paragraph_centered",
                    "text": titulo_anexo,
                    "bold": True, "size": 13,
                    "space_before": 12, "space_after": 12,
                })

            is_matriz = "matriz" in titulo_anexo.lower()
            if is_matriz and "matriz_consistencia" in data:
                blocks.append({
                    "type": "matriz",
                    "data": data["matriz_consistencia"],
                    "landscape": False,
                })
                rendered_matriz = True
                continue

            # Content block normal del anexo
            blocks.extend(_normalize_content_block(item))

    # Restore portrait
    if first_is_matriz:
        blocks.append({"type": "section_switch", "orientation": "portrait"})

    # Fallback: matriz como último anexo si no estaba en la lista
    if "matriz_consistencia" in data and not rendered_matriz:
        blocks.append({"type": "section_switch", "orientation": "landscape"})
        blocks.append({
            "type": "heading", "text": "ANEXOS",
            "level": 1, "centered": False,
        })
        blocks.append({
            "type": "paragraph_centered",
            "text": "Anexo 1: Matriz de Consistencia",
            "bold": True, "size": 13,
            "space_before": 12, "space_after": 12,
        })
        blocks.append({
            "type": "matriz",
            "data": data["matriz_consistencia"],
            "landscape": False,
        })
        blocks.append({"type": "section_switch", "orientation": "portrait"})

    return blocks
