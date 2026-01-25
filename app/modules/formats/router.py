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
- fastapi, app.core.pdf_converter, app.modules.formats.service, app.core.loaders.

Puntos de extension:
- Agregar nuevos endpoints de formatos o variantes de exportacion.

Donde tocar si falla:
- Revisar generacion en service y conversion PDF en _convert_docx_to_pdf.
"""
import hashlib
import json
import os
import shutil
import time
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path

import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from app.core.loaders import find_format_index, load_format_by_id
from app.core.paths import get_docx_cache_dir, get_pdf_cache_dir
from app.core.pdf_converter import convert_docx_to_pdf
from app.core.registry import get_provider
from app.core.templates import templates
from app.modules.formats import service

router = APIRouter(prefix="/formatos", tags=["formatos"])

_PDF_CACHE_MAX_AGE = int(os.getenv("PDF_CACHE_MAX_AGE", "3600"))
_PDF_PREWARM_ON_STARTUP = os.getenv("PDF_PREWARM_ON_STARTUP", "false").lower() in ("1", "true", "yes", "on")
_PDF_CONVERSION_TIMEOUT = float(os.getenv("PDF_CONVERSION_TIMEOUT", "120"))

logger = logging.getLogger(__name__)


def _ensure_cache_dirs() -> tuple[Path, Path]:
    """Crea (si falta) los directorios de cache DOCX/PDF."""
    docx_dir = get_docx_cache_dir()
    pdf_dir = get_pdf_cache_dir()
    docx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return docx_dir, pdf_dir


def _get_cached_docx_path(format_id: str) -> Path:
    """Ruta de cache DOCX para un format_id."""
    docx_dir, _ = _ensure_cache_dirs()
    safe_name = format_id.replace("/", "_")
    return docx_dir / f"{safe_name}.docx"


def _get_cached_pdf_path(format_id: str) -> Path:
    """Ruta de cache PDF para un format_id."""
    _, pdf_dir = _ensure_cache_dirs()
    safe_name = format_id.replace("/", "_")
    return pdf_dir / f"{safe_name}.pdf"


def _get_manifest_path(format_id: str) -> Path:
    """Ruta de manifest JSON para un format_id."""
    _, pdf_dir = _ensure_cache_dirs()
    safe_name = format_id.replace("/", "_")
    return pdf_dir / f"{safe_name}.manifest.json"


def _is_cache_fresh(path: Path, source_mtime: float) -> bool:
    """Verifica si el cache es mas nuevo que la fuente y no esta vacio."""
    if not path.exists():
        return False
    if path.stat().st_size <= 0:
        return False
    return path.stat().st_mtime >= source_mtime


def _calculate_sha256(path: Path) -> str:
    """Calcula SHA256 de un archivo."""
    sha = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _replace_cached_file(src: Path, dest: Path) -> None:
    """Reemplaza dest con src (copia segura si cambia de unidad)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(src, dest)
    except OSError:
        shutil.copy2(src, dest)
        try:
            src.unlink()
        except Exception:
            pass


def _build_etag(format_id: str, source_mtime: float) -> str:
    """Construye ETag estable basado en fuente."""
    raw = f"{format_id}:{int(source_mtime)}".encode("utf-8")
    return f"\"{hashlib.md5(raw).hexdigest()}\""


def _http_date(timestamp: float) -> str:
    """Convierte timestamp a HTTP-date."""
    ts = int(timestamp) if timestamp else int(time.time())
    return formatdate(ts, usegmt=True)


def _is_client_cache_valid(request: Request, etag: str, source_mtime: float) -> bool:
    """Evalua If-None-Match/If-Modified-Since para responder 304."""
    inm = request.headers.get("if-none-match")
    if inm and inm.strip() == etag:
        return True
    ims = request.headers.get("if-modified-since")
    if ims:
        try:
            ims_dt = parsedate_to_datetime(ims)
            if ims_dt.timestamp() >= source_mtime:
                return True
        except Exception:
            return False
    return False


def _build_cache_headers(format_id: str, source_mtime: float) -> dict[str, str]:
    """Construye headers HTTP para cache del navegador."""
    etag = _build_etag(format_id, source_mtime)
    return {
        "Cache-Control": f"public, max-age={_PDF_CACHE_MAX_AGE}",
        "ETag": etag,
        "Last-Modified": _http_date(source_mtime),
    }


def _write_manifest(
    format_id: str,
    json_path: Path,
    json_mtime: float,
    generator_path: Path | None,
    generator_mtime: float,
    docx_path: Path,
    pdf_path: Path,
) -> None:
    """Escribe un manifest JSON para depuracion de cache."""
    manifest_path = _get_manifest_path(format_id)
    payload = {
        "format_id": format_id,
        "json_path": str(json_path),
        "json_mtime": json_mtime,
        "generator_script_path": str(generator_path) if generator_path else None,
        "generator_mtime": generator_mtime,
        "created_at": _http_date(time.time()),
        "docx_path": str(docx_path),
        "pdf_path": str(pdf_path),
    }
    try:
        payload["sha256_pdf"] = _calculate_sha256(pdf_path)
    except Exception:
        payload["sha256_pdf"] = None
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _convert_docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """Convierte a PDF actualizando campos para que el indice salga completo."""
    convert_docx_to_pdf(docx_path, pdf_path, timeout=_PDF_CONVERSION_TIMEOUT)


def _ensure_docx_cached(format_id: str, source_mtime: float) -> Path:
    """Genera o reutiliza el DOCX cacheado."""
    docx_path = _get_cached_docx_path(format_id)
    if _is_cache_fresh(docx_path, source_mtime):
        logger.info("DOCX cache hit: %s", docx_path)
        return docx_path

    generated_path, _filename = service.generate_document(format_id)
    _replace_cached_file(Path(generated_path), docx_path)
    logger.info("DOCX generado: %s", docx_path)
    return docx_path


def _ensure_pdf_cached(format_id: str, source_mtime: float) -> Path:
    """Genera o reutiliza el PDF cacheado."""
    pdf_path = _get_cached_pdf_path(format_id)
    if _is_cache_fresh(pdf_path, source_mtime):
        logger.info("PDF cache hit: %s", pdf_path)
        return pdf_path

    docx_path = _ensure_docx_cached(format_id, source_mtime)
    if pdf_path.exists():
        try:
            pdf_path.unlink()
        except Exception:
            pass
    start = time.time()
    _convert_docx_to_pdf(str(docx_path), str(pdf_path))
    logger.info("PDF generado: %s (%.2fs)", pdf_path, time.time() - start)
    return pdf_path


def prewarm_pdfs() -> None:
    """Precalienta el cache de PDF si esta habilitado por entorno."""
    if not _PDF_PREWARM_ON_STARTUP:
        return

    try:
        from app.core.loaders import discover_format_files
    except Exception as exc:
        print(f"[WARN] prewarm import failed: {exc}")
        return

    items = discover_format_files(None)
    if not items:
        return

    # Prioriza UNAC; si no hay, precalienta todo lo disponible.
    candidates = [item.format_id for item in items if item.uni == "unac"]
    if not candidates:
        candidates = [item.format_id for item in items]

    for format_id in candidates:
        try:
            source_mtime = _get_source_mtime(format_id)
            _ensure_pdf_cached(format_id, source_mtime)
        except Exception as exc:
            logger.warning("prewarm failed %s: %s", format_id, exc)


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


def _get_source_info(format_id: str):
    """Obtiene info de fuentes para invalidacion y manifest."""
    item = find_format_index(format_id)
    if not item:
        return None, None, 0.0, None, 0.0, 0.0

    json_path = item.path
    json_mtime = json_path.stat().st_mtime if json_path.exists() else 0.0
    script_path = None
    script_mtime = 0.0
    extra_mtime = 0.0

    try:
        provider = get_provider(item.uni)
        generator = provider.get_generator_command(item.categoria)
        script_path = _resolve_generator_path(generator)
        script_mtime = script_path.stat().st_mtime if script_path and script_path.exists() else 0.0
    except Exception:
        script_path = None
        script_mtime = 0.0

    extra_paths = [
        Path(__file__).resolve().parent / "service.py",
        Path(__file__).resolve().parents[2] / "core" / "loaders.py",
    ]
    for path in extra_paths:
        if path.exists():
            extra_mtime = max(extra_mtime, path.stat().st_mtime)

    source_mtime = max(json_mtime, script_mtime, extra_mtime)
    return item, json_path, json_mtime, script_path, script_mtime, source_mtime


def _get_source_mtime(format_id: str) -> float:
    """Obtiene mtime total de fuentes para invalidar cache PDF."""
    _item, _json_path, _json_mtime, _script_path, _script_mtime, source_mtime = _get_source_info(format_id)
    return source_mtime


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
async def get_format_pdf(format_id: str, request: Request):
    """Genera el DOCX, lo convierte a PDF y lo devuelve."""
    try:
        item, json_path, json_mtime, script_path, script_mtime, source_mtime = _get_source_info(format_id)
        headers = _build_cache_headers(format_id, source_mtime)
        cached_pdf = _get_cached_pdf_path(format_id)

        if _is_cache_fresh(cached_pdf, source_mtime):
            # Reutiliza PDF si el JSON y el generador no cambiaron.
            logger.info("PDF cache hit (request): %s", cached_pdf)
            if _is_client_cache_valid(request, headers["ETag"], source_mtime):
                return Response(status_code=304, headers=headers)
            return FileResponse(
                path=str(cached_pdf),
                media_type="application/pdf",
                content_disposition_type="inline",
                headers=headers,
            )

        pdf_path = _ensure_pdf_cached(format_id, source_mtime)
        docx_path = _get_cached_docx_path(format_id)
        if item and json_path:
            _write_manifest(
                format_id=format_id,
                json_path=json_path,
                json_mtime=json_mtime,
                generator_path=script_path,
                generator_mtime=script_mtime,
                docx_path=docx_path,
                pdf_path=pdf_path,
            )

        headers = _build_cache_headers(format_id, source_mtime)
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            content_disposition_type="inline",
            headers=headers,
        )

    except Exception as e:
        logger.error("Error generando PDF: %s", e)
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar la vista previa. Intenta nuevamente en unos segundos.",
        )


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

