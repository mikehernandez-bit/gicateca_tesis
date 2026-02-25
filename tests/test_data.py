#!/usr/bin/env python
"""
Archivo: test_data.py
Proposito:
- Ejecuta pruebas manuales basicas sobre catalogo y formatos.

Responsabilidades:
- Invocar servicios de catalogo y formatos y reportar resultados en consola.
No hace:
- No modifica datos ni genera documentos.

Entradas/Salidas:
- Entradas: N/A (usa IDs de prueba fijos).
- Salidas: Codigo de salida 0/1 y logs en consola.

Dependencias:
- app.modules.catalog.service, app.modules.formats.service.

Puntos de extension:
- Agregar casos de prueba o IDs adicionales.

Donde tocar si falla:
- Revisar servicios llamados y los IDs de prueba.
"""
import sys
from pathlib import Path
from app.modules.catalog.service import get_all_formatos
from app.modules.formats.service import get_formato

def test_catalog():
    """Test catalog service returns formatos."""
    formatos = get_all_formatos()
    assert len(formatos) > 0, "Catalog should have at least one formato"
    for f in formatos:
        assert "id" in f, "Each formato must have an id"
        assert "titulo" in f, "Each formato must have a titulo"

def test_formats():
    """Test formats service loads known format IDs."""
    test_ids = [
        "unac-informe-cual",
        "unac-proyecto-cuant",
        "unac-maestria-cual",
    ]
    for format_id in test_ids:
        formato = get_formato(format_id)
        assert formato is not None, f"{format_id} should load"
        assert "titulo" in formato, f"{format_id} must have titulo"

if __name__ == "__main__":
    success = test_catalog() and test_formats()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Tests failed!")
        sys.exit(1)
