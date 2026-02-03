"""
Archivo: app/universities/unac/provider.py
Proposito:
- Declara el provider UNAC para discovery y generadores por categoria.

Responsabilidades:
- Configurar code/display_name/data_dir y mapa de generadores.
- Fase 2: Definir defaults y default_logo_url para view-models.
No hace:
- No contiene logica de generacion ni lectura de formatos.

Entradas/Salidas:
- Entradas: N/A (constantes y rutas).
- Salidas: Instancia PROVIDER utilizada por el registry.

Dependencias:
- app.core.paths, app.universities.contracts.

Puntos de extension:
- Agregar categorias nuevas al generator_map.

Donde tocar si falla:
- Revisar rutas a generadores en centro_formatos.
"""

from pathlib import Path

from app.core.paths import get_data_dir
from app.universities.contracts import SimpleUniversityProvider

# Carpeta local que contiene los generadores DOCX de UNAC.
BASE_DIR = Path(__file__).resolve().parent / "centro_formatos"

# Instancia principal que el registry descubre via PROVIDER.
PROVIDER = SimpleUniversityProvider(
    code="unac",
    display_name="UNAC",
    data_dir=get_data_dir("unac"),
    generator_map={
        "informe": BASE_DIR / "generador_informe_tesis.py",
        "maestria": BASE_DIR / "generador_maestria.py",
        "proyecto": BASE_DIR / "generador_proyecto_tesis.py",
    },
    # Fase 2: Defaults para view-models de carátula
    default_logo_url="/static/assets/LogoUNAC.png",
    defaults={
        "universidad": "UNIVERSIDAD NACIONAL DEL CALLAO",
        "lugar": "CALLAO, PERÚ",
        "anio": "2026",
    },
)
