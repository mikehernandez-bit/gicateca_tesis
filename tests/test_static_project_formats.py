import json
from pathlib import Path


PROJECT_FORMATS = [
    Path("app/data/unac/proyecto/unac_proyecto_cuant.json"),
    Path("app/data/unac/proyecto/unac_proyecto_cual.json"),
]


def test_unac_project_formats_include_budget_table_template():
    for path in PROJECT_FORMATS:
        data = json.loads(path.read_text(encoding="utf-8"))
        chapter = next(item for item in data["cuerpo"] if item["titulo"] == "VI. PRESUPUESTO")
        assert len(chapter["contenido"]) == 1
        table = chapter["contenido"][0]
        assert table["tipo"] == "tabla"
        assert table["titulo"] == "Tabla 6.1 Presupuesto de investigación"
        assert table["encabezados"] == [
            "N°",
            "DESCRIPCIÓN DEL GASTO",
            "CANTIDAD",
            "COSTO UNIT. (S/.)",
            "COSTO TOTAL (S/.)",
        ]
        assert table["estilo"]["orientacion_pagina"] == "portrait"
        assert table["filas"][0] == ["1. RECURSOS HUMANOS", "", "", "", "2,000.00"]
        assert table["filas"][-1] == ["TOTAL GENERAL", "", "", "", "S/. 7,779.00"]
        assert table["fila_total"] == 13
        assert any(cell["texto"] == "TOTAL GENERAL" and cell["cols_span"] == 4 for cell in table["celdas_fusionadas"])


def test_unac_project_formats_include_schedule_table_template():
    for path in PROJECT_FORMATS:
        data = json.loads(path.read_text(encoding="utf-8"))
        chapter = next(item for item in data["cuerpo"] if item["titulo"] == "V. CRONOGRAMA DE ACTIVIDADES")
        assert len(chapter["contenido"]) == 1
        table = chapter["contenido"][0]
        assert table["tipo"] == "tabla"
        assert table["titulo"] == "Tabla 5.1 Cronograma de actividades"
        assert table["encabezados"][0] == "FASES Y ACTIVIDADES"
        assert table["encabezados"][1] == "2025"
        assert table["estilo"]["orientacion_pagina"] == "landscape"
        assert table["meses"] == ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
        assert len(table["filas_fase"]) == 8
        assert any(row[0] == "8.4. Diapositivas y preparación de sustentación" and row[12] == "●" for row in table["filas"])
        assert any(cell["texto"] == "2025" and cell["cols_span"] == 12 for cell in table["celdas_fusionadas"])


def test_unac_project_quant_bases_teoricas_has_no_static_matrix_tables():
    path = Path("app/data/unac/proyecto/unac_proyecto_cuant.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    chapter = next(item for item in data["cuerpo"] if item["titulo"] == "II. MARCO TEÓRICO")
    section = next(item for item in chapter["contenido"] if item.get("texto") == "2.2 Bases teóricas")

    assert "mostrar_matriz" not in section
    assert "tablas_especiales" not in section


def test_metodologia_chapter_has_no_cronograma_resumido_table():
    for path in PROJECT_FORMATS:
        data = json.loads(path.read_text(encoding="utf-8"))
        chapter = next(item for item in data["cuerpo"] if item["titulo"] == "IV. METODOLOGÍA DEL PROYECTO")
        titles = {
            str(item.get("titulo") or "").strip()
            for item in chapter.get("contenido", [])
            if isinstance(item, dict)
        }
        assert "Cronograma Resumido de Actividades" not in titles


def test_unac_project_quant_has_no_repeated_operationalization_table_33():
    path = Path("app/data/unac/proyecto/unac_proyecto_cuant.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    chapter = next(item for item in data["cuerpo"] if item["titulo"] == "III. HIPÓTESIS Y VARIABLES")
    tables = [
        item
        for item in chapter.get("contenido", [])
        if isinstance(item, dict) and item.get("tipo") == "tabla"
    ]
    assert not any(str(table.get("titulo") or "").strip() == "Operacionalización de Variables" for table in tables)
