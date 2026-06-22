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


def test_merge_values_forces_unac_project_cover_institutional_labels() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "caratula": {
            "facultad": "Facultad de Ingeniería Mecánica y de Energía",
            "escuela": "Unidad de Posgrado",
            "tipo_documento": "PROYECTO DE INVESTIGACIÓN",
        },
    }
    values = {
        "tipo_documento": "Tesis de Maestría",
        "frase_grado": "PARA OPTAR EL GRADO ACADÉMICO DE MAESTRO EN GERENCIA DE MANTENIMIENTO",
    }

    merged = merge_values(data, values)

    assert merged["caratula"]["facultad"] == "ESCUELA DE POSGRADO"
    assert (
        merged["caratula"]["escuela"]
        == "UNIDAD DE POSGRADO DE LA FACULTAD DE INGENIERÍA MECÁNICA Y DE ENERGÍA"
    )
    assert merged["caratula"]["tipo_documento"] == "PROYECTO DE INVESTIGACIÓN"
    assert merged["tipo_documento"] == "PROYECTO DE INVESTIGACIÓN"


def test_merge_values_exposes_structured_project_tables_at_root() -> None:
    values = {
        "matriz_consistencia": {"problema_general": "P"},
        "operacionalizacion_vi": {"variable": "VI", "filas": [{"dimension": "D1"}]},
        "operacionalizacion_vd": {"variable": "VD", "filas": [{"dimension": "D2"}]},
    }

    merged = merge_values({"caratula": {}}, values)

    assert merged["values"]["matriz_consistencia"]["problema_general"] == "P"
    assert merged["matriz_consistencia"]["problema_general"] == "P"
    assert merged["operacionalizacion_vi"]["filas"][0]["dimension"] == "D1"
    assert merged["operacionalizacion_vd"]["filas"][0]["dimension"] == "D2"


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
            "dedicatoria": {
                "titulo": "DEDICATORIA",
                "texto": "[Escriba aqui su dedicatoria...]",
            },
            "agradecimientos": {
                "titulo": "AGRADECIMIENTO",
                "texto": "[Escriba aqui su agradecimiento...]",
            },
        }
    }
    ai_sections = [
        {
            "path": "DEDICATORIA",
            "content": "Dedico este trabajo a mi familia por su apoyo constante.",
        },
        {
            "path": "AGRADECIMIENTO",
            "content": "Agradezco a mi asesor y a la universidad por el acompanamiento brindado.",
        },
    ]

    result = apply_ai_content(data, ai_sections)

    assert result["preliminares"]["dedicatoria"]["_ai_content"].startswith(
        "Dedico este trabajo"
    )
    assert result["preliminares"]["agradecimientos"]["_ai_content"].startswith(
        "Agradezco a mi asesor"
    )


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

    assert result["preliminares"]["abreviaturas"]["_ai_content"].startswith(
        "IA: Inteligencia Artificial"
    )


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

    assert len(contenido) == 1
    assert contenido[0]["titulo"] == "Cronograma base"
    assert contenido[0]["_ai_generated"] is True


def test_apply_ai_content_skips_unac_project_chapter_level_text() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "III. HIPOTESIS Y VARIABLES",
                "contenido": [
                    {"texto": "3.1 Hipotesis"},
                ],
            }
        ],
    }
    ai_sections = [
        {
            "path": "III. HIPOTESIS Y VARIABLES",
            "content": "Este texto del capitulo padre no debe mezclarse con 3.1.",
        },
        {
            "path": "III. HIPOTESIS Y VARIABLES/3.1 Hipotesis",
            "content": "Hipotesis general validada.",
        },
    ]

    result = apply_ai_content(data, ai_sections)
    chapter = result["cuerpo"][0]
    child = chapter["contenido"][0]

    assert "_ai_content" not in chapter
    assert "Este texto del capitulo padre" not in str(child)
    assert child["_ai_content"] == "Hipotesis general validada."


def test_apply_ai_content_allows_unac_project_chapter_level_when_no_child_sections() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [],
            }
        ],
    }
    ai_sections = [
        {
            "path": "V. CRONOGRAMA DE ACTIVIDADES",
            "content": [
                {
                    "tipo": "tabla",
                    "titulo": "Cronograma dinamico",
                    "encabezados": ["Actividad", "Periodo"],
                    "filas": [["Revision", "Mes 1"]],
                }
            ],
        }
    ]

    result = apply_ai_content(data, ai_sections)
    chapter = result["cuerpo"][0]

    assert chapter["_ai_content"][0]["titulo"] == "Cronograma dinamico"
    assert chapter["contenido"][0]["titulo"] == "Cronograma dinamico"
    assert chapter["contenido"][0]["_ai_generated"] is True


def test_apply_ai_content_ignores_chapter_text_for_schedule_when_static_table_exists() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 5.1 Cronograma de actividades",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Planificacion", "X"]],
                        "orientacion": "landscape",
                    }
                ],
            }
        ],
    }
    ai_sections = [
        {
            "path": "V. CRONOGRAMA DE ACTIVIDADES",
            "content": "Texto narrativo no permitido antes de la tabla.",
        }
    ]

    result = apply_ai_content(data, ai_sections)
    chapter = result["cuerpo"][0]
    contenido = chapter["contenido"]

    assert "_ai_content" not in chapter
    assert isinstance(contenido, list)
    assert len(contenido) == 1
    assert contenido[0]["tipo"] == "tabla"
    assert contenido[0]["titulo"] == "Tabla 5.1 Cronograma de actividades"


def test_apply_ai_content_prunes_unselected_chapters_with_selected_sections() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "III. HIPOTESIS Y VARIABLES",
                "contenido": [{"texto": "3.1 Hipotesis"}],
            },
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 5.1 Cronograma de actividades",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Planificacion", "X"]],
                    }
                ],
            },
            {
                "titulo": "VI. PRESUPUESTO",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 6.1 Presupuesto de investigacion",
                        "encabezados": ["Concepto", "Costo"],
                        "filas": [["Analisis", "1000"]],
                    }
                ],
            },
        ],
    }
    ai_sections = [
        {
            "path": "III. HIPOTESIS Y VARIABLES/3.1 Hipotesis",
            "content": "Hipotesis general aplicada al proyecto.",
        }
    ]
    selected_sections = [
        {"section_path": "Título + Información Básica"},
        {"section_path": "III. HIPOTESIS Y VARIABLES/3.1 Hipotesis"},
    ]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)

    assert [cap["titulo"] for cap in result["cuerpo"]] == ["III. HIPOTESIS Y VARIABLES"]
    assert result["cuerpo"][0]["contenido"][0]["_ai_content"].startswith("Hipotesis general")


def test_apply_ai_content_prunes_unselected_introduccion_with_selected_sections() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "preliminares": {
            "introduccion": {
                "titulo": "INTRODUCCION",
                "texto": "Texto base de introduccion",
            }
        },
        "cuerpo": [
            {
                "titulo": "III. HIPOTESIS Y VARIABLES",
                "contenido": [{"texto": "3.1 Hipotesis"}],
            }
        ],
    }
    ai_sections = [
        {
            "path": "INTRODUCCION",
            "content": "Contenido que no debe aparecer si la introduccion no fue seleccionada.",
        },
        {
            "path": "III. HIPOTESIS Y VARIABLES/3.1 Hipotesis",
            "content": "Hipotesis general aplicada al proyecto.",
        },
    ]
    selected_sections = [
        {"section_path": "TÃ­tulo + InformaciÃ³n BÃ¡sica"},
        {"section_path": "III. HIPOTESIS Y VARIABLES/3.1 Hipotesis"},
    ]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)

    assert "introduccion" not in result["preliminares"]
    assert [cap["titulo"] for cap in result["cuerpo"]] == ["III. HIPOTESIS Y VARIABLES"]


def test_apply_ai_content_keeps_selected_introduccion_with_selected_sections() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "preliminares": {
            "introduccion": {
                "titulo": "INTRODUCCION",
                "texto": "Texto base de introduccion",
            }
        },
    }
    ai_sections = [
        {
            "path": "INTRODUCCION",
            "content": "Introduccion seleccionada para el documento final.",
        }
    ]
    selected_sections = [
        {"section_path": "INTRODUCCION"},
    ]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)

    assert result["preliminares"]["introduccion"]["_ai_content"].startswith(
        "Introduccion seleccionada"
    )


def test_apply_ai_content_merges_child_schedule_table_into_static_template() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "id": "tabla_5_1_cronograma_actividades",
                        "titulo": "Tabla 5.1 Cronograma de actividades",
                        "orientacion": "landscape",
                        "subtipo": "cronograma_actividades",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Planificacion", "X"]],
                        "estilo": {"modelo_referencia": "cronograma_actividades.docx"},
                    }
                ],
            }
        ],
    }
    ai_sections = [
        {
            "path": "V. CRONOGRAMA DE ACTIVIDADES/Cronograma Detallado de Actividades",
            "content": [
                {"tipo": "parrafo", "texto": "Tabla dinamica actualizada por IA."},
                {
                    "tipo": "tabla",
                    "titulo": "Cronograma dinamico del proyecto",
                    "subtipo": "cronograma_actividades",
                    "encabezados": ["Actividad", "Mes 1", "Mes 2"],
                    "filas": [["Levantamiento", "X", ""], ["Validacion", "", "X"]],
                },
            ],
        }
    ]
    selected_sections = [
        {"section_path": "V. CRONOGRAMA DE ACTIVIDADES/Cronograma Detallado de Actividades"},
    ]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)
    chapter = result["cuerpo"][0]
    contenido = chapter["contenido"]

    assert len(contenido) == 1
    assert contenido[0]["tipo"] == "tabla"
    assert contenido[0]["titulo"] == "Tabla 5.1 Cronograma de actividades"
    assert contenido[0]["id"] == "tabla_5_1_cronograma_actividades"
    assert contenido[0]["orientacion"] == "landscape"
    assert contenido[0]["subtipo"] == "cronograma_actividades"
    assert contenido[0]["estilo"]["modelo_referencia"] == "cronograma_actividades.docx"
    assert contenido[0]["encabezados"] == ["Actividad", "Mes 1", "Mes 2"]
    assert contenido[0]["filas"] == [["Levantamiento", "X", ""], ["Validacion", "", "X"]]
    assert contenido[0]["_ai_generated"] is True


def test_apply_ai_content_keeps_static_schedule_and_budget_tables_when_no_ai_table_arrives() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "V. CRONOGRAMA DE ACTIVIDADES",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 5.1 Cronograma de actividades",
                        "encabezados": ["Actividad", "Mes 1"],
                        "filas": [["Planificacion", "X"]],
                    }
                ],
            },
            {
                "titulo": "VI. PRESUPUESTO",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "titulo": "Tabla 6.1 Presupuesto de investigacion",
                        "encabezados": ["Concepto", "Costo"],
                        "filas": [["Analisis", "1000"]],
                    }
                ],
            },
        ],
    }
    ai_sections: list[dict[str, object]] = []
    selected_sections = [
        {"section_path": "V. CRONOGRAMA DE ACTIVIDADES"},
        {"section_path": "VI. PRESUPUESTO"},
    ]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)

    assert [cap["titulo"] for cap in result["cuerpo"]] == [
        "V. CRONOGRAMA DE ACTIVIDADES",
        "VI. PRESUPUESTO",
    ]
    assert result["cuerpo"][0]["contenido"][0]["titulo"] == "Tabla 5.1 Cronograma de actividades"
    assert result["cuerpo"][1]["contenido"][0]["titulo"] == "Tabla 6.1 Presupuesto de investigacion"
    assert "_ai_content" not in result["cuerpo"][0]
    assert "_ai_content" not in result["cuerpo"][1]


def test_apply_ai_content_merges_budget_table_into_static_template() -> None:
    data = {
        "_meta": {"id": "unac-proyecto-cuant"},
        "cuerpo": [
            {
                "titulo": "VI. PRESUPUESTO",
                "contenido": [
                    {
                        "tipo": "tabla",
                        "id": "tabla_6_1_presupuesto_investigacion",
                        "titulo": "Tabla 6.1 Presupuesto de investigacion",
                        "orientacion": "portrait",
                        "subtipo": "presupuesto_investigacion",
                        "encabezados": ["Base", "Costo"],
                        "filas": [["Analisis", "1000"]],
                        "estilo": {"modelo_referencia": "presupuesto_investigacion_vertical.docx"},
                    }
                ],
            }
        ],
    }
    ai_sections = [
        {
            "path": "VI. PRESUPUESTO/Presupuesto del Proyecto",
            "content": [
                {
                    "tipo": "tabla",
                    "titulo": "Presupuesto dinamico",
                    "subtipo": "presupuesto_investigacion",
                    "encabezados": ["N°", "Descripcion", "Cantidad", "Costo unit.", "Costo total"],
                    "filas": [
                        ["1. RECURSOS HUMANOS", "", "", "", "2,000.00"],
                        ["1.1", "Investigador", "1", "2,000.00", "2,000.00"],
                    ],
                    "filas_categoria": [0],
                    "fila_total": 1,
                    "celdas_combinadas": [{"fila": 0, "col_inicio": 0, "col_fin": 3, "texto": "1. RECURSOS HUMANOS"}],
                    "celdas_fusionadas": [{"fila": 1, "col": 0, "filas_span": 1, "cols_span": 4, "texto": "TOTAL GENERAL"}],
                }
            ],
        }
    ]
    selected_sections = [{"section_path": "VI. PRESUPUESTO/Presupuesto del Proyecto"}]

    result = apply_ai_content(data, ai_sections, selected_sections=selected_sections)
    contenido = result["cuerpo"][0]["contenido"]

    assert len(contenido) == 1
    assert contenido[0]["titulo"] == "Tabla 6.1 Presupuesto de investigacion"
    assert contenido[0]["id"] == "tabla_6_1_presupuesto_investigacion"
    assert contenido[0]["orientacion"] == "portrait"
    assert contenido[0]["subtipo"] == "presupuesto_investigacion"
    assert contenido[0]["estilo"]["modelo_referencia"] == "presupuesto_investigacion_vertical.docx"
    assert contenido[0]["encabezados"] == ["N°", "Descripcion", "Cantidad", "Costo unit.", "Costo total"]
    assert contenido[0]["filas"][0][0] == "1. RECURSOS HUMANOS"
    assert contenido[0]["_ai_generated"] is True


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


def test_apply_ai_content_matches_annex_by_position_when_base_title_is_not_annex() -> (
    None
):
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
    assert (
        tabla["_ai_content"][0]["titulo"]
        == "Tabla 15. Tabla de resultados complementarios"
    )
