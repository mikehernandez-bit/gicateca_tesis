from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "title": "Admin",
            "breadcrumb": "Admin",
            "active_nav": "admin",
        },
    )
