"""
Archivo: app/core/validation/references_validation.py
Validación de references_config.json por universidad.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.validation.issue import Issue, Severity

_SCHEMA_PATH = Path(__file__).parents[2] / "data" / "schemas" / "references_config.schema.json"
_SCHEMA: Optional[Dict] = None


def _get_schema() -> Dict:
    """Carga el schema de references_config (lazy)."""
    global _SCHEMA
    if _SCHEMA is None:
        if _SCHEMA_PATH.exists():
            _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            _SCHEMA = {}
    return _SCHEMA


def validate_references_config_schema(
    config_data: Dict[str, Any],
    file_path: Optional[str] = None
) -> List[Issue]:
    """Valida references_config contra schema."""
    issues: List[Issue] = []
    
    try:
        import jsonschema
        schema = _get_schema()
        if schema:
            jsonschema.validate(config_data, schema)
    except ImportError:
        # Validación manual
        if not isinstance(config_data.get("enabled"), list):
            issues.append(Issue(
                severity=Severity.ERROR,
                code="REFS_ENABLED_MISSING",
                message="Falta 'enabled' o no es array",
                file=file_path
            ))
    except Exception as e:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="REFS_SCHEMA_INVALID",
            message=str(e),
            file=file_path
        ))
    
    return issues


def validate_references_rules(
    config_data: Dict[str, Any],
    file_path: Optional[str] = None
) -> List[Issue]:
    """Valida reglas de negocio de references_config."""
    issues: List[Issue] = []
    
    enabled = config_data.get("enabled", [])
    default = config_data.get("default")
    
    # Regla 1: enabled no vacío
    if not enabled:
        issues.append(Issue(
            severity=Severity.WARN,
            code="REFS_ENABLED_EMPTY",
            message="Lista 'enabled' está vacía",
            file=file_path
        ))
    
    # Regla 2: default debe estar en enabled
    if default and enabled and default not in enabled:
        issues.append(Issue(
            severity=Severity.ERROR,
            code="REFS_DEFAULT_NOT_ENABLED",
            message=f"Default '{default}' no está en enabled: {enabled}",
            file=file_path
        ))
    
    return issues
