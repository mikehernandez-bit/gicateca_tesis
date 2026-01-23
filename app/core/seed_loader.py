"""
Archivo: app/core/seed_loader.py
Proposito:
- Carga datos semilla desde data/seed para entornos sin BD.

Responsabilidades:
- Leer archivos JSON de ejemplo y devolver listas/objetos.
No hace:
- No persiste datos ni valida schemas.

Entradas/Salidas:
- Entradas: nombre de archivo JSON de seed.
- Salidas: datos parseados o lista vacia si no existe.

Dependencias:
- pathlib.Path, json.

Puntos de extension:
- Reemplazar por acceso a BD o API externa.

Donde tocar si falla:
- Revisar rutas de data/seed y lectura UTF-8.
"""

from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[2]  # formatoteca_scaffold/
SEED_DIR = ROOT / "data" / "seed"

def load_json(filename: str) -> Any:
    """Carga un JSON de seed y retorna [] si no existe."""
    path = SEED_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
