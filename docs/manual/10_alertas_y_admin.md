# Alertas y Admin

## Módulo Alerts

### Descripción

El módulo **alerts** muestra notificaciones/alertas para los usuarios (mantenimiento, novedades, etc.).

### Endpoint

**GET `/alerts`**

Renderiza la vista de alertas para la universidad activa.

**Query Params:**
- `uni` (opcional): Código de universidad (default: `unac`).

**Fuente:** `app/modules/alerts/router.py` L32-50

```python
@router.get("/alerts", response_class=HTMLResponse)
def alerts(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)
    return templates.TemplateResponse(
        "pages/alerts.html",
        {
            "request": request,
            "alerts": provider.list_alerts(),
            # ...
        },
    )
```

### Origen de Datos

Las alertas se leen desde `app/data/{uni}/alerts.json`:

```json
[
  {
    "id": "1",
    "title": "Mantenimiento programado",
    "message": "El sistema estará en mantenimiento...",
    "type": "warning",
    "date": "2026-01-20"
  }
]
```

**Fuente:** `app/universities/contracts.py` L80-83

```python
def list_alerts(self) -> list:
    path = self.data_dir / "alerts.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
```

### Template

**Fuente:** `app/templates/pages/alerts.html` (~2KB)

---

## Módulo Admin

### Descripción

El módulo **admin** proporciona una vista de administración básica.

### Endpoint

**GET `/admin`**

Renderiza la vista principal de admin.

**Fuente:** `app/modules/admin/router.py` L33-45

```python
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
```

### Funcionalidad Actual

Actualmente el módulo admin:
- Renderiza una vista básica de administración.
- **TODO:** Implementar limpieza de cache, estadísticas, etc.

**Fuente:** `app/templates/pages/admin.html` (~2KB)

---

## Módulo Home

### Descripción

El módulo **home** renderiza la página de inicio.

### Endpoint

**GET `/`**

**Fuente:** `app/modules/home/router.py` L32-50

```python
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    uni = request.query_params.get("uni", "unac")
    provider = get_provider(uni)
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "alerts": provider.list_alerts()[:3],  # Muestra 3 alertas
            # ...
        },
    )
```

### Template

**Fuente:** `app/templates/pages/home.html` (~5KB)
