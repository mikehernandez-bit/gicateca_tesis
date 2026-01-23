"""
Archivo: app/core/loaders.py
Proposito:
- Carga datos JSON y construye el indice de formatos disponibles.

Responsabilidades:
- Leer JSON con UTF-8 y manejar errores comunes.
- Descubrir formatos por universidad/categoria/enfoque desde app/data.
- Proveer busqueda por format_id y lectura con _meta.
No hace:
- No valida reglas de negocio ni genera documentos.

Entradas/Salidas:
- Entradas: codigos de universidad y format_id.
- Salidas: items de indice y payloads JSON normalizados.

Dependencias:
- json, pathlib, app.core.registry, app.core.paths.

Puntos de extension:
- Ajustar heuristicas de discovery o normalizacion de IDs.

Donde tocar si falla:
- Revisar discovery, normalizacion de IDs o lectura JSON.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json_file(file_path: Path) -> Any:
    """Carga y parsea un archivo JSON con UTF-8."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in file: {file_path}")


def get_data_dir(uni: str = "unac") -> Path:
    """Obtiene la carpeta de datos para una universidad."""
    from app.core.paths import get_data_dir as _get_data_dir

    return _get_data_dir(uni or "unac")


@dataclass(frozen=True)
class FormatIndexItem:
    """Entrada inmutable del indice de formatos descubiertos."""
    format_id: str
    uni: str
    categoria: str
    enfoque: str
    path: Path
    titulo: str
    data: Optional[Dict[str, Any]] = None


_ENFOQUE_ALIASES = {
    "cual": "cual",
    "cualitativo": "cual",
    "cuant": "cuant",
    "cuantitativo": "cuant",
}

_IGNORE_FILENAMES = {"alerts.json"}
_HIDDEN_PREFIXES = ("_", "__")
_MOJIBAKE_PATTERNS = (
    "\u00c3",
    "\u00c2",
    "\u00e2\u20ac",
    "\u00e2\u20ac\u00a2",
    "\u00e2\u20ac\u201c",
    "\u00e2\u20ac\u201d",
    "\u00c3\u00a1",
    "\u00c3\u00a9",
    "\u00c3\u00ad",
    "\u00c3\u00b3",
    "\u00c3\u00ba",
    "\u00c3\u00b1",
    "\u00c3\u008d",
    "\u00c3\u009a",
)


def _contains_mojibake(text: str) -> bool:
    return any(token in text for token in _MOJIBAKE_PATTERNS)


def _scan_mojibake(value: Any, path: str, hits: list[tuple[str, str]], limit: int = 5) -> None:
    if len(hits) >= limit:
        return
    if isinstance(value, str):
        if _contains_mojibake(value):
            hits.append((path, value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _scan_mojibake(item, f"{path}.{key}", hits, limit)
            if len(hits) >= limit:
                return
        return
    if isinstance(value, list):
        for idx, item in enumerate(value):
            _scan_mojibake(item, f"{path}[{idx}]", hits, limit)
            if len(hits) >= limit:
                return


def _warn_if_mojibake(data: Any, format_id: str, source_path: Path) -> None:
    hits: list[tuple[str, str]] = []
    _scan_mojibake(data, "$", hits)
    if not hits:
        return
    print(f"[WARN] Posible mojibake en {format_id} ({source_path}):")
    for location, sample in hits:
        snippet = sample.replace("\n", " ").strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(f"  - {location}: {snippet}")


def _is_ignored_path(path: Path) -> bool:
    """Indica si un path debe excluirse del discovery."""
    if path.name in _IGNORE_FILENAMES:
        return True
    if path.name.endswith(".sample.json"):
        return True
    for part in path.parts:
        if part.startswith(_HIDDEN_PREFIXES):
            return True
    return False


def _normalize_format_id(raw_id: str, uni: str) -> str:
    """Normaliza el format_id a un slug estable con prefijo de universidad."""
    if not raw_id:
        return ""
    normalized = re.sub(r"[_\s]+", "-", raw_id.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized.startswith(f"{uni}-"):
        normalized = f"{uni}-{normalized}"
    return normalized


def _derive_enfoque(tokens: List[str]) -> str:
    """Deriva el enfoque (cual/cuant/general) desde tokens del nombre."""
    for token in tokens:
        mapped = _ENFOQUE_ALIASES.get(token)
        if mapped:
            return mapped
    return "general"


def _humanize_id(format_id: str, uni: str) -> str:
    """Convierte un format_id en titulo humano si no hay titulo."""
    cleaned = format_id
    if cleaned.startswith(f"{uni}-"):
        cleaned = cleaned[len(uni) + 1 :]
    parts = [p for p in re.split(r"[-_]+", cleaned) if p]
    return " ".join(word.capitalize() for word in parts) or format_id


def _discover_for_uni(uni: str) -> List[FormatIndexItem]:
    """Descubre formatos para una universidad especifica."""
    from app.core.registry import get_provider

    data_dir = get_provider(uni).get_data_dir()
    if not data_dir.exists():
        return []

    items: List[FormatIndexItem] = []
    seen_ids: set[str] = set()

    for path in data_dir.rglob("*.json"):
        if _is_ignored_path(path):
            continue

        rel_path = path.relative_to(data_dir)
        categoria = rel_path.parent.name.lower() if rel_path.parent != Path(".") else "general"
        stem = path.stem
        tokens = [t for t in re.split(r"[_-]+", stem.lower()) if t]
        enfoque = _derive_enfoque(tokens)

        # Lee JSON; si falla, se omite el contenido pero se conserva el indice.
        try:
            data = load_json_file(path)
        except Exception:
            data = None

        if isinstance(data, list):
            # Soporta listas de formatos dentro de un mismo JSON (ej. UNI).
            for idx, entry in enumerate(data):
                if not isinstance(entry, dict):
                    continue
                raw_id = entry.get("id") or entry.get("format_id") or f"{stem}-{idx + 1}"
                entry_tokens = [t for t in re.split(r"[_-]+", str(raw_id).lower()) if t]
                entry_categoria = (entry.get("tipo_formato") or entry.get("categoria") or categoria).lower()
                entry_enfoque = (entry.get("enfoque") or _derive_enfoque(entry_tokens)).lower()
                format_id = _normalize_format_id(str(raw_id), uni)
                if format_id in seen_ids:
                    continue
                seen_ids.add(format_id)

                titulo = entry.get("titulo") or entry.get("title") or _humanize_id(format_id, uni)
                items.append(
                    FormatIndexItem(
                        format_id=format_id,
                        uni=uni,
                        categoria=entry_categoria,
                        enfoque=entry_enfoque,
                        path=path.resolve(),
                        titulo=str(titulo),
                        data=dict(entry),
                    )
                )
            continue

        if isinstance(data, dict):
            raw_id = data.get("id") or stem
            titulo = data.get("titulo")
        else:
            raw_id = stem
            titulo = None

        format_id = _normalize_format_id(str(raw_id), uni)
        if format_id in seen_ids:
            continue
        seen_ids.add(format_id)
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


def discover_format_files(uni: Optional[str] = None) -> List[FormatIndexItem]:
    """Descubre JSON de formatos para una universidad o todas."""
    if uni:
        return _discover_for_uni((uni or "unac").strip().lower())

    from app.core.registry import list_universities

    items: List[FormatIndexItem] = []
    for code in list_universities():
        items.extend(_discover_for_uni(code))

    items.sort(key=lambda item: (item.uni, item.categoria, item.enfoque, item.titulo.lower(), item.format_id))
    return items


def find_format_index(format_id: str) -> Optional[FormatIndexItem]:
    """Busca un formato por ID normalizado."""
    if not format_id:
        return None
    parts = format_id.split("-")
    uni = (parts[0] if parts else "unac").strip().lower()
    normalized = _normalize_format_id(format_id, uni)
    try:
        items = discover_format_files(uni)
    except KeyError:
        return None
    for item in items:
        if item.format_id == normalized:
            return item
    return None


def load_format_by_id(format_id: str) -> Dict[str, Any]:
    """Carga JSON por format_id y agrega _meta si falta."""
    item = find_format_index(format_id)
    if not item:
        raise FileNotFoundError(f"Formato no encontrado: {format_id}")

    data = item.data if item.data is not None else load_json_file(item.path)
    if isinstance(data, list):
        # Selecciona la entrada exacta cuando el JSON contiene lista.
        match = None
        for entry in data:
            if not isinstance(entry, dict):
                continue
            raw_id = entry.get("id") or entry.get("format_id")
            if raw_id and _normalize_format_id(str(raw_id), item.uni) == item.format_id:
                match = entry
                break
        data = match or data
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
        _warn_if_mojibake(payload, item.format_id, item.path)
        return payload
    payload = {"_meta": {"format_id": item.format_id, "uni": item.uni, "path": str(item.path)}, "data": data}
    _warn_if_mojibake(payload, item.format_id, item.path)
    return payload
