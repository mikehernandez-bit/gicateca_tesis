"""
Archivo: app/modules/formats/router.py
Proposito:
- Define rutas HTTP para detalle de formatos, data y exportacion DOCX/PDF.

Responsabilidades:
- Renderizar vistas de detalle y versiones.
- Generar DOCX y convertir a PDF cuando se solicita.
- Servir JSON completo para vista previa.
No hace:
- No implementa discovery ni logica de negocio de formatos.

Entradas/Salidas:
- Entradas: format_id en URL y requests HTTP.
- Salidas: HTMLResponse, FileResponse (DOCX/PDF) o JSONResponse.

Dependencias:
- fastapi, win32com (PDF), app.modules.formats.service, app.core.loaders.

Puntos de extension:
- Agregar nuevos endpoints de formatos o variantes de exportacion.

Donde tocar si falla:
- Revisar generacion en service y conversion PDF en _convert_docx_to_pdf.
"""
import tempfile
from pathlib import Path

import pythoncom
import win32com.client
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from app.core.loaders import find_format_index, load_format_by_id
from app.core.registry import get_provider
from app.core.templates import templates
from app.modules.formats import service

router = APIRouter(prefix="/formatos", tags=["formatos"])


def _convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """Convierte a PDF actualizando campos para que el índice salga completo."""
    # Automatiza Word para actualizar indices y exportar a PDF.
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
    """Retorna la ruta de cache para PDFs generados."""
    cache_dir = Path(tempfile.gettempdir()) / "formatoteca_unac_pdf_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_name = format_id.replace("/", "_")
    return cache_dir / f"{safe_name}.pdf"


def _resolve_generator_path(generator) -> Path | None:
    """Resuelve la ruta del script generador desde el provider."""
    if isinstance(generator, (list, tuple)):
        candidates = []
        for part in generator:
            try:
                path = Path(str(part))
            except Exception:
                continue
            if path.exists():
                candidates.append(path)
        for path in candidates:
            if path.suffix.lower() == ".py":
                return path
        return candidates[0] if candidates else None
    path = Path(generator)
    return path if path.exists() else None


def _get_source_mtime(format_id: str) -> float:
    """Obtiene mtime del JSON y script para invalidar cache PDF."""
    item = find_format_index(format_id)
    if not item:
        return 0.0
    json_path = item.path
    json_mtime = json_path.stat().st_mtime if json_path.exists() else 0.0
    script_mtime = 0.0
    try:
        provider = get_provider(item.uni)
        generator = provider.get_generator_command(item.categoria)
        script_path = _resolve_generator_path(generator)
        script_mtime = script_path.stat().st_mtime if script_path and script_path.exists() else 0.0
    except Exception:
        script_mtime = 0.0
    return max(json_mtime, script_mtime)


@router.get("/{format_id}", response_class=HTMLResponse)
async def get_format_detail(format_id: str, request: Request):
    """Renderiza el detalle de un formato."""
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
    """Renderiza el historial de versiones de un formato."""
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
    """Genera un DOCX para el formato solicitado."""
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
    """Genera el DOCX, lo convierte a PDF y lo devuelve."""
    try:
        cached_pdf = _get_cached_pdf_path(format_id)
        source_mtime = _get_source_mtime(format_id)
        if cached_pdf.exists() and cached_pdf.stat().st_mtime >= source_mtime:
            # Reutiliza PDF si el JSON y el generador no cambiaron.
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
    # Endpoint de data cruda para vistas y preview.
    try:
        data = load_format_by_id(format_id)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="JSON no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

