"""
Archivo: app/modules/catalog/router.py
Proposito:
- Define rutas HTTP para el catalogo y generacion de documentos.

Responsabilidades:
- Renderizar la vista /catalog con datos de discovery.
- Recibir solicitudes de generacion y entregar DOCX.
No hace:
- No implementa discovery ni genera documentos directamente.

Entradas/Salidas:
- Entradas: Request HTTP, query params y payload JSON de generacion.
- Salidas: HTMLResponse o FileResponse con DOCX.

Dependencias:
- fastapi, app.core.templates, app.modules.catalog.service.

Puntos de extension:
- Agregar filtros o endpoints adicionales del catalogo.

Donde tocar si falla:
- Revisar handlers y servicio de catalogo/generacion.
"""

from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import ValidationError

from app.core.templates import templates
from app.modules.catalog.schemas import FormatoGenerateIn
from app.modules.catalog import service

router = APIRouter()


@router.get("/catalog", response_class=HTMLResponse)
async def get_catalog(request: Request):
    """Renderiza la vista del catalogo con formatos descubiertos."""
    uni = request.query_params.get("uni")
    if uni and uni.strip().lower() == "all":
        uni = None
    # Construye catalogo para una universidad o todas.
    catalog = service.build_catalog(uni)
    formatos = catalog["formatos"]
    return templates.TemplateResponse(
        "pages/catalog.html",
        {
            "request": request,
            "title": "Catalogo",
            "breadcrumb": "Catalogo",
            "active_nav": "catalog",
            "formatos": formatos,
            "catalogo": catalog["grouped"],
            "active_uni": uni,
            "uni_name": (uni or "ALL").upper(),
        },
    )


@router.post("/catalog/generate")
async def generate_document(request: Request, background_tasks: BackgroundTasks):
    """Genera un DOCX a partir de un formato y lo devuelve como archivo."""
    try:
        payload = FormatoGenerateIn(**(await request.json()))
    except ValidationError:
        return JSONResponse({"error": "Datos invalidos"}, status_code=400)

    try:
        output_path, filename = service.generate_document(payload.format, payload.sub_type, payload.uni or "unac")
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    # Limpia el archivo temporal luego de enviar la respuesta.
    background_tasks.add_task(service.cleanup_temp_file, output_path)
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=background_tasks,
    )
