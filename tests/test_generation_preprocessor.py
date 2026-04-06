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


def test_apply_ai_content_injects_preliminares_sections_beyond_introduccion() -> None:
    data = {
        "preliminares": {
            "dedicatoria": {"titulo": "DEDICATORIA", "texto": "[Escriba aqui su dedicatoria...]"},
            "agradecimientos": {"titulo": "AGRADECIMIENTO", "texto": "[Escriba aqui su agradecimiento...]"},
        }
    }
    ai_sections = [
        {"path": "DEDICATORIA", "content": "Dedico este trabajo a mi familia por su apoyo constante."},
        {"path": "AGRADECIMIENTO", "content": "Agradezco a mi asesor y a la universidad por el acompanamiento brindado."},
    ]

    result = apply_ai_content(data, ai_sections)

    assert result["preliminares"]["dedicatoria"]["_ai_content"].startswith("Dedico este trabajo")
    assert result["preliminares"]["agradecimientos"]["_ai_content"].startswith("Agradezco a mi asesor")


def test_apply_ai_content_injects_abbreviations_preliminary() -> None:
    data = {
        "preliminares": {
            "indices": {"abreviaturas": "INDICE DE ABREVIATURAS"},
        }
    }
    ai_sections = [
        {
            "path": "INDICE DE ABREVIATURAS",
            "content": "IA: Inteligencia Artificial\nERP: Planificacion de recursos empresariales",
        }
    ]

    result = apply_ai_content(data, ai_sections)

    assert result["preliminares"]["abreviaturas"]["_ai_content"].startswith("IA: Inteligencia Artificial")


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


def test_apply_ai_content_tags_structured_chapter_blocks_as_ai_generated() -> None:
    data = {
        "cuerpo": [
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Cronograma base",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Base", "X"]],
                    }
                ],
            }
        ]
    }
    ai_sections = [
        {
            "path": "V. CRONOGRAMA DE ACTIVIDADES",
            "content": [
                {
                    "tipo": "tabla",
                    "titulo": "Cronograma final",
                    "encabezados": ["Actividad", "Mes 1"],
                    "filas": [["Real", "X"]],
                }
            ],
        }
    ]

    result = apply_ai_content(data, ai_sections)
    contenido = result["cuerpo"][0]["contenido"]

    assert contenido[0]["titulo"] == "Cronograma final"
    assert contenido[0]["_ai_generated"] is True
    assert contenido[1]["titulo"] == "Cronograma base"
    assert "_ai_generated" not in contenido[1]


def test_apply_ai_content_injects_final_references_section() -> None:
    data = {
        "finales": {
            "referencias": {
                "titulo": "IX. REFERENCIAS BIBLIOGRAFICAS",
                "ejemplos_apa": ["Base 1"],
            }
        }
    }
    ai_sections = [
        {
            "path": "IX. REFERENCIAS BIBLIOGRAFICAS",
            "content": (
                "Las siguientes referencias son propuestas academicas simuladas.\n\n"
                "Morales, J. (2024). Texto uno.\n\n"
                "Rojas, M. (2023). Texto dos."
            ),
        }
    ]

    result = apply_ai_content(data, ai_sections)
    referencias = result["finales"]["referencias"]

    assert referencias["_ai_content"].startswith("Las siguientes referencias")
    assert "ejemplos_apa" in referencias


def test_apply_ai_content_matches_annex_by_prefix_when_title_changes() -> None:
    data = {
        "finales": {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 1: Matriz de consistencia",
                        "tabla": {"headers": ["Base"], "rows": [["Ejemplo"]]},
                    }
                ],
            }
        }
    }
    ai_sections = [
        {
            "path": "ANEXOS/Anexo 1: Matriz de consistencia final",
            "content": [
                {"tipo": "parrafo", "texto": "Contenido final del anexo."},
                {
                    "tipo": "tabla",
                    "titulo": "Matriz de consistencia final",
                    "encabezados": ["Problema", "Objetivo"],
                    "filas": [["P1", "O1"]],
                },
            ],
        }
    ]

    result = apply_ai_content(data, ai_sections)
    anexo = result["finales"]["anexos"]["lista"][0]

    assert anexo["titulo"] == "Anexo 1: Matriz de consistencia final"
    assert anexo["_ai_content"][0]["texto"] == "Contenido final del anexo."
    assert anexo["_ai_content"][1]["titulo"] == "Matriz de consistencia final"


def test_apply_ai_content_matches_annex_by_position_when_base_title_is_not_annex() -> None:
    data = {
        "finales": {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {"titulo": "Figura A1. Registro fotográfico"},
                    {"titulo": "Tabla 15. Tabla de resultados complementarios"},
                ],
            }
        }
    }
    ai_sections = [
        {
            "path": "ANEXOS/Anexo 1: Registro fotográfico",
            "content": [
                {"tipo": "parrafo", "texto": "Evidencia 1. Vista frontal del equipo."}
            ],
        },
        {
            "path": "ANEXOS/Anexo 2: Tabla de resultados complementarios",
            "content": [
                {
                    "tipo": "tabla",
                    "titulo": "Tabla 15. Tabla de resultados complementarios",
                    "encabezados": ["Indicador", "Valor"],
                    "filas": [["Disponibilidad", "96%"]],
                }
            ],
        },
    ]

    result = apply_ai_content(data, ai_sections)
    foto = result["finales"]["anexos"]["lista"][0]
    tabla = result["finales"]["anexos"]["lista"][1]

    assert foto["titulo"] == "Anexo 1: Registro fotográfico"
    assert foto["_ai_content"][0]["texto"] == "Evidencia 1. Vista frontal del equipo."
    assert tabla["titulo"] == "Anexo 2: Tabla de resultados complementarios"
    assert tabla["_ai_content"][0]["titulo"] == "Tabla 15. Tabla de resultados complementarios"
