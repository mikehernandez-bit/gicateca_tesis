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
├── format-viewer.js    # Vista detalle (~33KB)
├── navigation.js       # Navegación (~1KB)
└── references.js       # UI de referencias (~22KB)
```

**Fuente:** `app/static/js/` (4 archivos)

---

## format-viewer.js — Vista Previa de Carátula ("Ojo")

### Descripción

Este archivo maneja toda la lógica de la vista de detalle de formatos, incluyendo:

1. **Descarga de DOCX** (`downloadDocument`)
2. **Vista previa PDF** (`openPdfModal`)
3. **Vista previa de Carátula** (`previewCover`)
4. **Vista previa de Índice** (`previewIndex`)
5. **Vista previa de Capítulos** (`previewChapter`)

### Carátula (previewCover)

Cuando el usuario hace clic en el "ojo" de carátula:

1. Se abre un modal.
2. Se llama a `/formatos/{format_id}/data` para obtener el JSON.
3. Se extraen los campos de `data.caratula`.
4. Se renderiza la carátula con:
   - Logo (según universidad: UNAC o UNI).
   - Universidad, facultad, escuela.
   - Título, frase de grado, autor, asesor.
   - Lugar y año.

**Fuente:** `app/static/js/format-viewer.js` L104-195

```javascript
async function previewCover(formatId) {
    const data = await fetchFormatJson(formatId);
    const c = data.caratula || {};
    
    // Selección de logo
    if (formatId.toLowerCase().startsWith('uni')) {
        logoImg.src = "/static/assets/LogoUNI.png";
    } else {
        logoImg.src = "/static/assets/LogoUNAC.png";
    }
    
    // Renderizado de campos...
}
```

### Índice (previewIndex)

Construye una tabla de contenidos inteligente:

1. Si existe `data.estructura`, la usa directamente.
2. Si no, infiere desde `data.cuerpo` o `data.secciones`.
3. Renderiza con niveles jerárquicos (Capítulo, Sección, Subsección).

**Fuente:** `app/static/js/format-viewer.js` L202-372

### Capítulos (previewChapter)

Muestra el detalle de un capítulo específico:

1. Busca el capítulo en `data.cuerpo`, `data.secciones` o `data.finales`.
2. Renderiza según el tipo de contenido:
   - Lista de contenidos.
   - Items/subitems jerárquicos.
   - Instrucción + lista.
   - Texto simple.

**Fuente:** `app/static/js/format-viewer.js` L379-567

---

## catalog.js — Filtros del Catálogo

Maneja:
- Filtros por universidad.
- Filtros por tipo de formato.
- Búsqueda por texto.

**Fuente:** `app/static/js/catalog.js` (~16KB)

---

## references.js — UI de Referencias

Maneja:
- Carga dinámica de normas via `/api/referencias`.
- Expansión de detalles.
- Filtros por tags.

**Fuente:** `app/static/js/references.js` (~22KB)
