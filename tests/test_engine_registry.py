"""
=============================================================================
ARCHIVO: tests/test_engine_registry.py
FASE: Block Engine - Fase 1
=============================================================================

PROPÓSITO:
Tests unitarios para el registry del Block Engine.
Verifica registro de renderers, despacho de blocks, y manejo de errores.

TESTS INCLUIDOS:
- test_register_and_dispatch: registrar renderer y verificar que render_block despacha
- test_render_block_unknown_type: block con tipo no registrado → warning, no crash
- test_render_block_missing_type: block sin campo 'type' → warning, no crash
- test_render_block_invalid_block: block no-dict → warning, no crash
- test_duplicate_register: registrar mismo tipo 2 veces → ValueError
- test_register_empty_type: tipo vacío → ValueError
- test_list_registered: verificar lista de tipos registrados
- test_is_registered: verificar consulta de tipo registrado
- test_render_blocks_sequence: renderizar lista de blocks en orden
- test_render_blocks_error_recovery: si un renderer falla, continúa con el siguiente

CÓMO EJECUTAR:
    py -m pytest tests/test_engine_registry.py -v

COMUNICACIÓN CON OTROS MÓDULOS:
- IMPORTA:
  - app/engine/registry.py
  - app/engine/types.py
=============================================================================
"""
import pytest

from app.engine.registry import (
    _RENDERERS,
    _clear_registry,
    is_registered,
    list_registered,
    register,
    render_block,
    render_blocks,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Guarda los renderers reales, limpia para el test, y restaura después."""
    saved = dict(_RENDERERS)
    _clear_registry()
    yield
    _clear_registry()
    _RENDERERS.update(saved)


# ──────────────────────────────────────────────────────────────
# REGISTRO Y DESPACHO
# ──────────────────────────────────────────────────────────────

class TestRegisterAndDispatch:
    """Tests para el decorador @register y render_block."""

    def test_register_and_dispatch(self):
        """Un renderer registrado se invoca correctamente con render_block."""
        calls = []

        @register("test_type")
        def render_test(doc, block):
            calls.append(block)

        block = {"type": "test_type", "text": "hello"}
        render_block(None, block)  # doc=None, el renderer no lo usa

        assert len(calls) == 1
        assert calls[0] is block

    def test_register_multiple_types(self):
        """Se pueden registrar múltiples tipos sin conflicto."""

        @register("type_a")
        def render_a(doc, block):
            pass

        @register("type_b")
        def render_b(doc, block):
            pass

        assert is_registered("type_a")
        assert is_registered("type_b")
        assert set(list_registered()) == {"type_a", "type_b"}

    def test_renderer_receives_doc_and_block(self):
        """El renderer recibe exactamente doc y block como argumentos."""
        received = {}

        @register("check_args")
        def render_check(doc, block):
            received["doc"] = doc
            received["block"] = block

        sentinel_doc = object()
        sentinel_block = {"type": "check_args", "data": 42}

        render_block(sentinel_doc, sentinel_block)

        assert received["doc"] is sentinel_doc
        assert received["block"] is sentinel_block


# ──────────────────────────────────────────────────────────────
# MANEJO DE ERRORES
# ──────────────────────────────────────────────────────────────

class TestErrorHandling:
    """Tests para robustez del registry ante inputs inválidos."""

    def test_render_block_unknown_type(self):
        """Block con tipo no registrado no crashea, solo warning."""
        # No debe lanzar excepción
        render_block(None, {"type": "nonexistent"})

    def test_render_block_missing_type(self):
        """Block sin campo 'type' no crashea."""
        render_block(None, {"text": "sin tipo"})

    def test_render_block_empty_type(self):
        """Block con type='' no crashea."""
        render_block(None, {"type": ""})

    def test_render_block_invalid_block_string(self):
        """Block que no es dict (string) no crashea."""
        render_block(None, "not a dict")

    def test_render_block_invalid_block_none(self):
        """Block que es None no crashea."""
        render_block(None, None)

    def test_render_block_invalid_block_list(self):
        """Block que es lista no crashea."""
        render_block(None, [1, 2, 3])

    def test_duplicate_register_raises(self):
        """Registrar el mismo tipo dos veces lanza ValueError."""

        @register("duplicate")
        def render_first(doc, block):
            pass

        with pytest.raises(ValueError, match="Renderer duplicado"):

            @register("duplicate")
            def render_second(doc, block):
                pass

    def test_register_empty_type_raises(self):
        """Registrar tipo vacío lanza ValueError."""
        with pytest.raises(ValueError, match="string no vacío"):

            @register("")
            def render_empty(doc, block):
                pass

    def test_register_whitespace_type_raises(self):
        """Registrar tipo solo espacios lanza ValueError."""
        with pytest.raises(ValueError, match="string no vacío"):

            @register("   ")
            def render_spaces(doc, block):
                pass


# ──────────────────────────────────────────────────────────────
# CONSULTAS AL REGISTRY
# ──────────────────────────────────────────────────────────────

class TestRegistryQueries:
    """Tests para list_registered e is_registered."""

    def test_list_registered_empty(self):
        """Registry vacío retorna lista vacía."""
        assert list_registered() == []

    def test_list_registered_sorted(self):
        """list_registered retorna tipos en orden alfabético."""

        @register("zebra")
        def r1(doc, block):
            pass

        @register("alpha")
        def r2(doc, block):
            pass

        @register("middle")
        def r3(doc, block):
            pass

        assert list_registered() == ["alpha", "middle", "zebra"]

    def test_is_registered_true(self):
        """is_registered retorna True para tipo registrado."""

        @register("exists")
        def r(doc, block):
            pass

        assert is_registered("exists") is True

    def test_is_registered_false(self):
        """is_registered retorna False para tipo no registrado."""
        assert is_registered("ghost") is False


# ──────────────────────────────────────────────────────────────
# RENDER_BLOCKS (LISTA)
# ──────────────────────────────────────────────────────────────

class TestRenderBlocks:
    """Tests para render_blocks (procesamiento de lista de blocks)."""

    def test_render_blocks_sequence(self):
        """render_blocks procesa blocks en orden."""
        order = []

        @register("seq_a")
        def ra(doc, block):
            order.append("a")

        @register("seq_b")
        def rb(doc, block):
            order.append("b")

        blocks = [
            {"type": "seq_a"},
            {"type": "seq_b"},
            {"type": "seq_a"},
        ]
        render_blocks(None, blocks)

        assert order == ["a", "b", "a"]

    def test_render_blocks_empty_list(self):
        """render_blocks con lista vacía no crashea."""
        render_blocks(None, [])

    def test_render_blocks_error_recovery(self):
        """Si un renderer falla, render_blocks continúa con el siguiente."""
        calls = []

        @register("good")
        def render_good(doc, block):
            calls.append("good")

        @register("bad")
        def render_bad(doc, block):
            raise RuntimeError("fallo intencional")

        blocks = [
            {"type": "good"},
            {"type": "bad"},
            {"type": "good"},
        ]
        # No debe lanzar excepción gracias al try/except interno
        render_blocks(None, blocks)

        # El primero y tercero se ejecutaron, el segundo falló pero no interrumpió
        assert calls == ["good", "good"]

    def test_render_blocks_skips_unknown(self):
        """render_blocks ignora blocks con tipo no registrado."""
        calls = []

        @register("known")
        def render_known(doc, block):
            calls.append(block.get("id"))

        blocks = [
            {"type": "known", "id": 1},
            {"type": "unknown", "id": 2},
            {"type": "known", "id": 3},
        ]
        render_blocks(None, blocks)

        assert calls == [1, 3]


# ──────────────────────────────────────────────────────────────
# CLEAR REGISTRY (para tests)
# ──────────────────────────────────────────────────────────────

class TestClearRegistry:
    """Tests para _clear_registry."""

    def test_clear_removes_all(self):
        """_clear_registry vacía el registry completamente."""

        @register("temp")
        def r(doc, block):
            pass

        assert is_registered("temp")
        _clear_registry()
        assert not is_registered("temp")
        assert list_registered() == []
