"""
Tests de reglas de catálogo público de formatos.

Valida que:
- configs/references no se publiquen en /formats
- formatos con publish=false no se publiquen
- versión pública ignore configs excluidos
- versión pública cambie al modificar formatos publicables
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.loaders import FormatIndexItem
from app.main import app
from app.modules.api import service


def _client() -> TestClient:
    return TestClient(app)


def test_formats_excludes_references_config_from_real_catalog() -> None:
    client = _client()
    response = client.get("/api/v1/formats")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert "unac-references-config" not in ids
    assert "uni-references-config" not in ids


def test_formats_excludes_publish_false(monkeypatch) -> None:
    public_item = FormatIndexItem(
        format_id="unac-public-format",
        uni="unac",
        categoria="proyecto",
        enfoque="general",
        path=Path("/tmp/unac/proyecto/public.json"),
        titulo="Formato Publico",
    )
    hidden_item = FormatIndexItem(
        format_id="unac-hidden-format",
        uni="unac",
        categoria="proyecto",
        enfoque="general",
        path=Path("/tmp/unac/proyecto/hidden.json"),
        titulo="Formato Oculto",
    )

    payloads = {
        "unac-public-format": {
            "_meta": {
                "id": "unac-public-format",
                "entity": "format",
                "publish": True,
                "title": "Formato Publico",
                "university": "unac",
                "category": "proyecto",
            },
            "caratula": {"titulo": ""},
        },
        "unac-hidden-format": {
            "_meta": {
                "id": "unac-hidden-format",
                "entity": "format",
                "publish": False,
                "title": "Formato Oculto",
                "university": "unac",
                "category": "proyecto",
            },
            "caratula": {"titulo": ""},
        },
    }

    monkeypatch.setattr(
        service,
        "discover_format_files",
        lambda university=None: [public_item, hidden_item],
    )
    monkeypatch.setattr(service, "load_format_by_id", lambda format_id: payloads[format_id])

    client = _client()
    response = client.get("/api/v1/formats")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert "unac-public-format" in ids
    assert "unac-hidden-format" not in ids


def test_public_version_ignores_config_changes(monkeypatch) -> None:
    public_item = FormatIndexItem(
        format_id="unac-public-format",
        uni="unac",
        categoria="proyecto",
        enfoque="general",
        path=Path("/tmp/unac/proyecto/public.json"),
        titulo="Formato Publico",
    )
    config_item = FormatIndexItem(
        format_id="unac-references-config",
        uni="unac",
        categoria="general",
        enfoque="general",
        path=Path("/tmp/unac/configs/references_config.json"),
        titulo="References Config",
    )

    state = {"config_title": "Normas v1"}

    def _load(format_id: str):
        if format_id == "unac-public-format":
            return {
                "_meta": {
                    "id": "unac-public-format",
                    "entity": "format",
                    "publish": True,
                    "title": "Formato Publico",
                    "university": "unac",
                    "category": "proyecto",
                },
                "caratula": {"titulo": ""},
            }
        return {
            "_meta": {"entity": "config", "publish": False},
            "title": state["config_title"],
            "enabled": ["apa7"],
        }

    monkeypatch.setattr(
        service,
        "discover_format_files",
        lambda university=None: [public_item, config_item],
    )
    monkeypatch.setattr(service, "load_format_by_id", _load)

    version_1 = service.get_catalog_version_info().version
    state["config_title"] = "Normas v2"
    version_2 = service.get_catalog_version_info().version

    assert version_1 == version_2


def test_public_version_changes_on_publishable_change(monkeypatch) -> None:
    public_item = FormatIndexItem(
        format_id="unac-public-format",
        uni="unac",
        categoria="proyecto",
        enfoque="general",
        path=Path("/tmp/unac/proyecto/public.json"),
        titulo="Formato Publico",
    )

    state = {"title": "Formato Publico"}

    def _load(format_id: str):
        assert format_id == "unac-public-format"
        return {
            "_meta": {
                "id": "unac-public-format",
                "entity": "format",
                "publish": True,
                "title": state["title"],
                "university": "unac",
                "category": "proyecto",
            },
            "caratula": {"titulo": state["title"]},
        }

    monkeypatch.setattr(service, "discover_format_files", lambda university=None: [public_item])
    monkeypatch.setattr(service, "load_format_by_id", _load)

    version_1 = service.get_catalog_version_info().version
    state["title"] = "Formato Publico Actualizado"
    version_2 = service.get_catalog_version_info().version

    assert version_1 != version_2


def test_format_detail_returns_404_for_non_publicable(monkeypatch) -> None:
    hidden_item = FormatIndexItem(
        format_id="unac-hidden-format",
        uni="unac",
        categoria="proyecto",
        enfoque="general",
        path=Path("/tmp/unac/proyecto/hidden.json"),
        titulo="Formato Oculto",
    )

    monkeypatch.setattr(service, "discover_format_files", lambda university=None: [hidden_item])
    monkeypatch.setattr(
        service,
        "load_format_by_id",
        lambda format_id: {
            "_meta": {
                "id": "unac-hidden-format",
                "entity": "format",
                "publish": False,
                "title": "Formato Oculto",
                "university": "unac",
                "category": "proyecto",
            },
            "caratula": {"titulo": ""},
        },
    )

    client = _client()
    response = client.get("/api/v1/formats/unac-hidden-format")
    assert response.status_code == 404
