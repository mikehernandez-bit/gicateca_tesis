"""Shared API contract for AI-generated content payloads.

This module defines the canonical ``aiResult.sections[].content`` shape used by
the public GicaTesis API. The contract is backward-compatible with plain-text
content while also accepting structured blocks (paragraphs, tables, figures).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


_CANONICAL_PLACEHOLDER_PATH = "assets/placeholder_figura.png"


class ParagraphBlock(BaseModel):
    tipo: Literal["parrafo"]
    texto: str = Field(..., description="Paragraph text")

    @field_validator("texto")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("Paragraph text cannot be empty")
        return text


class TableBlock(BaseModel):
    tipo: Literal["tabla"]
    encabezados: list[str] = Field(..., min_length=1)
    filas: list[list[str]] = Field(..., min_length=1)
    id: Optional[str] = None
    titulo: Optional[str] = None
    nota_pie: Optional[str] = None
    orientacion: Optional[Literal["portrait", "landscape"]] = None

    @field_validator("encabezados")
    @classmethod
    def _validate_headers(cls, value: list[str]) -> list[str]:
        headers = [str(item or "").strip() for item in value]
        if not any(item for item in headers):
            raise ValueError("Table must define at least one non-empty header")
        return headers

    @field_validator("filas")
    @classmethod
    def _validate_rows(cls, value: list[list[str]]) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in value:
            if not isinstance(row, (list, tuple)):
                raise ValueError("Each table row must be a list")
            cells = [str(cell or "").strip() for cell in row]
            rows.append(cells)
        if not rows:
            raise ValueError("Table must define at least one row")
        return rows

    @model_validator(mode="after")
    def _normalize_rows(self) -> "TableBlock":
        header_count = len(self.encabezados)
        normalized: list[list[str]] = []
        for row in self.filas:
            cells = list(row[:header_count])
            if len(cells) < header_count:
                cells.extend([""] * (header_count - len(cells)))
            if any(cell.strip() for cell in cells):
                normalized.append(cells)
        if not normalized:
            raise ValueError(
                "Table must keep at least one non-empty row after normalization"
            )
        self.filas = normalized
        if self.orientacion is None:
            self.orientacion = "landscape" if header_count > 5 else "portrait"
        return self


class FigureBlock(BaseModel):
    tipo: Literal["figura"]
    caption: str = Field(..., description="Figure caption")
    ruta_placeholder: Optional[str] = None
    id: Optional[str] = None
    titulo: Optional[str] = None
    fuente: Optional[str] = None
    nota: Optional[str] = None
    nota_color: Optional[str] = None
    diagram_type: Optional[str] = None
    diagram_data: Optional[dict[str, Any]] = None
    numbered: bool = True

    @field_validator("caption")
    @classmethod
    def _validate_caption(cls, value: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("Figure caption cannot be empty")
        return text

    @field_validator("ruta_placeholder", mode="before")
    @classmethod
    def _normalize_placeholder_path(cls, value: Any) -> Optional[str]:
        text = str(value or "").strip()
        if not text:
            return None
        if text.lower() == "placeholder":
            return _CANONICAL_PLACEHOLDER_PATH
        return text

    @model_validator(mode="after")
    def _validate_visual_source(self) -> "FigureBlock":
        if not self.ruta_placeholder and not self.diagram_type:
            raise ValueError("Figure must define an image path or a deterministic diagram")
        return self


class FormulaBlock(BaseModel):
    tipo: Literal["formula"]
    id: Optional[str] = None
    texto: Optional[str] = None
    latex: Optional[str] = None
    numero: Optional[str] = None
    alineacion: Literal["center", "left", "right"] = "center"

    @model_validator(mode="after")
    def _validate_formula_text(self) -> "FormulaBlock":
        text = str(self.texto or "").strip()
        latex = str(self.latex or "").strip()
        if not text and not latex:
            raise ValueError("Formula must define texto or latex")
        self.texto = text or None
        self.latex = latex or None
        if self.numero is not None:
            self.numero = str(self.numero or "").strip() or None
        return self


AIBlock = Annotated[
    Union[ParagraphBlock, TableBlock, FigureBlock, FormulaBlock],
    Field(discriminator="tipo"),
]
AIContent = Union[str, list[AIBlock]]


class AISection(BaseModel):
    """A section of AI-generated content."""

    sectionId: Optional[str] = Field(
        default=None,
        description="Stable section ID from sectionIndex",
    )
    path: Optional[str] = Field(
        default=None,
        description="Section path like 'Capitulo I/Introduccion'",
    )
    content: AIContent = Field(
        ...,
        description="AI-generated section content: plain text or structured blocks",
    )

    @model_validator(mode="after")
    def validate_locator(self) -> "AISection":
        if not (self.sectionId or self.path):
            raise ValueError(
                "AISection requires at least one locator: path or sectionId"
            )
        return self


class AIResult(BaseModel):
    """AI-generated content result."""

    sections: list[AISection] = Field(default_factory=list)


def serialize_ai_content(content: AIContent) -> Any:
    """Return JSON-serializable content for the generation preprocessor."""
    if isinstance(content, str):
        return content
    return [block.model_dump(exclude_none=True) for block in content]


def serialize_ai_sections(sections: list[AISection]) -> list[dict[str, Any]]:
    """Serialize section models into the dict shape expected downstream."""
    serialized: list[dict[str, Any]] = []
    for section in sections:
        serialized.append(
            {
                "sectionId": section.sectionId,
                "path": section.path,
                "content": serialize_ai_content(section.content),
            }
        )
    return serialized


def validation_error_to_detail(exc: ValidationError) -> list[dict[str, Any]]:
    """Return FastAPI-friendly error payloads preserving Pydantic details."""
    return [dict(item) for item in exc.errors()]
