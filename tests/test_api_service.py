"""
Tests para app.modules.api.service

Cubren:
- Determinismo del hash (mismo input = mismo hash)
- Cambio de version al modificar contenido
- Estabilidad de IDs
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.modules.api.service import (
    canonical_json_bytes,
    compute_format_hash,
    get_catalog_version,
    InternalFormat,
    load_all_formats,
    map_to_dto_summary,
    map_to_dto_detail,
)


class TestCanonicalJsonBytes:
    """Tests para serialización canónica."""

    def test_same_content_different_order_same_bytes(self):
        """Mismo contenido en diferente orden debe dar mismo resultado."""
        obj1 = {"b": 2, "a": 1, "c": 3}
        obj2 = {"a": 1, "c": 3, "b": 2}

        assert canonical_json_bytes(obj1) == canonical_json_bytes(obj2)

    def test_no_spaces_in_output(self):
        """Output no debe tener espacios innecesarios."""
        obj = {"key": "value", "number": 123}
        result = canonical_json_bytes(obj)

        assert b" " not in result
        assert b'{"key":"value","number":123}' == result

    def test_nested_objects_sorted(self):
        """Objetos anidados también deben estar ordenados."""
        obj = {"z": {"b": 2, "a": 1}, "a": 1}
        result = canonical_json_bytes(obj)

        # a debe venir antes que z en el nivel superior
        assert result.index(b'"a"') < result.index(b'"z"')


class TestComputeFormatHash:
    """Tests para hash de formato."""

    @pytest.fixture
    def sample_format(self) -> InternalFormat:
        return InternalFormat(
            id="unac:general:test-format",
            title="Test Format",
            university="unac",
            category="general",
            document_type="tesis",
            raw_data={"_meta": {"id": "test"}},
            source_path=Path("/fake/path.json"),
            fields=[{"name": "titulo", "label": "Título", "type": "text"}],
            assets=[{"id": "unac:logo:main", "kind": "logo"}],
        )

    def test_hash_is_deterministic(self, sample_format):
        """Mismo formato produce mismo hash."""
        hash1 = compute_format_hash(sample_format)
        hash2 = compute_format_hash(sample_format)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_hash_changes_on_content_change(self, sample_format):
        """Hash cambia si cambia el contenido."""
        hash_original = compute_format_hash(sample_format)

        # Modificar un campo
        modified = InternalFormat(
            id=sample_format.id,
            title="Modified Title",  # Cambiado
            university=sample_format.university,
            category=sample_format.category,
            document_type=sample_format.document_type,
            raw_data=sample_format.raw_data,
            source_path=sample_format.source_path,
            fields=sample_format.fields,
            assets=sample_format.assets,
        )
        hash_modified = compute_format_hash(modified)

        assert hash_original != hash_modified


class TestCatalogVersion:
    """Tests para versión global del catálogo."""

    def test_version_is_deterministic(self):
        """Mismos formatos producen misma versión."""
        formats = [
            InternalFormat(
                id="unac:test:a",
                title="A",
                university="unac",
                category="test",
                document_type=None,
                raw_data={},
                source_path=Path("/a.json"),
                fields=[],
                assets=[],
            ),
            InternalFormat(
                id="unac:test:b",
                title="B",
                university="unac",
                category="test",
                document_type=None,
                raw_data={},
                source_path=Path("/b.json"),
                fields=[],
                assets=[],
            ),
        ]

        v1 = get_catalog_version(formats)
        v2 = get_catalog_version(formats)

        assert v1 == v2

    def test_version_changes_on_format_change(self):
        """Versión cambia si cambia un formato."""
        base_formats = [
            InternalFormat(
                id="unac:test:a",
                title="A",
                university="unac",
                category="test",
                document_type=None,
                raw_data={},
                source_path=Path("/a.json"),
                fields=[],
                assets=[],
            ),
        ]
        v1 = get_catalog_version(base_formats)

        modified_formats = [
            InternalFormat(
                id="unac:test:a",
                title="A Modified",  # Cambió el título
                university="unac",
                category="test",
                document_type=None,
                raw_data={},
                source_path=Path("/a.json"),
                fields=[],
                assets=[],
            ),
        ]
        v2 = get_catalog_version(modified_formats)

        assert v1 != v2


class TestDTOMapping:
    """Tests para mapeo a DTOs."""

    @pytest.fixture
    def sample_format(self) -> InternalFormat:
        return InternalFormat(
            id="unac:general:sample",
            title="Sample Format",
            university="unac",
            category="general",
            document_type="tesis",
            raw_data={},
            source_path=Path("/sample.json"),
            fields=[
                {"name": "titulo", "label": "Título", "type": "text", "required": True},
                {"name": "autor", "label": "Autor", "type": "text"},
            ],
            assets=[{"id": "unac:logo:main", "kind": "logo"}],
            template_kind="docx",
        )

    def test_summary_maps_correctly(self, sample_format):
        """FormatSummary tiene los campos correctos."""
        summary = map_to_dto_summary(sample_format)

        assert summary.id == "unac:general:sample"
        assert summary.title == "Sample Format"
        assert summary.university == "unac"
        assert summary.category == "general"
        assert summary.documentType == "tesis"
        assert len(summary.version) == 16  # Hash corto

    def test_detail_maps_correctly(self, sample_format):
        """FormatDetail tiene estructura completa."""
        detail = map_to_dto_detail(sample_format)

        assert detail.id == "unac:general:sample"
        assert len(detail.fields) == 2
        assert detail.fields[0].name == "titulo"
        assert detail.fields[0].required is True
        assert len(detail.assets) == 1
        assert detail.assets[0].kind == "logo"
        assert detail.templateRef is not None
        assert detail.templateRef.kind == "docx"
