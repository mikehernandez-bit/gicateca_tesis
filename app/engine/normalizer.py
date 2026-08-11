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

_ABBR_LINE_RE = re.compile(r"^\s*([A-Za-z0-9./-]{2,})\s*(?:\t|:|[-–—])\s*(.+?)\s*$")
_ABBR_PAREN_RE = re.compile(r"^\s*(.+?)\s*\(([^()]{2,20})\)\s*$")


_ABBR_IN_TEXT_RE = re.compile(r"([A-Za-z][^()\n]{3,120}?)\s*\(([A-Za-z][A-Za-z0-9./-]{1,19})\)")
_ABBR_REVERSED_IN_TEXT_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9./-]{1,19})\s*\(([^()]{3,120})\)")
_ABBR_MEANING_TOKEN_RE = re.compile(r"[A-Za-zÃÃ‰ÃÃ“ÃšÃœÃ‘Ã¡Ã©Ã­Ã³ÃºÃ¼Ã±]+")
_ABBR_REFERENCE_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_AI_LEVEL3_HEADING_RE = re.compile(r"^\s*(\d+\.\d+\.\d+\.?)\s+(.+?)\s*$")
# Detecta caracteres típicos de fórmulas matemáticas para evitar que sean
# interpretados como subtítulos nivel 3 y aparezcan en el índice de contenidos.
_MATH_FORMULA_RE = re.compile(
    r"[=²³⁴⁵⁶⁷⁸⁹·±∑∫√÷×αβγδσμλπεζηθ]"
    r"|[+\-*/]{1}(?:\s|$)"   # operadores aritméticos en contexto de fórmula
    r"|\b[a-z]\s*=\s*[A-Za-z0-9(]"  # variable = expresión (e.g. n = N...)
    r"|\([^)]{1,10}\)\s*[+\-*/]"  # (expr) OP ...
    r"|\d+\s*/\s*\d+"  # fracción numérica: 1 / 2
)
# Elimina marcadores Markdown de negrita/cursiva (**texto**, __texto__, *texto*)
_MARKDOWN_BOLD_RE = re.compile(r"(\*{1,3}|_{1,3})(.+?)\1")
_ABBR_AUTHOR_LIKE_RE = re.compile(
    r"^[A-ZÃÃ‰ÃÃ“ÃšÃ‘][a-zÃ¡Ã©Ã­Ã³ÃºÃ±]+(?:\s+[A-ZÃÃ‰ÃÃ“ÃšÃ‘][a-zÃ¡Ã©Ã­Ã³ÃºÃ±]+){0,3}(?:\s+et al\.?)?(?:,\s*(?:19|20)\d{2})?$",
    re.IGNORECASE,
)
_ABBR_STOPWORDS = {
    "A",
    "AL",
    "AN",
    "AND",
    "DE",
    "DEL",
    "EL",
    "EN",
    "ET",
    "LA",
    "LAS",
    "LOS",
    "OF",
    "PARA",
    "POR",
    "THE",
    "Y",
}
_COMMON_ABBREVIATIONS: Dict[str, tuple[str, str]] = {
    "IA": ("IA", "Inteligencia Artificial"),
    "AI": ("AI", "Artificial Intelligence"),
    "ML": ("ML", "Machine Learning"),
    "DL": ("DL", "Deep Learning"),
    "IOT": ("IoT", "Internet de las Cosas"),
    "CNN": ("CNN", "Convolutional Neural Network"),
    "RNN": ("RNN", "Recurrent Neural Network"),
    "ODS": ("ODS", "Objetivos de Desarrollo Sostenible"),
    "SAE": ("SAE", "Society of Automotive Engineers"),
    "SPSS": ("SPSS", "Statistical Package for the Social Sciences"),
    "KPI": ("KPI", "Key Performance Indicator"),
    "FMEA": ("FMEA", "Failure Mode and Effects Analysis"),
    "MTBF": ("MTBF", "Mean Time Between Failures"),
    "UNAC": ("UNAC", "Universidad Nacional del Callao"),
    "ERP": ("ERP", "Enterprise Resource Planning"),
    "API": ("API", "Application Programming Interface"),
    "SQL": ("SQL", "Structured Query Language"),
    "PLC": ("PLC", "Programmable Logic Controller"),
    "SCADA": ("SCADA", "Supervisory Control and Data Acquisition"),
    "GPS": ("GPS", "Global Positioning System"),
    "CAD": ("CAD", "Computer-Aided Design"),
}


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


def _looks_like_template_example_title(text: Any) -> bool:
    normalized = _norm_upper(str(text or ""))
    return bool(normalized and "EJEMPLO" in normalized)


def _looks_like_template_example_image(image: dict[str, Any]) -> bool:
    ruta = str(image.get("ruta", "") or "").strip().lower()
    titulo = image.get("titulo")
    return "figura_ejemplo" in ruta or _looks_like_template_example_title(titulo)


def _looks_like_template_placeholder_text(text: Any) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    normalized = _norm_upper(raw)
    if ("[" in raw and "]" in raw) or ("{{" in raw and "}}" in raw):
        return True
    markers = (
        "ESCRIBA AQUI",
        "COMPLETE",
        "COMPLETAR",
        "INSERTAR",
        "AGREGAR",
        "LLENAR",
        "COLOCAR EL SIGNIFICADO",
        "REEMPLACE POR",
    )
    return any(marker in normalized for marker in markers)


def _looks_like_placeholder_table_cell(value: Any) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    normalized = _norm_upper(raw)
    if raw.startswith("[") and raw.endswith("]"):
        return True
    markers = (
        "COMPLETAR",
        "AUTOR 1",
        "AUTOR 2",
        "VARIABLE",
        "RESULTADO",
        "SI/NO",
        "NOMBRE",
        "INDICADOR",
    )
    return any(marker in normalized for marker in markers)


def _looks_like_placeholder_table_data(table_like: Any) -> bool:
    if not isinstance(table_like, dict):
        return False
    rows = table_like.get("rows")
    if not isinstance(rows, list):
        rows = table_like.get("filas")
    if not isinstance(rows, list):
        return False

    visible_cells: list[str] = []
    placeholder_cells = 0
    for row in rows:
        if not isinstance(row, (list, tuple)):
            continue
        for cell in row:
            text = str(cell or "").strip()
            if not text:
                continue
            visible_cells.append(text)
            if _looks_like_placeholder_table_cell(text):
                placeholder_cells += 1

    if not visible_cells:
        return True
    return placeholder_cells == len(visible_cells)


def _looks_like_annex_filler_text(text: Any) -> bool:
    normalized = _norm_upper(str(text or ""))
    if not normalized:
        return False
    markers = (
        "ESTA SECCION CONTIENE",
        "EN ESTA SECCION SE PRESENTA",
        "EN ESTA SECCION SE PRESENTAN",
        "EN PRIMER LUGAR",
        "A CONTINUACI",
        "A CONTINUACION SE PRESENTAN LOS ANEXOS",
        "ADEMAS SE ADJUNTA",
        "ADEMAS, SE ADJUNTA",
        "ADICIONALMENTE",
        "ASIMISMO",
        "FINALMENTE",
        "EL PRIMER ANEXO INCLUYE",
        "OTRO ANEXO RELEVANTE",
        "LOS ANEXOS TAMBIEN CONTIENEN",
        "SE ADJUNTA",
    )
    return any(marker in normalized for marker in markers)


def _looks_like_annex_useful_paragraph(text: Any) -> bool:
    normalized = _norm_upper(str(text or ""))
    if not normalized:
        return False
    useful_prefixes = (
        "PREGUNTA",
        "ITEM",
        "ITEMS",
        "EVIDENCIA",
        "REGISTRO",
        "CODIGO",
        "COD.",
    )
    if any(normalized.startswith(prefix) for prefix in useful_prefixes):
        return True
    return bool(re.match(r"^\s*(\d+[\).:-]|[A-Z]{2,}-\d+)", str(text or "").strip()))


def _strip_annex_inner_title_prefix(text: Any) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    if _norm_upper(raw).startswith("ANEXO"):
        return raw
    cleaned = re.sub(
        r"^\s*(TABLA|FIGURA)\s*[A-Z0-9.-]*\s*[:.)-]*\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip(" .:-")
    return cleaned or raw


def _strip_figure_caption_prefix(text: Any) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    cleaned = re.sub(
        r"^\s*FIGURA\s*[A-Z0-9.-]*\s*[:.)-]*\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip(" .:-")
    return cleaned or raw


def _resolve_annex_heading_text(item: dict[str, Any], position: int) -> str:
    raw = str(item.get("titulo", "") or "").strip()
    if raw and _norm_upper(raw).startswith("ANEXO"):
        return raw
    cleaned = _strip_annex_inner_title_prefix(raw)
    if cleaned:
        return f"Anexo {position}: {cleaned}"
    return f"Anexo {position}"


def _normalize_annex_blocks(blocks: List[Block]) -> List[Block]:
    cleaned: List[Block] = []
    has_structural_blocks = any(
        block.get("type") in {"table", "legacy_table", "matriz", "image"}
        for block in blocks
    )

    for block in blocks:
        block_type = block.get("type")
        text = str(block.get("text", "") or "").strip()

        if block_type in {"paragraph", "note"}:
            if not text or _looks_like_annex_filler_text(text):
                continue
            if has_structural_blocks and not _looks_like_annex_useful_paragraph(text):
                continue

        normalized = dict(block)
        if block_type == "table":
            normalized.pop("titulo", None)
        elif block_type == "legacy_table":
            normalized["titulo"] = ""
        elif block_type == "image":
            normalized["omit_caption"] = True

        cleaned.append(normalized)

    return cleaned


def _normalize_annex_content(content: Any) -> List[Block]:
    return _normalize_annex_blocks(_normalize_ai_content(content))


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
        return tab_split[0].strip(), tab_split[1].strip()

    match = _ABBR_LINE_RE.match(raw)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    paren_match = _ABBR_PAREN_RE.match(raw)
    if paren_match:
        meaning = paren_match.group(1).strip()
        sigla = paren_match.group(2).strip()
        return sigla, meaning

    return None


def _normalize_abbreviation_display(sigla: str) -> str:
    raw = str(sigla or "").strip()
    if not raw:
        return ""
    canonical = _COMMON_ABBREVIATIONS.get(_norm_upper(raw))
    if canonical:
        return canonical[0]
    return raw.upper()


def _is_valid_abbreviation_candidate(sigla: str) -> bool:
    raw = str(sigla or "").strip()
    if not raw:
        return False
    normalized = _norm_upper(raw)
    if normalized in _COMMON_ABBREVIATIONS:
        return True
    if not 2 <= len(raw) <= 8:
        return False
    if not re.fullmatch(r"[A-Za-z0-9./-]+", raw):
        return False
    if re.fullmatch(r"(?:19|20)\d{2}", raw):
        return False

    letters = [char for char in raw if char.isalpha()]
    if len(letters) < 2:
        return False

    upper_count = sum(char.isupper() for char in letters)
    lower_count = sum(char.islower() for char in letters)
    if lower_count and upper_count < 2:
        return False
    if raw.isalpha() and raw[0].isupper() and raw[1:].islower():
        return False
    if raw.islower():
        return False

    return True


def _looks_like_reference_like_meaning(meaning: str) -> bool:
    text = re.sub(r"\s+", " ", str(meaning or "").strip())
    if not text:
        return True
    if re.fullmatch(r"(?:19|20)\d{2}", text):
        return True
    if _ABBR_AUTHOR_LIKE_RE.match(text) and _ABBR_REFERENCE_RE.search(text):
        return True
    return False


def _meaning_matches_sigla(meaning: str, sigla: str) -> bool:
    normalized_sigla = _norm_upper(sigla)
    if normalized_sigla in _COMMON_ABBREVIATIONS:
        return True
    tokens = [
        token
        for token in _ABBR_MEANING_TOKEN_RE.findall(str(meaning or ""))
        if _norm_upper(token) not in _ABBR_STOPWORDS
    ]
    if len(tokens) < 2:
        return False
    acronym = "".join(token[0].upper() for token in tokens if token)
    return acronym == normalized_sigla


def _append_abbreviation_row(
    rows: List[Dict[str, str]],
    seen: set[str],
    sigla: str,
    meaning: str,
) -> None:
    raw_sigla = str(sigla or "").strip()
    display = _normalize_abbreviation_display(raw_sigla)
    expanded = re.sub(r"\s+", " ", str(meaning or "").strip()).strip(" .;:-")
    normalized_key = _norm_upper(display)
    canonical = _COMMON_ABBREVIATIONS.get(normalized_key)
    if canonical:
        display, expanded = canonical
        normalized_key = _norm_upper(display)
    if (
        not normalized_key
        or not expanded
        or not _is_valid_abbreviation_candidate(raw_sigla)
        or _looks_like_reference_like_meaning(expanded)
        or not _meaning_matches_sigla(expanded, display)
    ):
        return
    if normalized_key in seen:
        return
    seen.add(normalized_key)
    rows.append({"sigla": display, "meaning": expanded})


def _extract_generated_text_fragments(data: dict) -> List[str]:
    fragments: List[str] = []

    def add_content(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            text = value.strip()
            if text:
                fragments.append(text)
            return
        if isinstance(value, list):
            for item in value:
                add_content(item)
            return
        if not isinstance(value, dict):
            return

        block_type = _norm_upper(value.get("tipo", ""))
        if block_type == "PARRAFO":
            add_content(value.get("texto"))
            return
        if block_type == "FIGURA":
            add_content(value.get("titulo") or value.get("caption"))
            return
        if block_type == "TABLA":
            add_content(value.get("titulo"))
            return

        for key in ("_ai_content", "parrafos"):
            add_content(value.get(key))

    preliminares = data.get("preliminares", {})
    if isinstance(preliminares, dict):
        for key, item in preliminares.items():
            if key in {"indices", "abreviaturas"}:
                continue
            if isinstance(item, dict):
                add_content(item.get("_ai_content"))
                add_content(item.get("parrafos"))

    for chapter in data.get("cuerpo", []) if isinstance(data.get("cuerpo"), list) else []:
        if not isinstance(chapter, dict):
            continue
        add_content(chapter.get("_ai_content"))
        for item in chapter.get("contenido", []) if isinstance(chapter.get("contenido"), list) else []:
            if not isinstance(item, dict):
                continue
            add_content(item.get("_ai_content"))
            add_content(item.get("parrafos"))

    finales = data.get("finales", {})
    if isinstance(finales, dict):
        anexos = finales.get("anexos")
        if isinstance(anexos, dict):
            for item in anexos.get("lista", []) if isinstance(anexos.get("lista"), list) else []:
                if isinstance(item, dict):
                    add_content(item.get("_ai_content"))

    return fragments


def _derive_document_abbreviation_rows(data: dict | None) -> List[Dict[str, str]]:
    if not isinstance(data, dict):
        return []

    rows: List[Dict[str, str]] = []
    seen: set[str] = set()

    for fragment in _extract_generated_text_fragments(data):
        for line in fragment.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            parsed = _parse_abbreviation_line(line)
            if parsed:
                sigla, meaning = parsed
                canonical = _COMMON_ABBREVIATIONS.get(_norm_upper(sigla))
                if canonical:
                    sigla, meaning = canonical
                _append_abbreviation_row(rows, seen, sigla, meaning)

        for meaning, sigla in _ABBR_IN_TEXT_RE.findall(fragment):
            cleaned_meaning = re.sub(r"\s+", " ", meaning).strip(" .;:-")
            if len(cleaned_meaning.split()) > 12:
                continue
            canonical = _COMMON_ABBREVIATIONS.get(_norm_upper(sigla))
            if canonical:
                sigla, cleaned_meaning = canonical
            _append_abbreviation_row(rows, seen, sigla, cleaned_meaning)

        for sigla, meaning in _ABBR_REVERSED_IN_TEXT_RE.findall(fragment):
            cleaned_meaning = re.sub(r"\s+", " ", meaning).strip(" .;:-")
            if len(cleaned_meaning.split()) > 12:
                continue
            canonical = _COMMON_ABBREVIATIONS.get(_norm_upper(sigla))
            if canonical:
                sigla, cleaned_meaning = canonical
            _append_abbreviation_row(rows, seen, sigla, cleaned_meaning)

        normalized_fragment = _norm_upper(fragment)
        for key, (display, meaning) in _COMMON_ABBREVIATIONS.items():
            if re.search(rf"(?<![A-Z0-9]){re.escape(key)}(?![A-Z0-9])", normalized_fragment):
                _append_abbreviation_row(rows, seen, display, meaning)

    return rows


def _collect_abbreviation_rows(source: Any, *, document_source: dict | None = None) -> List[Dict[str, str]]:
    source_rows: List[Dict[str, str]] = []
    source_seen: set[str] = set()
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
                for key in ("_ai_content", "texto", "contenido", "parrafos", "ejemplo"):
                    add_line(value.get(key))
                for item in (
                    value.get("items", [])
                    if isinstance(value.get("items"), list)
                    else []
                ):
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
        canonical = _COMMON_ABBREVIATIONS.get(_norm_upper(sigla))
        if canonical:
            sigla, meaning = canonical
        _append_abbreviation_row(source_rows, source_seen, sigla, meaning)

    derived_rows = _derive_document_abbreviation_rows(document_source)
    if derived_rows:
        derived_siglas = {_norm_upper(row["sigla"]) for row in derived_rows}
        source_rows = [
            row for row in source_rows if _norm_upper(row["sigla"]) in derived_siglas
        ]

    rows: List[Dict[str, str]] = []
    seen: set[str] = set()
    for row in source_rows:
        _append_abbreviation_row(rows, seen, row["sigla"], row["meaning"])
    for row in derived_rows:
        _append_abbreviation_row(rows, seen, row["sigla"], row["meaning"])

    return rows


def _build_abbreviations_blocks(
    title: str,
    source: Any,
    *,
    document_source: dict | None = None,
) -> List[Block]:
    heading = str(title or "").strip() or "INDICE DE ABREVIATURAS"
    rows = _collect_abbreviation_rows(source, document_source=document_source)
    blocks: List[Block] = [
        {
            "type": "heading",
            "text": heading,
            "level": 1,
            "centered": True,
        }
    ]

    if rows:
        blocks.append(
            {
                "type": "abbreviations_table",
                "rows": rows,
            }
        )
    else:
        fallback_text = "No se identificaron abreviaturas relevantes en el presente documento."
        if isinstance(source, dict):
            ai_text = str(source.get("_ai_content") or "").strip()
            if ai_text and not _looks_like_template_placeholder_text(ai_text):
                fallback_text = ai_text
        elif isinstance(source, str):
            source_text = str(source or "").strip()
            if source_text and not _looks_like_template_placeholder_text(source_text):
                fallback_text = source_text
        blocks.append({"type": "paragraph", "text": fallback_text})

    blocks.append({"type": "page_break"})
    return blocks


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

    return _apply_consecutive_landscape_table_policy(blocks)


def _is_landscape_table_block(block: Any) -> bool:
    if not isinstance(block, dict):
        return False
    if str(block.get("type") or "").strip().lower() != "table":
        return False
    orientation = str(block.get("orientacion") or "").strip().lower()
    return orientation == "landscape"


def _apply_consecutive_landscape_table_policy(blocks: List[Block]) -> List[Block]:
    """Avoid redundant portrait restores between consecutive landscape tables.

    When two or more landscape canonical tables are consecutive, only the last
    one should restore portrait orientation. This prevents blank pages produced
    by back-to-back section switches (landscape -> portrait -> landscape).
    """
    if not blocks:
        return blocks

    normalized: List[Block] = []
    index = 0
    total = len(blocks)

    while index < total:
        current = blocks[index]
        if not _is_landscape_table_block(current):
            normalized.append(current)
            index += 1
            continue

        run_end = index
        while run_end + 1 < total and _is_landscape_table_block(blocks[run_end + 1]):
            run_end += 1

        for table_index in range(index, run_end + 1):
            table_block = dict(blocks[table_index])
            if table_index < run_end:
                table_block["restore_portrait"] = False
            normalized.append(table_block)

        index = run_end + 1

    return normalized


# ═══════════════════════════════════════════════════════════════
# CARÁTULA
# ═══════════════════════════════════════════════════════════════


def _normalize_caratula(data: dict) -> List[Block]:
    c = data.get("caratula", {})
    if not c:
        return []

    is_unac_maestria = data.get("_meta", {}).get("id", "").startswith("unac-maestria")
    is_unac_proyecto = data.get("_meta", {}).get("id", "").startswith("unac-proyecto")
    is_unac_informe = data.get("_meta", {}).get("id", "").startswith("unac-informe")
    # Proyecto e Informe de Tesis UNAC deben compartir exactamente la misma
    # maqueta de carátula que Maestría: es la única que sustituye autor,
    # asesor, línea de investigación y título con los datos reales del
    # proyecto en vez de imprimir el texto placeholder tal cual del JSON.
    if is_unac_maestria or is_unac_proyecto or is_unac_informe:
        return [{"type": "caratula_unac_maestria", "data": data, "caratula": c}]

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
        blocks.append(
            {
                "type": "centered_text",
                "text": uni_name,
                "bold": True,
                "size": 16,
                "space_after": 6,
            }
        )

    if c.get("facultad"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["facultad"].upper(),
                "bold": True,
                "size": 14,
                "space_after": 6,
            }
        )
    if c.get("escuela"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["escuela"].upper(),
                "bold": True,
                "size": 14,
                "space_after": 24,
            }
        )

    # Logo — el renderer resolverá el path usando resolve_logo_path(data)
    blocks.append(
        {
            "type": "logo",
            "data": {
                "configuracion": data.get("configuracion", {}),
                "_meta": data.get("_meta", {}),
            },
            "width_inches": 2.0,
        }
    )

    if c.get("tipo_documento"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["tipo_documento"].upper(),
                "bold": True,
                "size": 16,
                "space_before": 40,
            }
        )

    raw_title = _first_nonempty_text([c.get("titulo")])
    fallback_title = _first_nonempty_text(
        [
            data.get("title"),
            (data.get("project") or {}).get("title")
            if isinstance(data.get("project"), dict)
            else None,
            (data.get("values") or {}).get("title")
            if isinstance(data.get("values"), dict)
            else None,
        ]
    )
    placeholder_title = _first_nonempty_text([c.get("titulo_placeholder")])

    if raw_title and not _looks_like_cover_title_placeholder(raw_title):
        titulo = raw_title
    elif fallback_title:
        titulo = fallback_title
    else:
        titulo = raw_title or placeholder_title

    if titulo:
        blocks.append(
            {
                "type": "centered_text",
                "text": titulo,
                "bold": True,
                "size": 14,
                "space_before": 30,
                "space_after": 30,
            }
        )

    frase_grado = c.get("frase_grado")
    if frase_grado and not _is_instructional_cover_phrase(frase_grado):
        blocks.append(
            {
                "type": "centered_text",
                "text": frase_grado,
                "size": 12,
                "space_before": 10,
            }
        )

    grado = c.get("grado_objetivo") or c.get("grado") or c.get("carrera")
    if grado:
        blocks.append(
            {
                "type": "centered_text",
                "text": grado.upper(),
                "bold": True,
                "size": 13,
                "space_after": 40,
            }
        )

    # Autor / Asesor
    if c.get("label_autor"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["label_autor"],
                "bold": True,
                "size": 12,
            }
        )
    if c.get("autor_valor"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["autor_valor"],
                "size": 12,
                "space_after": 12,
            }
        )
    if c.get("label_asesor"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["label_asesor"],
                "bold": True,
                "size": 12,
                "space_before": 12,
            }
        )
    if c.get("asesor_valor"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["asesor_valor"],
                "size": 12,
                "space_after": 12,
            }
        )

    if c.get("label_linea"):
        blocks.append(
            {
                "type": "centered_text",
                "text": c["label_linea"],
                "size": 11,
                "italic": True,
                "space_after": 40,
            }
        )

    # Footer: lugar + año
    lugar = c.get("lugar", "")
    anio = c.get("anio", "")
    footer = f"{lugar}\n{anio}".strip() if (lugar or anio) else ""
    if not footer:
        footer = c.get("lugar_fecha") or f"{c.get('fecha', '')}\n{c.get('pais', '')}"
    if footer.strip():
        blocks.append(
            {
                "type": "centered_text",
                "text": footer,
                "bold": True,
                "size": 12,
                "space_before": 60,
            }
        )

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
            blocks.append(
                {
                    "type": "centered_text",
                    "text": p["titulo"],
                    "bold": True,
                    "size": 14,
                    "space_before": 200,
                }
            )

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

    is_unac_maestria = data.get("_meta", {}).get("id", "").startswith("unac-maestria")
    is_unac_proyecto = data.get("_meta", {}).get("id", "").startswith("unac-proyecto")
    # Proyecto de Tesis UNAC debe compartir exactamente la misma maqueta
    # de información básica que Maestría.
    if is_unac_maestria or is_unac_proyecto:
        return [{"type": "info_basica_unac_maestria", "data": data, "info": info}]

    blocks: List[Block] = []

    blocks.append(
        {
            "type": "paragraph_centered",
            "text": info.get("titulo", "INFORMACIÓN BÁSICA"),
            "bold": True,
            "size": 14,
            "space_before": 12,
            "space_after": 12,
        }
    )

    if "elementos" in info:
        blocks.append(
            {
                "type": "info_table",
                "elementos": info["elementos"],
            }
        )

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

    optional_preliminary_keys = {"dedicatoria", "agradecimiento", "agradecimientos", "abstract"}

    # Secciones de texto simples
    for key in ["dedicatoria", "agradecimiento", "agradecimientos", "resumen", "abstract"]:
        if key not in pre:
            continue
        item = pre[key]
        heading_text = item if isinstance(item, str) else item.get("titulo", key.upper())
        content_blocks: List[Block] = []

        if isinstance(item, dict):
            if item.get("_ai_content"):
                content_blocks = _normalize_ai_content(item["_ai_content"])
            elif item.get("texto") and not _looks_like_template_placeholder_text(item["texto"]):
                content_blocks = [{"type": "paragraph", "text": item["texto"]}]

        if key in optional_preliminary_keys and not content_blocks:
            continue

        blocks.append(
            {
                "type": "heading",
                "text": heading_text,
                "level": 1,
                "centered": True,
            }
        )
        blocks.extend(content_blocks)
        blocks.append({"type": "page_break"})

    rendered_abbreviations_from_indices = False

    # Índices
    if "indices" in pre:
        rendered_abbreviations_from_indices = _indices_include_abbreviations(
            pre["indices"]
        )
        blocks.extend(
            _normalize_indices(
                pre["indices"],
                pre.get("abreviaturas"),
                document_source=data,
            )
        )

    # Abreviaturas fuera del bloque de indices
    if "abreviaturas" in pre and not rendered_abbreviations_from_indices:
        abbr = pre.get("abreviaturas")
        title = "INDICE DE ABREVIATURAS"
        if isinstance(abbr, dict):
            title = str(abbr.get("titulo", title) or title)
        elif isinstance(abbr, str) and abbr.strip():
            title = abbr.strip()
        blocks.extend(
            _build_abbreviations_blocks(
                title,
                abbr,
                document_source=data,
            )
        )

    # Tablas en preliminares (contenido extra)
    for item in pre.get("contenido", []):
        if isinstance(item, dict) and item.get("tipo") == "tabla":
            blocks.append({"type": "table", **item})

    # Introducción
    if "introduccion" in pre:
        intro = pre["introduccion"]
        blocks.append(
            {
                "type": "heading",
                "text": intro.get("titulo", "INTRODUCCIÓN"),
                "level": 1,
                "centered": True,
            }
        )
        if intro.get("_ai_content"):
            blocks.extend(_normalize_ai_content(intro["_ai_content"]))
        elif intro.get("texto") and not _looks_like_template_placeholder_text(intro.get("texto", "")):
            blocks.append({"type": "paragraph", "text": intro.get("texto", "")})
        blocks.append({"type": "page_break"})

    return blocks


def _normalize_indices(
    idx,
    abbreviations_source: Any = None,
    *,
    document_source: dict | None = None,
) -> List[Block]:
    """Normaliza índices en ambos formatos (dict simple o list detallada)."""
    blocks: List[Block] = []

    if isinstance(idx, dict):
        for k, title in idx.items():
            if k == "placeholder":
                continue
            if k == "abreviaturas":
                heading_title = title if isinstance(title, str) else ""
                blocks.extend(
                    _build_abbreviations_blocks(
                        heading_title,
                        abbreviations_source,
                        document_source=document_source,
                    )
                )
                continue

            entry = _FIELD_MAP.get(k)
            if entry:
                field_code, exclude = entry
                if field_code:
                    # Campo TOC de Word (contenido, tablas, figuras)
                    blocks.append(
                        {
                            "type": "toc_field",
                            "field_code": field_code,
                            "heading_text": title,
                            "exclude_from_toc": exclude,
                        }
                    )
                else:
                    # Sin campo TOC, pero con Heading 1 para aparecer en el indice
                    blocks.append(
                        {
                            "type": "heading",
                            "text": title,
                            "level": 1,
                            "centered": True,
                        }
                    )
                    blocks.append({"type": "page_break"})
            else:
                # Otra key custom
                blocks.append(
                    {
                        "type": "paragraph_centered",
                        "text": title,
                        "bold": True,
                        "size": 14,
                        "space_before": 12,
                        "space_after": 12,
                    }
                )
                blocks.append({"type": "page_break"})

    elif isinstance(idx, list):
        for item in idx:
            titulo = item.get("titulo", "")

            if "ABREVIATURAS" in str(titulo).upper():
                source = abbreviations_source or item
                heading_title = titulo if isinstance(titulo, str) else ""
                blocks.extend(
                    _build_abbreviations_blocks(
                        heading_title,
                        source,
                        document_source=document_source,
                    )
                )
                continue

            entry = _LIST_FIELD_MAP.get(titulo)
            if entry:
                field_code, exclude = entry
                if field_code:
                    blocks.append(
                        {
                            "type": "toc_field",
                            "field_code": field_code,
                            "heading_text": titulo,
                            "exclude_from_toc": exclude,
                        }
                    )
                else:
                    # Sin campo TOC, pero con Heading 1 para aparecer en el indice
                    blocks.append(
                        {
                            "type": "heading",
                            "text": titulo,
                            "level": 1,
                            "centered": True,
                        }
                    )
                    if "items" in item:
                        blocks.append(
                            {
                                "type": "index_items",
                                "items": item["items"],
                            }
                        )
                    blocks.append({"type": "page_break"})
            else:
                blocks.append(
                    {
                        "type": "paragraph_centered",
                        "text": titulo,
                        "bold": True,
                        "size": 14,
                        "space_before": 12,
                        "space_after": 12,
                    }
                )
                if "items" in item:
                    blocks.append(
                        {
                            "type": "index_items",
                            "items": item["items"],
                        }
                    )
                blocks.append({"type": "page_break"})

    return blocks


# ═══════════════════════════════════════════════════════════════
# CUERPO (capítulos)
# ═══════════════════════════════════════════════════════════════


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [text for item in value if (text := _clean_text(item))]
    if isinstance(value, str):
        return [line.strip(" -•\t") for line in value.splitlines() if line.strip(" -•\t")]
    return []


def _is_unac_project_document(data: dict | None) -> bool:
    """True para documentos UNAC que usan el pipeline de datos estructurados
    (matriz de consistencia + operacionalizacion de variables): Proyecto e
    Informe de Tesis. Sin esto, las tablas 3.1/3.2 y los bloques de
    problema/objetivos/hipotesis recuperados desde los datos del proyecto
    quedan vacios para cualquier formato que no sea "unac-proyecto".
    """
    if not isinstance(data, dict):
        return False
    format_id = str(data.get("_meta", {}).get("id", "") or "")
    return format_id.startswith("unac-proyecto") or format_id.startswith("unac-informe")


def _document_values(data: dict | None) -> dict:
    if not isinstance(data, dict):
        return {}
    return _as_dict(data.get("values"))


def _matrix_data(data: dict | None) -> dict:
    if not isinstance(data, dict):
        return {}
    values = _document_values(data)
    return _as_dict(data.get("matriz_consistencia") or values.get("matriz_consistencia"))


def _matrix_value(data: dict, flat_key: str, group: str = "", nested_key: str = "") -> str:
    matriz = _matrix_data(data)
    values = _document_values(data)
    if flat := _clean_text(matriz.get(flat_key)):
        return flat
    if flat_value := _clean_text(values.get(flat_key)):
        return flat_value
    if group and nested_key:
        nested = _as_dict(matriz.get(group))
        if nested_value := _clean_text(nested.get(nested_key)):
            return nested_value
    return ""


def _matrix_list(data: dict, flat_key: str, group: str = "", nested_key: str = "") -> list[str]:
    matriz = _matrix_data(data)
    values = _document_values(data)
    values_list = _clean_list(values.get(flat_key))
    direct = _clean_list(matriz.get(flat_key))
    if direct:
        return direct
    if values_list:
        return values_list
    if group and nested_key:
        nested = _as_dict(matriz.get(group))
        return _clean_list(nested.get(nested_key))
    return []


def _matrix_variable_name(data: dict, kind: str) -> str:
    matriz = _matrix_data(data)
    values = _document_values(data)
    flat_key = f"variable_{kind}"
    if text := _clean_text(matriz.get(flat_key) or values.get(flat_key)):
        return text
    if kind == "independiente" and (text := _clean_text(values.get("vi"))):
        return text
    if kind == "dependiente" and (text := _clean_text(values.get("vd"))):
        return text
    variables = _as_dict(matriz.get("variables"))
    variable = _as_dict(variables.get(kind))
    return _clean_text(variable.get("nombre"))


def _matrix_dimensions(data: dict, kind: str) -> list[str]:
    matriz = _matrix_data(data)
    values = _document_values(data)
    flat_key = f"dimensiones_variable_{kind}"
    direct = _clean_list(matriz.get(flat_key)) or _clean_list(values.get(flat_key))
    if direct:
        return direct
    variables = _as_dict(matriz.get("variables"))
    variable = _as_dict(variables.get(kind))
    return _clean_list(variable.get("dimensiones"))


def _operationalization_data(data: dict, kind: str) -> dict:
    values = _document_values(data)
    aliases = (
        ("operacionalizacion_vi", "operacionalizacion_variable_independiente")
        if kind == "independiente"
        else ("operacionalizacion_vd", "operacionalizacion_variable_dependiente")
    )
    for key in aliases:
        found = _as_dict(data.get(key) or values.get(key))
        if found:
            return found
    return {}


def _operationalization_rows(data: dict, kind: str) -> list[dict]:
    raw = _operationalization_data(data, kind).get("filas")
    if not isinstance(raw, list):
        raw = _operationalization_data(data, kind).get("rows")
    rows = [row for row in raw if isinstance(row, dict)] if isinstance(raw, list) else []
    if rows:
        return rows
    return [{"dimension": dimension} for dimension in _matrix_dimensions(data, kind)]


def _has_project_matrix_content(data: dict, *keys: str) -> bool:
    if not _is_unac_project_document(data):
        return False
    nested_aliases = {
        "problema_general": ("problemas", "general"),
        "problemas_especificos": ("problemas", "especificos"),
        "objetivo_general": ("objetivos", "general"),
        "objetivos_especificos": ("objetivos", "especificos"),
        "hipotesis_general": ("hipotesis", "general"),
        "hipotesis_especificas": ("hipotesis", "especificos"),
    }
    for key in keys:
        group, nested_key = nested_aliases.get(key, ("", ""))
        if _matrix_value(data, key, group, nested_key) or _matrix_list(data, key, group, nested_key):
            return True
    return False


def _make_bullet_paragraphs(items: list[str]) -> list[Block]:
    return [{"type": "paragraph", "text": f"• {item}"} for item in items if item]


def _normalize_problem_formulation(data: dict) -> list[Block]:
    if not _has_project_matrix_content(data, "problema_general", "problemas_especificos"):
        return []
    blocks: list[Block] = []
    general = _matrix_value(data, "problema_general", "problemas", "general")
    specific = _matrix_list(data, "problemas_especificos", "problemas", "especificos")
    if general:
        blocks.append({"type": "paragraph_bold", "text": "Problema general"})
        blocks.append({"type": "paragraph", "text": general})
    if specific:
        blocks.append({"type": "paragraph_bold", "text": "Problemas específicos"})
        blocks.extend(_make_bullet_paragraphs(specific))
    return blocks


def _normalize_objectives(data: dict) -> list[Block]:
    if not _has_project_matrix_content(data, "objetivo_general", "objetivos_especificos"):
        return []
    blocks: list[Block] = []
    general = _matrix_value(data, "objetivo_general", "objetivos", "general")
    specific = _matrix_list(data, "objetivos_especificos", "objetivos", "especificos")
    if general:
        blocks.append({"type": "paragraph_bold", "text": "Objetivo general"})
        blocks.append({"type": "paragraph", "text": general})
    if specific:
        blocks.append({"type": "paragraph_bold", "text": "Objetivos específicos"})
        blocks.extend(_make_bullet_paragraphs(specific))
    return blocks


def _normalize_hypotheses(data: dict) -> list[Block]:
    if not _has_project_matrix_content(data, "hipotesis_general", "hipotesis_especificas"):
        return []
    blocks: list[Block] = []
    general = _matrix_value(data, "hipotesis_general", "hipotesis", "general")
    specific = _matrix_list(data, "hipotesis_especificas", "hipotesis", "especificos")
    if general:
        blocks.append({"type": "paragraph_bold", "text": "Hipótesis general"})
        blocks.append({"type": "paragraph", "text": general})
    if specific:
        blocks.append({"type": "paragraph_bold", "text": "Hipótesis específicas"})
        blocks.extend(_make_bullet_paragraphs(specific))
    return blocks


def _technique_cell(row: dict, *, dependent: bool) -> str:
    tecnica = _clean_text(row.get("tecnica") or row.get("metodo_tecnica") or row.get("metodoTecnica"))
    instrumento = _clean_text(
        row.get("instrumento")
        or row.get("tecnica_instrumentos")
        or row.get("tecnicaInstrumentos")
    )
    if tecnica and instrumento and tecnica != instrumento:
        return f"Técnica:\n{tecnica}\n\nInstrumento:\n{instrumento}"
    if dependent and tecnica:
        return f"Método/Técnica:\n{tecnica}"
    if tecnica:
        return f"Técnica:\n{tecnica}"
    if instrumento:
        return f"Instrumento:\n{instrumento}"
    return ""


def _operationalization_table(data: dict, *, kind: str) -> Block | None:
    op = _operationalization_data(data, kind)
    fallback_variable = _matrix_variable_name(data, kind)
    variable = _clean_text(op.get("variable")) or fallback_variable
    definition = _clean_text(op.get("definicion_conceptual") or op.get("definicionConceptual"))
    operational = _clean_text(op.get("definicion_operacional") or op.get("definicionOperacional"))
    rows = _operationalization_rows(data, kind)
    if not variable and not definition and not operational and not rows:
        return None

    is_dependent = kind == "dependiente"
    headers = [
        "VARIABLE" if is_dependent else "VARIABLES",
        "DEFINICIÓN CONCEPTUAL",
        "DEFINICIÓN OPERACIONAL",
        "DIMENSIONES",
        "INDICADORES",
        "ÍNDICE",
        "MÉTODO Y TÉCNICA" if is_dependent else "TÉCNICA E INSTRUMENTOS",
    ]
    label = "Variable Dependiente" if is_dependent else "Variable Independiente"
    table_rows: list[list[str]] = []
    for index, row in enumerate(rows or [{}]):
        table_rows.append(
            [
                f"{label}:\n{variable}" if index == 0 else "",
                definition if index == 0 else "",
                operational if index == 0 else "",
                _clean_text(row.get("dimension")),
                _clean_text(row.get("indicador")),
                _clean_text(row.get("indice")),
                _technique_cell(row, dependent=is_dependent),
            ]
        )

    row_count = max(1, len(table_rows))
    title = (
        "Tabla 3.2 Operacionalización de variable dependiente"
        if is_dependent
        else "Tabla 3.1 Operacionalización de variable independiente"
    )
    return {
        "type": "table",
        "titulo": title,
        "orientacion": "landscape",
        "encabezados": headers,
        "filas": table_rows,
        "celdas_fusionadas": [
            {"fila": 0, "col": 0, "filas_span": row_count},
            {"fila": 0, "col": 1, "filas_span": row_count},
            {"fila": 0, "col": 2, "filas_span": row_count},
        ],
        "estilo": {
            "encabezado_color": "D9D9D9",
            "fuente_size": 8,
        },
    }


def _normalize_operationalization_section(data: dict) -> list[Block]:
    if not _is_unac_project_document(data):
        return []
    tables = [
        table
        for table in (
            _operationalization_table(data, kind="independiente"),
            _operationalization_table(data, kind="dependiente"),
        )
        if table
    ]
    if not tables:
        return []
    if len(tables) == 1:
        return tables

    first = dict(tables[0])
    second = dict(tables[1])
    # 3.1 must stay immediately below heading 3.2 and 3.2 must start on a
    # new horizontal page; keep landscape active between both tables.
    first["restore_portrait"] = False
    return [first, {"type": "page_break"}, second]


def _normalize_project_structured_section(data: dict | None, item: dict) -> list[Block]:
    # Keep a narrow fallback only for UNAC 3.2 operacionalizacion:
    # if AI did not provide structured tables, recover 3.1/3.2 from
    # operationalization values so those required tables are not lost.
    if not _is_unac_project_document(data):
        return []

    title = _norm_upper(item.get("texto", ""))
    if "OPERACIONALIZACION" in title:
        ai_content = item.get("_ai_content")
        if isinstance(ai_content, list) and any(
            isinstance(block, dict) and str(block.get("tipo", "")).strip().lower() == "tabla"
            for block in ai_content
        ):
            return []
        return _normalize_operationalization_section(data or {})

    if "PROBLEMA GENERAL" in title:
        general = _matrix_value(data, "problema_general", "problemas", "general")
        if general:
            return [{"type": "paragraph", "text": general}]
    
    if "PROBLEMA ESPEC" in title or "PROBLEMAS ESPEC" in title:
        specific = _matrix_list(data, "problemas_especificos", "problemas", "especificos")
        if specific:
            return _make_bullet_paragraphs(specific)

    if "OBJETIVO GENERAL" in title:
        general = _matrix_value(data, "objetivo_general", "objetivos", "general")
        if general:
            return [{"type": "paragraph", "text": general}]
            
    if "OBJETIVO ESPEC" in title or "OBJETIVOS ESPEC" in title:
        specific = _matrix_list(data, "objetivos_especificos", "objetivos", "especificos")
        if specific:
            return _make_bullet_paragraphs(specific)
            
    if "HIPÓTESIS GENERAL" in title or "HIPOTESIS GENERAL" in title:
        general = _matrix_value(data, "hipotesis_general", "hipotesis", "general")
        if general:
            return [{"type": "paragraph", "text": general}]
            
    if "HIPÓTESIS ESPEC" in title or "HIPOTESIS ESPEC" in title:
        specific = _matrix_list(data, "hipotesis_especificas", "hipotesis", "especificos")
        if specific:
            return _make_bullet_paragraphs(specific)

    return []


def _normalize_cuerpo(data: dict) -> List[Block]:
    cuerpo = data.get("cuerpo", [])
    if not cuerpo:
        return []

    blocks: List[Block] = []

    for index, cap in enumerate(cuerpo):
        # Salto de pagina antes de cada capitulo (excepto el primero).
        # Evita insertar un salto justo despues del titulo.
        chapter_title = str(cap.get("titulo", "") or "")
        if index > 0:
            blocks.append({"type": "page_break"})

        chapter_items = cap.get("contenido", []) if isinstance(cap.get("contenido"), list) else []
        has_landscape_table = any(
            isinstance(item, dict)
            and str(item.get("tipo") or "").strip().lower() == "tabla"
            and str(item.get("orientacion") or "").strip().lower() == "landscape"
            for item in chapter_items
        )
        if has_landscape_table:
            # Keep chapter heading and its first landscape table in the same
            # landscape section to avoid blank portrait pages before the table.
            blocks.append({"type": "section_switch", "orientation": "landscape"})

        # Título del capítulo
        blocks.append(
            {
                "type": "heading",
                "text": chapter_title,
                "level": 1,
                "centered": False,
                "space_after": 12,
            }
        )

        # Nota del capítulo
        if "nota_capitulo" in cap:
            blocks.append({"type": "note", "text": cap["nota_capitulo"]})

        # Contenido del capítulo
        chapter_has_ai = bool(cap.get("_ai_content")) or any(
            isinstance(item, dict) and item.get("_ai_content")
            for item in cap.get("contenido", [])
        )
        for item in cap.get("contenido", []):
            if (
                chapter_has_ai
                and isinstance(item, dict)
                and item.get("tipo") in {"tabla", "figura"}
                and not item.get("_ai_generated")
            ):
                continue
            blocks.extend(_normalize_content_item(item, data))

        # Ejemplos APA a nivel de capítulo
        if "ejemplos_apa" in cap:
            blocks.append(
                {
                    "type": "apa_examples",
                    "ejemplos": cap["ejemplos_apa"],
                }
            )

    return blocks


def _normalize_content_item(
    item,
    document_data: dict | None = None,
    parent_item: dict | None = None,
) -> List[Block]:
    """Normaliza un item de contenido (dentro de cuerpo o anexos).

    Soporta:
    - str → párrafo
    - dict con tipo='parrafo' → párrafo (desde IA estructurada)
    - dict con tipo='tabla' → tabla canónica (con landscape automático)
    - dict con tipo='figura' → caption + imagen placeholder
    - dict con texto → subtítulo + content_block
    """
    blocks: List[Block] = []

    # String simple
    if isinstance(item, str):
        blocks.append({"type": "paragraph", "text": item})
        return blocks

    if not isinstance(item, dict):
        return blocks

    # Párrafo estructurado desde IA (tipo == "parrafo")
    if item.get("tipo") == "parrafo":
        texto = item.get("texto", "")
        if texto:
            normalized_text = texto.replace("\r\n", "\n").replace("\r", "\n")
            lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]
            if not lines:
                return blocks
            
            if parent_item and "texto" in parent_item:
                parent_title = _norm_upper(_MARKDOWN_BOLD_RE.sub(r"\2", str(parent_item["texto"])).strip())
                first_line_norm = _norm_upper(_MARKDOWN_BOLD_RE.sub(r"\2", lines[0]).strip()).lstrip("# ").strip()
                if first_line_norm == parent_title or first_line_norm.startswith(parent_title + " "):
                    lines = lines[1:]
                    if not lines:
                        return blocks

            first_line_clean = _MARKDOWN_BOLD_RE.sub(r"\2", lines[0]).strip()
            if first_line_clean.startswith("###"):
                first_line_clean = first_line_clean.lstrip("#").strip()
            
            heading_match = _AI_LEVEL3_HEADING_RE.match(first_line_clean)
            if heading_match and not _MATH_FORMULA_RE.search(heading_match.group(2)):
                blocks.append(
                    {
                        "type": "heading",
                        "text": f"{heading_match.group(1)} {heading_match.group(2)}".strip(),
                        "level": 3,
                        "centered": False,
                        "space_before": 8,
                        "space_after": 8,
                    }
                )
                remainder = " ".join(lines[1:]).strip()
                if remainder:
                    blocks.append({"type": "paragraph", "text": remainder})
            else:
                blocks.append({"type": "paragraph", "text": " ".join(lines)})
        return blocks

    # Figura sugerida por IA (tipo == "figura")
    if item.get("tipo") == "figura":
        caption = str(item.get("caption") or "").strip()
        title = str(item.get("titulo") or "").strip() or _strip_figure_caption_prefix(caption)
        ruta = item.get("ruta_placeholder") or item.get("ruta", "")
        if ruta and ruta.lower() != "placeholder":
            # Heredar nota de instrucción detallada del padre si la figura no tiene una propia
            nota_actual = item.get("nota") or item.get("note")
            if not nota_actual and parent_item:
                nota_actual = (
                    parent_item.get("nota")
                    or parent_item.get("note")
                    or parent_item.get("instruccion_detallada")
                )

            # Si aún no hay nota, generar una genérica azul para guiar al estudiante.
            # Esto garantiza que todas las figuras (incluidas las de 2.2 Bases Teóricas)
            # siempre tengan una instrucción visible debajo de la imagen.
            if not nota_actual:
                figure_label = title or caption or "la figura"
                nota_actual = (
                    f"Guía para elaborar la figura: Diseña un esquema gráfico profesional titulado \"{figure_label}\" "
                    "que sirva como soporte visual y académico del desarrollo de esta sección. El diagrama debe "
                    "estructurarse mediante bloques relacionales, diagramas de flujo o mapas conceptuales según "
                    "corresponda a la naturaleza del subtema. Define con claridad las variables clave, los procesos "
                    "involucrados o la arquitectura del sistema. Conecta los elementos conceptuales con líneas "
                    "y flechas direccionales que muestren la secuencia lógica y el sentido de las relaciones. "
                    "Utiliza formas geométricas consistentes (rectángulos, óvalos o círculos) y un esquema de colores "
                    "sobrio y contrastante para mejorar la legibilidad. Asegura que todos los textos, variables y "
                    "rótulos de la figura utilicen una fuente Arial de 10 puntos sin negritas ni marcadores adicionales. "
                    "En la parte inferior de la figura, incluye siempre la fuente correspondiente en formato APA "
                    "estándar (por ejemplo, 'Fuente: Elaboración propia' o la cita del autor correspondiente) "
                    "y una nota técnica descriptiva que explique brevemente el contenido de la figura y su "
                    "vinculación directa con el sustento analítico del proyecto."
                )

            # Heredar color o forzar azul si se heredó una nota
            color_actual = item.get("nota_color") or item.get("note_color")
            if not color_actual and parent_item:
                color_actual = parent_item.get("nota_color") or parent_item.get("note_color")
            if nota_actual and not color_actual:
                color_actual = "0000FF"  # Azul institucional para notas

            blocks.append(
                {
                    "type": "image",
                    "titulo": title,
                    "ruta": ruta,
                    "fuente": item.get("fuente", "Elaboración propia"),
                    "ancho_cm": item.get("ancho_cm"),
                    "placeholder": True,
                    "nota": nota_actual,
                    "nota_color": color_actual,
                    "placeholder_text": item.get("placeholder_text") or item.get("texto_placeholder"),
                }
            )
        elif caption:
            blocks.append({"type": "paragraph", "text": caption})
        return blocks

    # Tabla canónica directa (tipo == "tabla" a nivel de contenido[])
    # The table renderer (table.py) handles landscape internally via
    # switch_to_landscape/switch_to_portrait, so we only need to resolve
    # "auto" orientation here and pass the correct value.
    if item.get("tipo") == "tabla":
        if _looks_like_placeholder_table_data(item) or _looks_like_template_example_title(item.get("titulo")):
            return blocks
        orientacion = (item.get("orientacion") or "auto").strip().lower()
        if orientacion == "auto":
            headers = item.get("encabezados") or item.get("columnas", [])
            if isinstance(headers, list) and len(headers) > 5:
                item["orientacion"] = "landscape"
            else:
                item["orientacion"] = "portrait"
        elif orientacion in ("horizontal",):
            item["orientacion"] = "landscape"
        elif orientacion in ("vertical",):
            item["orientacion"] = "portrait"
        blocks.append({"type": "table", **item})
        return blocks

    # Subtítulo
    if "texto" in item:
        _subtitulo_text = str(item["texto"] or "").strip()
        # Limpiar marcadores Markdown (e.g. **2.2.1 Título** → 2.2.1 Título,
        # ### 2.2.1 Título → 2.2.1 Título)
        _subtitulo_clean = _MARKDOWN_BOLD_RE.sub(r"\2", _subtitulo_text).strip()
        if _subtitulo_clean.startswith("###"):
            _subtitulo_clean = _subtitulo_clean.lstrip("#").strip()
        _heading_match = _AI_LEVEL3_HEADING_RE.match(_subtitulo_clean)
        if _heading_match and not _MATH_FORMULA_RE.search(_heading_match.group(2)):
            # e.g. "2.2.1 Título" → Heading 3 formal (aparece en TOC)
            blocks.append(
                {
                    "type": "heading",
                    "text": f"{_heading_match.group(1)} {_heading_match.group(2)}".strip(),
                    "level": 3,
                    "centered": False,
                    "space_before": 8,
                    "space_after": 8,
                }
            )
        elif _MATH_FORMULA_RE.search(_subtitulo_clean) or not re.match(r"^\d+\.", _subtitulo_clean):
            # Si el texto parece una fórmula matemática (p.ej. "D = MTBF / (MTBF + MTTR)")
            # o no tiene un prefijo numérico (p.ej. "N.N"), emitirlo como párrafo para que
            # NO aparezca en el índice de contenidos (TOC) de Word.
            blocks.append({"type": "paragraph", "text": _subtitulo_clean or _subtitulo_text})
        else:
            blocks.append(
                {
                    "type": "black_heading",
                    "text": _subtitulo_clean or _subtitulo_text,
                    "level": 2,
                    "size": 12,
                    "centered": False,
                }
            )

    special_blocks = _normalize_project_structured_section(document_data, item)
    if special_blocks:
        blocks.extend(special_blocks)
        return blocks

    ai_content = item.get("_ai_content")
    if ai_content:
        blocks.extend(_normalize_ai_content(ai_content, parent_item=item))
        return blocks

    # Content block compartido (notas, párrafos, tablas, imágenes)
    blocks.extend(_normalize_content_block(item))

    return blocks


def _normalize_ai_content(
    content: Any,
    parent_item: dict | None = None,
) -> List[Block]:
    """Render AI-injected content as the source of truth for a node."""
    if isinstance(content, str):
        normalized_text = content.replace("\r\n", "\n").replace("\r", "\n")
        parts = [
            part.strip()
            for part in re.split(
                r"\n\s*\n",
                normalized_text,
            )
            if part and part.strip()
        ]
        blocks: List[Block] = []
        for part in parts:
            lines = [line.strip() for line in part.split("\n") if line.strip()]
            if not lines:
                continue

            if parent_item and "texto" in parent_item:
                parent_title = _norm_upper(_MARKDOWN_BOLD_RE.sub(r"\2", str(parent_item["texto"])).strip())
                first_line_norm = _norm_upper(_MARKDOWN_BOLD_RE.sub(r"\2", lines[0]).strip()).lstrip("# ").strip()
                if first_line_norm == parent_title or first_line_norm.startswith(parent_title + " "):
                    lines = lines[1:]
                    if not lines:
                        continue

            # Limpiar marcadores Markdown (e.g. **2.2.1 Título** → 2.2.1 Título)
            first_line_clean = _MARKDOWN_BOLD_RE.sub(r"\2", lines[0]).strip()
            if first_line_clean.startswith("###"):
                first_line_clean = first_line_clean.lstrip("#").strip()
            heading_match = _AI_LEVEL3_HEADING_RE.match(first_line_clean)
            if heading_match and not _MATH_FORMULA_RE.search(heading_match.group(2)):
                blocks.append(
                    {
                        "type": "heading",
                        "text": f"{heading_match.group(1)} {heading_match.group(2)}".strip(),
                        "level": 3,
                        "centered": False,
                        "space_before": 8,
                        "space_after": 8,
                    }
                )
                remainder = " ".join(lines[1:]).strip()
                if remainder:
                    blocks.append({"type": "paragraph", "text": remainder})
                continue

            blocks.append({"type": "paragraph", "text": " ".join(lines)})
        return blocks

    if isinstance(content, dict):
        return _normalize_content_item(content, parent_item=parent_item)

    if not isinstance(content, list):
        return []

    blocks: List[Block] = []
    for item in content:
        blocks.extend(_normalize_content_item(item, parent_item=parent_item))
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
        table_title = item.get("tabla_titulo") or item.get("titulo")
        if not _looks_like_template_example_title(table_title) and not _looks_like_placeholder_table_data(item["tabla"]):
            blocks.append(
                {
                    "type": "legacy_table",
                    "tabla": item["tabla"],
                    "titulo": item.get("tabla_titulo"),
                    "nota": item.get("tabla_nota"),
                }
            )

    # tablas_especiales (array de tablas legacy)
    if "tablas_especiales" in item:
        for te in item["tablas_especiales"]:
            if isinstance(te, dict):
                if _looks_like_template_example_title(te.get("titulo")) or _looks_like_placeholder_table_data(te):
                    continue
                blocks.append(
                    {
                        "type": "legacy_table",
                        "tabla": te,
                        "titulo": te.get("titulo"),
                    }
                )

    # Tabla canónica (tabla_data)
    if "tabla_data" in item and isinstance(item["tabla_data"], dict):
        if not _looks_like_placeholder_table_data(item["tabla_data"]):
            blocks.append({"type": "table", **item["tabla_data"]})

    # Imágenes
    if "imagenes" in item:
        for img in item["imagenes"]:
            ruta = str(img.get("ruta", "") or "").strip()
            if (
                not ruta
                or ruta.lower() == "placeholder"
                or _looks_like_template_example_image(img)
            ):
                continue
            blocks.append(
                {
                    "type": "image",
                    "titulo": img.get("titulo", ""),
                    "ruta": ruta,
                    "fuente": img.get("fuente", ""),
                    "nota": img.get("nota") or img.get("note"),
                    "placeholder_text": img.get("placeholder_text") or img.get("texto_placeholder"),
                }
            )

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

    blocks: List[Block] = [{"type": "page_break"}]
    ref = fin["referencias"]

    if isinstance(ref, str):
        blocks.append(
            {
                "type": "heading",
                "text": ref,
                "level": 1,
                "centered": False,
            }
        )
    else:
        blocks.append(
            {
                "type": "heading",
                "text": ref.get("titulo", "REFERENCIAS BIBLIOGRÁFICAS"),
                "level": 1,
                "centered": False,
            }
        )
        ai_content = ref.get("_ai_content")
        if ai_content:
            blocks.extend(_normalize_ai_content(ai_content))
            blocks.append({"type": "page_break"})
            return blocks
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
        blocks.append(
            {
                "type": "heading",
                "text": anx,
                "level": 1,
                "centered": False,
            }
        )
    else:
        blocks.append(
            {
                "type": "heading",
                "text": anx.get("titulo_seccion", "ANEXOS"),
                "level": 1,
                "centered": False,
            }
        )

        for position, item in enumerate(lista, start=1):
            # String simple
            if isinstance(item, str):
                blocks.append({"type": "paragraph", "text": item})
                continue

            if not isinstance(item, dict):
                continue

            titulo_anexo = _resolve_annex_heading_text(item, position)
            if titulo_anexo:
                blocks.append(
                    {
                        "type": "paragraph_bold",
                        "text": titulo_anexo,
                        "size": 13,
                    }
                )

            # Tabla canónica directa
            if item.get("tipo") == "tabla":
                table_block = dict(item)
                table_block.pop("titulo", None)
                blocks.extend(_normalize_annex_blocks([{"type": "table", **table_block}]))
                continue

            ai_content = item.get("_ai_content")
            if ai_content:
                if "matriz" in titulo_anexo.lower():
                    rendered_matriz = True
                blocks.extend(_normalize_annex_content(ai_content))
                continue

            is_matriz = "matriz" in titulo_anexo.lower()
            if is_matriz and "matriz_consistencia" in data:
                blocks.append(
                    {
                        "type": "matriz",
                        "data": data["matriz_consistencia"],
                        "landscape": False,
                    }
                )
                rendered_matriz = True
                continue

            # Content block normal del anexo
            blocks.extend(_normalize_annex_blocks(_normalize_content_block(item)))

    # Restore portrait
    if first_is_matriz:
        blocks.append({"type": "section_switch", "orientation": "portrait"})

    # Fallback: matriz como último anexo si no estaba en la lista
    if "matriz_consistencia" in data and not rendered_matriz:
        blocks.append({"type": "section_switch", "orientation": "landscape"})
        blocks.append(
            {
                "type": "heading",
                "text": "ANEXOS",
                "level": 1,
                "centered": False,
            }
        )
        blocks.append(
            {
                "type": "paragraph_bold",
                "text": "Anexo 1: Matriz de Consistencia",
                "size": 13,
            }
        )
        blocks.append(
            {
                "type": "matriz",
                "data": data["matriz_consistencia"],
                "landscape": False,
            }
        )
        blocks.append({"type": "section_switch", "orientation": "portrait"})

    return blocks
