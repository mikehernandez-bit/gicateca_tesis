"""
Tests para validación de repositorio.
Verifica schemas, reglas y detección de errores.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_format_schema_valid():
    """Test: formato válido pasa schema."""
    from app.core.validation.format_validation import validate_format_schema
    
    valid_format = {
        "_meta": {
            "id": "test-format",
            "uni": "unac"
        },
        "caratula": {}
    }
    
    issues = validate_format_schema(valid_format)
    errors = [i for i in issues if i.is_error()]
    
    assert len(errors) == 0, f"No debería haber errores: {errors}"
    
    print("✅ test_format_schema_valid PASSED")


def test_format_schema_missing_meta():
    """Test: formato sin _meta genera error."""
    from app.core.validation.format_validation import validate_format_schema
    
    invalid_format = {
        "caratula": {}
    }
    
    issues = validate_format_schema(invalid_format)
    errors = [i for i in issues if i.is_error()]
    
    assert len(errors) > 0, "Debería detectar error de _meta faltante"
    assert any("META" in i.code for i in errors), "Error debería mencionar META"
    
    print("✅ test_format_schema_missing_meta PASSED")


def test_format_rules_uni_mismatch():
    """Test: detecta mismatch entre _meta.uni y carpeta."""
    from app.core.validation.format_validation import validate_format_rules
    
    format_data = {
        "_meta": {
            "id": "test",
            "uni": "uni"  # Dice UNI
        }
    }
    
    # Pero esperamos UNAC (simulando carpeta unac/)
    issues = validate_format_rules(format_data, expected_uni_code="unac")
    errors = [i for i in issues if i.is_error()]
    
    assert len(errors) > 0, "Debería detectar mismatch"
    assert any("MISMATCH" in i.code for i in errors), f"Error debería ser MISMATCH: {errors}"
    
    print("✅ test_format_rules_uni_mismatch PASSED")


def test_id_collision_detection():
    """Test: detecta IDs duplicados."""
    from app.core.validation.repo_checks import check_id_collisions
    
    format_files = [
        (Path("file1.json"), {"_meta": {"id": "same-id", "uni": "unac"}}),
        (Path("file2.json"), {"_meta": {"id": "same-id", "uni": "unac"}}),  # Duplicado
        (Path("file3.json"), {"_meta": {"id": "other-id", "uni": "unac"}}),
    ]
    
    issues = check_id_collisions(format_files)
    
    assert len(issues) == 1, f"Debería detectar 1 colisión: {issues}"
    assert "COLLISION" in issues[0].code, "Error debería ser ID_COLLISION"
    
    print("✅ test_id_collision_detection PASSED")


def test_references_config_valid():
    """Test: references_config válido pasa validación."""
    from app.core.validation.references_validation import (
        validate_references_config_schema,
        validate_references_rules,
    )
    
    valid_config = {
        "enabled": ["apa7", "ieee"],
        "default": "apa7"
    }
    
    schema_issues = validate_references_config_schema(valid_config)
    rule_issues = validate_references_rules(valid_config)
    
    all_errors = [i for i in (schema_issues + rule_issues) if i.is_error()]
    
    assert len(all_errors) == 0, f"No debería haber errores: {all_errors}"
    
    print("✅ test_references_config_valid PASSED")


def test_references_default_not_in_enabled():
    """Test: detecta default que no está en enabled."""
    from app.core.validation.references_validation import validate_references_rules
    
    invalid_config = {
        "enabled": ["apa7", "ieee"],
        "default": "chicago"  # No está en enabled
    }
    
    issues = validate_references_rules(invalid_config)
    errors = [i for i in issues if i.is_error()]
    
    assert len(errors) > 0, "Debería detectar default inválido"
    
    print("✅ test_references_default_not_in_enabled PASSED")


def run_all_tests():
    """Ejecuta todos los tests de validación."""
    print("=" * 60)
    print("TESTS: repo_validation")
    print("=" * 60)
    
    try:
        test_format_schema_valid()
        test_format_schema_missing_meta()
        test_format_rules_uni_mismatch()
        test_id_collision_detection()
        test_references_config_valid()
        test_references_default_not_in_enabled()
        
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
