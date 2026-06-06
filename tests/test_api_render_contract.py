from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.api import generation_router, render_router
from app.modules.api.ai_content_contract import AIResult
from app.modules.generation.service import ArtifactInfo, GenerationResult
from app.modules.generation.preprocessor import apply_ai_content


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_format_id(client: TestClient) -> str:
    response = client.get("/api/v1/formats")
    assert response.status_code == 200
    data = response.json()
    if not data:
        pytest.skip("No publishable formats available")
    return data[0]["id"]


def test_render_docx_accepts_plain_text_content(
    client: TestClient,
    valid_format_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    out_path = tmp_path / "plain.docx"
    out_path.write_bytes(b"plain-docx")
    captured: dict[str, object] = {}

    def fake_generate(format_id: str, values: dict, ai_result):
        captured["format_id"] = format_id
        captured["values"] = values
        captured["sections"] = (
            render_router.serialize_ai_sections(ai_result.sections) if ai_result else []
        )
        return out_path, "plain.docx"

    monkeypatch.setattr(render_router, "_generate_simulation_docx", fake_generate)

    response = client.post(
        "/api/v1/render/docx",
        json={
            "formatId": valid_format_id,
            "values": {"title": "Demo"},
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "sectionId": "sec-1",
                        "path": "INTRODUCCION",
                        "content": "Texto plano de introduccion.",
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    assert captured["format_id"] == valid_format_id
    assert captured["sections"] == [
        {
            "sectionId": "sec-1",
            "path": "INTRODUCCION",
            "content": "Texto plano de introduccion.",
        }
    ]


def test_render_docx_accepts_structured_content_and_normalizes_placeholder(
    client: TestClient,
    valid_format_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    out_path = tmp_path / "structured.docx"
    out_path.write_bytes(b"structured-docx")
    captured: dict[str, object] = {}

    def fake_generate(format_id: str, values: dict, ai_result):
        captured["sections"] = (
            render_router.serialize_ai_sections(ai_result.sections) if ai_result else []
        )
        return out_path, "structured.docx"

    monkeypatch.setattr(render_router, "_generate_simulation_docx", fake_generate)

    response = client.post(
        "/api/v1/render/docx",
        json={
            "formatId": valid_format_id,
            "values": {"title": "Demo"},
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "sectionId": "sec-2",
                        "path": "II. MARCO TEORICO/2.1 Bases teoricas",
                        "content": [
                            {"tipo": "parrafo", "texto": "Parrafo valido."},
                            {
                                "tipo": "tabla",
                                "titulo": "Tabla 1. Variables",
                                "encabezados": ["Variable", "Indicador"],
                                "filas": [["A", "I1"]],
                            },
                            {
                                "tipo": "figura",
                                "caption": "Figura 1. Arquitectura propuesta.",
                                "ruta_placeholder": "placeholder",
                                "nota": "Guía para elaborar la figura: usar datos reales.",
                                "nota_color": "0000FF",
                            },
                        ],
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    sections = captured["sections"]
    assert isinstance(sections, list)
    content = sections[0]["content"]
    assert isinstance(content, list)
    assert content[1]["orientacion"] == "portrait"
    assert content[2]["ruta_placeholder"] == "assets/placeholder_figura.png"
    assert content[2]["nota"] == "Guía para elaborar la figura: usar datos reales."
    assert content[2]["nota_color"] == "0000FF"



def test_render_docx_accepts_structured_paragraph_and_formula_content(
    client: TestClient,
    valid_format_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    out_path = tmp_path / "formula.docx"
    out_path.write_bytes(b"formula-docx")
    captured: dict[str, object] = {}

    def fake_generate(format_id: str, values: dict, ai_result):
        captured["sections"] = (
            render_router.serialize_ai_sections(ai_result.sections) if ai_result else []
        )
        return out_path, "formula.docx"

    monkeypatch.setattr(render_router, "_generate_simulation_docx", fake_generate)

    response = client.post(
        "/api/v1/render/docx",
        json={
            "formatId": valid_format_id,
            "values": {},
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "sectionId": "sec-13",
                        "path": "IV. METODOLOG?A DEL PROYECTO/4.1 Tipo y dise?o de investigaci?n",
                        "content": [
                            {"tipo": "parrafo", "texto": "La investigaci?n es aplicada."},
                            {"tipo": "formula", "texto": "M O1 X O2", "numero": "1"},
                        ],
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    content = captured["sections"][0]["content"]
    assert [item["tipo"] for item in content] == ["parrafo", "formula"]
    assert content[1]["texto"] == "M O1 X O2"

def test_render_pdf_accepts_structured_content(
    client: TestClient,
    valid_format_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    docx_path = tmp_path / "structured.docx"
    docx_path.write_bytes(b"structured-docx")

    def fake_generate(format_id: str, values: dict, ai_result):
        return docx_path, "structured.docx"

    def fake_convert_docx_to_pdf(src: str, dest: str) -> None:
        Path(dest).write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(render_router, "_generate_simulation_docx", fake_generate)
    import app.core.pdf_converter as pdf_converter

    monkeypatch.setattr(pdf_converter, "convert_docx_to_pdf", fake_convert_docx_to_pdf)

    response = client.post(
        "/api/v1/render/pdf",
        json={
            "formatId": valid_format_id,
            "values": {"title": "Demo"},
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "path": "V. CRONOGRAMA DE ACTIVIDADES/Cronograma de ejecucion",
                        "content": [
                            {"tipo": "parrafo", "texto": "Texto previo."},
                            {
                                "tipo": "tabla",
                                "titulo": "Cronograma",
                                "encabezados": [
                                    "Actividad",
                                    "Mes 1",
                                    "Mes 2",
                                    "Mes 3",
                                    "Mes 4",
                                    "Mes 5",
                                ],
                                "filas": [["Revision", "X", "", "", "", ""]],
                            },
                        ],
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_generate_endpoint_accepts_structured_content(
    client: TestClient,
    valid_format_id: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}
    docx_path = tmp_path / "artifact.docx"
    docx_path.write_bytes(b"docx")

    def fake_generate_artifacts(
        project_id: str, format_id: str, values: dict, ai_result, mode: str
    ):
        captured["project_id"] = project_id
        captured["format_id"] = format_id
        captured["ai_result"] = ai_result
        return GenerationResult(
            project_id=project_id,
            run_id="gen-test-001",
            format_id=format_id,
            status="success",
            artifacts=[
                ArtifactInfo(
                    type="docx",
                    path=docx_path,
                    download_url="/api/v1/artifacts/gen-test-001/docx",
                ),
            ],
        )

    monkeypatch.setattr(
        generation_router, "generate_artifacts", fake_generate_artifacts
    )

    response = client.post(
        "/api/v1/generate",
        json={
            "projectId": "proj-test-1",
            "formatId": valid_format_id,
            "values": {"title": "Demo"},
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "path": "ANEXOS/Anexo 1",
                        "content": [
                            {"tipo": "parrafo", "texto": "Texto de anexo."},
                            {
                                "tipo": "figura",
                                "caption": "Figura 1. Placeholder.",
                                "ruta_placeholder": "placeholder",
                            },
                        ],
                    }
                ]
            },
        },
    )

    assert response.status_code == 200
    ai_result = captured["ai_result"]
    assert (
        ai_result["sections"][0]["content"][1]["ruta_placeholder"]
        == "assets/placeholder_figura.png"
    )


def test_render_docx_rejects_invalid_structured_block(
    client: TestClient, valid_format_id: str
) -> None:
    response = client.post(
        "/api/v1/render/docx",
        json={
            "formatId": valid_format_id,
            "mode": "simulation",
            "aiResult": {
                "sections": [
                    {
                        "path": "II. MARCO TEORICO/2.1 Bases teoricas",
                        "content": [
                            {
                                "tipo": "tabla",
                                "titulo": "Tabla rota",
                                "filas": [["A"]],
                            }
                        ],
                    }
                ]
            },
        },
    )

    assert response.status_code == 422


def test_preprocessor_flattens_invalid_dict_without_stringifying() -> None:
    data = {
        "preliminares": {
            "introduccion": {
                "titulo": "INTRODUCCION",
                "texto": "Placeholder",
            }
        }
    }
    ai_sections = [
        {
            "path": "INTRODUCCION",
            "content": {"tipo": "desconocido", "titulo": "Solo titulo visible"},
        }
    ]

    result = apply_ai_content(data, ai_sections)
    intro = result["preliminares"]["introduccion"]
    assert "tipo" not in str(intro.get("_ai_content", ""))
    assert intro["_ai_content"] == "Solo titulo visible"


def test_ai_result_preserves_schedule_blank_headers_and_full_width() -> None:
    result = AIResult.model_validate(
        {
            "sections": [
                {
                    "sectionId": "sec-0025",
                    "path": "V. CRONOGRAMA DE ACTIVIDADES",
                    "content": [
                        {
                            "tipo": "tabla",
                            "subtipo": "cronograma_actividades",
                            "titulo": "Tabla 5.1 Cronograma de actividades",
                            "encabezados": ["FASES Y ACTIVIDADES", "2025", *["" for _ in range(11)]],
                            "filas": [
                                ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"],
                                ["1. PLANIFICACIÓN Y DISEÑO", *["" for _ in range(12)]],
                                ["1.1. Actividad", "", "X", "", "", "", "", "", "", "", "", "", ""],
                            ],
                            "orientacion": "landscape",
                        }
                    ],
                }
            ]
        }
    )

    sections = render_router.serialize_ai_sections(result.sections)
    table = sections[0]["content"][0]

    assert len(table["encabezados"]) == 13
    assert table["encabezados"][1] == "2025"
    assert table["encabezados"][2:] == ["" for _ in range(11)]
    assert len(table["filas"][0]) == 13
    assert table["filas"][0][1:] == ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
