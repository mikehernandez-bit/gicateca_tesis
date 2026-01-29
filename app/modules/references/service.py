"""
Archivo: app/modules/references/service.py
Proposito:
- Implementa la logica de carga y discovery de normas bibliograficas (data-driven).

Responsabilidades:
- Listar normas disponibles desde app/data/references/*.json.
- Cargar configuracion por universidad (app/data/<uni>/references.json).
- Construir respuestas resumidas o detalladas para la API.
No hace:
- No define rutas HTTP ni renderiza templates.

Entradas/Salidas:
- Entradas: codigo de universidad, id de norma.
- Salidas: dicts JSON listos para API/UI.

Dependencias:
- json, pathlib, app.core.paths.

Puntos de extension:
- Agregar validaciones de schema o nuevas fuentes de datos.

Donde tocar si falla:
- Revisar _load_json, rutas de data y reglas de order/enabled.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.core.paths import get_data_root
from app.core.registry import get_provider, list_universities


_HIDDEN_PREFIXES = ("_", "__")


def _load_json(path: Path) -> Any:
    """Lee un JSON con UTF-8 y retorna su contenido."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _references_root() -> Path:
    """Retorna la carpeta de normas globales."""
    return get_data_root() / "references"


def _iter_reference_files() -> List[Path]:
    """Lista archivos JSON de normas globales (ignora prefijos ocultos)."""
    root = _references_root()
    if not root.exists():
        return []
    files: List[Path] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.name.lower()):
        if path.name.startswith(_HIDDEN_PREFIXES):
            continue
        files.append(path)
    return files


def list_reference_ids() -> List[str]:
    """Retorna lista de IDs disponibles (stem de archivo)."""
    return [path.stem for path in _iter_reference_files()]


def list_references() -> List[Dict[str, Any]]:
    """Carga todas las normas globales."""
    items: List[Dict[str, Any]] = []
    for path in _iter_reference_files():
        payload = _load_json(path)
        if isinstance(payload, dict):
            items.append(payload)
    return items


def get_reference(ref_id: str) -> Dict[str, Any]:
    """Carga una norma global por ID."""
    if not ref_id:
        raise FileNotFoundError("ref_id requerido")
    path = _references_root() / f"{ref_id}.json"
    if not path.exists():
        raise FileNotFoundError(ref_id)
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("Formato de norma invalido")
    return payload


def _default_config(uni: str, available: Iterable[str]) -> Dict[str, Any]:
    """Construye configuracion por defecto para una universidad."""
    enabled = list(available)
    return {
        "university": uni,
        "title": f"Normas de citacion ({uni.upper()})",
        "enabled": enabled,
        "order": enabled,
        "notes": {},
    }


def get_uni_config(uni: str, available: Iterable[str]) -> Dict[str, Any]:
    """Carga configuracion por universidad o genera defaults."""
    code = (uni or "unac").strip().lower()
    config_path = get_data_root() / code / "references_config.json"

    if not config_path.exists():
        return _default_config(code, available)

    payload = _load_json(config_path)
    if not isinstance(payload, dict):
        return _default_config(code, available)

    config = dict(payload)
    config.setdefault("university", code)
    config.setdefault("title", f"Normas de citacion ({code.upper()})")
    config.setdefault("enabled", list(available))
    config.setdefault("order", list(config.get("enabled", list(available))))
    config.setdefault("notes", {})

    # Filtra enabled/order a IDs disponibles.
    available_set = set(available)
    config["enabled"] = [ref_id for ref_id in config.get("enabled", []) if ref_id in available_set]
    config["order"] = [ref_id for ref_id in config.get("order", []) if ref_id in available_set]
    if not config["order"]:
        config["order"] = list(config["enabled"])
    return config


def build_reference_index(uni: str) -> Dict[str, Any]:
    """Construye el indice resumido de normas para una universidad."""
    available = list_reference_ids()
    config = get_uni_config(uni, available)

    summaries: List[Dict[str, Any]] = []
    available_map = {item.get("id") or item.get("id_ref") or item.get("codigo"): item for item in list_references()}

    ordered_ids = [ref_id for ref_id in config["order"] if ref_id in available]
    # Asegura que se muestren todas las normas aunque no estén en order.
    for ref_id in available:
        if ref_id not in ordered_ids:
            ordered_ids.append(ref_id)
    for ref_id in ordered_ids:
        item = available_map.get(ref_id)
        if not item:
            continue
        summaries.append(
            {
                "id": item.get("id") or ref_id,
                "titulo": item.get("titulo") or ref_id,
                "tags": item.get("tags", []),
                "descripcion": item.get("descripcion", ""),
                "preview": item.get("preview"),
            }
        )

    return {
        "config": {
            "university": config.get("university", uni),
            "title": config.get("title"),
            "enabled": config.get("enabled", []),
            "order": config.get("order", []),
            "notes": config.get("notes", {}),
        },
        "items": summaries,
    }


def get_reference_detail(ref_id: str, uni: str) -> Dict[str, Any]:
    """Retorna norma completa con nota especifica de universidad (si existe)."""
    payload = get_reference(ref_id)
    available = list_reference_ids()
    config = get_uni_config(uni, available)
    note = (config.get("notes") or {}).get(ref_id)
    used_by: List[Dict[str, str]] = []
    for code in list_universities():
        try:
            config_for_uni = get_uni_config(code, available)
        except Exception:
            continue
        if ref_id not in (config_for_uni.get("enabled") or []):
            continue
        try:
            provider = get_provider(code)
            used_by.append({"code": provider.code, "name": provider.display_name})
        except KeyError:
            used_by.append({"code": code, "name": code.upper()})
    detail = dict(payload)
    if note:
        detail["nota_universidad"] = note
    detail["uni"] = config.get("university", (uni or "unac").strip().lower())
    detail["usado_por"] = used_by
    return detail
