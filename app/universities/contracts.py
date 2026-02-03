"""
Archivo: app/universities/contracts.py
Proposito:
- Define el contrato (Protocol) para providers de universidades.

Responsabilidades:
- Especificar metodos requeridos por el core (data_dir, generators, alerts).
- Proveer una implementacion simple reutilizable con defaults para view-models.
No hace:
- No descubre providers ni carga formatos directamente.

Entradas/Salidas:
- Entradas: categorias de formato y rutas de datos.
- Salidas: comandos de generacion y listas de datos auxiliares.

Dependencias:
- dataclasses, typing, pathlib, json.

Puntos de extension:
- Agregar metodos al contrato si se necesitan nuevas capacidades.

Donde tocar si falla:
- Revisar cumplimiento del contrato en provider.py de cada universidad.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, Optional, Protocol, Sequence, Union, runtime_checkable

GeneratorCommand = Union[Path, Sequence[str]]


@runtime_checkable
class UniversityProvider(Protocol):
    code: str
    display_name: str
    data_dir: Path
    name: str

    def get_data_dir(self) -> Path:
        """Retorna la carpeta app/data/<code>."""

    def get_generator_command(self, category: str) -> GeneratorCommand:
        """Retorna el comando o ruta del generador para una categoria."""

    def list_alerts(self) -> list:
        """Retorna la lista de alertas de la universidad."""

    def list_formatos(self) -> list:
        """Retorna formatos legacy si existe formatos.json."""


@dataclass(frozen=True)
class SimpleUniversityProvider:
    """
    Implementacion simple del contrato UniversityProvider.
    
    Fase 2: Incluye default_logo_url y defaults para view-models de carátula.
    """
    code: str
    display_name: str
    data_dir: Path
    generator_map: Dict[str, GeneratorCommand]
    name: Optional[str] = None
    
    # Fase 2: Nuevos campos para view-models
    default_logo_url: str = "/static/assets/LogoGeneric.png"
    defaults: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normaliza name para templates legacy que esperan provider.name.
        if self.name is None:
            object.__setattr__(self, "name", self.display_name)

    def get_data_dir(self) -> Path:
        """Devuelve la carpeta de datos asociada al provider."""
        return self.data_dir

    def get_generator_command(self, category: str) -> GeneratorCommand:
        """Resuelve el generador segun la categoria solicitada."""
        category = (category or "").strip().lower()
        if category not in self.generator_map:
            raise ValueError(f"generator not available for category {category}")
        return self.generator_map[category]

    def list_alerts(self) -> list:
        """Carga alertas desde alerts.json si existe."""
        path = self.data_dir / "alerts.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def list_formatos(self) -> list:
        """Carga formatos legacy desde formatos.json si existe."""
        path = self.data_dir / "formatos.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    
    def get_default(self, key: str, fallback: str = "") -> str:
        """Obtiene un valor de defaults con fallback."""
        return self.defaults.get(key, fallback)
