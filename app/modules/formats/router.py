"""Router for formats module."""
import tempfile
from pathlib import Path

import pythoncom
import win32com.client
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from app.core.loaders import find_format_index, load_format_by_id
from app.core.templates import templates
from app.modules.formats import service

router = APIRouter(prefix="/formatos", tags=["formatos"])


def _convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """Convierte a PDF actualizando campos para que el índice salga completo."""
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        doc = word.Documents.Open(docx_path, ReadOnly=0, AddToRecentFiles=False)
        doc.Fields.Update()
        for toc in doc.TablesOfContents:
            toc.Update()
        for tof in doc.TablesOfFigures:
            tof.Update()
        doc.SaveAs(pdf_path, FileFormat=17)
    finally:
        if doc is not None:
            doc.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def _get_cached_pdf_path(format_id: str) -> Path:
    cache_dir = Path(tempfile.gettempdir()) / "formatoteca_unac_pdf_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_name = format_id.replace("/", "_")
    return cache_dir / f"{safe_name}.pdf"


def _get_source_mtime(format_id: str) -> float:
    item = find_format_index(format_id)
    if not item:
        return 0.0
    json_path = item.path
    script_name = service.SCRIPTS_CONFIG.get(item.categoria)
    script_path = service.CF_DIR / script_name if script_name else None
    json_mtime = json_path.stat().st_mtime if json_path.exists() else 0.0
    script_mtime = script_path.stat().st_mtime if script_path and script_path.exists() else 0.0
    return max(json_mtime, script_mtime)


@router.get("/{format_id}", response_class=HTMLResponse)
async def get_format_detail(format_id: str, request: Request):
    """Get detail view for a specific format."""
    try:
        formato = service.get_formato(format_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    return templates.TemplateResponse(
        "pages/detail.html",
        {
            "request": request,
            "formato": formato,
            "title": formato["titulo"],
            "breadcrumb": formato["titulo"],
        },
    )


@router.get("/{format_id}/versions", response_class=HTMLResponse)
async def get_format_versions(format_id: str, request: Request):
    """Get version history for a specific format."""
    try:
        formato = service.get_formato(format_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Formato no encontrado")
    
    versions = [
        {"version": "2.0", "date": "2026-01-17", "changes": "Actualización de plantilla"},
        {"version": "1.0", "date": "2025-12-01", "changes": "Versión inicial"},
    ]
    
    return templates.TemplateResponse(
        "pages/versions.html",
        {
            "request": request,
            "formato": formato,
            "versions": versions,
        },
    )


@router.post("/{format_id}/generate")
async def generate_format_document(format_id: str, background_tasks: BackgroundTasks):
    """Generate a DOCX document for the given format."""
    try:
        output_path, filename = service.generate_document(format_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    
    background_tasks.add_task(service.cleanup_temp_file, output_path)
    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{format_id}/pdf")
async def get_format_pdf(format_id: str):
    """Genera el Word, lo convierte a PDF y lo devuelve."""
    try:
        cached_pdf = _get_cached_pdf_path(format_id)
        source_mtime = _get_source_mtime(format_id)
        if cached_pdf.exists() and cached_pdf.stat().st_mtime >= source_mtime:
            return FileResponse(
                path=str(cached_pdf),
                media_type="application/pdf",
                content_disposition_type="inline",
            )

        docx_path, _ = service.generate_document(format_id)
        _convert_docx_to_pdf(str(docx_path), str(cached_pdf))
        service.cleanup_temp_file(docx_path)

        return FileResponse(
            path=str(cached_pdf),
            media_type="application/pdf",
            content_disposition_type="inline",
        )

    except Exception as e:
        print(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


@router.get("/{format_id}/data")
async def get_format_data_json(format_id: str):
    """
    Devuelve el contenido JSON completo del formato.
    Usado para hidratar vistas dinamicas.
    """
    try:
        data = load_format_by_id(format_id)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JSON no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

