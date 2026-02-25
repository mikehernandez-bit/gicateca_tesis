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

import logging
import re
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Dict

from app.universities.contracts import SimpleUniversityProvider, UniversityProvider

logger = logging.getLogger(__name__)

_UNIVERSITIES_DIR = Path(__file__).resolve().parents[1] / "universities"
_DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
_SHARED_GENERATOR = _UNIVERSITIES_DIR / "shared" / "universal_generator.py"
_CODE_RE = re.compile(r"^[a-z0-9_-]+$")
_IGNORE_DATA_DIRS = {"schemas", "references", "__pycache__"}


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
    """Descubre providers disponibles: primero explicitos, luego auto-discovery desde app/data/."""
    providers: Dict[str, UniversityProvider] = {}

    # 1. Providers explicitos (app/universities/*/provider.py) — prioridad maxima.
    for module_name in _iter_provider_modules():
        provider = _load_provider(module_name)
        _validate_provider(provider)
        code = provider.code
        if code in providers:
            raise ValueError(f"Codigo de universidad duplicado: {code}")
        providers[code] = provider

    # 2. Auto-discovery desde app/data/*/ para universidades sin provider.py explicito.
    if _DATA_ROOT.exists():
        for child in sorted(_DATA_ROOT.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            code = child.name.lower()
            if code in _IGNORE_DATA_DIRS or code.startswith(("_", ".")):
                continue
            if not _CODE_RE.match(code):
                continue
            if code in providers:
                continue  # Ya tiene provider explicito, no sobreescribir.
            # Detectar categorias de formato desde subdirectorios con *.json
            categories = _detect_categories(child)
            if not categories:
                continue  # Sin formatos, no registrar.
            generator_map = {cat: _SHARED_GENERATOR for cat in categories}
            auto_provider = SimpleUniversityProvider(
                code=code,
                display_name=code.upper(),
                data_dir=child,
                generator_map=generator_map,
                default_logo_url=f"/static/assets/Logo{code.upper()}.png",
                defaults={},
            )
            providers[code] = auto_provider
            logger.info("Auto-discovered university '%s' from app/data/%s/", code, code)

    return providers


def _detect_categories(data_dir: Path) -> list[str]:
    """Detecta categorias de formato en un directorio de universidad."""
    categories = []
    for sub in sorted(data_dir.iterdir()):
        if not sub.is_dir():
            continue
        if sub.name.startswith(("_", ".")) or sub.name == "__pycache__":
            continue
        # Verificar que tiene al menos un JSON de formato
        if any(f.suffix == ".json" for f in sub.iterdir() if f.is_file()):
            categories.append(sub.name.lower())
    return categories


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


def clear_provider_cache() -> None:
    """Invalida el cache de providers. Llamar despues de agregar/eliminar universidades."""
    discover_providers.cache_clear()
