"""
Archivo: app/modules/generation/preprocessor.py
Proposito:
- Procesa datos JSON antes de la generacion de documentos.

Responsabilidades:
- Eliminar claves de instruccion/guia recursivamente.
- Fusionar valores del usuario en placeholders.
- Inyectar contenido IA en las secciones correspondientes.
- Gestionar archivos JSON temporales.
No hace:
- No genera documentos DOCX/PDF directamente.
- No define rutas HTTP.

Entradas/Salidas:
- Entradas: datos JSON crudos, valores de usuario, contenido IA.
- Salidas: datos JSON procesados listos para el generador.

Dependencias:
- Ninguna externa (solo tipos de Python estandar).

Puntos de extension:
- Agregar nuevas claves a EXCLUDED_KEYS si se crean nuevas guias.
- Agregar nuevos patrones de placeholder en merge_values.

Donde tocar si falla:
- Si un campo de guia no se limpia, agregarlo a EXCLUDED_KEYS.
- Si un placeholder no se reemplaza, agregar patron en merge_values.
"""

from __future__ import annotations

import re
import unicodedata
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


# Keys that should NOT appear in the final document
EXCLUDED_KEYS: Set[str] = frozenset(
    {
        "nota",
        "nota_capitulo",
        "nota_general",
        "notas",
        "instruccion",
        "instrucciones",
        "instruccion_detallada",
        "guia",
        "guias",
        "ejemplo",
        "ejemplos",
        "comentario",
        "comentarios",
        "observacion",
        "observaciones",
        "placeholder",
        "tipo_vista",
        "vista_previa",
    }
)

_FENCE_RE = re.compile(r"```[\s\S]*?```")
_MARKDOWN_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_INSERTAR_RE = re.compile(r"\[\s*insertar[^\]]*\]", re.IGNORECASE)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_TABLA_PLACEHOLDER_RE = re.compile(r"^\s*tabla\s+de\s+ejemplo\b", re.IGNORECASE)
_PATH_SEPARATOR_RE = re.compile(r"\s*/\s*")
_WHITESPACE_RE = re.compile(r"\s+")
_ANNEX_PREFIX_RE = re.compile(r"^(ANEXO\s+\d+)\b")


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_upper(text: str) -> str:
    return _strip_accents(text or "").upper().strip()


def _normalize_path(path: str) -> str:
    normalized = _strip_accents(str(path or ""))
    normalized = normalized.replace("\\", "/")
    normalized = _PATH_SEPARATOR_RE.sub("/", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.upper().strip().strip("/")


def _is_index_path(path: str) -> bool:
    normalized = _normalize_path(path)
    if not normalized:
        return False
    if "ABREVIATURAS" in normalized:
        return False
    parts = [part.strip() for part in normalized.split("/") if part.strip()]
    return any(part.startswith("INDICE") for part in parts)


def _collect_selected_paths(
    selected_sections: List[Dict[str, Any]] | List[str] | None,
) -> Set[str]:
    if not isinstance(selected_sections, list):
        return set()

    selected_paths: Set[str] = set()
    for item in selected_sections:
        if isinstance(item, str):
            normalized = _normalize_path(item)
            if normalized:
                selected_paths.add(normalized)
            continue
        if not isinstance(item, dict):
            continue
        for key in ("section_path", "sectionPath", "path", "section_id", "sectionId", "id"):
            normalized = _normalize_path(str(item.get(key) or ""))
            if normalized:
                selected_paths.add(normalized)
    return selected_paths


def _path_selected(path: str, selected_paths: Set[str]) -> bool:
    if not selected_paths:
        return True
    normalized = _normalize_path(path)
    if not normalized:
        return False
    for selected in selected_paths:
        if normalized == selected:
            return True
        if normalized.startswith(f"{selected}/"):
            return True
        if selected.startswith(f"{normalized}/"):
            return True
    return False


def _selected_token_present(selected_paths: Set[str], token: str) -> bool:
    normalized_token = _normalize_path(token)
    if not normalized_token:
        return False
    return any(normalized_token in selected for selected in selected_paths)


def _looks_like_placeholder(value: str) -> bool:
    if not value or not value.strip():
        return True

    normalized = _norm_upper(value)
    if "[" in value and "]" in value:
        return True
    if "{" in value and "}" in value:
        return True
    if "<" in value and ">" in value:
        return True

    placeholder_markers = (
        "TITULO DEL PROYECTO",
        "TITULO COMPLETO DEL TRABAJO",
        "ESCRIBA AQUI",
        "NOMBRE DE LA",
        "NOMBRES Y APELLIDOS",
        "TITULO DE LA TESIS",
    )
    return any(marker in normalized for marker in placeholder_markers)


def _pick_first_nonempty(values: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        raw = values.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text:
            return text
    return ""


def _apply_cover_fallbacks(data: Dict[str, Any], values: Dict[str, Any]) -> None:
    caratula = data.get("caratula")
    if not isinstance(caratula, dict):
        return
    document_id = str((data.get("_meta") or {}).get("id") or "").strip().lower()
    is_unac_project = document_id.startswith("unac-proyecto")

    # 1. Autor(es)
    autores = []
    for prefix in ("autor1", "autor2"):
        nombre = str(values.get(f"{prefix}_nombres", "") or "").strip()
        if nombre:
            autores.append(nombre)
    if autores:
        caratula["autores"] = autores

    # 2. Asesor
    asesor_nombre = str(values.get("asesor_nombres", "") or "").strip()
    if asesor_nombre:
        caratula["asesor"] = asesor_nombre

    # 3. Línea de investigación
    linea = str(values.get("linea_investigacion", "") or "").strip()
    if linea:
        caratula["linea_investigacion"] = linea

    # 4. Título
    project_obj = values.get("project")
    title_value = _pick_first_nonempty(
        values,
        ["titulo", "title", "project_title", "projectTitle"],
    )
    if not title_value and isinstance(project_obj, dict):
        nested_title = project_obj.get("title")
        if nested_title is not None and str(nested_title).strip():
            title_value = str(nested_title).strip()
    if title_value:
        caratula["titulo"] = title_value

    # 5. Año/Lugar
    lugar = str(values.get("lugar_caratula", "") or "").strip()
    anio = str(values.get("anio", "") or "").strip()
    if lugar or anio:
        parts = [p for p in (lugar, anio) if p]
        caratula["lugar"] = ", ".join(parts)

    fallback_map = {
        "facultad": ["facultad", "faculty"],
        "escuela": ["escuela", "school"],
        "autor_valor": ["autor_valor", "autor", "author"],
        "asesor_valor": ["asesor_valor", "asesor", "advisor"],
    }
    for cover_key, candidates in fallback_map.items():
        if cover_key in caratula and not _looks_like_placeholder(
            str(caratula[cover_key])
        ):
            continue  # Already filled by user directly or by new logic
        picked = _pick_first_nonempty(values, candidates)
        if picked:
            caratula[cover_key] = picked

    # New institutional direct mappings
    for dest, src in [
        ("universidad", "universidad"),
        ("escuela", "escuela"),
        ("tipo_documento", "tipo_documento"),
        ("frase_grado", "frase_grado"),
        ("titulo", "titulo"),
        ("titulo_investigacion", "titulo"),
        ("autor1_nombres", "autor1_nombres"),
        ("asesor_nombres", "asesor_nombres"),
        ("linea_investigacion", "linea_investigacion"),
        ("anio", "anio"),
        ("lugar", "lugar_caratula"),
    ]:
        val = str(values.get(src, "") or "").strip()
        if val:
            caratula[dest] = val
            # ALSO INJECT AT ROOT LEVEL FOR FLEXIBILITY
            data[dest] = val

    if is_unac_project:
        fixed_project_cover = {
            "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
            "facultad": "ESCUELA DE POSGRADO",
            "escuela": "UNIDAD DE POSGRADO DE LA FACULTAD DE INGENIERÍA MECÁNICA Y DE ENERGÍA",
            "tipo_documento": "PROYECTO DE INVESTIGACIÓN",
            "frase_grado": "PARA OPTAR EL GRADO ACADÉMICO DE MAESTRO EN GERENCIA DE MANTENIMIENTO",
            "pais": "PERÚ",
        }
        caratula.update(fixed_project_cover)
        data.update(fixed_project_cover)


def _apply_unac_maestria_smart_replacements(
    data: Dict[str, Any], values: Dict[str, Any]
) -> None:
    """
    Last-mile hardcoded placeholder replacement for UNAC Master's thesis.
    Targets exact strings seen in institutional templates.
    """
    v = values or {}

    # 1. Define replacements map
    # Key: Placeholder string to find
    # Value: Variable name in 'values' to replace with
    replacements = {
        # Carátula
        "[TÍTULO DE LA TESIS]": v.get("titulo"),
        '"[TÍTULO DE LA TESIS]"': v.get("titulo"),
        # NOTA: Se elimina "[Apellidos y nombres]" global porque causaba que el asesor
        # reemplazara al autor si este último faltaba. El renderizado estructural ya
        # maneja los nombres en sus lugares correctos.
        "[Nombre de la línea]": v.get("linea_investigacion"),
        # Información Básica
        "[Nombre de Facultad]": v.get("facultad"),
        "[Nombre Unidad de Investigación]": v.get("unidad_investigacion"),
        "[Título de tesis]": v.get("titulo"),
        "Bach. [Apellidos y nombres]": f"Bach. {v.get('autor1_nombres')}"
        if v.get("autor1_nombres")
        else None,
        "Dr. [Apellidos y nombres]": f"Dr. {v.get('asesor_nombres')}"
        if v.get("asesor_nombres")
        else None,
        "[Lugar de ejecución]": v.get("lugar_ejecucion"),
        "[Unidad de análisis]": v.get("unidad_analisis"),
        "[TIPO]": v.get("tipo"),
        "[ENFOQUE]": v.get("enfoque"),
        "[DISEÑO DE INVESTIGACIÓN]": v.get("diseno_investigacion"),
        "[LÍNEA OCDE 1]": v.get("tema_ocde_1"),
        "[LÍNEA OCDE 2]": v.get("tema_ocde_2"),
        "[LÍNEA OCDE 3]": v.get("tema_ocde_3"),
        # Matriz de Consistencia y otros apartados técnicos
        "¿[Problema general de la investigación]?": f"¿{v.get('problema_general')}?"
        if v.get("problema_general")
        else None,
        "[Objetivo general de la investigación]": v.get("objetivo_general"),
        "[Hipótesis general de la investigación]": v.get("hipotesis_general"),
        "[Variable independiente]": v.get("vi"),
        "[Variable dependiente]": v.get("vd"),
        "[Línea de investigación]": v.get("linea_investigacion"),
        "[Población y muestra]": f"{v.get('poblacion', '')} / {v.get('muestra', '')}".strip()
        if v.get("poblacion") or v.get("muestra")
        else None,
        # Carátula - Reemplazos genéricos post-enfocados
        # Se aplican al final para no interferir con los prefijados (Bach./Dr.)
        "[Apellidos y nombres]": v.get("autor1_nombres") or v.get("asesor_nombres"),
        "[Nombre de la facultad]": v.get("facultad"),
        "[AÑO]": v.get("anio"),
        # Hoja de Jurado y Actas
        "[ASESOR]": v.get("asesor_nombres"),
        "[dd de mes de aaaa]": v.get("fecha_sustentacion"),
    }

    def _recursive_replace(obj: Any) -> Any:
        if isinstance(obj, str):
            res = obj
            for placeholder, val in replacements.items():
                if val and placeholder in res:
                    res = res.replace(placeholder, str(val))
            return res
        elif isinstance(obj, dict):
            return {k: _recursive_replace(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_recursive_replace(item) for item in obj]
        return obj

    # Apply replacement recursively to the whole doc structure (caratula, info_basica, matriz, etc.)
    for key in list(data.keys()):
        data[key] = _recursive_replace(data[key])


def _apply_informacion_basica_values(
    data: Dict[str, Any], values: Dict[str, Any]
) -> None:
    informacion_basica = data.get("informacion_basica")
    if not isinstance(informacion_basica, dict):
        return

    # 1. Autor(es)
    autores_info = []
    for prefix in ("autor1", "autor2"):
        nombre = str(values.get(f"{prefix}_nombres", "") or "").strip()
        if not nombre:
            continue
        prefix_label = "Bach. " if prefix.startswith("autor") else "Dr. "
        autores_info.append(
            {
                "nombre": f"{prefix_label}{nombre}",
                "dni": str(values.get(f"{prefix}_dni", "") or "[DNI]").strip(),
                "orcid": str(values.get(f"{prefix}_orcid", "") or "[ORCID]").strip(),
            }
        )
    if autores_info:
        informacion_basica["autores"] = autores_info

    # 2. Asesor
    asesor_nombre = str(values.get("asesor_nombres", "") or "").strip()
    if asesor_nombre:
        informacion_basica["asesor"] = {
            "nombre": f"Dr. {asesor_nombre}",
            "dni": str(values.get("asesor_dni", "") or "[DNI]").strip(),
            "orcid": str(values.get("asesor_orcid", "") or "[ORCID]").strip(),
        }

    # 3. Campos directos
    for dest, src in [
        ("titulo_investigacion", "titulo"),
        ("lugar_ejecucion", "lugar_ejecucion"),
        ("unidad_analisis", "unidad_analisis"),
        ("tipo", "tipo"),
        ("enfoque", "enfoque"),
        ("diseno_investigacion", "diseno_investigacion"),
        ("facultad", "facultad"),
        ("unidad_investigacion", "unidad_investigacion"),
    ]:
        val = str(values.get(src, "") or "").strip()
        if val:
            informacion_basica[dest] = val

    # 4. Temas OCDE
    temas = [str(values.get(f"tema_ocde_{i}", "") or "").strip() for i in (1, 2, 3)]
    temas = [t for t in temas if t]
    if temas:
        informacion_basica["tema_ocde"] = temas


def sanitize_ai_text(content: str) -> str:
    """Last-mile cleanup for AI text before DOCX insertion."""
    text = (content or "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\f", "\n").replace("\v", "\n")
    text = _FENCE_RE.sub("", text)

    cleaned_lines: List[str] = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        if _MARKDOWN_HEADER_RE.match(line):
            line = _MARKDOWN_HEADER_RE.sub("", line)

        if line.count("|") >= 2 or _TABLE_SEPARATOR_RE.match(line):
            continue

        upper_line = _norm_upper(line)
        if "FIGURA DE EJEMPLO" in upper_line:
            continue
        if _TABLA_PLACEHOLDER_RE.match(line):
            continue
        if _INSERTAR_RE.search(line):
            continue

        line = line.replace("**", "").replace("__", "")
        line = line.replace("`", "")
        line = re.sub(r"^\s*[-*]\s+", "", line)
        line = re.sub(r"^\s*\d+\.\s+", "", line)

        cleaned_lines.append(line.strip())

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def exclude_instruction_keys(obj: Any) -> Any:
    """Recursively remove instruction/guidance keys from format data."""
    if isinstance(obj, dict):
        return {
            key: exclude_instruction_keys(value)
            for key, value in obj.items()
            if key.lower() not in EXCLUDED_KEYS
        }
    elif isinstance(obj, list):
        return [exclude_instruction_keys(item) for item in obj]
    return obj


def merge_values(
    data: Dict[str, Any],
    values: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge user-provided values into format placeholders.

    Looks for placeholder patterns like "[TITULO]" or "{autor}"
    and replaces with actual values.
    """

    def _replace_placeholders(obj: Any) -> Any:
        if isinstance(obj, str):
            result = obj
            for key, value in values.items():
                if value is None:
                    continue
                # Skip empty strings to prevent accidental clearing of placeholders
                # when data is missing but the key exists.
                val_str = str(value).strip()
                if not val_str:
                    continue
                patterns = [
                    f"[{key.upper()}]",
                    f"[{key}]",
                    f"{{{key}}}",
                    f"<{key}>",
                ]
                for pattern in patterns:
                    if pattern in result:
                        result = result.replace(pattern, val_str)
            return result
        elif isinstance(obj, dict):
            return {k: _replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_replace_placeholders(item) for item in obj]
        return obj

    merged = _replace_placeholders(data)
    if isinstance(merged, dict):
        if values:
            merged["values"] = deepcopy(values)
            for key in (
                "matriz_consistencia",
                "operacionalizacion_vi",
                "operacionalizacion_vd",
                "operacionalizacion_variable_independiente",
                "operacionalizacion_variable_dependiente",
            ):
                if key in values and values[key] not in (None, "", [], {}):
                    merged[key] = deepcopy(values[key])

        # DIAGNOSTIC: Log the keys in values
        logger.info(
            f"PREPROCESSOR: Received values keys: {list((values or {}).keys())}"
        )
        if values and "autor1_nombres" in values:
            logger.info(
                f"PREPROCESSOR: autor1_nombres found: {values.get('autor1_nombres')}"
            )

        _apply_cover_fallbacks(merged, values or {})
        _apply_informacion_basica_values(merged, values or {})

        # Smart UNAC-Maestria replacement for hardcoded institutional placeholders
        try:
            _apply_unac_maestria_smart_replacements(merged, values or {})
        except Exception as e:
            logger.error(f"PREPROCESSOR: Smart replacement failed: {e}")
    return merged


def _inject_ai_into_informacion_basica(data: Dict[str, Any], content: Any) -> None:
    """Inject AI content specialized for the informacion_basica block."""
    info = data.get("informacion_basica")
    if not isinstance(info, dict):
        return

    # Store it in a hidden/internal key that the renderer can pick up
    info["_ai_content"] = content

    # Also attempt to replace common placeholders if content is text
    if isinstance(content, str) and content.strip():
        # This is a fallback: if the AI generated a block of text for the basic info,
        # we might want to show it somewhere.
        # For now, we just ensure it's available for the renderer.
        pass


def apply_ai_content(
    data: Dict[str, Any],
    ai_sections: List[Dict[str, Any]],
    selected_sections: List[Dict[str, Any]] | List[str] | None = None,
) -> Dict[str, Any]:
    """
    Apply AI content to the document structure.

    Maps AI sections to document sections by canonical path and injects
    content into renderable body fields without overwriting heading labels.

    Content may be a plain string (sanitized text) or a list of structured
    objects (paragraphs, tables, figures) which are passed through directly.
    """

    def _coerce_visible_text(value: Any) -> str:
        """Extract visible text from block-like objects without stringifying raw dict/list values."""
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            return ""
        for key in ("texto", "caption", "titulo"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return text.strip()
        return ""

    content_map: Dict[str, Any] = {}  # str or List[dict]
    content_display_map: Dict[str, str] = {}
    for section in ai_sections:
        raw_content = section.get("content", "")

        # Structured content (list of typed objects): pass through as-is
        if isinstance(raw_content, list) and raw_content:
            processed_content = raw_content
        elif isinstance(raw_content, dict):
            processed_content = _coerce_visible_text(raw_content)
            if not processed_content:
                continue
        elif isinstance(raw_content, str):
            processed_content = sanitize_ai_text(raw_content)
            if not processed_content:
                continue
        else:
            continue

        for locator_key in ("path", "sectionId", "section_id"):
            locator = str(section.get(locator_key, "") or "").strip()
            normalized_locator = _normalize_path(locator)
            if not normalized_locator or _is_index_path(normalized_locator):
                continue
            content_map[normalized_locator] = processed_content
            if locator_key == "path":
                content_display_map[normalized_locator] = (
                    locator.replace("\\", "/").split("/")[-1].strip()
                )

    def _consume_content(*candidates: str) -> Any:  # str or List[dict]
        for candidate in candidates:
            normalized_candidate = _normalize_path(candidate)
            if normalized_candidate and normalized_candidate in content_map:
                return content_map.pop(normalized_candidate)

        for candidate in candidates:
            leaf = _normalize_path(candidate).split("/")[-1]
            if not leaf:
                continue
            matches = [
                key for key in content_map if key == leaf or key.endswith(f"/{leaf}")
            ]
            if len(matches) == 1:
                return content_map.pop(matches[0])

        return ""

    def _consume_annex_content(
        candidate: str,
        *,
        annex_position: int | None = None,
    ) -> tuple[Any, str]:  # str or List[dict], matched leaf
        normalized_candidate = _normalize_path(candidate)
        leaf = normalized_candidate.split("/")[-1] if normalized_candidate else ""
        match = _ANNEX_PREFIX_RE.match(leaf)
        if match:
            annex_prefix = match.group(1)
        elif annex_position is not None:
            annex_prefix = f"ANEXO {annex_position}"
        else:
            return "", ""
        matches = [
            key
            for key in content_map
            if _ANNEX_PREFIX_RE.match(key.split("/")[-1] if key else "")
            and _ANNEX_PREFIX_RE.match(key.split("/")[-1]).group(1) == annex_prefix
        ]
        if len(matches) == 1:
            matched_key = matches[0]
            return (
                content_map.pop(matched_key),
                content_display_map.get(matched_key, matched_key.split("/")[-1]),
            )
        return "", ""

    def _flatten_to_text(content: Any) -> str:
        """Convert structured content to plain text, discarding non-paragraph structural blocks."""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return _coerce_visible_text(content)
        if not isinstance(content, list):
            return ""
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict) and item.get("tipo") == "parrafo":
                texto = item.get("texto", "")
                if texto:
                    parts.append(texto)
                continue
            fallback = _coerce_visible_text(item)
            if (
                fallback
                and isinstance(item, dict)
                and item.get("tipo") not in {"tabla", "figura"}
            ):
                parts.append(fallback)
        return "\n\n".join(parts)

    def _inject_into_render_fields(
        target: Dict[str, Any],
        content: Any,
        *,
        allow_text_override: bool = False,
    ) -> None:
        """Inject AI content into renderable fields while preserving heading fields.

        Handles both plain strings and structured content lists.
        """

        def _tag_ai_generated_blocks(value: Any) -> Any:
            if not isinstance(value, list):
                return value
            tagged: List[Any] = []
            for item in value:
                if isinstance(item, dict):
                    block = dict(item)
                    block["_ai_generated"] = True
                    tagged.append(block)
                else:
                    tagged.append(item)
            return tagged

        # Structured content (list of typed objects): inject into contenido[]
        if isinstance(content, list):
            ai_blocks = _tag_ai_generated_blocks(content)
            existing = target.get("contenido")
            if isinstance(existing, list):
                target["contenido"] = ai_blocks + existing
            else:
                target["contenido"] = ai_blocks
            return

        # Plain string path
        if not isinstance(content, str) or not content.strip():
            return

        parrafos = target.get("parrafos")
        if isinstance(parrafos, list):
            target["parrafos"] = [content]
            return

        if allow_text_override and isinstance(target.get("texto"), str):
            target["texto"] = content
            return

        contenido = target.get("contenido")
        if isinstance(contenido, list):
            if contenido and all(isinstance(item, str) for item in contenido):
                target["contenido"] = [content]
            else:
                target["contenido"] = [content] + contenido
            return

        # Last resort for blocks without explicit paragraph fields.
        target["parrafos"] = [content]

    # --- INFORMACION BASICA SPECIAL HANDLING ---
    # Many formats treat 'Información Básica' as a top-level block, not a section.
    ib_content = _consume_content("INFORMACION BASICA", "DATOS GENERALES")
    if ib_content:
        _inject_ai_into_informacion_basica(data, ib_content)

    # --- BODY INJECTION ---

    def _inject_chapter_content(capitulo: Dict[str, Any], content: Any) -> None:
        """Inject content into a chapter. Handles both str and list."""

        def _tag_ai_generated_blocks(value: Any) -> Any:
            if not isinstance(value, list):
                return value
            tagged: List[Any] = []
            for item in value:
                if isinstance(item, dict):
                    block = dict(item)
                    block["_ai_generated"] = True
                    tagged.append(block)
                else:
                    tagged.append(item)
            return tagged

        # Structured content: inject directly into contenido[]
        if isinstance(content, list):
            ai_blocks = _tag_ai_generated_blocks(content)
            existing = capitulo.get("contenido")
            if isinstance(existing, list):
                capitulo["contenido"] = ai_blocks + existing
            else:
                capitulo["contenido"] = ai_blocks
            return

        # Plain string: original behavior
        contenido = capitulo.get("contenido")
        if not isinstance(contenido, list):
            capitulo["contenido"] = [{"parrafos": [content]}]
            return

        for item in contenido:
            if isinstance(item, dict):
                existing = item.get("parrafos")
                if isinstance(existing, list):
                    item["parrafos"] = [content] + existing
                else:
                    item["parrafos"] = [content]
                return

        contenido.insert(0, {"parrafos": [content]})

    result = deepcopy(data)
    selected_paths = _collect_selected_paths(selected_sections)
    document_id = str(
        (
            result.get("_meta", {})
            if isinstance(result.get("_meta"), dict)
            else {}
        ).get("id", "")
        or ""
    ).strip().lower()
    is_unac_project = document_id.startswith("unac-proyecto")

    preliminares = result.get("preliminares")
    if isinstance(preliminares, dict):

        def _preliminary_selected(default_title: str, *extra_titles: str) -> bool:
            if not selected_paths:
                return True
            candidate_titles = [default_title, *extra_titles]
            for candidate in candidate_titles:
                normalized_candidate = str(candidate or "").strip()
                if not normalized_candidate:
                    continue
                if _path_selected(normalized_candidate, selected_paths):
                    return True
                if _path_selected(
                    f"PRELIMINARES/{normalized_candidate}",
                    selected_paths,
                ):
                    return True
                if _selected_token_present(selected_paths, normalized_candidate):
                    return True
            return False

        def _preliminary_title(item: Any, default_title: str) -> str:
            if isinstance(item, dict):
                return str(item.get("titulo", default_title) or default_title).strip()
            if isinstance(item, str):
                return str(item or default_title).strip() or default_title
            return default_title

        def _inject_text_preliminary(key: str, default_title: str) -> None:
            item = preliminares.get(key)
            if item is None:
                return
            title = _preliminary_title(item, default_title)
            item_content = _consume_content(
                title,
                f"PRELIMINARES/{title}",
                default_title,
                f"PRELIMINARES/{default_title}",
            )
            if not item_content:
                return
            safe_text = _flatten_to_text(item_content)
            if not safe_text:
                return
            if isinstance(item, dict):
                _inject_into_render_fields(
                    item,
                    safe_text,
                    allow_text_override=True,
                )
                item["_ai_content"] = safe_text
            else:
                preliminares[key] = {
                    "titulo": title,
                    "texto": safe_text,
                    "_ai_content": safe_text,
                }

        for prelim_key, default_title in (
            ("dedicatoria", "DEDICATORIA"),
            ("agradecimiento", "AGRADECIMIENTO"),
            ("agradecimientos", "AGRADECIMIENTOS"),
            ("resumen", "RESUMEN"),
            ("introduccion", "INTRODUCCION"),
        ):
            _inject_text_preliminary(prelim_key, default_title)

        if "introduccion" in preliminares and not _preliminary_selected(
            "INTRODUCCION",
            "INTRODUCCIÓN",
        ):
            preliminares.pop("introduccion", None)

        abbreviations = preliminares.get("abreviaturas")
        abbreviations_title = _preliminary_title(
            abbreviations,
            "INDICE DE ABREVIATURAS",
        )
        abbreviations_content = _consume_content(
            abbreviations_title,
            f"PRELIMINARES/{abbreviations_title}",
            "ABREVIATURAS",
            "INDICE DE ABREVIATURAS",
            "PRELIMINARES/ABREVIATURAS",
            "PRELIMINARES/INDICE DE ABREVIATURAS",
        )
        if abbreviations_content:
            safe_abbreviations = _flatten_to_text(abbreviations_content)
            if safe_abbreviations:
                if isinstance(abbreviations, dict):
                    abbreviations["_ai_content"] = safe_abbreviations
                else:
                    preliminares["abreviaturas"] = {
                        "titulo": abbreviations_title,
                        "_ai_content": safe_abbreviations,
                    }

    def _extract_table_blocks(content: Any) -> List[Dict[str, Any]]:
        tables: List[Dict[str, Any]] = []
        if isinstance(content, dict):
            block_type = str(content.get("tipo") or "").strip().lower()
            if block_type == "tabla":
                tables.append(dict(content))
            return tables
        if not isinstance(content, list):
            return tables
        for block in content:
            if not isinstance(block, dict):
                continue
            if str(block.get("tipo") or "").strip().lower() == "tabla":
                tables.append(dict(block))
        return tables

    def _consume_child_table_blocks(chapter_title: str) -> List[Dict[str, Any]]:
        chapter_key = _normalize_path(chapter_title)
        if not chapter_key:
            return []
        prefix = f"{chapter_key}/"
        candidate_keys = sorted([key for key in content_map if key.startswith(prefix)])
        for key in candidate_keys:
            tables = _extract_table_blocks(content_map.get(key))
            if tables:
                content_map.pop(key, None)
                return tables
        return []

    def _merge_ai_table_into_template_table(
        template_table: Dict[str, Any],
        ai_table: Dict[str, Any],
    ) -> Dict[str, Any]:
        merged = deepcopy(template_table)
        dynamic_keys = (
            "encabezados",
            "filas",
            "anio",
            "meses",
            "simbolo_marca",
            "filas_fase",
            "filas_categoria",
            "fila_total",
            "celdas_combinadas",
            "celdas_fusionadas",
            "nota_pie",
            "fuente",
            "nota",
            "nota_color",
        )
        for key in dynamic_keys:
            if key in ai_table and ai_table.get(key) not in (None, ""):
                merged[key] = deepcopy(ai_table.get(key))

        for identity_key in ("tipo", "id", "titulo", "orientacion", "subtipo"):
            if merged.get(identity_key) in (None, "") and ai_table.get(identity_key) not in (None, ""):
                merged[identity_key] = deepcopy(ai_table.get(identity_key))

        if "estilo" not in merged and isinstance(ai_table.get("estilo"), dict):
            merged["estilo"] = deepcopy(ai_table.get("estilo"))
        if "estilos" not in merged and isinstance(ai_table.get("estilos"), dict):
            merged["estilos"] = deepcopy(ai_table.get("estilos"))

        merged["_ai_generated"] = True
        return merged

    def _apply_ai_table_over_static_template(
        capitulo: Dict[str, Any],
        ai_tables: List[Dict[str, Any]],
    ) -> bool:
        if not ai_tables:
            return False
        contenido = capitulo.get("contenido")
        if not isinstance(contenido, list):
            return False

        ai_table = next(
            (
                table
                for table in ai_tables
                if isinstance(table, dict)
                and str(table.get("tipo", "")).strip().lower() == "tabla"
            ),
            None,
        )
        if not isinstance(ai_table, dict):
            return False

        for index, item in enumerate(contenido):
            if not isinstance(item, dict):
                continue
            if str(item.get("tipo", "")).strip().lower() != "tabla":
                continue
            contenido[index] = _merge_ai_table_into_template_table(item, ai_table)
            return True
        return False

    cuerpo = result.get("cuerpo")
    if isinstance(cuerpo, list):
        filtered_chapters: List[Dict[str, Any]] = []
        for capitulo in cuerpo:
            if not isinstance(capitulo, dict):
                continue

            capitulo_titulo = str(capitulo.get("titulo", "") or "").strip()
            if not capitulo_titulo:
                continue
            if selected_paths and not _path_selected(capitulo_titulo, selected_paths):
                continue

            normalized_capitulo_titulo = _normalize_path(capitulo_titulo).lower()
            is_schedule_or_budget_chapter = any(
                token in normalized_capitulo_titulo
                for token in ("cronograma", "presupuesto")
            )
            chapter_has_static_table = isinstance(capitulo.get("contenido"), list) and any(
                isinstance(child, dict) and str(child.get("tipo", "")).strip().lower() == "tabla"
                for child in capitulo.get("contenido", [])
            )

            capitulo_content = _consume_content(
                capitulo_titulo,
                f"CUERPO/{capitulo_titulo}",
            )
            chapter_has_child_sections = isinstance(capitulo.get("contenido"), list) and any(
                isinstance(child, dict) and str(child.get("texto", "") or "").strip()
                for child in capitulo.get("contenido", [])
            )
            skip_chapter_level_ai = is_unac_project and chapter_has_child_sections
            if (
                is_schedule_or_budget_chapter
                and chapter_has_static_table
                and isinstance(capitulo_content, str)
            ):
                # Keep chapter title immediately followed by the existing table.
                # Ignore chapter-level narrative text for schedule/budget.
                capitulo_content = ""
            schedule_or_budget_tables: List[Dict[str, Any]] = []
            if is_schedule_or_budget_chapter and chapter_has_static_table:
                schedule_or_budget_tables = _extract_table_blocks(capitulo_content)
                if not schedule_or_budget_tables:
                    schedule_or_budget_tables = _consume_child_table_blocks(capitulo_titulo)
                if schedule_or_budget_tables:
                    if _apply_ai_table_over_static_template(
                        capitulo,
                        schedule_or_budget_tables,
                    ):
                        capitulo["_ai_content"] = deepcopy(schedule_or_budget_tables)
                    else:
                        tagged_tables: List[Dict[str, Any]] = []
                        for table_block in schedule_or_budget_tables:
                            tagged = dict(table_block)
                            tagged["_ai_generated"] = True
                            tagged_tables.append(tagged)
                        capitulo["contenido"] = tagged_tables
                        capitulo["_ai_content"] = tagged_tables
                    filtered_chapters.append(capitulo)
                    continue
            if (
                selected_paths
                and is_unac_project
                and is_schedule_or_budget_chapter
                and chapter_has_static_table
            ):
                # If no AI replacement table arrives, keep the canonical table
                # already defined by the institutional template.
                capitulo.pop("_ai_content", None)
                filtered_chapters.append(capitulo)
                continue
            if capitulo_content and not skip_chapter_level_ai:
                _inject_chapter_content(capitulo, capitulo_content)
                capitulo["_ai_content"] = capitulo_content

            contenido_items = capitulo.get("contenido")
            if not isinstance(contenido_items, list):
                filtered_chapters.append(capitulo)
                continue

            if selected_paths:
                pruned_items: List[Any] = []
                for item in contenido_items:
                    if not isinstance(item, dict):
                        pruned_items.append(item)
                        continue
                    item_titulo_candidate = str(item.get("texto", "") or "").strip()
                    if not item_titulo_candidate:
                        pruned_items.append(item)
                        continue
                    if _path_selected(
                        f"{capitulo_titulo}/{item_titulo_candidate}",
                        selected_paths,
                    ):
                        pruned_items.append(item)
                capitulo["contenido"] = pruned_items
                contenido_items = pruned_items

            for item in contenido_items:
                if not isinstance(item, dict):
                    continue
                item_titulo = str(item.get("texto", "") or "").strip()
                if not item_titulo:
                    continue
                item_content = _consume_content(
                    f"{capitulo_titulo}/{item_titulo}",
                    item_titulo,
                    f"CUERPO/{capitulo_titulo}/{item_titulo}",
                )
                if not item_content:
                    continue
                _inject_into_render_fields(
                    item, item_content, allow_text_override=False
                )
                item["_ai_content"] = item_content
            filtered_chapters.append(capitulo)
        result["cuerpo"] = filtered_chapters

    finales = result.get("finales")
    if isinstance(finales, dict):
        if selected_paths and not _selected_token_present(selected_paths, "REFERENCIAS"):
            finales.pop("referencias", None)
        if selected_paths and not _selected_token_present(selected_paths, "ANEXOS"):
            finales.pop("anexos", None)

        referencias = finales.get("referencias")
        if isinstance(referencias, dict):
            referencias_titulo = str(
                referencias.get("titulo", "REFERENCIAS BIBLIOGRAFICAS")
                or "REFERENCIAS BIBLIOGRAFICAS"
            )
            referencias_content = _consume_content(
                referencias_titulo,
                f"FINALES/{referencias_titulo}",
                "REFERENCIAS",
                "REFERENCIAS BIBLIOGRAFICAS",
            )
            if referencias_content:
                safe_references = _flatten_to_text(referencias_content)
                if safe_references:
                    referencias["_ai_content"] = safe_references
        elif isinstance(referencias, str):
            referencias_titulo = str(
                referencias or "REFERENCIAS BIBLIOGRAFICAS"
            ).strip()
            referencias_content = _consume_content(
                referencias_titulo,
                f"FINALES/{referencias_titulo}",
                "REFERENCIAS",
                "REFERENCIAS BIBLIOGRAFICAS",
            )
            if referencias_content:
                safe_references = _flatten_to_text(referencias_content)
                if safe_references:
                    finales["referencias"] = {
                        "titulo": referencias_titulo,
                        "_ai_content": safe_references,
                    }

        anexos = finales.get("anexos")
        if isinstance(anexos, dict):
            anexos_titulo = str(anexos.get("titulo", "ANEXOS") or "ANEXOS")
            anexos_lista = anexos.get("lista")
            if isinstance(anexos_lista, list):
                for position, item in enumerate(anexos_lista, start=1):
                    if not isinstance(item, dict):
                        continue
                    item_titulo = str(
                        item.get("texto") or item.get("titulo") or ""
                    ).strip()
                    if not item_titulo:
                        continue
                    item_content = _consume_content(
                        f"{anexos_titulo}/{item_titulo}",
                        f"ANEXOS/{item_titulo}",
                        item_titulo,
                    )
                    resolved_annex_title = ""
                    if not item_content:
                        item_content, resolved_annex_title = _consume_annex_content(
                            f"ANEXOS/{item_titulo}",
                            annex_position=position,
                        )
                    if not item_content:
                        continue
                    if resolved_annex_title:
                        item["titulo"] = resolved_annex_title
                    _inject_into_render_fields(
                        item, item_content, allow_text_override=False
                    )
                    item["_ai_content"] = item_content

    return result


def cleanup_temp_json(path: Path) -> None:
    """Delete temporary JSON file created for rendering."""
    try:
        path.unlink()
    except Exception:
        pass
