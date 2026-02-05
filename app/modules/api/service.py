"""
Archivo: app/modules/api/service.py
Propósito:
- Carga formatos desde la fuente real y los mapea a DTOs.
- Calcula hashes determinísticos y versión global del catálogo.

Responsabilidades:
- Leer formatos via loaders existentes.
- Normalizar a estructura interna.
- Calcular formatHash por contenido (no por mtime).
- Calcular catalogVersion global.
- Mapear a DTOs públicos.
No hace:
- No maneja HTTP ni headers (eso es del router).

Dependencias:
- app.core.loaders (discover_format_files, load_format_by_id)
- app.core.registry (get_provider)
- hashlib, json

Puntos de extensión:
- Agregar caché en memoria si el rendimiento lo requiere.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.loaders import discover_format_files, load_format_by_id, FormatIndexItem
from app.core.registry import get_provider
from app.modules.api.dtos import (
    AssetRef,
    CatalogValidationResponse,
    CatalogVersionResponse,
    FieldType,
    FormatDetail,
    FormatField,
    FormatSummary,
    FormatValidationError,
    RuleSet,
    TemplateRef,
)


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL FORMAT REPRESENTATION
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InternalFormat:
    """Representación interna de un formato cargado."""
    id: str
    title: str
    university: str
    category: str
    document_type: Optional[str]
    raw_data: Dict[str, Any]
    source_path: Path
    fields: List[Dict[str, Any]] = field(default_factory=list)
    assets: List[Dict[str, Any]] = field(default_factory=list)
    template_kind: Optional[str] = None
    template_path: Optional[Path] = None
    rules: Optional[Dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# HASH UTILITIES (DETERMINISTIC)
# ─────────────────────────────────────────────────────────────────────────────

def canonical_json_bytes(obj: Any) -> bytes:
    """
    Serializa un objeto a JSON canónico (ordenado, sin espacios).
    Garantiza hash determinístico independiente del orden de inserción.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_format_hash(fmt: InternalFormat) -> str:
    """
    Calcula hash SHA256 del contenido real del formato.
    Incluye: raw_data normalizada + template bytes (si existe).
    NO depende de mtimes como fuente de verdad.
    """
    hasher = hashlib.sha256()

    # 1. Hash del JSON normalizado (sin paths internos)
    normalized = {
        "id": fmt.id,
        "title": fmt.title,
        "university": fmt.university,
        "category": fmt.category,
        "document_type": fmt.document_type,
        "fields": fmt.fields,
        "assets": [{"id": a.get("id"), "kind": a.get("kind")} for a in fmt.assets],
        "rules": fmt.rules,
    }
    hasher.update(canonical_json_bytes(normalized))

    # 2. Hash del template si existe
    if fmt.template_path and fmt.template_path.exists():
        try:
            hasher.update(fmt.template_path.read_bytes())
        except Exception:
            pass  # Si no se puede leer, no afecta el hash

    return hasher.hexdigest()


def make_stable_format_id(uni: str, category: str, title: str, raw_id: str) -> str:
    """
    Genera un ID estable basado en contenido lógico, no en paths.
    Formato: {university}:{category}:{slug}
    """
    # Slug del título
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().strip())
    slug = slug.strip("-")[:50]  # Limitar longitud

    # Si el raw_id ya tiene estructura estable, preferirlo
    if raw_id and ":" in raw_id:
        return raw_id

    base_id = f"{uni}:{category}:{slug}"
    return base_id


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT LOADING AND NORMALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def _extract_fields(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrae campos del wizard desde la estructura del formato.
    Busca en: caratula, campos, fields, etc.
    """
    fields = []
    order = 0

    # Buscar en secciones conocidas
    caratula = data.get("caratula") or {}
    if isinstance(caratula, dict):
        for key, value in caratula.items():
            if key.startswith("_"):
                continue
            order += 1
            field_def = {
                "name": key,
                "label": _humanize_label(key),
                "type": _infer_field_type(key, value),
                "required": False,
                "default": value if isinstance(value, (str, int, float, bool)) else None,
                "order": order,
            }
            fields.append(field_def)

    # También buscar en "campos" o "fields" si existen
    for key in ("campos", "fields"):
        raw_fields = data.get(key)
        if isinstance(raw_fields, list):
            for item in raw_fields:
                if isinstance(item, dict):
                    order += 1
                    item["order"] = item.get("order", order)
                    fields.append(item)

    return fields


def _humanize_label(key: str) -> str:
    """Convierte nombre técnico a etiqueta legible."""
    label = key.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in label.split())


def _infer_field_type(key: str, value: Any) -> str:
    """Infiere tipo de campo según nombre y valor."""
    key_lower = key.lower()
    if "fecha" in key_lower or "date" in key_lower:
        return "date"
    if "numero" in key_lower or "number" in key_lower or isinstance(value, (int, float)):
        return "number"
    if "descripcion" in key_lower or "observ" in key_lower or "notas" in key_lower:
        return "textarea"
    if isinstance(value, bool):
        return "boolean"
    return "text"


def _extract_assets(data: Dict[str, Any], uni: str) -> List[Dict[str, Any]]:
    """
    Extrae assets (logos, imágenes) desde la configuración.
    """
    assets = []
    config = data.get("configuracion") or {}

    # Logo principal
    ruta_logo = config.get("ruta_logo")
    if ruta_logo:
        # Generar ID estable basado en el path lógico
        logo_id = f"{uni}:logo:main"
        assets.append({
            "id": logo_id,
            "kind": "logo",
            "original_path": ruta_logo,
        })

    return assets


def _resolve_asset_url(asset: Dict[str, Any], base_url: str = "/api/v1/assets") -> str:
    """
    Resuelve la URL pública de un asset.
    """
    asset_id = asset.get("id", "unknown")
    # Usar el ID como parte de la URL para estabilidad
    safe_id = asset_id.replace(":", "/")
    return f"{base_url}/{safe_id}"


def _extract_template_info(data: Dict[str, Any], uni: str) -> Tuple[Optional[str], Optional[Path]]:
    """
    Extrae información de la plantilla asociada.
    """
    # Buscar en configuración o generador
    config = data.get("configuracion") or {}
    generator = config.get("generator") or config.get("plantilla")

    if generator:
        kind = "docx"  # Default para GicaTesis
        # No exponemos el path real, solo el tipo
        return kind, None

    return None, None


def load_internal_format(item: FormatIndexItem) -> InternalFormat:
    """
    Carga un formato desde el índice y lo normaliza a estructura interna.
    """
    # Cargar datos completos
    try:
        data = load_format_by_id(item.format_id)
    except Exception:
        data = item.data or {}

    # Extraer metadata
    meta = data.get("_meta") or {}

    # Generar ID estable (preferir el existente si está bien formado)
    stable_id = item.format_id  # Ya viene normalizado de loaders.py

    # Extraer campos
    fields = _extract_fields(data)

    # Extraer assets
    assets = _extract_assets(data, item.uni)

    # Extraer template info
    template_kind, template_path = _extract_template_info(data, item.uni)

    # Extraer reglas (si existen)
    rules = None
    config = data.get("configuracion") or {}
    if any(k in config for k in ("margenes", "margins", "fuente", "font", "interlineado")):
        rules = {
            "margins": config.get("margenes") or config.get("margins"),
            "font": config.get("fuente") or config.get("font"),
            "lineSpacing": config.get("interlineado") or config.get("lineSpacing"),
        }

    # Preferir valores de _meta si existen (fuente de verdad = JSON)
    # Fallback a valores derivados del loader para compatibilidad legacy
    return InternalFormat(
        id=meta.get("id") or stable_id,
        title=meta.get("title") or item.titulo,
        university=meta.get("university") or item.uni,
        category=meta.get("category") or item.categoria,
        document_type=meta.get("documentType") or meta.get("tipo_documento") or item.enfoque,
        raw_data=data,
        source_path=item.path,
        fields=fields,
        assets=assets,
        template_kind=template_kind,
        template_path=template_path,
        rules=rules,
    )


def is_publishable_format(fmt: InternalFormat) -> bool:
    """
    Determina si un formato es publicable en el catálogo público.
    
    Reglas de inclusión (escalables):
    1. Si tiene _meta.publish == True -> publicable
    2. Si tiene _meta.publish == False -> NO publicable
    3. Si NO tiene _meta.publish:
       - Heurística: tiene 'caratula' Y 'cuerpo' -> es formato real (publicable)
       - Si no tiene estas estructuras -> es config (NO publicable)
    """
    meta = fmt.raw_data.get("_meta") or {}
    
    # Si _meta.publish está definido, usar ese valor
    if "publish" in meta:
        return bool(meta.get("publish"))
    
    # Si _meta.entity != "format", no es publicable
    entity = meta.get("entity", "").lower()
    if entity and entity != "format":
        return False  # es config u otro tipo
    
    # Heurística: formatos reales tienen 'caratula' y/o 'cuerpo'
    has_caratula = "caratula" in fmt.raw_data
    has_cuerpo = "cuerpo" in fmt.raw_data
    
    return has_caratula or has_cuerpo


def load_all_formats(university: Optional[str] = None, include_unpublished: bool = False) -> List[InternalFormat]:
    """
    Carga todos los formatos disponibles (opcionalmente filtrados por universidad).
    
    Args:
        university: Filtrar por código de universidad
        include_unpublished: Si True, incluye formatos no publicables (para diagnóstico)
    
    Returns:
        Lista de formatos. Por defecto solo los publicables.
    """
    items = discover_format_files(university)
    formats = []
    for item in items:
        try:
            fmt = load_internal_format(item)
            
            # Filtrar solo publicables a menos que se pida incluir todos
            if include_unpublished or is_publishable_format(fmt):
                formats.append(fmt)
        except Exception:
            # Skip formatos que no se pueden cargar
            continue
    return formats


# ─────────────────────────────────────────────────────────────────────────────
# CATALOG VERSIONING
# ─────────────────────────────────────────────────────────────────────────────

def get_catalog_version(formats: Optional[List[InternalFormat]] = None) -> str:
    """
    Calcula la versión global del catálogo.
    Es un hash de todos los hashes individuales ordenados por ID.
    """
    if formats is None:
        formats = load_all_formats()

    # Construir lista de pares id:hash ordenada
    pairs = []
    for fmt in formats:
        fmt_hash = compute_format_hash(fmt)
        pairs.append(f"{fmt.id}:{fmt_hash}")

    pairs.sort()

    # Hash global
    global_content = "\n".join(pairs)
    return hashlib.sha256(global_content.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# DTO MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def map_to_dto_summary(fmt: InternalFormat) -> FormatSummary:
    """Mapea formato interno a DTO de resumen."""
    fmt_hash = compute_format_hash(fmt)
    return FormatSummary(
        id=fmt.id,
        title=fmt.title,
        university=fmt.university,
        category=fmt.category,  # Ahora viene directamente de _meta.category
        documentType=fmt.document_type,
        version=fmt_hash[:16],  # Hash corto para versión
    )


def map_to_dto_detail(fmt: InternalFormat) -> FormatDetail:
    """Mapea formato interno a DTO de detalle."""
    fmt_hash = compute_format_hash(fmt)

    # Mapear campos con validación de tipo
    fields = []
    for f in fmt.fields:
        raw_type = f.get("type", "text")
        # Normalizar tipo al enum válido
        try:
            field_type = FieldType(raw_type)
        except ValueError:
            field_type = FieldType.TEXT  # Fallback a text si es inválido

        # options solo para select, None para otros
        options = None
        if field_type == FieldType.SELECT:
            raw_options = f.get("options")
            if raw_options and isinstance(raw_options, list) and len(raw_options) > 0:
                options = raw_options
            else:
                # Si select no tiene opciones válidas, convertir a text
                field_type = FieldType.TEXT

        fields.append(FormatField(
            name=f.get("name", ""),
            label=f.get("label", f.get("name", "")),
            type=field_type,
            required=f.get("required", False),
            default=f.get("default"),
            options=options,
            validation=f.get("validation"),
            order=f.get("order"),
            section=f.get("section"),
        ))

    # Mapear assets
    assets = []
    for a in fmt.assets:
        assets.append(AssetRef(
            id=a.get("id", ""),
            kind=a.get("kind", "unknown"),
            url=_resolve_asset_url(a),
        ))

    # Template ref
    template_ref = None
    if fmt.template_kind:
        template_ref = TemplateRef(
            kind=fmt.template_kind,
            uri=f"gicatesis://templates/{fmt.id}",
        )

    # Rules
    rules = None
    if fmt.rules:
        rules = RuleSet(
            margins=fmt.rules.get("margins"),
            font=fmt.rules.get("font"),
            lineSpacing=fmt.rules.get("lineSpacing"),
        )

    return FormatDetail(
        id=fmt.id,
        title=fmt.title,
        university=fmt.university,
        category=fmt.category,  # Ahora viene directamente de _meta.category
        documentType=fmt.document_type,
        version=fmt_hash[:16],
        templateRef=template_ref,
        fields=fields,
        assets=assets,
        rules=rules,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC SERVICE API
# ─────────────────────────────────────────────────────────────────────────────

def list_formats(
    university: Optional[str] = None,
    category: Optional[str] = None,
    document_type: Optional[str] = None,
) -> Tuple[List[FormatSummary], str]:
    """
    Lista formatos con filtros opcionales.
    Retorna: (lista de summaries, catalogVersion)
    """
    formats = load_all_formats(university)

    # Filtros adicionales
    if category:
        formats = [f for f in formats if f.category.lower() == category.lower()]
    if document_type:
        formats = [f for f in formats if f.document_type and f.document_type.lower() == document_type.lower()]

    # Calcular versión
    catalog_version = get_catalog_version(formats) if formats else hashlib.sha256(b"empty").hexdigest()

    # Mapear a DTOs
    summaries = [map_to_dto_summary(f) for f in formats]

    return summaries, catalog_version


def get_format_detail_by_id(format_id: str) -> Tuple[Optional[FormatDetail], Optional[str]]:
    """
    Obtiene el detalle de un formato por ID.
    Retorna: (FormatDetail, formatHash) o (None, None) si no existe.
    """
    # Buscar en el catálogo
    formats = load_all_formats()

    for fmt in formats:
        if fmt.id == format_id:
            detail = map_to_dto_detail(fmt)
            fmt_hash = compute_format_hash(fmt)
            return detail, fmt_hash

    return None, None


def get_catalog_version_info() -> CatalogVersionResponse:
    """
    Obtiene información de versión del catálogo.
    """
    formats = load_all_formats()
    version = get_catalog_version(formats)
    generated_at = datetime.now(timezone.utc).isoformat()

    return CatalogVersionResponse(
        version=version,
        generatedAt=generated_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CATALOG VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

VALID_FIELD_TYPES = {"text", "textarea", "number", "date", "select", "boolean"}


def validate_format_dict(fmt: InternalFormat) -> List[FormatValidationError]:
    """
    Valida un formato interno y retorna lista de errores.
    Detecta: tipos inválidos, select sin options, IDs vacíos, etc.
    """
    errors: List[FormatValidationError] = []

    # Validar campos requeridos
    if not fmt.id or fmt.id.strip() == "":
        errors.append(FormatValidationError(
            format_id=fmt.id or "unknown",
            field=None,
            error="Format ID is empty or missing",
            error_type="missing_id",
        ))

    if not fmt.title or fmt.title.strip() == "":
        errors.append(FormatValidationError(
            format_id=fmt.id,
            field="title",
            error="Format title is empty or missing",
            error_type="missing_field",
        ))

    if not fmt.university or fmt.university.strip() == "":
        errors.append(FormatValidationError(
            format_id=fmt.id,
            field="university",
            error="University code is empty or missing",
            error_type="missing_field",
        ))

    # Validar campos del wizard
    for i, field in enumerate(fmt.fields):
        field_name = field.get("name", f"field_{i}")

        # Validar tipo
        field_type = field.get("type", "text")
        if field_type not in VALID_FIELD_TYPES:
            errors.append(FormatValidationError(
                format_id=fmt.id,
                field=field_name,
                error=f"Invalid field type '{field_type}'. Valid types: {VALID_FIELD_TYPES}",
                error_type="invalid_type",
            ))

        # Validar select/options
        options = field.get("options")
        if field_type == "select":
            if not options or not isinstance(options, list) or len(options) == 0:
                errors.append(FormatValidationError(
                    format_id=fmt.id,
                    field=field_name,
                    error="Field type 'select' requires non-empty 'options' list",
                    error_type="missing_options",
                ))
        elif options is not None:
            errors.append(FormatValidationError(
                format_id=fmt.id,
                field=field_name,
                error=f"Field type '{field_type}' should not have 'options'",
                error_type="unexpected_options",
            ))

    # Validar assets
    for i, asset in enumerate(fmt.assets):
        asset_id = asset.get("id", f"asset_{i}")

        if not asset_id or asset_id.strip() == "":
            errors.append(FormatValidationError(
                format_id=fmt.id,
                field=f"asset_{i}",
                error="Asset ID is empty",
                error_type="missing_asset_id",
            ))

        if not asset.get("kind"):
            errors.append(FormatValidationError(
                format_id=fmt.id,
                field=asset_id,
                error="Asset kind is missing",
                error_type="missing_asset_kind",
            ))

    return errors


def validate_catalog() -> CatalogValidationResponse:
    """
    Valida todo el catálogo y retorna reporte de errores.
    """
    formats = load_all_formats()
    all_errors: List[FormatValidationError] = []
    seen_ids: Dict[str, str] = {}  # id -> source_path for duplicate detection
    valid_count = 0

    for fmt in formats:
        # Check for duplicate IDs
        if fmt.id in seen_ids:
            all_errors.append(FormatValidationError(
                format_id=fmt.id,
                field=None,
                error=f"Duplicate format ID. Also found in: {seen_ids[fmt.id]}",
                error_type="duplicate_id",
            ))
        else:
            seen_ids[fmt.id] = str(fmt.source_path)

        # Validate individual format
        format_errors = validate_format_dict(fmt)
        if format_errors:
            all_errors.extend(format_errors)
        else:
            valid_count += 1

    return CatalogValidationResponse(
        total_formats=len(formats),
        valid_formats=valid_count,
        invalid_formats=len(formats) - valid_count,
        errors=all_errors,
    )

