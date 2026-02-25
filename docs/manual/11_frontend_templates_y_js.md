# Frontend: Templates y JavaScript

## Templates Jinja2

### Ubicacion

```
app/templates/
+-- base.html              # Layout principal (~2KB)
+-- components/            # Componentes reutilizables
|   +-- cover_modal.html   # Modal de caratula (~5KB)
|   +-- header.html        # Header/navegacion (~1KB)
|   `-- sidebar.html       # Sidebar (~3KB)
`-- pages/                 # Paginas
    +-- admin.html         # Panel admin (~2KB)
    +-- alerts.html        # Alertas (~2KB)
    +-- catalog.html       # Catalogo (~10KB)
    +-- detail.html        # Detalle de formato (~12KB)
    +-- home.html          # Inicio (~5KB)
    +-- references.html    # Referencias (~4KB)
    `-- versions.html      # Versiones (~2KB)
```

**Fuente:** `app/templates/` (3 componentes + 7 paginas)

### Template Base

`base.html` define el layout comun:
- Header con navegacion.
- Contenedor principal.
- Footer.
- Inclusion de CSS/JS comunes.

**Fuente:** `app/templates/base.html` (~2KB)

---

## JavaScript

### Ubicacion

```
app/static/js/
+-- catalog.js          # UI del catalogo (~13KB)
+-- cover-preview.js    # Modal unificado de caratula (~7KB)
+-- format-viewer.js    # Vista detalle (~30KB)
+-- gica-api.js         # Helpers API centralizados (~3KB)
+-- gica-dom.js         # Helpers DOM centralizados (~3KB)
+-- navigation.js       # Navegacion (~1KB)
`-- references.js       # UI de referencias (~22KB)
```

**Fuente:** `app/static/js/` (7 archivos)

---

## Helpers Centralizados (Fase 1)

### gica-dom.js

Helpers DOM reutilizables para evitar duplicacion entre modulos:
- Funciones de creacion de elementos
- Manipulacion de clases y estilos
- Utilidades de query

**Fuente:** `app/static/js/gica-dom.js` (~3KB)

### gica-api.js

Helpers API centralizados:
- Funciones fetch con manejo de errores
- Utilidades de request/response

**Fuente:** `app/static/js/gica-api.js` (~3KB)

---

## Caratula unificada (modal + JS unico)

### Componente: `components/cover_modal.html`
- Fuente unica del modal HTML de caratula.
- IDs esperados por el controlador: `c-uni`, `c-fac`, `c-esc`, `c-logo`, `c-titulo`, `c-guia`, `c-frase`, `c-grado`,
  `c-label-autor`, `c-autor`, `c-label-asesor`, `c-asesor`, `c-lugar`, `c-anio`.

**Fuente:** `app/templates/components/cover_modal.html`

### Controlador: `cover-preview.js`
- API publica global:
  - `window.GicaCover.open(formatId)`
  - `window.GicaCover.close()`
- Compatibilidad: `window.previewCover(formatId)` es alias de `GicaCover.open`.
- Reglas de logo:
  1) `data.configuracion.ruta_logo` (si existe y se normaliza)
  2) fallback a `/static/assets/LogoUNI.png` o `/static/assets/LogoUNAC.png` segun universidad.
- Universidad se resuelve con prioridad:
  1) `data._meta.uni`
  2) prefijo del `formatId`
  3) default `unac`
- Cache-buster en JSON de formato: `/formatos/{id}/data?t=...`

**Fuente:** `app/static/js/cover-preview.js`

### Integraciones
- `catalog.html` y `detail.html` **incluyen** el componente `components/cover_modal.html`.
- `catalog.html` y `detail.html` **cargan** `cover-preview.js` antes de sus JS especificos.
- `catalog.js` y `format-viewer.js` delegan a `GicaCover`.

**Archivos involucrados**
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/templates/pages/catalog.html`
- `app/templates/pages/detail.html`
- `app/static/js/catalog.js`
- `app/static/js/format-viewer.js`

**Como probar**
1) Abrir `/catalog` -> modo Caratulas -> "Ver Caratula".
2) Abrir `/formatos/{id}` -> "Caratula Institucional".
3) Verificar que ambos modales muestran el mismo contenido y logo.

## format-viewer.js -- Vista Detalle (PDF/Indice/Capitulos)

### Descripcion

Este archivo maneja toda la logica de la vista de detalle de formatos, incluyendo:

1. **Descarga de DOCX** (`downloadDocument`)
2. **Vista previa PDF** (`openPdfModal`)
3. **Vista previa de Caratula** (`previewCover`)
4. **Vista previa de Indice** (`previewIndex`)
5. **Vista previa de Capitulos** (`previewChapter`)

### Caratula (previewCover)

`format-viewer.js` **ya no renderiza** la caratula por si mismo. En su lugar, delega la apertura del modal al controlador unificado `cover-preview.js`:

```javascript
async function previewCover(formatId) {
    if (window.GicaCover && window.GicaCover.open) {
        return window.GicaCover.open(formatId);
    }
    console.error('GicaCover no disponible');
}
```

**Fuente:** `app/static/js/format-viewer.js` (funcion `previewCover`)

### Indice (previewIndex)

Construye una tabla de contenidos inteligente:

1. Si existe `data.estructura`, la usa directamente.
2. Si no, infiere desde `data.cuerpo` o `data.secciones`.
3. Renderiza con niveles jerarquicos (Capitulo, Seccion, Subseccion).

**Fuente:** `app/static/js/format-viewer.js` (funcion `previewIndex`)

### Capitulos (previewChapter)

Muestra el detalle de un capitulo especifico:

1. Busca el capitulo en `data.cuerpo`, `data.secciones` o `data.finales`.
2. Renderiza segun el tipo de contenido:
   - Lista de contenidos.
   - Items/subitems jerarquicos.
   - Instruccion + lista.
   - Texto simple.

**Fuente:** `app/static/js/format-viewer.js` (funcion `previewChapter`)

---

## catalog.js -- Filtros del Catalogo

Maneja:
- Filtros por universidad.
- Filtros por tipo de formato.
- Busqueda por texto.
- Vista previa de caratula en modo Caratulas delegando a `window.GicaCover`.

**Fuente:** `app/static/js/catalog.js` (~13KB)

---

## references.js -- UI de Referencias

Maneja:
- Carga dinamica de normas via `/api/referencias`.
- Expansion de detalles.
- Filtros por tags.

**Fuente:** `app/static/js/references.js` (~22KB)
