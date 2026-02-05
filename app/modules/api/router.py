"""
Archivo: app/modules/api/router.py
Propósito:
- Define endpoints HTTP de la API v1 de Formatos.
- Implementa ETag/If-None-Match para cache 304.

Responsabilidades:
- Recibir requests HTTP, delegar a service, retornar responses.
- Manejar headers de cache (ETag, Cache-Control, 304).
No hace:
- No carga datos directamente (delega a service).

Dependencias:
- fastapi, app.modules.api.service, app.modules.api.dtos

Puntos de extensión:
- Agregar endpoints de assets si se necesita.
"""
from typing import Optional

from fastapi import APIRouter, Header, Query, Response
from fastapi.responses import JSONResponse

from app.modules.api import service
from app.modules.api.dtos import CatalogValidationResponse, CatalogVersionResponse, FormatDetail, FormatSummary

router = APIRouter(prefix="/api/v1", tags=["formats-api"])

# Cache settings
CACHE_MAX_AGE = 60  # seconds
CACHE_CONTROL = f"public, max-age={CACHE_MAX_AGE}"


def _normalize_etag(etag: Optional[str]) -> Optional[str]:
    """Normaliza ETag (quita comillas si existen)."""
    if not etag:
        return None
    return etag.strip().strip('"')


def _make_etag(value: str) -> str:
    """Crea ETag con comillas."""
    return f'"{value}"'


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/formats - Lista de formatos
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/formats", response_model=list[FormatSummary])
async def list_formats(
    university: Optional[str] = Query(None, description="Filtrar por universidad"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    documentType: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
) -> Response:
    """
    Lista todos los formatos disponibles.

    Soporta filtros opcionales y cache vía ETag.
    Si If-None-Match coincide con la versión actual, retorna 304.
    """
    summaries, catalog_version = service.list_formats(
        university=university,
        category=category,
        document_type=documentType,
    )

    etag = _make_etag(catalog_version)

    # Check If-None-Match
    client_etag = _normalize_etag(if_none_match)
    if client_etag and client_etag == catalog_version:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": CACHE_CONTROL,
            },
        )

    # Serializar respuesta
    content = [s.model_dump() for s in summaries]

    return JSONResponse(
        content=content,
        headers={
            "ETag": etag,
            "Cache-Control": CACHE_CONTROL,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/formats/version - Versión del catálogo
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/formats/version", response_model=CatalogVersionResponse)
async def get_catalog_version() -> JSONResponse:
    """
    Obtiene la versión actual del catálogo de formatos.

    Útil para check rápido de cambios sin descargar todo el catálogo.
    """
    version_info = service.get_catalog_version_info()

    return JSONResponse(
        content=version_info.model_dump(),
        headers={
            "Cache-Control": "public, max-age=30",  # TTL más corto para versión
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/formats/validate - Diagnóstico del catálogo
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/formats/validate", response_model=CatalogValidationResponse)
async def validate_catalog() -> CatalogValidationResponse:
    """
    Valida el catálogo completo y reporta inconsistencias.

    Este endpoint es útil para:
    - Detectar formatos con errores antes de consumirlos
    - Diagnóstico de problemas de datos
    - CI/CD: verificar que el catálogo está sano

    Returns:
        CatalogValidationResponse con estadísticas y lista de errores.
    """
    return service.validate_catalog()


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/formats/{format_id} - Detalle de formato
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/formats/{format_id}", response_model=FormatDetail)
async def get_format_detail(
    format_id: str,
    if_none_match: Optional[str] = Header(None, alias="If-None-Match"),
) -> Response:
    """
    Obtiene el detalle completo de un formato.

    Incluye campos del wizard, assets y reglas.
    Soporta cache vía ETag.
    """
    detail, format_hash = service.get_format_detail_by_id(format_id)

    if detail is None:
        return JSONResponse(
            content={"detail": f"Formato no encontrado: {format_id}"},
            status_code=404,
        )

    etag = _make_etag(format_hash)

    # Check If-None-Match
    client_etag = _normalize_etag(if_none_match)
    if client_etag and client_etag == format_hash:
        return Response(
            status_code=304,
            headers={
                "ETag": etag,
                "Cache-Control": CACHE_CONTROL,
            },
        )

    return JSONResponse(
        content=detail.model_dump(),
        headers={
            "ETag": etag,
            "Cache-Control": CACHE_CONTROL,
        },
    )



# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/assets/{asset_path:path} - Servir assets
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/assets/{asset_path:path}")
async def get_asset(asset_path: str) -> Response:
    """
    Sirve un asset por su path lógico.

    Seguridad:
    - No permite path traversal (../)
    - Solo sirve desde directorios permitidos
    """
    from pathlib import Path
    from fastapi.responses import FileResponse

    # Validar path traversal
    if ".." in asset_path or asset_path.startswith("/"):
        return JSONResponse(
            content={"detail": "Path inválido"},
            status_code=400,
        )

    # Friendly logo aliases (compatibilidad)
    def _map_logo(code: str):
        if not code:
            return None
        if code.lower() == "generic":
            return "assets/LogoGeneric.png"
        return f"assets/Logo{code.upper()}.png"

    if asset_path.startswith("logos/"):
        mapped = _map_logo(Path(asset_path).stem)
        if mapped:
            asset_path = mapped
    else:
        parts = asset_path.split("/")
        if len(parts) == 3 and parts[1] == "logo" and parts[2] == "main":
            mapped = _map_logo(parts[0])
            if mapped:
                asset_path = mapped

    # Base directory para assets (static)
    base_dir = Path(__file__).parents[2] / "static"

    # Resolver path
    target_path = (base_dir / asset_path).resolve()

    # Verificar que está dentro de base_dir
    try:
        target_path.relative_to(base_dir.resolve())
    except ValueError:
        return JSONResponse(
            content={"detail": "Path fuera de directorio permitido"},
            status_code=403,
        )

    if not target_path.exists() or not target_path.is_file():
        return JSONResponse(
            content={"detail": "Asset no encontrado"},
            status_code=404,
        )

    # Determinar media type
    suffix = target_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(target_path),
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # Assets son más estables
        },
    )
