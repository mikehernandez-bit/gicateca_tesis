from __future__ import annotations

import json
from pathlib import Path

from app.engine.normalizer import normalize


ROOT = Path(__file__).resolve().parents[1]


def _load_json(*parts: str) -> dict:
    path = ROOT.joinpath(*parts)
    return json.loads(path.read_text(encoding="utf-8"))


def test_unac_proyecto_cuant_matches_maestria_cover_and_info_definition() -> None:
    maestria = _load_json("app", "data", "unac", "maestria", "unac_maestria_cuant.json")
    proyecto = _load_json("app", "data", "unac", "proyecto", "unac_proyecto_cuant.json")

    assert proyecto["caratula"] == maestria["caratula"]
    assert proyecto["informacion_basica"] == maestria["informacion_basica"]


def test_unac_proyecto_cual_matches_maestria_cover_and_info_definition() -> None:
    maestria = _load_json("app", "data", "unac", "maestria", "unac_maestria_cual.json")
    proyecto = _load_json("app", "data", "unac", "proyecto", "unac_proyecto_cual.json")

    assert proyecto["caratula"] == maestria["caratula"]
    assert proyecto["informacion_basica"] == maestria["informacion_basica"]


def test_unac_proyecto_normalizes_to_maestria_cover_and_info_blocks() -> None:
    proyecto = _load_json("app", "data", "unac", "proyecto", "unac_proyecto_cuant.json")

    blocks = normalize(proyecto)
    block_types = [block["type"] for block in blocks]

    assert "caratula_unac_maestria" in block_types
    assert "info_basica_unac_maestria" in block_types
