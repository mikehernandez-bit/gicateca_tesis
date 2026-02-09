"""
Archivo: app/modules/api/dtos.py
Propósito:
- Define contratos de datos (DTOs) estables para la API de Formatos v1.
- Estos modelos son el contrato público que GicaGen consume.
- STRICT: extra="forbid" para rechazar campos no esperados.

Responsabilidades:
- Definir estructuras Pydantic inmutables y validadas.
- Proveer serialización JSON consistente.
- Validar reglas de negocio (select requiere options, etc.)
No hace:
- No carga datos ni calcula hashes (eso es del service).

Dependencias:
- pydantic

Puntos de extensión:
- Agregar campos opcionales según evolucione el dominio.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# FIELD TYPE ENUM (STRICT)
# -----------------------------------------------------------------------------

class FieldType(str, Enum):
    """Tipos de campo permitidos - strict enum."""
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    BOOLEAN = "boolean"


# -----------------------------------------------------------------------------
# STRICT DTOs
# -----------------------------------------------------------------------------

class FormatField(BaseModel):
    """Campo de entrada para el wizard de generación."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nombre técnico del campo")
    label: str = Field(..., description="Etiqueta visible en UI")
    type: FieldType = Field(default=FieldType.TEXT, description="Tipo de input")
    required: bool = Field(default=False, description="Si es obligatorio")
    default: Optional[Any] = Field(default=None, description="Valor por defecto")
    options: Optional[List[str]] = Field(default=None, description="Opciones si type=select")
    validation: Optional[Dict[str, Any]] = Field(
        default=None, description="Reglas de validación (regex, min, max, etc.)"
    )
    order: Optional[int] = Field(default=None, description="Orden de aparición")
    section: Optional[str] = Field(default=None, description="Sección/grupo del campo")

    @model_validator(mode="after")
    def validate_select_options(self) -> "FormatField":
        """Valida que select tenga options y otros tipos no."""
        if self.type == FieldType.SELECT:
            if not self.options or len(self.options) == 0:
                raise ValueError("Field type 'select' requires non-empty 'options' list")
        else:
            if self.options is not None:
                raise ValueError(f"Field type '{self.type.value}' must not have 'options'")
        return self


class TemplateRef(BaseModel):
    """Referencia a la plantilla de generación."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: str = Field(..., description="Tipo de plantilla: docx, html, etc.")
    uri: str = Field(..., description="URI lógica estable (no path interno)")


class AssetRef(BaseModel):
    """Referencia a un asset (logo, imagen, etc.)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="ID estable del asset")
    kind: str = Field(..., min_length=1, description="Tipo: logo, image, signature, etc.")
    url: str = Field(..., min_length=1, description="URL pública estable")

    @field_validator("url")
    @classmethod
    def validate_url_not_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Asset url cannot be empty")
        return v


class RuleSet(BaseModel):
    """Reglas de formato opcionales (márgenes, fuentes, etc.)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    margins: Optional[Dict[str, float]] = Field(default=None, description="Márgenes en cm")
    font: Optional[str] = Field(default=None, description="Fuente principal")
    fontSize: Optional[int] = Field(default=None, description="Tamaño de fuente")
    lineSpacing: Optional[float] = Field(default=None, description="Interlineado")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Reglas adicionales")


class FormatSummary(BaseModel):
    """Resumen de un formato para listados."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="ID estable único del formato")
    title: str = Field(..., min_length=1, description="Título legible")
    university: str = Field(..., min_length=1, description="Código de universidad (unac, uni, etc.)")
    category: str = Field(..., min_length=1, description="Categoría (general, especifica, etc.)")
    documentType: Optional[str] = Field(default=None, description="Tipo de documento")
    version: str = Field(..., min_length=1, description="Hash corto del contenido")


class FormatDetail(BaseModel):
    """Detalle completo de un formato para generación."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="ID estable único")
    title: str = Field(..., min_length=1, description="Título legible")
    university: str = Field(..., min_length=1, description="Código de universidad")
    category: str = Field(..., min_length=1, description="Categoría")
    documentType: Optional[str] = Field(default=None, description="Tipo de documento")
    version: str = Field(..., min_length=1, description="Hash del contenido")
    templateRef: Optional[TemplateRef] = Field(default=None, description="Referencia a plantilla")
    fields: List[FormatField] = Field(default_factory=list, description="Campos del wizard")
    assets: List[AssetRef] = Field(default_factory=list, description="Assets asociados")
    rules: Optional[RuleSet] = Field(default=None, description="Reglas de formato")
    definition: Dict[str, Any] = Field(
        default_factory=dict,
        description="Definicion JSON completa del formato (estructura extendida para n8n)",
    )


class CatalogVersionResponse(BaseModel):
    """Respuesta del endpoint de versión."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(..., min_length=1, description="Hash global del catálogo")
    generatedAt: str = Field(..., min_length=1, description="Timestamp ISO de generación")


# -----------------------------------------------------------------------------
# VALIDATION RESPONSE (for /validate endpoint)
# -----------------------------------------------------------------------------

class FormatValidationError(BaseModel):
    """Error de validación de un formato específico."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    format_id: str = Field(..., description="ID del formato con error")
    field: Optional[str] = Field(default=None, description="Campo específico si aplica")
    error: str = Field(..., description="Descripción del error")
    error_type: str = Field(..., description="Tipo de error (missing_field, invalid_type, etc.)")


class CatalogValidationResponse(BaseModel):
    """Respuesta del endpoint de validación del catálogo."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_formats: int = Field(..., description="Total de formatos en el catálogo")
    valid_formats: int = Field(..., description="Formatos válidos")
    invalid_formats: int = Field(..., description="Formatos con errores")
    errors: List[FormatValidationError] = Field(default_factory=list, description="Lista de errores")
