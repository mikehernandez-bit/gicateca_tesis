"""
=============================================================================
ARCHIVO: app/core/validation/format_validation.py
FASE: 3 - Calidad y Validación
=============================================================================

PROPÓSITO:
Valida formatos JSON contra el schema y reglas de negocio.
Detecta problemas como _meta faltante, mismatch de universidad, logos inválidos.

FUNCIONES PRINCIPALES:
- validate_format_schema(format_data, file_path) -> List[Issue]
  Valida contra app/data/schemas/format.schema.json
  Usa jsonschema si disponible, sino validación manual básica.
  
- validate_format_rules(format_data, expected_uni_code, file_path) -> List[Issue]
  Valida reglas de negocio:
  1. _meta.id existe y no vacío
  2. _meta.uni existe y minúsculas
  3. _meta.uni coincide con carpeta (expected_uni_code)
  4. ruta_logo tiene formato válido

COMUNICACIÓN CON OTROS MÓDULOS:
- LEE: app/data/schemas/format.schema.json
- IMPORTA: issue.py (Issue, Severity)
- Es CONSUMIDO por:
  - scripts/validate_data.py
  - tests/test_repo_validation.py

CÓDIGOS DE ERROR QUE GENERA:
- SCHEMA_INVALID, META_MISSING, META_ID_MISSING, META_UNI_MISSING
- META_ID_EMPTY, META_UNI_EMPTY, META_UNI_CASE
- UNI_MISMATCH, LOGO_PATH_INVALID, LOGO_EXT_INVALID

=============================================================================
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.validation.issue import Issue, Severity

# Cargar schema desde archivo
_SCHEMA_PATH = Path(__file__).parents[2] / "data" / "schemas" / "format.schema.json"
_SCHEMA: Optional[Dict] = None


def _get_schema() -> Dict:
    """Carga el schema de formato (lazy)."""
    global _SCHEMA
    if _SCHEMA is None:
        if _SCHEMA_PATH.exists():
            _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            _SCHEMA = {}
    return _SCHEMA


def validate_format_schema(format_data: Dict[str, Any], file_path: Optional[str] = None) -> List[Issue]:
    """
    Valida un formato contra el JSON schema.
    Retorna lista de Issues (vacía si pasa).
    """
    issues: List[Issue] = []
    
    try:
        import jsonschema
        schema = _get_schema()
        if schema:
            jsonschema.validate(format_data, schema)
    except ImportError:
        # jsonschema no instalado, hacer validación manual básica
        return _validate_schema_manual(format_data, file_path)
    except jsonschema.ValidationError as e:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="SCHEMA_INVALID",
            message=str(e.message),
            file=file_path,
            context=str(e.path)
        ))
    except Exception as e:
        issues.append(Issue(
            severity=Severity.WARN,
            code="SCHEMA_ERROR",
            message=f"Error validando schema: {e}",
            file=file_path
        ))
    
    return issues


def _validate_schema_manual(format_data: Dict[str, Any], file_path: Optional[str] = None) -> List[Issue]:
    """Validación manual básica cuando jsonschema no está disponible."""
    issues: List[Issue] = []
    
    # Verificar _meta existe
    meta = format_data.get("_meta")
    if not meta:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_MISSING",
            message="Falta campo _meta",
            file=file_path
        ))
        return issues
    
    if not isinstance(meta, dict):
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_INVALID",
            message="_meta debe ser un objeto",
            file=file_path
        ))
        return issues
    
    # Verificar _meta.id
    if not meta.get("id"):
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_ID_MISSING",
            message="Falta _meta.id",
            file=file_path
        ))
    
    # Verificar _meta.uni
    if not meta.get("uni"):
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_UNI_MISSING",
            message="Falta _meta.uni",
            file=file_path
        ))
    
    return issues


def validate_format_rules(
    format_data: Dict[str, Any],
    expected_uni_code: Optional[str] = None,
    file_path: Optional[str] = None
) -> List[Issue]:
    """
    Valida reglas de negocio sobre un formato.
    
    Args:
        format_data: Diccionario del formato.
        expected_uni_code: Código de universidad esperado (por carpeta).
        file_path: Ruta del archivo para contexto.
    
    Returns:
        Lista de Issues.
    """
    issues: List[Issue] = []
    
    meta = format_data.get("_meta") or {}
    cfg = format_data.get("configuracion") or {}
    
    # Regla 1: _meta.id no vacío
    meta_id = meta.get("id", "")
    if not meta_id or not str(meta_id).strip():
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_ID_EMPTY",
            message="_meta.id está vacío",
            file=file_path
        ))
    
    # Regla 2: _meta.uni no vacío y minúsculas
    meta_uni = meta.get("uni", "")
    if not meta_uni or not str(meta_uni).strip():
        issues.append(Issue(
            severity=Severity.ERROR,
            code="META_UNI_EMPTY",
            message="_meta.uni está vacío",
            file=file_path
        ))
    elif str(meta_uni) != str(meta_uni).lower():
        issues.append(Issue(
            severity=Severity.WARN,
            code="META_UNI_CASE",
            message=f"_meta.uni debería ser minúsculas: {meta_uni}",
            file=file_path
        ))
    
    # Regla 3: Coincidencia con carpeta
    if expected_uni_code and meta_uni:
        if str(meta_uni).lower() != str(expected_uni_code).lower():
            issues.append(Issue(
                severity=Severity.ERROR,
                code="UNI_MISMATCH",
                message=f"_meta.uni '{meta_uni}' no coincide con carpeta '{expected_uni_code}'",
                file=file_path
            ))
    
    # Regla 4: ruta_logo válida
    ruta_logo = cfg.get("ruta_logo")
    if ruta_logo:
        ruta = str(ruta_logo)
        # Debe contener /static/ o ser relativa válida
        if "/static/" not in ruta and not ruta.startswith("/"):
            issues.append(Issue(
                severity=Severity.WARN,
                code="LOGO_PATH_INVALID",
                message=f"ruta_logo puede no ser válida: {ruta}",
                file=file_path
            ))
        # Extensión válida
        ext = ruta.lower().split(".")[-1] if "." in ruta else ""
        if ext and ext not in ("png", "jpg", "jpeg", "webp", "svg"):
            issues.append(Issue(
                severity=Severity.WARN,
                code="LOGO_EXT_INVALID",
                message=f"ruta_logo con extensión inusual: {ext}",
                file=file_path
            ))
    
    return issues
