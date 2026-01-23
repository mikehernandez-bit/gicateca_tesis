"""
Archivo: app/modules/references/router.py
Proposito:
- Define endpoints para la vista y API de referencias bibliograficas.

Responsabilidades:
- Renderizar la pagina /referencias.
- Exponer API data-driven de normas y detalle por norma.
No hace:
- No implementa discovery directo ni escribe datos.

Entradas/Salidas:
- Entradas: query param uni, ref_id.
- Salidas: HTMLResponse o JSONResponse.

Dependencias:
- fastapi, app.core.templates, app.modules.references.service.

Puntos de extension:
- Agregar endpoints para busqueda avanzada o exportacion.

Donde tocar si falla:
- Revisar service.py y templates/pages/references.html.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.registry import get_provider
from app.core.templates import templates
from app.modules.references import service

router = APIRouter()


def _resolve_uni_context(uni: str) -> tuple[str, str]:
    """Resuelve code y nombre visible; fallback si no existe provider."""
    code = (uni or "unac").strip().lower()
    try:
        provider = get_provider(code)
        return provider.code, provider.display_name
    except KeyError:
        return code, code.upper()


@router.get("/referencias", response_class=HTMLResponse)
def references_page(request: Request):
    """Renderiza la vista principal de referencias bibliograficas."""
    uni = request.query_params.get("uni", "unac")
    uni_code, uni_name = _resolve_uni_context(uni)
    return templates.TemplateResponse(
        "pages/references.html",
        {
            "request": request,
            "title": "Referencias Bibliograficas",
            "breadcrumb": "Referencias",
            "active_nav": "references",
            "active_uni": uni_code,
            "uni_name": uni_name,
        },
    )


@router.get("/api/referencias")
def get_references_index(request: Request):
    """Retorna listado resumido y configuracion por universidad."""
    uni = request.query_params.get("uni", "unac")
    payload = service.build_reference_index(uni)
    return JSONResponse(content=payload)


@router.get("/api/referencias/{ref_id}")
def get_reference_detail(ref_id: str, request: Request):
    """Retorna la norma completa por ID."""
    uni = request.query_params.get("uni", "unac")
    try:
        payload = service.get_reference_detail(ref_id, uni)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Norma no encontrada")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse(content=payload)

