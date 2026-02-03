"""
Módulo de validación de datos para GicaTesis.
Provee validadores de schemas y reglas de negocio.
"""
from app.core.validation.format_validation import (
    validate_format_schema,
    validate_format_rules,
)
from app.core.validation.references_validation import (
    validate_references_config_schema,
    validate_references_rules,
)
from app.core.validation.repo_checks import (
    check_id_collisions,
    check_providers_registered,
    check_assets_exist,
    run_all_repo_checks,
)
from app.core.validation.issue import Issue, Severity

__all__ = [
    "Issue",
    "Severity",
    "validate_format_schema",
    "validate_format_rules",
    "validate_references_config_schema",
    "validate_references_rules",
    "check_id_collisions",
    "check_providers_registered",
    "check_assets_exist",
    "run_all_repo_checks",
]
