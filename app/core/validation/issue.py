"""
=============================================================================
ARCHIVO: app/core/validation/issue.py
FASE: 3 - Calidad y Validación
=============================================================================

PROPÓSITO:
Define el tipo Issue para reportar errores y warnings durante la validación.
Es el tipo base que devuelven todas las funciones de validación.

CLASES:
- Severity (Enum): ERROR | WARN
- Issue (dataclass): Representa un problema encontrado
  Campos: severity, code, message, file, context

COMUNICACIÓN CON OTROS MÓDULOS:
- Es IMPORTADO por:
  - format_validation.py
  - references_validation.py
  - repo_checks.py
  - scripts/validate_data.py

EJEMPLO DE USO:
    from app.core.validation.issue import Issue, Severity
    
    issue = Issue(
        severity=Severity.ERROR,
        code="META_MISSING",
        message="Falta campo _meta",
        file="formato.json"
    )
    print(issue)  # [ERROR] META_MISSING - Falta campo _meta (formato.json)

=============================================================================
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    """Severidad del issue de validación."""
    ERROR = "ERROR"
    WARN = "WARN"


@dataclass
class Issue:
    """Representa un issue de validación."""
    severity: Severity
    code: str
    message: str
    file: Optional[str] = None
    context: Optional[str] = None
    
    def __str__(self) -> str:
        parts = [f"[{self.severity.value}]", self.code, "-", self.message]
        if self.file:
            parts.append(f"({self.file})")
        return " ".join(parts)
    
    def is_error(self) -> bool:
        return self.severity == Severity.ERROR
