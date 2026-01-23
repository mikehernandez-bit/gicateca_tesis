"""
Archivo: app/modules/admin/router.py
Proposito:
- Define rutas HTTP para la seccion de administracion (UI).

Responsabilidades:
- Registrar endpoints del modulo admin.
- Renderizar la plantilla principal de administracion.
No hace:
- No contiene logica de negocio ni acceso a datos.

Entradas/Salidas:
- Entradas: Request HTTP.
- Salidas: HTMLResponse con template admin.

Dependencias:
- fastapi, app.core.templates.

Puntos de extension:
- Agregar rutas nuevas de administracion.

Donde tocar si falla:
- Revisar el handler y la plantilla pages/admin.html.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    """Renderiza la vista principal de admin."""
    # Render del template base de administracion.
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "title": "Admin",
            "breadcrumb": "Admin",
            "active_nav": "admin",
        },
    )
