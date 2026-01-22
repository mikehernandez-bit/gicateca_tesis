#!/usr/bin/env python
"""Test script to verify catalog data loading."""
import sys
from pathlib import Path
from app.modules.catalog.service import get_all_formatos
from app.modules.formats.service import get_formato

def test_catalog():
    """Test catalog service."""
    print("=" * 60)
    print("Testing Catalog Service")
    print("=" * 60)
    
    try:
        formatos = get_all_formatos()
        print(f"✓ Loaded {len(formatos)} formatos")
        
        for i, f in enumerate(formatos, 1):
            print(f"\n{i}. {f['titulo']}")
            print(f"   ID: {f['id']}")
            print(f"   Tipo: {f['tipo']}")
            print(f"   Estado: {f['estado']}")
            print(f"   Versión: {f['version']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_formats():
    """Test formats service."""
    print("\n" + "=" * 60)
    print("Testing Formats Service")
    print("=" * 60)
    
    test_ids = [
        "unac-informe-cual",
        "unac-proyecto-cuant",
        "unac-maestria-cual"
    ]
    
    for format_id in test_ids:
        try:
            formato = get_formato(format_id)
            print(f"✓ {format_id}")
            print(f"  Título: {formato['titulo']}")
            print(f"  Versión: {formato['version']}")
        except Exception as e:
            print(f"✗ {format_id}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_catalog() and test_formats()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Tests failed!")
        sys.exit(1)
