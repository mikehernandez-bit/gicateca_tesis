from pathlib import Path
from unittest.mock import patch

import pytest
from docx import Document

from app.engine.field_stabilizer import FieldStabilizationError, stabilize_docx_fields


def _docx(tmp_path: Path) -> Path:
    path = tmp_path / "base.docx"
    Document().save(path)
    return path


def test_stabilizer_stops_when_page_mapping_converges(tmp_path) -> None:
    path = _docx(tmp_path)
    mapping = (("Introducción", 8),)
    with (
        patch("app.engine.field_stabilizer._uses_word_com", return_value=False),
        patch("app.engine.field_stabilizer.convert_docx_to_pdf") as convert,
        patch("app.engine.field_stabilizer._update_cached_results", side_effect=[mapping, mapping]),
    ):
        report = stabilize_docx_fields(path, max_cycles=3)

    assert report == {"cycles": 2, "entries": 1}
    assert convert.call_count == 2


def test_stabilizer_fails_when_three_cycles_do_not_converge(tmp_path) -> None:
    path = _docx(tmp_path)
    with (
        patch("app.engine.field_stabilizer._uses_word_com", return_value=False),
        patch("app.engine.field_stabilizer.convert_docx_to_pdf"),
        patch(
            "app.engine.field_stabilizer._update_cached_results",
            side_effect=[(("Introducción", 8),), (("Introducción", 9),), (("Introducción", 10),)],
        ),
    ):
        with pytest.raises(FieldStabilizationError, match="no convergio"):
            stabilize_docx_fields(path, max_cycles=3)
