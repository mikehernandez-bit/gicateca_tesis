# Formatoteca

Este repositorio es una estructura base en **Python + FastAPI + Jinja2** para una “biblioteca de formatos de tesis”.
La idea es que cada colaborador tome un **módulo** (Catálogo, Detalle, Alertas, etc.) y lo complete mediante Pull Requests.

## Ejecutar (local)
# Windows: 
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
# Visual Code:
pip install -r requirements.txt
python uvicorn app.main:app --reload

Luego abre:
- Home: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/catalog
- Alertas: http://127.0.0.1:8000/alerts

## Estructura
- `app/modules/home/` -> Inicio
- `app/modules/catalog/` -> Catálogo + filtros (placeholder)
- `app/modules/formats/` -> Detalle + versiones (placeholder)
- `app/modules/alerts/` -> Notificaciones (placeholder)
- `app/modules/admin/` -> Panel Admin (placeholder)
- `app/templates/` -> HTML (Jinja). Cada pantalla está en `templates/pages/`.
- `data/seed/` -> JSON de ejemplo (para que la UI tenga contenido sin BD).

## Reglas
- No hacer push directo a `main`.

## Verificacion de encoding
- Ejecutar: `python scripts/check_mojibake.py`
  
## Mockup original
Está guardado en `ui/mockup/index.html` como referencia visual.
