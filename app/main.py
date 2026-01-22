from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.modules.home.router import router as home_router
from app.modules.catalog.router import router as catalog_router
from app.modules.formats.router import router as formats_router
from app.modules.alerts.router import router as alerts_router
from app.modules.admin.router import router as admin_router

app = FastAPI(title="Formatoteca", version="0.1.0")

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/recursos_data", StaticFiles(directory="app/data/unac"), name="data_unac")

# Routers (cada módulo es una sección del mockup)
app.include_router(home_router)
app.include_router(catalog_router)
app.include_router(formats_router)
app.include_router(alerts_router)
app.include_router(admin_router)
