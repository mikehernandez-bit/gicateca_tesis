# Formatos: Detalle y Exportacion

## Descripcion

El modulo **formats** maneja la vista de detalle de un formato especifico, la generacion de DOCX, la conversion a PDF y la exposicion del JSON para previsualizaciones.

---

## Endpoints

### GET `/formatos/{format_id}`

Renderiza el detalle de un formato.

**Fuente:** `app/modules/formats/router.py`

### POST `/formatos/{format_id}/generate`

Genera un DOCX para el formato solicitado.

**Response:** Archivo DOCX para descarga.

**Fuente:** `app/modules/formats/router.py`

### GET `/formatos/{format_id}/pdf`

Genera el DOCX, lo convierte a PDF y lo devuelve.

**Headers de Cache:**
- `ETag`: SHA256 del DOCX (primeros 16 caracteres)
- `Cache-Control`: `no-store` (para forzar regeneracion si cambia)

**Fuente:** `app/modules/formats/router.py`

### GET `/formatos/{format_id}/data`

Devuelve el contenido JSON completo del formato.

**Uso:** Para hidratar vistas dinamicas (caratula, indice, capitulos).

**Fuente:** `app/modules/formats/router.py`

---

## Vista previa de caratula (HTML)

En la vista de detalle, el boton **"Caratula Institucional"** abre el **modal unificado** de caratula (HTML), controlado por `cover-preview.js`.

Flujo:
1. `detail.html` incluye `components/cover_modal.html`.
2. `cover-preview.js` expone `window.GicaCover.open(formatId)`.
3. `format-viewer.js` delega el preview al controlador unificado.

**Archivos involucrados**
- `app/templates/pages/detail.html`
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/static/js/format-viewer.js`

**Como probar**
1) Abrir `/formatos/{id}`.
2) Click en "Caratula Institucional".
3) Confirmar que el modal muestra datos del JSON del formato.

---

## Cache de DOCX y PDF

El sistema cachea los archivos generados en:

```
app/.cache/
+-- docx/
|   `-- {format_id}.docx
`-- pdf/
    +-- {format_id}-{hash}.pdf
    `-- {format_id}.manifest.json
```

### Criterios de Frescura

El cache se invalida si:

1. **mtime del JSON fuente** es mas nuevo que el cache.
2. **mtime del script generador** es mas nuevo que el cache.
3. **mtime de archivos core** (loaders.py, service.py) cambia.

**Fuente:** `app/modules/formats/router.py`

### Hash del PDF

El nombre del PDF incluye un hash SHA256 del DOCX fuente:

```
unac-informe-cual-abc123def456.pdf
```

Esto asegura que si el DOCX cambia, el PDF tambien se regenera.

---

## Generacion de Documentos

La generacion utiliza el **Block Engine** (`app/engine/`):

1. **Service** busca el formato y resuelve el provider.
2. **Provider** retorna la ruta al generador (`universal_generator.py`).
3. **Generador unificado** lee el JSON y usa el Block Engine:
   - `normalizer.py` convierte JSON -> `List[Block]`
   - `registry.py` invoca renderers por tipo
   - Renderers producen contenido DOCX
4. El DOCX resultante se retorna como `FileResponse`.
5. `BackgroundTasks` limpia el temporal despues.

**Fuente:** `app/universities/shared/universal_generator.py`, `app/engine/`

---

## Manifest de Cache

Para cada PDF cacheado, se genera un manifest JSON con informacion de depuracion:

```json
{
  "format_id": "unac-informe-cual",
  "json_path": "app/data/unac/informe/...",
  "json_mtime": 1234567890.0,
  "generator_script_path": "app/universities/shared/universal_generator.py",
  "generator_mtime": 1234567890.0,
  "created_at": "Mon, 01 Jan 2026 00:00:00 GMT",
  "docx_path": "...",
  "pdf_path": "...",
  "docx_sha256": "abc123...",
  "sha256_pdf": "def456..."
}
```

**Fuente:** `app/modules/formats/router.py`
