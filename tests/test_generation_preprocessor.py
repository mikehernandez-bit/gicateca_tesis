"""Tests for generation preprocessor transformations."""

from __future__ import annotations

from app.modules.generation.preprocessor import (
    apply_ai_content,
    merge_values,
    sanitize_ai_text,
)


def test_merge_values_sets_cover_title_when_placeholder_is_literal() -> None:
    data = {
        "caratula": {
            "titulo_placeholder": "TITULO DEL PROYECTO",
        }
    }
    values = {"title": "Implementacion de IA en procesos logisticos"}

    merged = merge_values(data, values)

    assert merged["caratula"]["titulo"] == "Implementacion de IA en procesos logisticos"


def test_sanitize_ai_text_removes_markdown_and_placeholder_lines() -> None:
    raw = (
        "# Encabezado markdown\n"
        "**Texto en negrita**\n"
        "Linea con formfeed\f\n"
        "| Col A | Col B |\n"
        "| --- | --- |\n"
        "FIGURA DE EJEMPLO\n"
        "[Insertar grafico de procesos]\n"
        "Parrafo final valido.\n"
    )

    cleaned = sanitize_ai_text(raw)

    assert "#" not in cleaned
    assert "**" not in cleaned
    assert "|" not in cleaned
    assert "FIGURA DE EJEMPLO" not in cleaned.upper()
    assert "Insertar" not in cleaned
    assert "\f" not in cleaned
    assert "Parrafo final valido." in cleaned


def test_apply_ai_content_injects_sanitized_text_in_target_section() -> None:
    data = {
        "preliminares": {
            "introduccion": {
                "titulo": "INTRODUCCION",
                "texto": "texto base",
            }
        }
    }
    ai_sections = [
        {
            "path": "INTRODUCCION",
            "content": "# Intro\n**Texto limpio**\nFIGURA DE EJEMPLO\nContenido final.",
        }
    ]

    result = apply_ai_content(data, ai_sections)
    intro_text = result["preliminares"]["introduccion"]["texto"]

    assert "Texto limpio" in intro_text
    assert "Contenido final." in intro_text
    assert "#" not in intro_text
    assert "**" not in intro_text
    assert "FIGURA DE EJEMPLO" not in intro_text.upper()


def test_apply_ai_content_keeps_index_items_unchanged_when_titles_overlap() -> None:
    data = {
        "preliminares": {
            "indices": [
                {
                    "titulo": "INDICE",
                    "items": [
                        {"texto": "I. PLANTEAMIENTO DEL PROBLEMA", "pag": 2},
                    ],
                }
            ]
        },
        "cuerpo": [
            {
                "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
                "contenido": [
                    {"texto": "1.1 Descripcion de la realidad problematica"},
                ],
            }
        ],
    }
    ai_sections = [
        {
            "path": "I. PLANTEAMIENTO DEL PROBLEMA/1.1 Descripcion de la realidad problematica",
            "content": "Contenido academico generado para la subseccion.",
        }
    ]

    result = apply_ai_content(data, ai_sections)

    index_item_text = result["preliminares"]["indices"][0]["items"][0]["texto"]
    body_item = result["cuerpo"][0]["contenido"][0]

    assert index_item_text == "I. PLANTEAMIENTO DEL PROBLEMA"
    assert body_item["texto"] == "1.1 Descripcion de la realidad problematica"
    assert body_item["parrafos"] == ["Contenido academico generado para la subseccion."]


def test_apply_ai_content_ignores_index_paths_from_ai_result() -> None:
    data = {
        "preliminares": {
            "indices": [
                {
                    "titulo": "INDICE",
                    "items": [
                        {"texto": "INTRODUCCION", "pag": 1},
                    ],
                }
            ],
            "introduccion": {
                "titulo": "INTRODUCCION",
                "texto": "Texto base",
            },
        }
    }
    ai_sections = [
        {"path": "INDICE", "content": "Texto que nunca debe inyectarse"},
    ]

    result = apply_ai_content(data, ai_sections)

    assert result["preliminares"]["indices"][0]["items"][0]["texto"] == "INTRODUCCION"
    assert result["preliminares"]["introduccion"]["texto"] == "Texto base"
