# Formatoteca (Scaffold base)

Este repositorio es un **cascarón** (estructura base) en **Python + FastAPI + Jinja2** para una “biblioteca de formatos de tesis”.
La idea es que cada practicante tome un **módulo** (Catálogo, Detalle, Alertas, etc.) y lo complete mediante Pull Requests.

## Ejecutar (local)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Luego abre:
- Home: http://127.0.0.1:8000/
- Catálogo: http://127.0.0.1:8000/catalog
- Alertas: http://127.0.0.1:8000/alerts

## Estructura (para repartir trabajo)
- `app/modules/home/` -> Inicio
- `app/modules/catalog/` -> Catálogo + filtros (placeholder)
- `app/modules/formats/` -> Detalle + versiones (placeholder)
- `app/modules/alerts/` -> Notificaciones (placeholder)
- `app/modules/admin/` -> Panel Admin (placeholder)
- `app/templates/` -> HTML (Jinja). Cada pantalla está en `templates/pages/`.
- `data/seed/` -> JSON de ejemplo (para que la UI tenga contenido sin BD).

## Reglas sugeridas de GitHub
- No hacer push directo a `main`.
- Cada tarea en una rama: `feature/catalog`, `feature/alerts`, etc.
- PR pequeño + 1 revisión antes de merge.

## Mockup original
Está guardado en `ui/mockup/index.html` como referencia visual.
