# Formatos: Detalle y Exportación

## Descripción

El módulo **formats** maneja la vista de detalle de un formato específico, la generación de DOCX, la conversión a PDF y la exposición del JSON para previsualizaciones.

---

## Endpoints

### GET `/formatos/{format_id}`

Renderiza el detalle de un formato.

**Fuente:** `app/modules/formats/router.py` L320-336

### POST `/formatos/{format_id}/generate`

Genera un DOCX para el formato solicitado.

**Response:** Archivo DOCX para descarga.

**Fuente:** `app/modules/formats/router.py` L362-377

### GET `/formatos/{format_id}/pdf`

Genera el DOCX, lo convierte a PDF y lo devuelve.

**Headers de Cache:**
- `ETag`: SHA256 del DOCX (primeros 16 caracteres)
- `Cache-Control`: `no-store` (para forzar regeneración si cambia)

**Fuente:** `app/modules/formats/router.py` L380-421

### GET `/formatos/{format_id}/data`

Devuelve el contenido JSON completo del formato.

**Uso:** Para hidratar vistas dinámicas (carátula, índice, capítulos).

**Fuente:** `app/modules/formats/router.py` L424-437

---

## Vista previa de carátula (HTML)

En la vista de detalle, el botón **“Carátula Institucional”** abre el **modal unificado** de carátula (HTML), controlado por `cover-preview.js`.

Flujo:
1. `detail.html` incluye `components/cover_modal.html`.
2. `cover-preview.js` expone `window.GicaCover.open(formatId)`.
3. `format-viewer.js` delega el preview al controlador unificado.

**Archivos involucrados**
- `app/templates/pages/detail.html`
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/static/js/format-viewer.js`

**Cómo probar**
1) Abrir `/formatos/{id}`.  
2) Click en “Carátula Institucional”.  
3) Confirmar que el modal muestra datos del JSON del formato.

---

## Cache de DOCX y PDF

El sistema cachea los archivos generados en:

```
app/.cache/
├── docx/
│   └── {format_id}.docx
└── pdf/
    ├── {format_id}-{hash}.pdf
    └── {format_id}.manifest.json
```

### Criterios de Frescura

El cache se invalida si:

1. **mtime del JSON fuente** es más nuevo que el cache.
2. **mtime del script generador** es más nuevo que el cache.
3. **mtime de archivos core** (loaders.py, service.py) cambia.

**Fuente:** `app/modules/formats/router.py` L86-92, L281-317

```python
def _is_cache_fresh(path: Path, source_mtime: float) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size <= 0:
        return False
    return path.stat().st_mtime >= source_mtime
```

### Hash del PDF

El nombre del PDF incluye un hash SHA256 del DOCX fuente:

```
unac-informe-cual-abc123def456.pdf
```

Esto asegura que si el DOCX cambia, el PDF también se regenera.

**Fuente:** `app/modules/formats/router.py` L70-76

---

## Servicio: `generate_document()`

```python
def generate_document(format_id: str, section_filter: Optional[str] = None):
    item = find_format_index(format_id)
    provider = get_provider(item.uni)
    generator = provider.get_generator_command(item.categoria)
    
    # Ejecuta el generador
    cmd, workdir = _resolve_generator_command(generator, json_path, output_path)
    result = subprocess.run(cmd, cwd=str(workdir), capture_output=True, text=True)
    
    return output_path, filename
```

**Fuente:** `app/modules/formats/service.py` L132-213

### Filtro de Secciones (Vista Previa)

El parámetro `section_filter="planteamiento"` permite generar un DOCX solo con el Capítulo I:

```python
if section_filter == "planteamiento":
    data["preliminares"] = {}
    data["finales"] = {}
    data["cuerpo"] = [cap for cap in data.get("cuerpo", [])
                      if "PLANTEAMIENTO" in cap.get("titulo", "").upper()]
```

**Fuente:** `app/modules/formats/service.py` L157-184

---

## Manifest de Cache

Para cada PDF cacheado, se genera un manifest JSON con información de depuración:

```json
{
  "format_id": "unac-informe-cual",
  "json_path": "app/data/unac/informe/...",
  "json_mtime": 1234567890.0,
  "generator_script_path": "app/universities/unac/centro_formatos/...",
  "generator_mtime": 1234567890.0,
  "created_at": "Mon, 01 Jan 2026 00:00:00 GMT",
  "docx_path": "...",
  "pdf_path": "...",
  "docx_sha256": "abc123...",
  "sha256_pdf": "def456..."
}
```

**Fuente:** `app/modules/formats/router.py` L165-192
