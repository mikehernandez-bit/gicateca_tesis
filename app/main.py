"""
Archivo: app/main.py
Proposito:
- Inicializa la aplicacion FastAPI, registra routers y configura middleware/globales.

Responsabilidades:
- Crear la instancia de FastAPI y montar recursos estaticos.
- Registrar routers de los modulos funcionales.
- Forzar charset UTF-8 en respuestas de texto/JSON.
No hace:
- No implementa logica de negocio ni acceso directo a datos.

Entradas/Salidas:
- Entradas: Requests HTTP entrantes.
- Salidas: Responses HTTP de los routers registrados.

Dependencias:
- FastAPI, StaticFiles, routers de app.modules.*.

Puntos de extension:
- Agregar middleware global o routers adicionales.
- Ajustar configuracion de montaje de estaticos.

Donde tocar si falla:
- Verificar middleware y rutas registradas en este archivo.
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.modules.home.router import router as home_router
from app.modules.catalog.router import router as catalog_router
from app.modules.formats.router import router as formats_router, prewarm_pdfs as _prewarm_pdfs
from app.modules.alerts.router import router as alerts_router
from app.modules.references.router import router as references_router
from app.modules.admin.router import router as admin_router
from app.modules.api.router import router as api_router
from app.modules.api.generation_router import router as generation_router
from app.modules.api.render_router import router as render_router

app = FastAPI(title="Formatoteca", version="0.1.0")


@app.on_event("startup")
def _prewarm_pdf_cache() -> None:
    # Precalienta PDFs solo si el flag de entorno esta activo.
    _prewarm_pdfs()

@app.middleware("http")
async def ensure_utf8_charset(request: Request, call_next):
    # Garantiza que respuestas textuales incluyan charset utf-8.
    response = await call_next(request)
    content_type = response.headers.get("content-type")
    if content_type:
        lower_type = content_type.lower()
        if (
            lower_type.startswith("text/")
            or lower_type.startswith("application/json")
            or lower_type.startswith("application/javascript")
        ) and "charset=" not in lower_type:
            response.headers["content-type"] = f"{content_type}; charset=utf-8"
    return response

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/recursos_data", StaticFiles(directory="app/data/unac"), name="data_unac")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return RedirectResponse(url="/static/assets/LogoUNAC.png")

# Routers (cada modulo es una seccion del mockup)
app.include_router(home_router)
app.include_router(catalog_router)
app.include_router(formats_router)
app.include_router(alerts_router)
app.include_router(admin_router)
app.include_router(references_router)
app.include_router(api_router)
app.include_router(generation_router)
app.include_router(render_router)
