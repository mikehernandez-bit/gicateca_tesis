# Frontend: Templates y JavaScript

## Templates Jinja2

### Ubicación

```
app/templates/
├── base.html              # Layout principal
├── components/            # Componentes reutilizables
│   └── ...
└── pages/                 # Páginas
    ├── admin.html         # Panel admin
    ├── alerts.html        # Alertas
    ├── catalog.html       # Catálogo (~12KB)
    ├── detail.html        # Detalle de formato (~15KB)
    ├── home.html          # Inicio (~5KB)
    ├── references.html    # Referencias (~4KB)
    └── versions.html      # Versiones (~2KB)
```

**Fuente:** `app/templates/pages/` (7 archivos)

### Template Base

`base.html` define el layout común:
- Header con navegación.
- Contenedor principal.
- Footer.
- Inclusión de CSS/JS comunes.

**Fuente:** `app/templates/base.html` (~1.5KB)

---

## JavaScript Principal

### Ubicación

```
app/static/js/
├── catalog.js          # UI del catálogo (~16KB)
├── cover-preview.js    # Modal unificado de carátula (~8.5KB)
├── format-viewer.js    # Vista detalle (~33KB)
├── navigation.js       # Navegación (~1KB)
└── references.js       # UI de referencias (~22KB)
```

**Fuente:** `app/static/js/` (5 archivos)

---

## Carátula unificada (modal + JS único)

### Componente: `components/cover_modal.html`
- Fuente única del modal HTML de carátula.
- IDs esperados por el controlador: `c-uni`, `c-fac`, `c-esc`, `c-logo`, `c-titulo`, `c-guia`, `c-frase`, `c-grado`,
  `c-label-autor`, `c-autor`, `c-label-asesor`, `c-asesor`, `c-lugar`, `c-anio`.

**Fuente:** `app/templates/components/cover_modal.html`

### Controlador: `cover-preview.js`
- API pública global:
  - `window.GicaCover.open(formatId)`
  - `window.GicaCover.close()`
- Compatibilidad: `window.previewCover(formatId)` es alias de `GicaCover.open`.
- Reglas de logo:
  1) `data.configuracion.ruta_logo` (si existe y se normaliza)
  2) fallback a `/static/assets/LogoUNI.png` o `/static/assets/LogoUNAC.png` según universidad.
- Universidad se resuelve con prioridad:
  1) `data._meta.uni`
  2) prefijo del `formatId`
  3) default `unac`
- Cache-buster en JSON de formato: `/formatos/{id}/data?t=...`

**Fuente:** `app/static/js/cover-preview.js`

### Integraciones
- `catalog.html` y `detail.html` **incluyen** el componente `components/cover_modal.html`.
- `catalog.html` y `detail.html` **cargan** `cover-preview.js` antes de sus JS específicos.
- `catalog.js` y `format-viewer.js` delegan a `GicaCover`.

**Archivos involucrados**
- `app/templates/components/cover_modal.html`
- `app/static/js/cover-preview.js`
- `app/templates/pages/catalog.html`
- `app/templates/pages/detail.html`
- `app/static/js/catalog.js`
- `app/static/js/format-viewer.js`

**Cómo probar**
1) Abrir `/catalog` → modo Carátulas → “Ver Carátula”.
2) Abrir `/formatos/{id}` → “Carátula Institucional”.
3) Verificar que ambos modales muestran el mismo contenido y logo.

## format-viewer.js — Vista Detalle (PDF/Índice/Capítulos)

### Descripción

Este archivo maneja toda la lógica de la vista de detalle de formatos, incluyendo:

1. **Descarga de DOCX** (`downloadDocument`)
2. **Vista previa PDF** (`openPdfModal`)
3. **Vista previa de Carátula** (`previewCover`)
4. **Vista previa de Índice** (`previewIndex`)
5. **Vista previa de Capítulos** (`previewChapter`)

### Carátula (previewCover)

`format-viewer.js` **ya no renderiza** la carátula por sí mismo. En su lugar, delega la apertura del modal al controlador unificado `cover-preview.js`:

```javascript
async function previewCover(formatId) {
    if (window.GicaCover && window.GicaCover.open) {
        return window.GicaCover.open(formatId);
    }
    console.error('GicaCover no disponible');
}
```

**Fuente:** `app/static/js/format-viewer.js` (función `previewCover`)

### Índice (previewIndex)

Construye una tabla de contenidos inteligente:

1. Si existe `data.estructura`, la usa directamente.
2. Si no, infiere desde `data.cuerpo` o `data.secciones`.
3. Renderiza con niveles jerárquicos (Capítulo, Sección, Subsección).

**Fuente:** `app/static/js/format-viewer.js` (función `previewIndex`)

### Capítulos (previewChapter)

Muestra el detalle de un capítulo específico:

1. Busca el capítulo en `data.cuerpo`, `data.secciones` o `data.finales`.
2. Renderiza según el tipo de contenido:
   - Lista de contenidos.
   - Items/subitems jerárquicos.
   - Instrucción + lista.
   - Texto simple.

**Fuente:** `app/static/js/format-viewer.js` (función `previewChapter`)

---

## catalog.js — Filtros del Catálogo

Maneja:
- Filtros por universidad.
- Filtros por tipo de formato.
- Búsqueda por texto.
- Vista previa de carátula en modo Carátulas delegando a `window.GicaCover`.

**Fuente:** `app/static/js/catalog.js` (~13KB)

---

## references.js — UI de Referencias

Maneja:
- Carga dinámica de normas via `/api/referencias`.
- Expansión de detalles.
- Filtros por tags.

**Fuente:** `app/static/js/references.js` (~22KB)
