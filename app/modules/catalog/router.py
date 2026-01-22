from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import ValidationError

from app.core.templates import templates
from app.modules.catalog.schemas import FormatoGenerateIn
from app.modules.catalog import service

router = APIRouter()


@router.get("/catalog", response_class=HTMLResponse)
async def get_catalog(request: Request):
    """Get all formats for catalog view."""
    formatos = service.get_all_formatos()
    return templates.TemplateResponse(
        "pages/catalog.html",
        {
            "request": request,
            "title": "Catalogo",
            "breadcrumb": "Catalogo",
            "active_nav": "catalog",
            "formatos": formatos,
            "active_uni": "unac",
            "uni_name": "UNAC",
        },
    )


@router.post("/catalog/generate")
async def generate_document(request: Request, background_tasks: BackgroundTasks):
    """Generate a document from a format."""
    try:
        payload = FormatoGenerateIn(**(await request.json()))
    except ValidationError:
        return JSONResponse({"error": "Datos invalidos"}, status_code=400)

    try:
        output_path, filename = service.generate_document(payload.format, payload.sub_type)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except RuntimeError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    background_tasks.add_task(service.cleanup_temp_file, output_path)
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        background=background_tasks,
    )

# NUEVO ENDPOINT PARA ENTREGAR DATOS AL MODAL (CARÁTULAS)
@router.get("/formatos/{format_id}/data")
async def get_format_data_api(format_id: str):
    """
    API que alimenta el Modal de Carátulas.
    Devuelve el JSON completo del formato solicitado.
    """
    try:
        data = service.get_format_json_content(format_id)
        return JSONResponse(content=data)
    except FileNotFoundError:
        return JSONResponse({"error": "Formato no encontrado"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    
    