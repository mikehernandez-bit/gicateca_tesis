"""Schemas for catalog module."""

from typing import List, Optional
from pydantic import BaseModel


class FormatoOut(BaseModel):
    id: Optional[str] = None
    uni: Optional[str] = None
    titulo: Optional[str] = None
    facultad: Optional[str] = None
    escuela: Optional[str] = None
    estado: Optional[str] = None
    version: Optional[str] = None
    fecha: Optional[str] = None
    resumen: Optional[str] = None
    archivos: Optional[List[dict]] = None
    historial: Optional[List[dict]] = None


class FormatoGenerateIn(BaseModel):
    format: str
    sub_type: str


class FormatoGenerateOut(BaseModel):
    ok: bool
    filename: str
    path: str
