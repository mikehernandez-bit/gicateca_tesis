"""
Tests de integración para API endpoints.

Cubren:
- GET /api/v1/formats (200, headers)
- GET /api/v1/formats/{id} (200, 404)
- GET /api/v1/formats/version
- ETag y 304 Not Modified
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """TestClient de FastAPI."""
    return TestClient(app)


class TestListFormats:
    """Tests para GET /api/v1/formats"""

    def test_returns_200_and_list(self, client):
        """Debe retornar 200 y una lista."""
        response = client.get("/api/v1/formats")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_has_etag_header(self, client):
        """Debe incluir header ETag."""
        response = client.get("/api/v1/formats")

        assert "ETag" in response.headers
        assert response.headers["ETag"].startswith('"')
        assert response.headers["ETag"].endswith('"')

    def test_has_cache_control_header(self, client):
        """Debe incluir header Cache-Control."""
        response = client.get("/api/v1/formats")

        assert "Cache-Control" in response.headers
        assert "max-age=" in response.headers["Cache-Control"]

    def test_304_with_matching_etag(self, client):
        """Debe retornar 304 si If-None-Match coincide."""
        # Primera request para obtener ETag
        response1 = client.get("/api/v1/formats")
        etag = response1.headers["ETag"]

        # Segunda request con If-None-Match
        response2 = client.get(
            "/api/v1/formats",
            headers={"If-None-Match": etag}
        )

        assert response2.status_code == 304

    def test_filter_by_university(self, client):
        """Filtro por universidad funciona."""
        response = client.get("/api/v1/formats?university=unac")

        assert response.status_code == 200
        data = response.json()
        # Todos deben ser de unac (si hay datos)
        for item in data:
            assert item["university"] == "unac"


class TestGetFormatDetail:
    """Tests para GET /api/v1/formats/{id}"""

    def test_returns_404_for_invalid_id(self, client):
        """ID inválido debe retornar 404."""
        response = client.get("/api/v1/formats/nonexistent-format-xyz")

        assert response.status_code == 404

    def test_returns_200_for_valid_id(self, client):
        """ID válido debe retornar 200 con detalle."""
        # Primero obtener un ID válido de la lista
        list_response = client.get("/api/v1/formats")
        formats = list_response.json()

        if not formats:
            pytest.skip("No hay formatos disponibles para testing")

        valid_id = formats[0]["id"]
        response = client.get(f"/api/v1/formats/{valid_id}")

        assert response.status_code == 200
        detail = response.json()
        assert detail["id"] == valid_id
        assert "title" in detail
        assert "fields" in detail

    def test_304_with_matching_etag(self, client):
        """Debe retornar 304 si If-None-Match coincide."""
        # Obtener ID válido
        list_response = client.get("/api/v1/formats")
        formats = list_response.json()

        if not formats:
            pytest.skip("No hay formatos disponibles")

        valid_id = formats[0]["id"]

        # Primera request
        response1 = client.get(f"/api/v1/formats/{valid_id}")
        etag = response1.headers["ETag"]

        # Segunda con If-None-Match
        response2 = client.get(
            f"/api/v1/formats/{valid_id}",
            headers={"If-None-Match": etag}
        )

        assert response2.status_code == 304


class TestCatalogVersion:
    """Tests para GET /api/v1/formats/version"""

    def test_returns_version_info(self, client):
        """Debe retornar version y generatedAt."""
        response = client.get("/api/v1/formats/version")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "generatedAt" in data
        assert len(data["version"]) == 64  # SHA256 hex

    def test_version_is_deterministic(self, client):
        """Llamadas consecutivas dan misma versión (sin cambios)."""
        response1 = client.get("/api/v1/formats/version")
        response2 = client.get("/api/v1/formats/version")

        assert response1.json()["version"] == response2.json()["version"]


class TestAssetsEndpoint:
    """Tests para GET /api/v1/assets/{path}"""

    def test_rejects_path_traversal(self, client):
        """Debe rechazar intentos de path traversal."""
        response = client.get("/api/v1/assets/../../../etc/passwd")

        # Puede ser 400 (bad request), 403 (forbidden), o 404 (not found after sanitization)
        assert response.status_code in (400, 403, 404)

    def test_returns_404_for_nonexistent(self, client):
        """Asset inexistente retorna 404."""
        response = client.get("/api/v1/assets/nonexistent.png")

        assert response.status_code == 404
