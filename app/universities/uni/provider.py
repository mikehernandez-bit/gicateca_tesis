"""
Archivo: app/universities/uni/provider.py
Proposito:
- Declara el provider UNI para discovery de formatos.

Responsabilidades:
- Configurar code/display_name/data_dir.
No hace:
- No define generadores (se espera error si se solicita).

Entradas/Salidas:
- Entradas: N/A (constantes y rutas).
- Salidas: Instancia PROVIDER utilizada por el registry.

Dependencias:
- app.core.paths, app.universities.contracts.

Puntos de extension:
- Agregar generadores al mapa cuando existan scripts.

Donde tocar si falla:
- Revisar data_dir o agregar generator_map si se requiere generar.
"""

from pathlib import Path

from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

# Instancia principal que el registry descubre via PROVIDER.
MODULE_DIR = Path(__file__).parent

PROVIDER = SimpleUniversityProvider(
    code="uni",
    display_name="UNI",
    data_dir=get_data_dir("uni"),
    generator_map={
        "informe": MODULE_DIR / "centro_formatos" / "generador_informe_tesis.py",
        "maestria": MODULE_DIR / "centro_formatos" / "generador_maestria.py",
        "posgrado": MODULE_DIR / "centro_formatos" / "generador_maestria.py",
        "proyecto": MODULE_DIR / "centro_formatos" / "generador_proyecto_tesis.py",
    },
)
