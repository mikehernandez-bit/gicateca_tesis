"""Shared loaders for data access across modules."""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(file_path: Path) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {file_path}")


def get_data_dir(uni: str = "unac") -> Path:
    """Get the path to the data directory for a university code."""
    uni = (uni or "unac").strip().lower()
    app_dir = Path(__file__).resolve().parents[1]
    return app_dir / "data" / uni


@dataclass(frozen=True)
class FormatIndexItem:
    format_id: str
    uni: str
    categoria: str
    enfoque: str
    path: Path
    titulo: str


_ENFOQUE_ALIASES = {
    "cual": "cual",
    "cualitativo": "cual",
    "cuant": "cuant",
    "cuantitativo": "cuant",
}

_IGNORE_FILENAMES = {"alerts.json"}


def _normalize_format_id(raw_id: str, uni: str) -> str:
    if not raw_id:
        return ""
    normalized = re.sub(r"[_\s]+", "-", raw_id.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized.startswith(f"{uni}-"):
        normalized = f"{uni}-{normalized}"
    return normalized


def _derive_enfoque(tokens: List[str]) -> str:
    for token in tokens:
        mapped = _ENFOQUE_ALIASES.get(token)
        if mapped:
            return mapped
    return "general"


def _humanize_id(format_id: str, uni: str) -> str:
    cleaned = format_id
    if cleaned.startswith(f"{uni}-"):
        cleaned = cleaned[len(uni) + 1 :]
    parts = [p for p in re.split(r"[-_]+", cleaned) if p]
    return " ".join(word.capitalize() for word in parts) or format_id


def discover_format_files(uni: str) -> List[FormatIndexItem]:
    """Discover JSON format files for a university."""
    uni = (uni or "unac").strip().lower()
    data_dir = get_data_dir(uni)
    if not data_dir.exists():
        return []

    items: List[FormatIndexItem] = []
    for path in data_dir.rglob("*.json"):
        if path.name in _IGNORE_FILENAMES:
            continue
        if path.name.endswith(".sample.json"):
            continue
        if "seed" in path.parts:
            continue
        if "_spec_backup" in path.parts:
            continue

        rel_path = path.relative_to(data_dir)
        categoria = rel_path.parent.name.lower() if rel_path.parent != Path(".") else "general"
        stem = path.stem
        tokens = [t for t in re.split(r"[_-]+", stem.lower()) if t]
        enfoque = _derive_enfoque(tokens)

        titulo = None
        try:
            data = load_json_file(path)
            if isinstance(data, dict):
                titulo = data.get("titulo")
                raw_id = data.get("id") or stem
            else:
                raw_id = stem
        except Exception:
            raw_id = stem

        format_id = _normalize_format_id(raw_id, uni)
        if not titulo:
            titulo = _humanize_id(format_id, uni)

        items.append(
            FormatIndexItem(
                format_id=format_id,
                uni=uni,
                categoria=categoria,
                enfoque=enfoque,
                path=path.resolve(),
                titulo=str(titulo),
            )
        )

    items.sort(key=lambda item: (item.categoria, item.enfoque, item.titulo.lower(), item.format_id))
    return items


def find_format_index(format_id: str) -> Optional[FormatIndexItem]:
    if not format_id:
        return None
    parts = format_id.split("-")
    uni = (parts[0] if parts else "unac").strip().lower()
    normalized = _normalize_format_id(format_id, uni)
    for item in discover_format_files(uni):
        if item.format_id == normalized:
            return item
    return None


def load_format_by_id(format_id: str) -> Dict[str, Any]:
    """Load raw JSON by format id, attaching metadata in _meta if missing."""
    item = find_format_index(format_id)
    if not item:
        raise FileNotFoundError(f"Formato no encontrado: {format_id}")

    data = load_json_file(item.path)
    if isinstance(data, dict):
        payload = dict(data)
        if "_meta" not in payload:
            payload["_meta"] = {
                "format_id": item.format_id,
                "uni": item.uni,
                "categoria": item.categoria,
                "enfoque": item.enfoque,
                "titulo": item.titulo,
                "path": str(item.path),
            }
        return payload
    return {"_meta": {"format_id": item.format_id, "uni": item.uni, "path": str(item.path)}, "data": data}
