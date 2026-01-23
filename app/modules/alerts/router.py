"""
Archivo: app/modules/alerts/router.py
Proposito:
- Define rutas HTTP para la seccion de alertas/notificaciones.

Responsabilidades:
- Resolver universidad activa y renderizar alerts.html.
No hace:
- No contiene logica de negocio ni acceso directo a archivos.

Entradas/Salidas:
- Entradas: Request HTTP con query param uni opcional.
- Salidas: HTMLResponse con alertas y contexto UI.

Dependencias:
- fastapi, app.core.templates, app.core.university_registry.

Puntos de extension:
- Agregar endpoints nuevos relacionados con alertas.

Donde tocar si falla:
- Revisar handler y provider.list_alerts().
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/alerts", response_class=HTMLResponse)
def alerts(request: Request):
    """Renderiza la vista de alertas para la universidad activa."""
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    # Se usa el provider para obtener alertas por universidad.
    return templates.TemplateResponse(
        "pages/alerts.html",
        {
            "request": request,
            "title": "Notificaciones",
            "breadcrumb": "Notificaciones",
            "alerts": provider.list_alerts(),
            "active_nav": "alerts",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )
