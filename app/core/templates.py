"""
Archivo: app/core/templates.py
Proposito:
- Configura el motor de plantillas Jinja2 para la UI.

Responsabilidades:
- Exponer la instancia de Jinja2Templates con el directorio correcto.
No hace:
- No renderiza vistas directamente ni maneja rutas.

Entradas/Salidas:
- Entradas: N/A.
- Salidas: Objeto templates reutilizable por routers.

Dependencias:
- fastapi.templating.Jinja2Templates, pathlib.Path.

Puntos de extension:
- Cambiar el directorio base de templates si la estructura cambia.

Donde tocar si falla:
- Revisar el path de templates y la inicializacion de Jinja2Templates.
"""

from pathlib import Path
from fastapi.templating import Jinja2Templates

# Raiz de la carpeta app/ para resolver templates.
BASE_DIR = Path(__file__).resolve().parents[1]  # app/
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
