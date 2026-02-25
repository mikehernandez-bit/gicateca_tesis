"""
Archivo: tests/conftest.py
Propósito: Configuración compartida de pytest — fixtures y sys.path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── Agregar raíz del proyecto al sys.path ──────────────────────
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ── Fixtures compartidos ───────────────────────────────────────

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Ruta raíz del proyecto."""
    return ROOT


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Directorio de datos JSON de formatos."""
    return project_root / "app" / "data"


@pytest.fixture(scope="session")
def unac_data_dir(data_dir: Path) -> Path:
    """Directorio de datos UNAC."""
    return data_dir / "unac"


@pytest.fixture(scope="session")
def uni_data_dir(data_dir: Path) -> Path:
    """Directorio de datos UNI."""
    return data_dir / "uni"
