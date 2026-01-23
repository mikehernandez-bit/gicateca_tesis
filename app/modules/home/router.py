"""
Archivo: app/modules/home/router.py
Proposito:
- Define la ruta principal (home) de la aplicacion.

Responsabilidades:
- Resolver universidad activa y renderizar home.html.
No hace:
- No contiene logica de negocio ni acceso directo a datos.

Entradas/Salidas:
- Entradas: Request HTTP con query param uni opcional.
- Salidas: HTMLResponse con contexto de UI.

Dependencias:
- fastapi, app.core.templates, app.core.university_registry.

Puntos de extension:
- Agregar secciones adicionales en la portada.

Donde tocar si falla:
- Revisar handler y plantilla pages/home.html.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Renderiza la pagina de inicio."""
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    # Muestra un resumen de alertas en la portada.
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Inicio",
            "breadcrumb": "Inicio",
            "alerts": provider.list_alerts()[:3],
            "active_nav": "home",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )
