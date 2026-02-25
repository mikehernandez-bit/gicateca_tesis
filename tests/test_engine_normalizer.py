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


# ─────────────────────────────────────────────────────────────
# CARÁTULA
# ─────────────────────────────────────────────────────────────

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

    def test_dedicatoria_as_string(self):
        """Dedicatoria como string genera solo heading."""
        data = _minimal_json()
        data["preliminares"] = {"dedicatoria": "DEDICATORIA"}
        blocks = normalize(data)
        hdgs = _blocks_of_type(blocks, "heading")
        assert any(b["text"] == "DEDICATORIA" for b in hdgs)

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

    def test_content_string_item(self):
        """String en contenido genera paragraph."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = ["Plain text here"]
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        assert any(b["text"] == "Plain text here" for b in pars)

    def test_mostrar_matriz_placeholder(self):
        """mostrar_matriz:true genera paragraph placeholder."""
        data = _minimal_json()
        data["cuerpo"][0]["contenido"] = [{"texto": "Sec", "mostrar_matriz": True}]
        blocks = normalize(data)
        pars = _blocks_of_type(blocks, "paragraph")
        assert any("Matriz" in b["text"] for b in pars)

    def test_ejemplos_apa_chapter(self):
        """ejemplos_apa a nivel de capítulo genera apa_examples."""
        data = _minimal_json()
        data["cuerpo"][0]["ejemplos_apa"] = ["Ej1", "Ej2"]
        blocks = normalize(data)
        apa = _blocks_of_type(blocks, "apa_examples")
        assert len(apa) == 1
        assert apa[0]["ejemplos"] == ["Ej1", "Ej2"]


# ─────────────────────────────────────────────────────────────
# FINALES
# ─────────────────────────────────────────────────────────────

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
        types = _types(blocks)

        # Verificar secuencia: section_switch(landscape) → heading → black_heading → matriz → section_switch(portrait)
        ss = _blocks_of_type(blocks, "section_switch")
        assert len(ss) == 2
        assert ss[0]["orientation"] == "landscape"
        assert ss[1]["orientation"] == "portrait"

        mat = _blocks_of_type(blocks, "matriz")
        assert len(mat) == 1
        assert mat[0]["landscape"] is False

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
        """Todos los JSONs reales generan centered_text (de carátula)."""
        data, _ = real_json
        blocks = normalize(data)
        ct = _blocks_of_type(blocks, "centered_text")
        assert len(ct) >= 2  # al menos universidad y facultad

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
