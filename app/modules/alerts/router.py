from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/alerts", response_class=HTMLResponse)
def alerts(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

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
