"""Tests for actionable errors emitted by DOCX generator subprocesses."""

from app.core.document_generator import _generator_failure_detail


def test_generator_failure_detail_reads_explicit_error_from_stdout() -> None:
    stdout = (
        "[INFO] Document saved\n"
        "[ERROR] correspondencia CITATION/fuentes inválida; sin citar=SIM_01\n"
    )

    detail = _generator_failure_detail(stdout, "")

    assert detail == "correspondencia CITATION/fuentes inválida; sin citar=SIM_01"


def test_generator_failure_detail_falls_back_to_stderr() -> None:
    detail = _generator_failure_detail("", "Traceback resumido\nFallo de conversión")

    assert detail == "Fallo de conversión"
