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
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Set


# Keys that should NOT appear in the final document
EXCLUDED_KEYS: Set[str] = frozenset({
    "nota", "nota_capitulo", "nota_general",
    "notas",
    "instruccion", "instrucciones", "instruccion_detallada",
    "guia", "guias",
    "ejemplo", "ejemplos",
    "comentario", "comentarios",
    "observacion", "observaciones",
    "placeholder",
    "tipo_vista", "vista_previa",
    "_meta", "version", "descripcion",
})

_FENCE_RE = re.compile(r"```[\s\S]*?```")
_MARKDOWN_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
_INSERTAR_RE = re.compile(r"\[\s*insertar[^\]]*\]", re.IGNORECASE)
_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
_TABLA_PLACEHOLDER_RE = re.compile(r"^\s*tabla\s+de\s+ejemplo\b", re.IGNORECASE)
_PATH_SEPARATOR_RE = re.compile(r"\s*/\s*")
_WHITESPACE_RE = re.compile(r"\s+")


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
    parts = [part.strip() for part in normalized.split("/") if part.strip()]
    return any(part.startswith("INDICE") for part in parts)


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

    project_obj = values.get("project")
    title_value = _pick_first_nonempty(
        values,
        ["title", "project_title", "projectTitle"],
    )
    if not title_value and isinstance(project_obj, dict):
        nested_title = project_obj.get("title")
        if nested_title is not None and str(nested_title).strip():
            title_value = str(nested_title).strip()
    if title_value:
        current_title = str(caratula.get("titulo") or caratula.get("titulo_placeholder") or "")
        if _looks_like_placeholder(current_title):
            caratula["titulo"] = title_value

    fallback_map = {
        "facultad": ["facultad", "faculty"],
        "escuela": ["escuela", "school"],
        "autor_valor": ["autor_valor", "autor", "author"],
        "asesor_valor": ["asesor_valor", "asesor", "advisor"],
    }
    for cover_key, candidates in fallback_map.items():
        picked = _pick_first_nonempty(values, candidates)
        if not picked:
            continue
        existing = str(caratula.get(cover_key, "") or "")
        if _looks_like_placeholder(existing):
            caratula[cover_key] = picked


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
                patterns = [
                    f"[{key.upper()}]",
                    f"[{key}]",
                    f"{{{key}}}",
                    f"<{key}>",
                ]
                for pattern in patterns:
                    if pattern in result:
                        result = result.replace(pattern, str(value))
            return result
        elif isinstance(obj, dict):
            return {k: _replace_placeholders(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_replace_placeholders(item) for item in obj]
        return obj

    merged = _replace_placeholders(data)
    if isinstance(merged, dict):
        _apply_cover_fallbacks(merged, values or {})
    return merged


def apply_ai_content(
    data: Dict[str, Any],
    ai_sections: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Apply AI content to the document structure.

    Maps AI sections to document sections by canonical path and injects
    content into renderable body fields without overwriting heading labels.
    """
    content_map: Dict[str, str] = {}
    for section in ai_sections:
        raw_content = sanitize_ai_text(section.get("content", ""))
        if not raw_content:
            continue

        for locator_key in ("path", "sectionId", "section_id"):
            locator = str(section.get(locator_key, "") or "").strip()
            normalized_locator = _normalize_path(locator)
            if not normalized_locator or _is_index_path(normalized_locator):
                continue
            content_map[normalized_locator] = raw_content

    def _consume_content(*candidates: str) -> str:
        for candidate in candidates:
            normalized_candidate = _normalize_path(candidate)
            if normalized_candidate and normalized_candidate in content_map:
                return content_map.pop(normalized_candidate)

        for candidate in candidates:
            leaf = _normalize_path(candidate).split("/")[-1]
            if not leaf:
                continue
            matches = [key for key in content_map if key == leaf or key.endswith(f"/{leaf}")]
            if len(matches) == 1:
                return content_map.pop(matches[0])

        return ""

    def _inject_into_render_fields(
        target: Dict[str, Any],
        content: str,
        *,
        allow_text_override: bool = False,
    ) -> None:
        """Inject AI text into renderable fields while preserving heading fields."""
        if not content.strip():
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

    def _inject_chapter_content(capitulo: Dict[str, Any], content: str) -> None:
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

    preliminares = result.get("preliminares")
    if isinstance(preliminares, dict):
        introduccion = preliminares.get("introduccion")
        if isinstance(introduccion, dict):
            intro_title = str(introduccion.get("titulo", "INTRODUCCION") or "INTRODUCCION")
            intro_content = _consume_content(
                intro_title,
                f"PRELIMINARES/{intro_title}",
                "INTRODUCCION",
                "PRELIMINARES/INTRODUCCION",
            )
            if intro_content:
                _inject_into_render_fields(
                    introduccion,
                    intro_content,
                    allow_text_override=True,
                )
                introduccion["_ai_content"] = intro_content

    cuerpo = result.get("cuerpo")
    if isinstance(cuerpo, list):
        for capitulo in cuerpo:
            if not isinstance(capitulo, dict):
                continue

            capitulo_titulo = str(capitulo.get("titulo", "") or "").strip()
            if not capitulo_titulo:
                continue

            capitulo_content = _consume_content(
                capitulo_titulo,
                f"CUERPO/{capitulo_titulo}",
            )
            if capitulo_content:
                _inject_chapter_content(capitulo, capitulo_content)
                capitulo["_ai_content"] = capitulo_content

            contenido_items = capitulo.get("contenido")
            if not isinstance(contenido_items, list):
                continue

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
                _inject_into_render_fields(item, item_content, allow_text_override=False)
                item["_ai_content"] = item_content

    finales = result.get("finales")
    if isinstance(finales, dict):
        anexos = finales.get("anexos")
        if isinstance(anexos, dict):
            anexos_titulo = str(anexos.get("titulo", "ANEXOS") or "ANEXOS")
            anexos_lista = anexos.get("lista")
            if isinstance(anexos_lista, list):
                for item in anexos_lista:
                    if not isinstance(item, dict):
                        continue
                    item_titulo = str(item.get("texto") or item.get("titulo") or "").strip()
                    if not item_titulo:
                        continue
                    item_content = _consume_content(
                        f"{anexos_titulo}/{item_titulo}",
                        f"ANEXOS/{item_titulo}",
                        item_titulo,
                    )
                    if not item_content:
                        continue
                    _inject_into_render_fields(item, item_content, allow_text_override=False)
                    item["_ai_content"] = item_content

    return result


def cleanup_temp_json(path: Path) -> None:
    """Delete temporary JSON file created for rendering."""
    try:
        path.unlink()
    except Exception:
        pass
