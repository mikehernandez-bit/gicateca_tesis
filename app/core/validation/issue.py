"""
Archivo: app/core/validation/issue.py
Define el tipo Issue para reportar errores y warnings de validación.
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
