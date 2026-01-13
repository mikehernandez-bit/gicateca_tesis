from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter()

@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    return templates.TemplateResponse(
        "pages/catalog.html",
        {
            "request": request,
            "title": "Catálogo",
            "breadcrumb": "Catálogo",
            "formatos": provider.list_formatos(),
            "active_nav": "catalog",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )
