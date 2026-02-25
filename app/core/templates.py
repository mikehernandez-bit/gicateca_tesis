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


def _get_favicon_url() -> str:
    """Construye la URL del favicon basada en la universidad por defecto."""
    from app.core.settings import get_default_uni_code
    code = get_default_uni_code().upper()
    return f"/static/assets/Logo{code}.png"


# Inyectar favicon_url como variable global en todos los templates.
templates.env.globals["favicon_url"] = _get_favicon_url()
