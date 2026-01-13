"""Lectura simple de data de ejemplo (sin BD).

Los practicantes pueden reemplazar esto luego por:
- Base de datos (PostgreSQL, SQLite)
- API externa
- Panel admin con persistencia
"""

from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parents[2]  # formatoteca_scaffold/
SEED_DIR = ROOT / "data" / "seed"

def load_json(filename: str) -> Any:
    path = SEED_DIR / filename
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
