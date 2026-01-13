from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.university_registry import get_provider

router = APIRouter(prefix="/formatos", tags=["formatos"])

@router.get("/{format_id}", response_class=HTMLResponse)
def detail(request: Request, format_id: str):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    formato = provider.get_formato(format_id)
    if not formato:
        raise HTTPException(status_code=404, detail="Formato no encontrado")

    return templates.TemplateResponse(
        "pages/detail.html",
        {
            "request": request,
            "title": "Detalle",
            "breadcrumb": "Detalle",
            "formato": formato,
            "active_nav": "catalog",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )

@router.get("/{format_id}/versions", response_class=HTMLResponse)
def versions(request: Request, format_id: str):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)

    formato = provider.get_formato(format_id)
    if not formato:
        raise HTTPException(status_code=404, detail="Formato no encontrado")

    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "title": "Historial",
            "breadcrumb": "Historial",
            "formato": formato,
            "active_nav": "catalog",
            "active_uni": provider.code,
            "uni_name": provider.name,
        },
    )
