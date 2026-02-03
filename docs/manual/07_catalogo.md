# Módulo Catálogo

## Descripción

El módulo **catalog** permite explorar los formatos disponibles y generar documentos DOCX.

---

## Endpoints

### GET `/catalog`

Renderiza la vista del catálogo con formatos descubiertos.

**Query Params:**
- `uni` (opcional): Código de universidad. Si es `"all"` o vacío, muestra todas.

**Fuente:** `app/modules/catalog/router.py` L37-58

```python
@router.get("/catalog", response_class=HTMLResponse)
async def get_catalog(request: Request):
    uni = request.query_params.get("uni")
    if uni and uni.strip().lower() == "all":
        uni = None
    catalog = service.build_catalog(uni)
    # ...
```

### POST `/catalog/generate`

Genera un DOCX a partir de un formato.

**Body (JSON):**
```json
{
  "format": "informe",
  "sub_type": "cual",
  "uni": "unac"
}
```

**Response:** Archivo DOCX para descarga.

**Fuente:** `app/modules/catalog/router.py` L61-83

---

## Servicio: `build_catalog()`

Construye el catálogo agrupado por universidad/categoría/enfoque.

**Proceso:**
1. Llama a `discover_format_files(uni)` para obtener todos los JSON.
2. Filtra los que son "referencias" (excluidos del catálogo).
3. Construye entradas con título, estado, versión, etc.
4. Agrupa por `{uni} -> {categoria} -> {enfoque}`.

**Fuente:** `app/modules/catalog/service.py` L157-181

### Exclusión de Referencias

El catálogo **excluye** formatos con keywords de referencias:

```python
_REFERENCE_KEYWORDS = {
    "references", "referencias", "bibliografia",
    "bibliografica", "bibliograficas",
}
```

**Fuente:** `app/modules/catalog/service.py` L57-63

---

## Template: `catalog.html`

La vista del catálogo utiliza:
- **Jinja2** para renderizar la lista de formatos.
- **JavaScript** (`catalog.js`) para filtros dinámicos.

**Fuente:** `app/templates/pages/catalog.html` (~12KB)

### Filtros en UI

El usuario puede filtrar por:
- **Universidad** (UNAC, UNI, ALL)
- **Tipo** (Tesis, Inv. Formativa, Suficiencia)

**Fuente:** `app/static/js/catalog.js`

---

## Carátulas (modo visual)

En modo **Carátulas**, el botón “Ver Carátula” abre el **modal unificado** de carátula, usando el mismo HTML/JS que el detalle.

Flujo:
1. `catalog.html` incluye `components/cover_modal.html`.
2. `cover-preview.js` controla la apertura del modal (`window.GicaCover.open`).
3. `catalog.js` delega a `GicaCover` mediante `previewCover(formatId)`.

**Archivos involucrados**
- `app/templates/pages/catalog.html`
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/static/js/catalog.js`

**Cómo probar**
1) Abrir `/catalog` y activar “Carátulas”.  
2) Click en “Ver Carátula”.  
3) Confirmar que el modal muestra datos del JSON del formato.

---

## Generación de Documentos

### Flujo

1. Frontend envía POST a `/catalog/generate` con `{format, sub_type, uni}`.
2. `service.generate_document()` resuelve el generador.
3. Se ejecuta el script Python que produce el DOCX.
4. Se retorna `FileResponse` con el archivo.
5. `BackgroundTasks` limpia el temporal después.

**Fuente:** `app/modules/catalog/service.py` L228-256

### Código Clave

```python
def generate_document(fmt_type: str, sub_type: str, uni: str = "unac"):
    provider = get_provider(uni)
    generator = provider.get_generator_command(fmt_type)
    
    json_path = provider.get_data_dir() / fmt_type / f"{provider.code}_{fmt_type}_{sub_type}.json"
    if not json_path.exists():
        raise RuntimeError(f"JSON no encontrado: {json_path}")
    
    # Ejecuta el generador
    cmd, workdir = _resolve_generator_command(generator, json_path, output_path)
    result = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True)
    # ...
```
