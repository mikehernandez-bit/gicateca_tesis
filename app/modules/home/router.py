from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

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
