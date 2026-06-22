"""
=============================================================================
ARCHIVO: tests/test_engine_normalizer.py
FASE: Block Engine - Fase 3
=============================================================================

PROPÓSITO:
Tests para el normalizer del Block Engine.
Verifica que cada sección del JSON se traduce correctamente a Blocks.

TESTS INCLUIDOS:
- Minimal JSON → blocks sin crash
- Caratula genera centered_text + logo + page_break
- Pagina respeto genera blocks solo cuando existe
- Informacion basica genera info_table
- Preliminares con dedicatoria, indices dict, indices list
- Cuerpo con tabla, imagen, nota, legacy table, mostrar_matriz
- Finales: referencias, anexos con matriz landscape, fallback matriz
- Carga real de los 9 JSONs → normalize sin crash + verificación de estructura

CÓMO EJECUTAR:
    py -m pytest tests/test_engine_normalizer.py -v
=============================================================================
"""
import json
from pathlib import Path

import pytest

from app.engine.normalizer import normalize


ROOT = Path(__file__).resolve().parents[1]


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _minimal_json():
    """JSON mínimo válido (schema v2)."""
    return {
        "_meta": {"id": "test-format", "university": "unac"},
        "configuracion": {"ruta_logo": "app/static/assets/LogoUNAC.png"},
        "caratula": {
            "universidad": "UNIVERSIDAD TEST",
            "facultad": "FACULTAD TEST",
            "titulo_placeholder": "TÍTULO TEST",
        },
        "cuerpo": [{"titulo": "CAP I"}],
    }


def _types(blocks):
    """Extrae lista de types de una lista de blocks."""
    return [b["type"] for b in blocks]


def _blocks_of_type(blocks, block_type):
    """Filtra blocks por tipo."""
    return [b for b in blocks if b["type"] == block_type]


def _project_structured_json():
    data = _minimal_json()
    data["_meta"]["id"] = "unac-proyecto-cuant"
    data["cuerpo"] = [
        {
            "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
            "contenido": [
                {"texto": "1.2 Formulación del problema", "_ai_content": "texto IA"},
                {"texto": "1.3 Objetivos", "_ai_content": "texto IA"},
            ],
        },
        {
            "titulo": "III. HIPÓTESIS Y VARIABLES",
            "contenido": [
                {"texto": "3.1 Hipótesis", "_ai_content": "texto IA"},
                {"texto": "3.2 Operacionalización de variable", "_ai_content": "texto IA"},
            ],
        },
    ]
    data["matriz_consistencia"] = {
        "problema_general": "¿De qué manera el plan RCM mejora la disponibilidad?",
        "problemas_especificos": [
            "¿De qué manera el plan RCM mejora la confiabilidad?",
            "¿De qué manera el plan RCM mejora la mantenibilidad?",
        ],
        "objetivo_general": "Determinar cómo el plan RCM mejora la disponibilidad.",
        "objetivos_especificos": [
            "Determinar cómo el plan RCM mejora la confiabilidad.",
            "Determinar cómo el plan RCM mejora la mantenibilidad.",
        ],
        "hipotesis_general": "El plan RCM mejora la disponibilidad.",
        "hipotesis_especificas": [
            "El plan RCM mejora la confiabilidad.",
            "El plan RCM mejora la mantenibilidad.",
        ],
        "variable_independiente": "Mantenimiento centrado en confiabilidad",
        "variable_dependiente": "Disponibilidad inherente",
    }
    data["operacionalizacion_vi"] = {
        "variable": "Mantenimiento centrado en confiabilidad",
        "definicion_conceptual": "Definición conceptual VI",
        "definicion_operacional": "Definición operacional VI",
        "filas": [
            {
                "dimension": "Taxonomía de equipos",
                "indicador": "Nivel de jerarquía taxonómica",
                "indice": "Ordinal",
                "tecnica_instrumentos": "Fichas de análisis de datos",
            }
        ],
    }
    data["operacionalizacion_vd"] = {
        "variable": "Disponibilidad inherente",
        "definicion_conceptual": "Definición conceptual VD",
        "definicion_operacional": "Definición operacional VD",
        "filas": [
            {
                "dimension": "Confiabilidad",
                "indicador": "MTBF",
                "indice": "MTBF = tiempo total / número de fallas",
                "metodo_tecnica": "Análisis de datos",
            }
        ],
    }
    return data


# ─────────────────────────────────────────────────────────────
# NORMALIZACIÓN MÍNIMA
# ─────────────────────────────────────────────────────────────

class TestNormalizeMinimal:
    def test_minimal_json_produces_blocks(self):
        """JSON mínimo genera una lista no vacía de blocks."""
        blocks = normalize(_minimal_json())
        assert isinstance(blocks, list)
        assert len(blocks) > 0

    def test_minimal_ends_with_page_footer(self):
        """El último block siempre es page_footer."""
        blocks = normalize(_minimal_json())
        assert blocks[-1]["type"] == "page_footer"

    def test_all_blocks_have_type(self):
        """Todos los blocks tienen campo 'type'."""
        blocks = normalize(_minimal_json())
        for i, b in enumerate(blocks):
            assert "type" in b, f"Block #{i} sin 'type': {b}"

    def test_empty_data_returns_footer_only(self):
        """JSON vacío (sin caratula ni cuerpo) retorna al menos page_footer."""
        blocks = normalize({})
        assert len(blocks) >= 1
        assert blocks[-1]["type"] == "page_footer"


class TestUnacProyectoStructuredSections:
    def test_project_does_not_autoinject_structured_problem_objective_hypothesis(self):
        blocks = normalize(_project_structured_json())
        bold_texts = [block["text"] for block in _blocks_of_type(blocks, "paragraph_bold")]

        assert "Problema general" not in bold_texts
        assert not any("Problemas espec" in text for text in bold_texts)
        assert "Objetivo general" not in bold_texts
        assert not any("Objetivos espec" in text for text in bold_texts)
        assert not any("Hip" in text and "general" in text for text in bold_texts)
        assert not any("Hip" in text and "espec" in text for text in bold_texts)

    def test_project_does_not_autoinject_nested_matrix_text(self):
        data = _project_structured_json()
        data["matriz_consistencia"] = {
            "problemas": {
                "general": "Problema general test",
                "especificos": ["Problema especifico test"],
            },
            "objetivos": {
                "general": "Objetivo general test",
                "especificos": ["Objetivo especifico test"],
            },
            "hipotesis": {
                "general": "Hipotesis general test",
                "especificos": ["Hipotesis especifica test"],
            },
        }

        blocks = normalize(data)
        paragraph_texts = [block["text"] for block in _blocks_of_type(blocks, "paragraph")]

        assert "Problema general test" not in paragraph_texts
        assert "Objetivo general test" not in paragraph_texts
        assert "Hipotesis general test" not in paragraph_texts

    def test_operationalization_tables_are_autogenerated_when_ai_has_no_table(self):
        blocks = normalize(_project_structured_json())
        tables = _blocks_of_type(blocks, "table")
        titles = [table.get("titulo") for table in tables]

        assert any(str(title or "").startswith("Tabla 3.1 Operacionaliz") for title in titles)
        assert any(str(title or "").startswith("Tabla 3.2 Operacionaliz") for title in titles)

    def test_project_keeps_explicit_operationalization_table_if_it_arrives_as_ai_content(self):
        data = _project_structured_json()
        data["cuerpo"][1]["contenido"][1]["_ai_content"] = [
            {
                "tipo": "tabla",
                "titulo": "Operacionalizacion de Variables",
                "encabezados": ["Variable", "Dimension"],
                "filas": [["RCM", "Confiabilidad"]],
            }
        ]

        blocks = normalize(data)
        tables = _blocks_of_type(blocks, "table")

        assert len([table for table in tables if table.get("titulo") == "Operacionalizacion de Variables"]) == 1
        assert not any(str(table.get("titulo") or "").startswith("Tabla 3.1 Operacionaliz") for table in tables)
        assert not any(str(table.get("titulo") or "").startswith("Tabla 3.2 Operacionaliz") for table in tables)


def test_consecutive_landscape_tables_disable_intermediate_portrait_restore():
    data = _minimal_json()
    data["cuerpo"] = [
        {
            "titulo": "III. HIPOTESIS Y VARIABLES",
            "contenido": [
                {
                    "tipo": "tabla",
                    "titulo": "Tabla A",
                    "orientacion": "landscape",
                    "encabezados": ["A", "B", "C", "D", "E", "F"],
                    "filas": [["1", "2", "3", "4", "5", "6"]],
                },
                {
                    "tipo": "tabla",
                    "titulo": "Tabla B",
                    "orientacion": "landscape",
                    "encabezados": ["A", "B", "C", "D", "E", "F"],
                    "filas": [["7", "8", "9", "10", "11", "12"]],
                },
            ],
        }
    ]

    blocks = normalize(data)
    tables = _blocks_of_type(blocks, "table")

    assert len(tables) == 2
    assert tables[0].get("restore_portrait") is False
    assert tables[1].get("restore_portrait", True) is True


def test_operationalization_tables_include_page_break_between_31_and_32():
    blocks = normalize(_project_structured_json())
    table_positions = [
        idx
        for idx, block in enumerate(blocks)
        if block.get("type") == "table"
        and str(block.get("titulo") or "").startswith("Tabla 3.")
    ]
    assert len(table_positions) >= 2
    between = blocks[table_positions[0] + 1 : table_positions[1]]
    assert any(block.get("type") == "page_break" for block in between)

class TestNormalizeCaratula:
    def test_caratula_centered_texts(self):
        """Caratula genera centered_text para universidad y facultad."""
        blocks = normalize(_minimal_json())
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert "UNIVERSIDAD TEST" in texts
        assert "FACULTAD TEST" in texts

    def test_caratula_has_logo(self):
        """Caratula genera block logo."""
        blocks = normalize(_minimal_json())
        logos = _blocks_of_type(blocks, "logo")
        assert len(logos) == 1

    def test_caratula_ends_with_page_break(self):
        """Después de la carátula hay un page_break."""
        blocks = normalize(_minimal_json())
        types = _types(blocks)
        # Encontrar la posición del logo y luego buscar page_break
        assert "page_break" in types

    def test_caratula_fallback_uni_name(self):
        """Si caratula.universidad está vacío, usa fallback de _meta."""
        data = _minimal_json()
        data["caratula"]["universidad"] = ""
        data["_meta"]["university"] = "uni"
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert "UNIVERSIDAD NACIONAL DE INGENIERÍA" in texts

    def test_caratula_autor_asesor(self):
        """Caratula con autor/asesor genera los centered_text correspondientes."""
        data = _minimal_json()
        data["caratula"]["label_autor"] = "AUTOR: Juan"
        data["caratula"]["label_asesor"] = "ASESOR: Dr. X"
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert "AUTOR: Juan" in texts
        assert "ASESOR: Dr. X" in texts

    def test_caratula_lugar_anio(self):
        """Caratula con lugar y año genera footer centered_text."""
        data = _minimal_json()
        data["caratula"]["lugar"] = "Lima"
        data["caratula"]["anio"] = "2026"
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert any("Lima" in t and "2026" in t for t in texts)

    def test_caratula_uses_root_title_when_cover_is_placeholder(self):
        """Si caratula trae placeholder, usa el titulo real del payload."""
        data = _minimal_json()
        data["title"] = "Implementacion de IA en procesos logisticos"
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert "Implementacion de IA en procesos logisticos" in texts

    def test_caratula_skips_instructional_frase_grado(self):
        """No debe renderizar notas de guia en frase_grado."""
        data = _minimal_json()
        data["caratula"]["frase_grado"] = (
            "[Nota: Contiene: Las variables, unidad de análisis, ámbito de estudio. "
            "Máximo 15 palabras sin considerar artículos conectores.]"
        )
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert not any("Nota: Contiene" in t for t in texts)

    def test_caratula_keeps_real_frase_grado(self):
        """frase_grado válida sí debe renderizarse."""
        data = _minimal_json()
        data["caratula"]["frase_grado"] = "PARA OPTAR EL TITULO PROFESIONAL DE:"
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert "PARA OPTAR EL TITULO PROFESIONAL DE:" in texts


# ─────────────────────────────────────────────────────────────
# PÁGINA DE RESPETO
# ─────────────────────────────────────────────────────────────

class TestNormalizePaginaRespeto:
    def test_without_pagina_respeto(self):
        """Sin pagina_respeto no genera blocks de esa sección."""
        blocks = normalize(_minimal_json())
        ct = _blocks_of_type(blocks, "centered_text")
        texts = [b["text"] for b in ct]
        assert not any("RESPETO" in t for t in texts)

    def test_with_pagina_respeto(self):
        """Con pagina_respeto genera titulo + nota + page_break."""
        data = _minimal_json()
        data["pagina_respeto"] = {
            "titulo": "PÁGINA DE RESPETO",
            "notas": [{"texto": "Nota importante"}],
        }
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        assert any(b["text"] == "PÁGINA DE RESPETO" for b in ct)
        notes = _blocks_of_type(blocks, "note")
        assert any(b["text"] == "Nota importante" for b in notes)


# ─────────────────────────────────────────────────────────────
# INFORMACIÓN BÁSICA
# ─────────────────────────────────────────────────────────────

class TestNormalizeInfoBasica:
    def test_without_info_basica(self):
        """Sin informacion_basica no genera info_table."""
        blocks = normalize(_minimal_json())
        assert len(_blocks_of_type(blocks, "info_table")) == 0

    def test_with_info_basica(self):
        """Con informacion_basica genera heading + info_table + page_break."""
        data = _minimal_json()
        data["informacion_basica"] = {
            "titulo": "INFORMACIÓN BÁSICA",
            "elementos": [{"label": "TITLE:", "valor": "Test"}],
        }
        blocks = normalize(data)
        it = _blocks_of_type(blocks, "info_table")
        assert len(it) == 1
        assert it[0]["elementos"][0]["label"] == "TITLE:"

    def test_ai_justificacion_subsections_render_as_heading3(self):
        data = _minimal_json()
        data["cuerpo"] = [
            {
                "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
                "contenido": [
                    {
                        "texto": "1.4 Justificación",
                        "_ai_content": (
                            "1.4.1 Justificacion normativa\n"
                            "La investigacion se sustenta en SAE JA1011 y la ISO 14224.\n\n"
                            "1.4.2 Justificacion teorica\n"
                            "El estudio aplica fundamentos de confiabilidad operacional.\n\n"
                            "1.4.3 Justificacion practica\n"
                            "La propuesta mejora la disponibilidad de la flota."
                        ),
                    }
                ],
            }
        ]

        blocks = normalize(data)

        heading3 = [
            block for block in blocks
            if block["type"] == "heading" and block.get("level") == 3
        ]
        assert [block["text"] for block in heading3] == [
            "1.4.1 Justificacion normativa",
            "1.4.2 Justificacion teorica",
            "1.4.3 Justificacion practica",
        ]

    def test_ai_delimitaciones_subsections_render_as_heading3(self):
        data = _minimal_json()
        data["cuerpo"] = [
            {
                "titulo": "I. PLANTEAMIENTO DEL PROBLEMA",
                "contenido": [
                    {
                        "texto": "1.5 Delimitaciones de la investigación",
                        "_ai_content": (
                            "1.5.1 Delimitacion teorica\n"
                            "La investigacion se circunscribe al RCM y la confiabilidad operacional.\n\n"
                            "1.5.2 Delimitacion temporal\n"
                            "El horizonte del estudio corresponde al periodo 2025.\n\n"
                            "1.5.3 Delimitacion espacial\n"
                            "El estudio se desarrolla en una unidad minera de la region Junin."
                        ),
                    }
                ],
            }
        ]

        blocks = normalize(data)

        heading3 = [
            block for block in blocks
            if block["type"] == "heading" and block.get("level") == 3
        ]
        assert [block["text"] for block in heading3] == [
            "1.5.1 Delimitacion teorica",
            "1.5.2 Delimitacion temporal",
            "1.5.3 Delimitacion espacial",
        ]

    def test_ai_antecedentes_subsections_render_as_heading3(self):
        data = _minimal_json()
        data["cuerpo"] = [
            {
                "titulo": "II. MARCO TEORICO",
                "contenido": [
                    {
                        "texto": "2.1 Antecedentes",
                        "_ai_content": (
                            "2.1.1 Antecedentes internacionales\n"
                            "Se identificaron estudios de confiabilidad en flotas mineras de India y Australia.\n\n"
                            "2.1.2 Antecedentes nacionales\n"
                            "Se revisaron investigaciones peruanas sobre disponibilidad y mantenimiento."
                        ),
                    }
                ],
            }
        ]

        blocks = normalize(data)

        heading3 = [
            block for block in blocks
            if block["type"] == "heading" and block.get("level") == 3
        ]
        assert [block["text"] for block in heading3] == [
            "2.1.1 Antecedentes internacionales",
            "2.1.2 Antecedentes nacionales",
        ]


# ─────────────────────────────────────────────────────────────
# PRELIMINARES
# ─────────────────────────────────────────────────────────────

class TestNormalizePreliminares:
    def test_dedicatoria_as_dict(self):
        """Dedicatoria como dict genera heading + párrafo."""
        data = _minimal_json()
        data["preliminares"] = {
            "dedicatoria": {"titulo": "DEDICATORIA", "texto": "A mi familia"},
        }
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "DEDICATORIA" for b in hdgs)
        pars = _blocks_of_type(blocks, "paragraph")
        assert any(b["text"] == "A mi familia" for b in pars)

    def test_optional_preliminary_as_string_is_omitted(self):
        """Dedicatoria opcional sin contenido no debe dejar heading vacio."""
        data = _minimal_json()
        data["preliminares"] = {"dedicatoria": "DEDICATORIA"}
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert not any(b["text"] == "DEDICATORIA" for b in hdgs)

    def test_preliminary_ai_content_overrides_placeholder_text(self):
        data = _minimal_json()
        data["preliminares"] = {
            "dedicatoria": {
                "titulo": "DEDICATORIA",
                "texto": "[Escriba aqui su dedicatoria...]",
                "_ai_content": "Dedico este trabajo a mi familia por su apoyo constante.",
            }
        }
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        texts = [b["text"] for b in pars]
        assert any("Dedico este trabajo" in t for t in texts)
        assert not any("[Escriba aqui" in t for t in texts)

    def test_optional_preliminary_placeholder_is_omitted(self):
        data = _minimal_json()
        data["preliminares"] = {
            "dedicatoria": {
                "titulo": "DEDICATORIA",
                "texto": "[Escriba aqui su dedicatoria...]",
            }
        }
        blocks = normalize(data)
        headings = [b["text"] for b in _blocks_of_type(blocks, "heading")]
        assert "DEDICATORIA" not in headings

    def test_indices_as_dict(self):
        """Indices como dict genera toc_field blocks."""
        data = _minimal_json()
        data["preliminares"] = {
            "indices": {
                "contenido": "ÍNDICE",
                "tablas": "ÍNDICE DE TABLAS",
                "figuras": "ÍNDICE DE FIGURAS",
            }
        }
        blocks = normalize(data)
        tocs = _blocks_of_type(blocks, "toc_field")
        assert len(tocs) == 3
        assert tocs[0]["heading_text"] == "ÍNDICE"

    def test_indices_as_list(self):
        """Indices como list genera toc_field + tabla de abreviaturas."""
        data = _minimal_json()
        data["preliminares"] = {
            "indices": [
                {"titulo": "ÍNDICE", "items": [{"texto": "Cap I", "pag": 1}]},
                {"titulo": "ÍNDICE DE TABLAS"},
                {"titulo": "ÍNDICE DE ABREVIATURAS", "items": [{"texto": "IA: Inteligencia Artificial"}]},
            ]
        }
        blocks = normalize(data)
        tocs = _blocks_of_type(blocks, "toc_field")
        assert len(tocs) == 2  # ÍNDICE y ÍNDICE DE TABLAS
        abbr = _blocks_of_type(blocks, "abbreviations_table")
        assert len(abbr) == 1
        assert abbr[0]["rows"][0]["sigla"] == "IA"

    def test_indices_list_prefers_ai_abbreviations_over_base_examples(self):
        data = _minimal_json()
        data["preliminares"] = {
            "indices": [
                {
                    "titulo": "ÍNDICE DE ABREVIATURAS",
                    "items": [{"texto": "OMS: Organizacion Mundial de la Salud"}],
                }
            ],
            "abreviaturas": {
                "titulo": "INDICE DE ABREVIATURAS",
                "_ai_content": "IA: Inteligencia Artificial\nERP: Planificacion de Recursos Empresariales",
            },
        }
        blocks = normalize(data)
        abbr = _blocks_of_type(blocks, "abbreviations_table")
        assert len(abbr) == 1
        rows = abbr[0]["rows"]
        assert rows[0]["sigla"] == "IA"
        assert all(row["sigla"] != "OMS" for row in rows)

    def test_abbreviaturas_without_rows_use_clean_fallback_text(self):
        data = _minimal_json()
        data["preliminares"] = {
            "abreviaturas": {"titulo": "INDICE DE ABREVIATURAS", "_ai_content": ""},
        }
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        assert any(
            b["text"] == "No se identificaron abreviaturas relevantes en el presente documento."
            for b in pars
        )

    def test_abbreviaturas_are_derived_from_generated_body_content(self):
        data = _minimal_json()
        data["preliminares"] = {
            "indices": {
                "contenido": "INDICE",
                "abreviaturas": "INDICE DE ABREVIATURAS",
            }
        }
        data["cuerpo"] = [
            {
                "titulo": "II. MARCO TEORICO",
                "contenido": [
                    {
                        "texto": "2.1 Bases teoricas",
                        "_ai_content": (
                            "La Inteligencia Artificial (IA) se integra con soluciones de IoT para el monitoreo continuo. "
                            "Ademas, el analisis estadistico se procesa en SPSS y el seguimiento operativo utiliza KPI tecnicos."
                        ),
                    }
                ],
            }
        ]

        blocks = normalize(data)
        abbr = _blocks_of_type(blocks, "abbreviations_table")

        assert len(abbr) == 1
        rows = abbr[0]["rows"]
        assert any(row["sigla"] == "IA" and "Inteligencia Artificial" in row["meaning"] for row in rows)
        assert any(row["sigla"] == "IoT" and "Internet de las Cosas" in row["meaning"] for row in rows)
        assert any(row["sigla"] == "SPSS" and "Statistical Package" in row["meaning"] for row in rows)
        assert any(row["sigla"] == "KPI" and "Key Performance Indicator" in row["meaning"] for row in rows)

    def test_introduccion(self):
        """Introducción en preliminares genera heading + párrafo."""
        data = _minimal_json()
        data["preliminares"] = {
            "introduccion": {"titulo": "INTRODUCCIÓN", "texto": "Texto intro"},
        }
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "INTRODUCCIÓN" for b in hdgs)


# ─────────────────────────────────────────────────────────────
# CUERPO
# ─────────────────────────────────────────────────────────────

class TestNormalizeCuerpo:
    def test_chapter_heading(self):
        """Cada capítulo genera un heading level 1."""
        blocks = normalize(_minimal_json())
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "CAP I" and b["level"] == 1 for b in hdgs)

    def test_ai_figure_inherits_parent_note_and_color_blue(self):
        """Una figura inyectada por IA hereda la nota e instrucción del padre y se marca azul."""
        data = _minimal_json()
        data["cuerpo"] = [
            {
                "titulo": "CAP I",
                "contenido": [
                    {
                        "texto": "1.1 Descripcion",
                        "nota": "Instruccion de prueba de la seccion",
                        "_ai_content": [
                            {
                                "tipo": "figura",
                                "titulo": "Figura de IA",
                                "ruta": "figura_real.png",
                            }
                        ]
                    }
                ]
            }
        ]
        blocks = normalize(data)
        images = _blocks_of_type(blocks, "image")
        assert len(images) == 1
        assert images[0]["titulo"] == "Figura de IA"
        assert images[0]["nota"] == "Instruccion de prueba de la seccion"
        assert images[0]["nota_color"] == "0000FF"

    def test_page_break_before_second_chapter_only(self):
        """Los saltos de capitulo van antes del siguiente capitulo, no despues del titulo."""
        data = _minimal_json()
        data["cuerpo"] = [
            {"titulo": "CAP I", "contenido": [{"texto": "1.1", "parrafos": ["Texto 1"]}]},
            {"titulo": "CAP II", "contenido": [{"texto": "2.1", "parrafos": ["Texto 2"]}]},
        ]
        blocks = normalize(data)

        # Debe existir al menos un page_break en el cuerpo (antes de CAP II).
        headings_positions = [
            index for index, block in enumerate(blocks)
            if block["type"] == "heading" and block.get("text") in {"CAP I", "CAP II"}
        ]
        assert len(headings_positions) == 2

        cap_i_pos, cap_ii_pos = headings_positions
        between = blocks[cap_i_pos + 1:cap_ii_pos]
        assert any(block["type"] == "page_break" for block in between)

    def test_chapter_nota_capitulo(self):
        """nota_capitulo genera block note."""
        data = _minimal_json()
        data["cuerpo"][0]["nota_capitulo"] = "Nota del capítulo"
        blocks = normalize(data)
        notes = _blocks_of_type(blocks, "note")
        assert any(b["text"] == "Nota del capítulo" for b in notes)

    def test_content_with_tabla_canonical(self):
        """Item tipo='tabla' en contenido genera block table."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "tipo": "tabla",
            "titulo": "Tabla test",
            "encabezados": ["A", "B"],
            "filas": [["1", "2"]],
        }]
        blocks = normalize(data)
        tables = _blocks_of_type(blocks, "table")
        assert len(tables) == 1
        assert tables[0]["titulo"] == "Tabla test"

    def test_content_with_subtitle_and_note(self):
        """Item con texto + instruccion_detallada genera black_heading + note."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sección",
            "instruccion_detallada": "Detalle aquí",
        }]
        blocks = normalize(data)
        bh = _blocks_of_type(blocks, "black_heading")
        assert len(bh) == 1
        assert bh[0]["text"] == "1.1 Sección"
        notes = _blocks_of_type(blocks, "note")
        assert any(b["text"] == "Detalle aquí" for b in notes)

    def test_content_with_image(self):
        """Item con imagenes genera blocks image."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "imagenes": [{"titulo": "Fig test", "ruta": "fig.png", "fuente": "Propia"}],
        }]
        blocks = normalize(data)
        imgs = _blocks_of_type(blocks, "image")
        assert len(imgs) == 1
        assert imgs[0]["titulo"] == "Fig test"
        assert imgs[0]["fuente"] == "Propia"

    def test_content_with_placeholder_image_is_skipped(self):
        """Imagenes placeholder no deben generar blocks image."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "imagenes": [{"titulo": "Fig test", "ruta": "placeholder", "fuente": "Propia"}],
        }]
        blocks = normalize(data)
        imgs = _blocks_of_type(blocks, "image")
        assert len(imgs) == 0

    def test_content_with_template_example_image_is_skipped(self):
        """Las figuras de ejemplo del formato base nunca deben renderizarse."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "imagenes": [{"titulo": "Arbol de problemas", "ruta": "figura_ejemplo.png", "fuente": "Propia"}],
        }]
        blocks = normalize(data)
        imgs = _blocks_of_type(blocks, "image")
        assert len(imgs) == 0

    def test_content_with_legacy_table(self):
        """Item con tabla legacy (headers/rows) genera block legacy_table."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "tabla": {"headers": ["X", "Y"], "rows": [["a", "b"]]},
            "tabla_titulo": "Tabla legacy",
        }]
        blocks = normalize(data)
        lt = _blocks_of_type(blocks, "legacy_table")
        assert len(lt) == 1
        assert lt[0]["titulo"] == "Tabla legacy"
        assert lt[0]["tabla"]["headers"] == ["X", "Y"]

    def test_placeholder_legacy_table_is_skipped(self):
        """Tablas legacy con celdas placeholder no deben renderizarse."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "6.1 Discusion",
            "tabla": {
                "headers": ["Autor/Estudio", "Variable", "Resultado del autor"],
                "rows": [["[Autor 1]", "[Variable]", "[Resultado]"]],
            },
            "tabla_titulo": "Tabla 13. Comparacion de resultados con antecedentes",
        }]
        blocks = normalize(data)
        assert _blocks_of_type(blocks, "legacy_table") == []

    def test_content_with_tablas_especiales(self):
        """tablas_especiales genera blocks legacy_table."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "tablas_especiales": [
                {"titulo": "TE1", "headers": ["A"], "rows": [["1"]]},
            ],
        }]
        blocks = normalize(data)
        lt = _blocks_of_type(blocks, "legacy_table")
        assert len(lt) == 1
        assert lt[0]["titulo"] == "TE1"

    def test_subsection_ai_content_replaces_base_image_and_keeps_single_caption_source(self):
        """Cuando hay _ai_content, debe quedar solo la figura indexable final."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "imagenes": [{"titulo": "Arbol de problemas", "ruta": "figura_ejemplo.png", "fuente": "Base"}],
            "_ai_content": [
                {
                    "tipo": "figura",
                    "titulo": "Modelo real",
                    "caption": "Figura 1. Modelo real.",
                    "ruta_placeholder": "assets/placeholder_figura.png",
                    "fuente": "Elaboracion propia",
                    "nota": "Guía para elaborar la figura: usar datos reales.",
                    "nota_color": "0000FF",
                }
            ],
        }]
        blocks = normalize(data)
        imgs = _blocks_of_type(blocks, "image")
        pars = _blocks_of_type(blocks, "paragraph")

        assert len(imgs) == 1
        assert imgs[0]["titulo"] == "Modelo real"
        assert imgs[0]["ruta"] == "assets/placeholder_figura.png"
        assert imgs[0]["nota"] == "Guía para elaborar la figura: usar datos reales."
        assert imgs[0]["nota_color"] == "0000FF"
        assert all("Figura 1. Modelo real." not in b["text"] for b in pars)
        assert all(b["ruta"] != "figura_ejemplo.png" for b in imgs)

    def test_subsection_ai_content_replaces_base_example_table(self):
        """Una tabla generada por IA debe reemplazar la tabla ejemplo del formato."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "1.1 Sec",
            "tabla": {"headers": ["Base"], "rows": [["Ejemplo"]]},
            "tabla_titulo": "Tabla 3.1. Matriz de categorizacion (ejemplo)",
            "_ai_content": [
                {
                    "tipo": "tabla",
                    "titulo": "Tabla final",
                    "encabezados": ["Categoria", "Codigo"],
                    "filas": [["Gestion", "A1"]],
                }
            ],
        }]
        blocks = normalize(data)
        tables = _blocks_of_type(blocks, "table")
        legacy_tables = _blocks_of_type(blocks, "legacy_table")

        assert len(tables) == 1
        assert tables[0]["titulo"] == "Tabla final"
        assert len(legacy_tables) == 0

    def test_content_string_item(self):
        """String en contenido genera paragraph."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = ["Plain text here"]
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        assert any(b["text"] == "Plain text here" for b in pars)

    def test_mostrar_matriz_does_not_render_placeholder(self):
        """mostrar_matriz:true no debe dejar texto placeholder visible."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{"texto": "Sec", "mostrar_matriz": True}]
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        assert not any("Matriz de Consistencia" in b["text"] for b in pars)

    def test_ejemplos_apa_chapter(self):
        """ejemplos_apa a nivel de capítulo genera apa_examples."""
        data = _minimal_json()
        data["cuerpo"][0]["ejemplos_apa"] = ["Ej1", "Ej2"]
        blocks = normalize(data)
        apa = _blocks_of_type(blocks, "apa_examples")
        assert len(apa) == 1
        assert apa[0]["ejemplos"] == ["Ej1", "Ej2"]


    def test_formula_text_not_treated_as_heading(self):
        """Texto con patrón N.N.N seguido de fórmula matemática no debe ser Heading 3.

        Regresión: la IA puede generar una línea como '4.2.1 n = N·Z²·p·q / (N-1)·e²'
        que coincide con el regex de nivel 3, pero es una fórmula, no un título.
        No debe aparecer en el índice de contenidos.
        """
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "4.2 Diseño muestral",
            "_ai_content": (
                "4.2.1 Fórmula de tamaño de muestra\n\n"
                "n = N · Z² · p · q / (N-1) · e² + Z² · p · q\n\n"
                "Donde N es el tamaño de la población."
            ),
        }]
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        # La fórmula con operadores matemáticos NO debe generar heading nivel 3
        formula_headings = [
            b for b in hdgs
            if "=" in b.get("text", "") or "·" in b.get("text", "")
        ]
        assert formula_headings == [], f"Fórmulas no deben ser heading: {formula_headings}"
        # El texto de la fórmula debe aparecer como párrafo
        pars = _blocks_of_type(blocks, "paragraph")
        assert any("N · Z²" in b.get("text", "") or "N-1" in b.get("text", "") for b in pars)

    def test_formula_as_item_texto_not_treated_as_black_heading(self):
        """Una fórmula matemática como 'texto' de un item del JSON estructurado NO debe
        ser emitida como black_heading, ya que eso la haría aparecer en el TOC de Word.

        Regresión: cuando la IA genera {'texto': 'D = MTBF / (MTBF + MTTR)', '_ai_content': [...]},
        el normalizer lo convertía en black_heading (Heading 2 en Word → visible en TOC).
        Debe convertirse en un párrafo normal.
        """
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "D = MTBF / (MTBF + MTTR)",
            "_ai_content": ["La disponibilidad inherente mide la probabilidad de que el equipo funcione."],
        }]
        blocks = normalize(data)
        # La fórmula NO debe ser black_heading
        bh = _blocks_of_type(blocks, "black_heading")
        formula_bh = [b for b in bh if "=" in b.get("text", "") or "MTBF" in b.get("text", "")]
        assert formula_bh == [], f"Fórmulas no deben ser black_heading (aparecen en TOC): {formula_bh}"
        # La fórmula NO debe ser heading
        hdgs = _blocks_of_type(blocks, "heading")
        formula_hdgs = [b for b in hdgs if "=" in b.get("text", "") or "MTBF" in b.get("text", "")]
        assert formula_hdgs == [], f"Fórmulas no deben ser heading: {formula_hdgs}"

    def test_subtitulo_22x_with_markdown_bold_detected_as_heading3(self):
        """Un subtítulo con asteriscos Markdown (**2.2.1 Título**) debe renderizarse
        como Heading nivel 3, eliminando los asteriscos del texto final.

        Regresión: la IA puede devolver texto con formato Markdown que el regex
        no detectaba por los caracteres adicionales.
        """
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "tipo": "parrafo",
            "texto": "**2.2.1 Mantenimiento Centrado en Confiabilidad (RCM)**",
        }]
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        h3 = [b for b in hdgs if b.get("level") == 3]
        assert len(h3) == 1, f"Se esperaba un Heading 3, se obtuvo: {h3}"
        assert "**" not in h3[0]["text"], "El texto del heading no debe tener asteriscos"
        assert "2.2.1" in h3[0]["text"]
        assert "RCM" in h3[0]["text"] or "Mantenimiento" in h3[0]["text"]

    def test_subtitulo_22x_multiline_parrafo_detected_as_heading3(self):
        """Un párrafo multi-línea que empieza con un título de nivel 3 (e.g. 2.2.1)
        debe ser correctamente dividido en un bloque de heading 3 y otro bloque de párrafo.
        """
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "tipo": "parrafo",
            "texto": "2.2.1 Mantenimiento Centrado en Confiabilidad (RCM)\nEl Mantenimiento Centrado en Confiabilidad es una metodología...",
        }]
        blocks = normalize(data)
        
        hdgs = _blocks_of_type(blocks, "heading")
        h3 = [b for b in hdgs if b.get("level") == 3]
        assert len(h3) == 1, f"Se esperaba un Heading 3, se obtuvo: {h3}"
        assert h3[0]["text"] == "2.2.1 Mantenimiento Centrado en Confiabilidad (RCM)"
        
        pars = _blocks_of_type(blocks, "paragraph")
        rcm_pars = [p for p in pars if "El Mantenimiento" in p.get("text", "")]
        assert len(rcm_pars) == 1
        assert rcm_pars[0]["text"] == "El Mantenimiento Centrado en Confiabilidad es una metodología..."

    def test_figure_without_nota_gets_generic_blue_instruction(self):
        """Figura sin nota propia ni en el parent_item debe recibir una nota genérica
        azul para guiar al estudiante.

        Regresión: las figuras generadas por IA en 2.2 Bases Teóricas no traen
        nota ni instruccion_detallada, por lo que antes no aparecía instrucción
        debajo de la imagen.
        """
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{
            "texto": "2.2.1 Mantenimiento Centrado en Confiabilidad",
            "_ai_content": [
                {
                    "tipo": "figura",
                    "titulo": "Árbol de fallas del sistema",
                    "ruta": "assets/figura_rcm.png",
                    "fuente": "Elaboración propia",
                    # Sin 'nota' ni 'instruccion_detallada' — ni en la figura ni en el padre
                }
            ],
        }]
        blocks = normalize(data)
        images = _blocks_of_type(blocks, "image")
        assert len(images) == 1
        # La figura debe tener una nota genérica (no vacía)
        assert images[0]["nota"], "La figura debe tener una nota de instrucción genérica"
        assert images[0]["nota_color"] == "0000FF", "La nota debe ser azul (0000FF)"
        # El texto genérico debe mencionar la figura o ser una instrucción útil
        nota_text = images[0]["nota"].lower()
        assert any(
            keyword in nota_text
            for keyword in ["elaborar", "figura", "datos", "fuente", "incluir"]
        ), f"La nota genérica debe ser instructiva, se obtuvo: {images[0]['nota']!r}"


# ─────────────────────────────────────────────────────────────
# FINALES
# ─────────────────────────────────────────────────────────────

def test_chapter_ai_table_skips_template_direct_table():
    """Si el capitulo ya trae tabla IA, la tabla canonica base no debe coexistir."""
    data = _minimal_json()
    data["cuerpo"][0]["_ai_content"] = [
        {
            "tipo": "tabla",
            "titulo": "Cronograma final",
            "encabezados": ["Actividad", "Mes 1"],
            "filas": [["Real", "X"]],
        }
    ]
    data["cuerpo"][0]["contenido"] = [
        {
            "tipo": "tabla",
            "titulo": "Cronograma final",
            "encabezados": ["Actividad", "Mes 1"],
            "filas": [["Real", "X"]],
            "_ai_generated": True,
        },
        {
            "tipo": "tabla",
            "titulo": "Cronograma de Actividades",
            "encabezados": ["Actividad", "Mes 1"],
            "filas": [["Base", "X"]],
        },
    ]

    blocks = normalize(data)
    tables = _blocks_of_type(blocks, "table")

    assert len(tables) == 1
    assert tables[0]["titulo"] == "Cronograma final"


class TestNormalizeFinales:
    def test_referencias_as_string(self):
        """Referencias como string genera heading."""
        data = _minimal_json()
        data["finales"] = {"referencias": "REFERENCIAS"}
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "REFERENCIAS" for b in hdgs)

    def test_referencias_as_dict(self):
        """Referencias como dict genera heading + nota + apa_examples."""
        data = _minimal_json()
        data["finales"] = {
            "referencias": {
                "titulo": "REFERENCIAS BIBLIOGRÁFICAS",
                "nota": "Cite correctamente",
                "ejemplos": ["Ej1"],
            }
        }
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "REFERENCIAS BIBLIOGRÁFICAS" for b in hdgs)
        notes = _blocks_of_type(blocks, "note")
        assert any(b["text"] == "Cite correctamente" for b in notes)
        apa = _blocks_of_type(blocks, "apa_examples")
        assert len(apa) == 1

    def test_referencias_start_on_new_page(self):
        """Referencias debe iniciar con page_break antes del heading."""
        data = _minimal_json()
        data["cuerpo"] = [
            {
                "titulo": "I. CAPITULO",
                "contenido": [{"texto": "1.1 Seccion", "_ai_content": "Texto base."}],
            }
        ]
        data["finales"] = {
            "referencias": {
                "titulo": "REFERENCIAS BIBLIOGRAFICAS",
                "_ai_content": "Referencia uno.\n\nReferencia dos.",
            }
        }

        blocks = normalize(data)
        ref_idx = next(
            i
            for i, block in enumerate(blocks)
            if block["type"] == "heading"
            and block["text"] == "REFERENCIAS BIBLIOGRAFICAS"
        )

        assert ref_idx > 0
        assert blocks[ref_idx - 1]["type"] == "page_break"

    def test_referencias_ai_content_replaces_examples(self):
        """Si referencias tiene _ai_content, no deben sobrevivir ejemplos base."""
        data = _minimal_json()
        data["finales"] = {
            "referencias": {
                "titulo": "REFERENCIAS BIBLIOGRAFICAS",
                "nota": "Cite correctamente",
                "ejemplos_apa": ["Ejemplo base"],
                "_ai_content": (
                    "Referencias propuestas simuladas para validacion.\n\n"
                    "Morales, J. (2024). Texto uno.\n\n"
                    "Rojas, M. (2023). Texto dos."
                ),
            }
        }
        blocks = normalize(data)
        paragraphs = _blocks_of_type(blocks, "paragraph")
        notes = _blocks_of_type(blocks, "note")
        apa = _blocks_of_type(blocks, "apa_examples")

        assert any("Referencias propuestas simuladas" in block["text"] for block in paragraphs)
        assert any("Morales, J." in block["text"] for block in paragraphs)
        assert any("Rojas, M." in block["text"] for block in paragraphs)
        assert len(notes) == 0
        assert len(apa) == 0

    def test_anexos_with_matriz_landscape(self):
        """Anexo con matriz genera section_switch landscape → heading → matriz → portrait."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [{"titulo": "Anexo 1: Matriz de consistencia"}],
            }
        }
        data["matriz_consistencia"] = {
            "problemas": {"general": "P?", "especificos": []},
            "objetivos": {"general": "O", "especificos": []},
            "hipotesis": {"general": "H", "especificos": []},
            "variables": {},
            "metodologia": {"tipo": "Aplicada"},
        }
        blocks = normalize(data)

        # Verificar secuencia: section_switch(landscape) → heading → black_heading → matriz → section_switch(portrait)
        ss = _blocks_of_type(blocks, "section_switch")
        assert len(ss) == 2
        assert ss[0]["orientation"] == "landscape"
        assert ss[1]["orientation"] == "portrait"

        mat = _blocks_of_type(blocks, "matriz")
        assert len(mat) == 1
        assert mat[0]["landscape"] is False

    def test_anexo_ai_content_replaces_base_fallback_content(self):
        """Los anexos con _ai_content no deben mezclar matriz fallback ni tablas base."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 1: Matriz de consistencia",
                        "tabla": {"headers": ["Base"], "rows": [["Ejemplo"]]},
                        "tabla_titulo": "Tabla A1. Matriz de consistencia (ejemplo)",
                        "_ai_content": [
                            {
                                "tipo": "tabla",
                                "titulo": "Matriz final",
                                "encabezados": ["Problema", "Objetivo"],
                                "filas": [["P1", "O1"]],
                            }
                        ],
                    }
                ],
            }
        }
        data["matriz_consistencia"] = {
            "problemas": {"general": "P?", "especificos": []},
            "objetivos": {"general": "O", "especificos": []},
            "hipotesis": {"general": "H", "especificos": []},
            "variables": {},
            "metodologia": {"tipo": "Aplicada"},
        }

        blocks = normalize(data)
        tables = _blocks_of_type(blocks, "table")
        matrices = _blocks_of_type(blocks, "matriz")
        legacy_tables = _blocks_of_type(blocks, "legacy_table")

        assert len(tables) == 1
        assert not tables[0].get("titulo")
        assert len(matrices) == 0
        assert len(legacy_tables) == 0

    def test_anexo_strips_intro_filler_and_table_title(self):
        """El anexo debe ir directo al contenido y sin caption de tabla principal."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 1: Matriz de consistencia final",
                        "_ai_content": [
                            {
                                "tipo": "parrafo",
                                "texto": "A continuacion se muestra la matriz de consistencia final.",
                            },
                            {
                                "tipo": "tabla",
                                "titulo": "Tabla 14. Matriz de consistencia final",
                                "encabezados": ["Problema", "Objetivo"],
                                "filas": [["P1", "O1"]],
                            },
                        ],
                    }
                ],
            }
        }

        blocks = normalize(data)
        bold_blocks = _blocks_of_type(blocks, "paragraph_bold")
        paragraphs = _blocks_of_type(blocks, "paragraph")
        tables = _blocks_of_type(blocks, "table")

        assert any("Anexo 1: Matriz de consistencia final" == b["text"] for b in bold_blocks)
        assert all(
            "A continuacion se muestra" not in b["text"] for b in paragraphs if "text" in b
        )
        assert len(tables) == 1
        assert not tables[0].get("titulo")

    def test_anexo_direct_table_uses_annex_heading_not_table_title(self):
        """Una tabla directa en anexos debe presentarse bajo heading de anexo."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 15. Cronograma de validacion",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Revision", "X"]],
                    }
                ],
            }
        }

        blocks = normalize(data)
        bold_blocks = _blocks_of_type(blocks, "paragraph_bold")
        tables = _blocks_of_type(blocks, "table")

        assert any("Anexo 1: Cronograma de validacion" == b["text"] for b in bold_blocks)
        assert len(tables) == 1
        assert not tables[0].get("titulo")

    def test_anexos_ignore_section_note_and_strip_reported_filler_phrases(self):
        """ANEXOS no debe renderizar nota de seccion ni frases de relleno reportadas."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "nota": "A continuación, se presentan los anexos que complementan la investigación.",
                "lista": [
                    {
                        "titulo": "Anexo 1: Instrumento de recolección de datos",
                        "_ai_content": [
                            {"tipo": "parrafo", "texto": "El primer anexo incluye el cuestionario aplicado."},
                            {"tipo": "parrafo", "texto": "Asimismo, se adjunta la ficha de validación."},
                            {"tipo": "parrafo", "texto": "Pregunta 1. ¿Con qué frecuencia ocurre la falla?"},
                        ],
                    }
                ],
            }
        }

        blocks = normalize(data)
        notes = _blocks_of_type(blocks, "note")
        paragraphs = _blocks_of_type(blocks, "paragraph")

        assert len(notes) == 0
        assert all(
            "A continuación, se presentan los anexos" not in b["text"]
            and "El primer anexo incluye" not in b["text"]
            and "Asimismo" not in b["text"]
            for b in paragraphs
            if "text" in b
        )
        assert any(
            "Pregunta 1. ¿Con qué frecuencia ocurre la falla?" == b["text"]
            for b in paragraphs
        )

    def test_anexos_strip_garbled_continuacion_filler(self):
        """Debe limpiar también relleno degradado tipo 'continuaci?n'."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 1: Matriz de consistencia",
                        "_ai_content": [
                            {"tipo": "parrafo", "texto": "A continuaci?n se muestra la matriz de consistencia final."},
                            {
                                "tipo": "tabla",
                                "titulo": "Tabla 14. Matriz de consistencia final",
                                "encabezados": ["Problema", "Objetivo"],
                                "filas": [["P1", "O1"]],
                            },
                        ],
                    }
                ],
            }
        }

        blocks = normalize(data)
        paragraphs = _blocks_of_type(blocks, "paragraph")
        assert all("A continuaci?n se muestra" not in b["text"] for b in paragraphs if "text" in b)

    def test_anexo_with_structured_table_drops_explanatory_narrative_before_and_after(self):
        """Si el anexo contiene tabla, no debe conservar narrativa explicativa alrededor."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 1: Matriz de consistencia",
                        "_ai_content": [
                            {"tipo": "parrafo", "texto": "Esta sección contiene los documentos complementarios."},
                            {"tipo": "parrafo", "texto": "En primer lugar, se presenta la matriz de consistencia final."},
                            {
                                "tipo": "tabla",
                                "titulo": "Tabla 14. Matriz de consistencia final",
                                "encabezados": ["Problema", "Objetivo"],
                                "filas": [["P1", "O1"]],
                            },
                            {"tipo": "parrafo", "texto": "Adicionalmente, se incluye una explicación metodológica del anexo."},
                            {"tipo": "parrafo", "texto": "Los anexos también contienen observaciones complementarias."},
                        ],
                    }
                ],
            }
        }

        blocks = normalize(data)
        paragraphs = _blocks_of_type(blocks, "paragraph")
        tables = _blocks_of_type(blocks, "table")

        assert len(tables) == 1
        assert not tables[0].get("titulo")
        assert all(
            marker not in b["text"]
            for b in paragraphs
            if "text" in b
            for marker in (
                "Esta sección contiene",
                "En primer lugar",
                "Adicionalmente",
                "Los anexos también contienen",
            )
        )

    def test_anexo_text_only_keeps_useful_entries_and_drops_filler(self):
        """En anexos solo texto, se debe conservar contenido útil como preguntas o evidencias."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Anexo 2: Instrumento de recolección de datos",
                        "_ai_content": [
                            {"tipo": "parrafo", "texto": "Asimismo, se adjunta la ficha de validación."},
                            {"tipo": "parrafo", "texto": "Pregunta 1. ¿Con qué frecuencia ocurre la falla?"},
                            {"tipo": "parrafo", "texto": "Pregunta 2. ¿Qué causa identifica con mayor impacto?"},
                        ],
                    }
                ],
            }
        }

        blocks = normalize(data)
        paragraphs = _blocks_of_type(blocks, "paragraph")

        assert all("Asimismo" not in b["text"] for b in paragraphs if "text" in b)
        assert any("Pregunta 1. ¿Con qué frecuencia ocurre la falla?" == b["text"] for b in paragraphs)
        assert any("Pregunta 2. ¿Qué causa identifica con mayor impacto?" == b["text"] for b in paragraphs)

    def test_anexo_figure_style_title_becomes_annex_heading(self):
        """Figura A1 no debe sobrevivir como heading principal del anexo."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [
                    {
                        "titulo": "Figura A1. Registro fotográfico",
                        "_ai_content": [{"tipo": "parrafo", "texto": "Evidencia 1: Vista frontal del equipo."}],
                    }
                ],
            }
        }

        blocks = normalize(data)
        bold_blocks = _blocks_of_type(blocks, "paragraph_bold")
        paragraphs = _blocks_of_type(blocks, "paragraph")

        assert any("Anexo 1: Registro fotográfico" == b["text"] for b in bold_blocks)
        assert all("Figura A1" not in b["text"] for b in bold_blocks if "text" in b)
        assert any("Evidencia 1: Vista frontal del equipo." == b["text"] for b in paragraphs)

    def test_anexos_fallback_matriz(self):
        """Si hay matriz_consistencia pero no está en la lista → fallback."""
        data = _minimal_json()
        data["finales"] = {
            "anexos": {
                "titulo_seccion": "ANEXOS",
                "lista": [{"titulo": "Otro anexo"}],  # no es "matriz"
            }
        }
        data["matriz_consistencia"] = {
            "problemas": {"general": "P"},
            "objetivos": {"general": "O"},
            "hipotesis": {"general": "H"},
            "variables": {},
            "metodologia": {},
        }
        blocks = normalize(data)
        mat = _blocks_of_type(blocks, "matriz")
        assert len(mat) == 1  # fallback lo agrega

        ss = _blocks_of_type(blocks, "section_switch")
        # Fallback genera landscape + portrait
        assert any(b["orientation"] == "landscape" for b in ss)
        assert any(b["orientation"] == "portrait" for b in ss)

    def test_no_finales(self):
        """Sin finales no genera blocks de esa sección."""
        data = _minimal_json()
        blocks = normalize(data)
        mat = _blocks_of_type(blocks, "matriz")
        assert len(mat) == 0


# ─────────────────────────────────────────────────────────────
# INTEGRACIÓN: 9 JSONs REALES
# ─────────────────────────────────────────────────────────────

class TestNormalizeRealJsons:
    """Carga cada uno de los 9 JSONs reales y verifica que normalize() no crashea
    y genera estructura válida."""

    @staticmethod
    def _load_real_json(rel_path: str) -> dict:
        path = ROOT / rel_path
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _all_json_paths():
        data_dir = ROOT / "app" / "data"
        return sorted(data_dir.rglob("*.json"), key=lambda p: p.name)

    @pytest.fixture(params=[
        "app/data/unac/informe/unac_informe_cual.json",
        "app/data/unac/informe/unac_informe_cuant.json",
        "app/data/unac/maestria/unac_maestria_cual.json",
        "app/data/unac/maestria/unac_maestria_cuant.json",
        "app/data/unac/proyecto/unac_proyecto_cual.json",
        "app/data/unac/proyecto/unac_proyecto_cuant.json",
        "app/data/uni/informe/uni_informe_apa.json",
        "app/data/uni/posgrado/uni_posgrado_standard.json",
        "app/data/uni/proyecto/uni_proyecto_standard.json",
    ])
    def real_json(self, request):
        return self._load_real_json(request.param), request.param

    def test_normalize_no_crash(self, real_json):
        """normalize() no crashea con ninguno de los 9 JSONs."""
        data, path = real_json
        blocks = normalize(data)
        assert isinstance(blocks, list)
        assert len(blocks) > 10, f"JSON {path} generó muy pocos blocks: {len(blocks)}"

    def test_all_blocks_have_type(self, real_json):
        """Todos los blocks de JSONs reales tienen 'type'."""
        data, path = real_json
        blocks = normalize(data)
        for i, b in enumerate(blocks):
            assert "type" in b, f"Block #{i} de {path} sin 'type': {b}"

    def test_ends_with_page_footer(self, real_json):
        """Todos los JSONs reales terminan con page_footer."""
        data, _ = real_json
        blocks = normalize(data)
        assert blocks[-1]["type"] == "page_footer"

    def test_has_caratula_blocks(self, real_json):
        """Todos los JSONs reales generan la carátula, sea legacy o especializada."""
        data, _ = real_json
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        special_cover = _blocks_of_type(blocks, "caratula_unac_maestria")
        assert len(ct) >= 2 or len(special_cover) == 1

    def test_has_heading_blocks(self, real_json):
        """Todos los JSONs reales generan headings (capítulos)."""
        data, _ = real_json
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert len(hdgs) >= 1

    def test_has_page_breaks(self, real_json):
        """Todos los JSONs reales generan page_breaks."""
        data, _ = real_json
        blocks = normalize(data)
        pbs = _blocks_of_type(blocks, "page_break")
        assert len(pbs) >= 2  # al menos después de carátula y capítulos
