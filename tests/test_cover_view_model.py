"""
=============================================================================
ARCHIVO: tests/test_cover_view_model.py
FASE: 3 - Calidad y Validación
=============================================================================

PROPÓSITO:
Tests unitarios para build_cover_view_model y funciones relacionadas.
Verifica que el view-model se construye correctamente para diferentes casos.

TESTS INCLUIDOS:
- test_unac_view_model(): Formato UNAC genera campos correctos
- test_uni_view_model(): Formato UNI genera campos correctos
- test_fallback_without_meta_uni(): Sin _meta.uni usa defaults del provider
- test_logo_path_normalization(): Normalización de rutas de logo

CÓMO EJECUTAR:
    python tests/test_cover_view_model.py
    # o con pytest:
    py -m pytest tests/test_cover_view_model.py -v

COMUNICACIÓN CON OTROS MÓDULOS:
- IMPORTA:
  - app/core/view_models.py (build_cover_view_model, normalize_logo_path)
  - app/core/registry.py (get_provider)
  - app/core/settings.py (get_default_uni_code)
- LEE:
  - app/data/unac/*.json (formatos reales para testing)
  - app/data/uni/*.json

REQUISITOS:
- Carpetas app/data/unac y app/data/uni deben existir con al menos un formato.

=============================================================================
"""
import json
import sys
from pathlib import Path

# Agregar raíz del proyecto
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_unac_view_model():
    """Test: formato UNAC genera view-model correcto."""
    from app.core.view_models import build_cover_view_model
    from app.core.registry import get_provider
    
    # Cargar un formato real de UNAC
    unac_dir = ROOT / "app" / "data" / "unac"
    if not unac_dir.exists():
        print("⚠️ test_unac_view_model SKIPPED (no hay carpeta unac)")
        return
    
    json_files = list(unac_dir.rglob("*.json"))
    
    # Filtrar archivos especiales
    format_files = [f for f in json_files if f.name not in (
        "alerts.json", "references_config.json", "formatos.json"
    )]
    
    if len(format_files) == 0:
        print("⚠️ test_unac_view_model SKIPPED (no hay formatos UNAC)")
        return
    
    # Usar el primer formato
    format_path = format_files[0]
    format_data = json.loads(format_path.read_text(encoding="utf-8"))
    
    provider = get_provider("unac")
    view_model = build_cover_view_model(format_data, provider)
    
    # Verificaciones
    assert "logo_url" in view_model, "Falta logo_url"
    assert view_model["logo_url"], "logo_url vacío"
    assert view_model["logo_url"].startswith("/static/"), "logo_url no comienza con /static/"
    
    assert "universidad" in view_model, "Falta universidad"
    assert view_model["universidad"], "universidad vacío"
    
    assert "lugar" in view_model, "Falta lugar"
    assert "anio" in view_model, "Falta anio"
    
    print(f"✅ test_unac_view_model PASSED ({format_path.name})")
    print(f"   logo_url: {view_model['logo_url']}")
    print(f"   universidad: {view_model['universidad'][:50]}...")


def test_uni_view_model():
    """Test: formato UNI genera view-model correcto."""
    from app.core.view_models import build_cover_view_model
    from app.core.registry import get_provider
    
    uni_dir = ROOT / "app" / "data" / "uni"
    json_files = list(uni_dir.rglob("*.json"))
    
    format_files = [f for f in json_files if f.name not in (
        "alerts.json", "references_config.json", "formatos.json"
    )]
    
    assert len(format_files) > 0, "No hay formatos UNI para testear"
    
    format_path = format_files[0]
    format_data = json.loads(format_path.read_text(encoding="utf-8"))
    
    provider = get_provider("uni")
    view_model = build_cover_view_model(format_data, provider)
    
    assert view_model["logo_url"], "logo_url vacío"
    assert view_model["universidad"], "universidad vacío"
    
    print(f"✅ test_uni_view_model PASSED ({format_path.name})")


def test_fallback_without_meta_uni():
    """Test: formato sin _meta.uni usa defaults del provider."""
    from app.core.view_models import build_cover_view_model
    from app.core.registry import get_provider
    from app.core.settings import get_default_uni_code
    
    # Formato minimal sin _meta.uni
    format_data = {
        "_meta": {"id": "test-format"},
        "caratula": {
            "titulo": "Título de Prueba"
        }
    }
    
    # Usar provider default
    default_uni = get_default_uni_code()
    provider = get_provider(default_uni)
    
    view_model = build_cover_view_model(format_data, provider)
    
    # Debe usar defaults del provider
    assert view_model["logo_url"], "logo_url debería tener fallback"
    assert view_model["titulo"] == "Título de Prueba", "titulo incorrecto"
    
    print(f"✅ test_fallback_without_meta_uni PASSED")
    print(f"   default_uni: {default_uni}")
    print(f"   logo_url: {view_model['logo_url']}")


def test_logo_path_normalization():
    """Test: normalización de rutas de logo."""
    from app.core.view_models import normalize_logo_path
    
    # Caso 1: app/static/...
    assert normalize_logo_path("app/static/assets/Logo.png") == "/static/assets/Logo.png"
    
    # Caso 2: ya normalizado
    assert normalize_logo_path("/static/assets/Logo.png") == "/static/assets/Logo.png"
    
    # Caso 3: ruta absoluta con /static/
    result = normalize_logo_path("C:/path/to/static/assets/Logo.png")
    assert result == "/static/assets/Logo.png"
    
    # Caso 4: vacío
    assert normalize_logo_path("") is None
    assert normalize_logo_path(None) is None
    
    print("✅ test_logo_path_normalization PASSED")


def run_all_tests():
    """Ejecuta todos los tests."""
    print("=" * 60)
    print("TESTS: cover_view_model")
    print("=" * 60)
    
    try:
        test_logo_path_normalization()
        test_unac_view_model()
        test_uni_view_model()
        test_fallback_without_meta_uni()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
