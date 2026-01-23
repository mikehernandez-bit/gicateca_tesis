"""
Archivo: app/core/registry.py
Proposito:
- Descubre e instancia providers de universidades de forma dinamica.

Responsabilidades:
- Escanear app/universities/*/provider.py y validar contrato.
- Exponer helpers para listar universidades y obtener provider por codigo.
No hace:
- No carga formatos ni genera documentos.

Entradas/Salidas:
- Entradas: codigo de universidad (str).
- Salidas: providers registrados (UniversityProvider).

Dependencias:
- importlib, pathlib, app.universities.contracts.

Puntos de extension:
- Ajustar reglas de discovery o validaciones de provider.

Donde tocar si falla:
- Verificar rutas de providers o errores de import en discovery.
"""
from __future__ import annotations

import re
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Dict

from app.universities.contracts import UniversityProvider

_UNIVERSITIES_DIR = Path(__file__).resolve().parents[1] / "universities"
_CODE_RE = re.compile(r"^[a-z0-9_-]+$")


def _iter_provider_modules():
    """Itera modulos provider disponibles en app/universities."""
    for child in sorted(_UNIVERSITIES_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        name = child.name
        if name in {"__pycache__"} or name.startswith(("_", ".")):
            continue
        if not (child / "provider.py").exists():
            continue
        yield f"app.universities.{name}.provider"


def _load_provider(module_name: str) -> UniversityProvider:
    """Carga un provider desde un modulo y valida su exposicion."""
    # Import dinamico para mantener el core libre de hardcodes.
    module = import_module(module_name)
    if hasattr(module, "PROVIDER"):
        provider = module.PROVIDER
    elif hasattr(module, "get_provider"):
        provider = module.get_provider()
    else:
        raise ImportError(f"Provider no expuesto en {module_name}")
    return provider


def _validate_provider(provider: UniversityProvider) -> None:
    """Valida el contrato minimo que debe cumplir un provider."""
    if not isinstance(provider, UniversityProvider):
        raise TypeError("Provider no cumple el contrato requerido.")
    if not isinstance(provider.code, str) or not provider.code:
        raise ValueError("Provider.code es requerido.")
    if not _CODE_RE.match(provider.code):
        raise ValueError(f"Provider.code invalido: {provider.code}")
    if not isinstance(provider.display_name, str) or not provider.display_name:
        raise ValueError("Provider.display_name es requerido.")
    data_dir = provider.get_data_dir()
    if not isinstance(data_dir, Path):
        raise TypeError("Provider.get_data_dir() debe retornar Path.")


@lru_cache(maxsize=1)
def discover_providers() -> Dict[str, UniversityProvider]:
    """Descubre providers disponibles en el filesystem."""
    providers: Dict[str, UniversityProvider] = {}
    for module_name in _iter_provider_modules():
        provider = _load_provider(module_name)
        _validate_provider(provider)
        code = provider.code
        if code in providers:
            raise ValueError(f"Codigo de universidad duplicado: {code}")
        providers[code] = provider
    return providers


def get_provider(code: str) -> UniversityProvider:
    """Retorna el provider por codigo o lanza KeyError si no existe."""
    code = (code or "").strip().lower()
    providers = discover_providers()
    if code in providers:
        return providers[code]
    raise KeyError(f"Universidad no registrada: {code}")


def list_universities() -> list[str]:
    """Lista codigos de universidades registradas."""
    return sorted(discover_providers().keys())
